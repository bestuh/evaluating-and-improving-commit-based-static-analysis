from git import Repo
import os, glob
import re
import clang.cindex
import random
import ast
import pandas as pd
from tqdm import tqdm
import argparse

import sys
sys.path.append("..")
import file_utils

# filenames for temporary files (without file-extension!)
SNAPSHOT_PATH = "snapshots/"
BEFORE_FILE = "pre_commit"
AFTER_FILE = "post_commit"
PRE = "pre"
POST = "post"

SKIPPED_FILE_EXTENSIONS = set()

#clang.cindex.Config.set_library_file("/usr/lib/llvm-10/lib/libclang.so")

def get_file_contents_at_commit(commit, file_path):
    try:
        return commit.tree[file_path].data_stream.read().decode("utf-8")
    except KeyError:
        print(f"File '{file_path}' does not exist in commit {commit.hexsha}")
        return None
    except UnicodeDecodeError:
        return commit.tree[file_path].data_stream.read().decode("latin-1")
    
def get_and_save_file_contents(commit, file_path_pre, file_path_post):
    # get contents
    file_content_pre = get_file_contents_at_commit(commit.parents[0], file_path_pre) # commit without the changes (i.e. the state before the commit happened)
    file_content_post = get_file_contents_at_commit(commit, file_path_post) # commit with the changes (i.e. the state after the commit)
    # delete old files
    _, file_extension = os.path.splitext(file_path_post)
    old_files = glob.glob(f"{SNAPSHOT_PATH}*")
    for old_file in old_files:
        os.remove(old_file)
    # create new files
    file_hash = str(random.getrandbits(128))
    pre_commit_snapshot = f"{SNAPSHOT_PATH}{BEFORE_FILE}_{file_hash}{file_extension}" 
    post_commit_snapshot = f"{SNAPSHOT_PATH}{AFTER_FILE}_{file_hash}{file_extension}" 
    with open(pre_commit_snapshot, "w") as file:
        file.write(file_content_pre)
    with open(post_commit_snapshot, "w") as file:
        file.write(file_content_post)
    
    return pre_commit_snapshot, post_commit_snapshot

def get_start_and_endline(start, end):
    if end == "0":
        return None, None
    start_line = int(start)
    lines_count = int(end or 1)
    end_line = start_line + lines_count - (1 if lines_count > 0 else 0)
    return start_line, end_line

          
def extract_context(hunks_per_file, file_path, snapshot_version, snapshot_path, include_doc_comments=True, num_context_lines=0):
    index = clang.cindex.Index.create()
    tu = index.parse(snapshot_path)
    with open(snapshot_path, "r", encoding="utf-8", newline="") as file:
        file_contents = file.read()
        file.seek(0)
        lines = file.readlines()

        for line_range, hunk_snapshots in hunks_per_file[file_path].items():
            line_number_start, line_number_end = parse_hunk_line_range(line_range, snapshot_version)
            if line_number_start is None or line_number_end is None:
                hunk_snapshots[snapshot_version] = None
                continue

            # range of the hunk
            from_line = max(0, line_number_start - 1)
            to_line = min(len(lines), line_number_end - 1 + 1)

            # range of the extracted context
            code_snippet = ""
            code_snippet_start_line = from_line
            code_snippet_end_line = from_line
            
            for line_number in range(line_number_start, line_number_end + 1):
                found_function = False
                # try to extract a function for the line
                for node in tu.cursor.walk_preorder():
                    if node.kind == clang.cindex.CursorKind.FUNCTION_DECL and node.extent.start.file.name == snapshot_path:
                        if overlaps(range_a=(line_number, line_number), range_b=(node.extent.start.line, node.extent.end.line)):
                            #print(f"Found {node.spelling} for line {line_number}")

                            function_body = file_contents[node.extent.start.offset:node.extent.end.offset]
                            comment_lines = []
                            if include_doc_comments:
                                for line in reversed(lines[:node.extent.start.line - 1]):
                                    if line.strip() == "" or line.strip().startswith("*") or line.strip().startswith("/*") or line.strip().startswith("*/") or line.strip().startswith("#"):
                                        comment_lines.append(line.strip())
                                    else:
                                        break
                                doc_comment = "\n".join(reversed(comment_lines)).strip()
                                doc_comment = doc_comment if doc_comment != "" else None
                            function_code = doc_comment + "\n" + function_body if (include_doc_comments and doc_comment is not None) else function_body
                            code_snippet = add_context_element_to_code_snippet(
                                (code_snippet, code_snippet_start_line, code_snippet_end_line), 
                                (function_code, node.extent.start.line - len(comment_lines), node.extent.end.line)
                            )
                            code_snippet_start_line = min(from_line, node.extent.start.line - len(comment_lines))
                            code_snippet_end_line = max(to_line, node.extent.end.line)
                            found_function = True
                        elif node.extent.start.line > line_number_end:
                            break
                
                # if that did not work, extract the raw change with some surrounding lines as context
                if not found_function and "".join(lines[line_number - 1:line_number]).strip() != "": # no function and not just an empty line
                    from_line_raw_context = max(0, line_number - 1 - num_context_lines)
                    to_line_raw_context = min(len(lines), line_number - 1 + 1 + num_context_lines)
                    raw_context = "".join(lines[from_line_raw_context:to_line_raw_context])
                    code_snippet = add_context_element_to_code_snippet(
                        (code_snippet, code_snippet_start_line, code_snippet_end_line), 
                        (raw_context, from_line_raw_context, to_line_raw_context)
                    )
                    code_snippet_start_line = min(from_line, from_line_raw_context)
                    code_snippet_end_line = max(from_line, to_line_raw_context)
            
            hunk_snapshots[snapshot_version] = code_snippet
        
        return hunks_per_file
    
def parse_hunk_line_range(line_range, snapshot_version):
    line_range = line_range.split("|")
    line_range_index = 0 if snapshot_version == PRE else 1
    line_number_start, line_number_end = line_range[line_range_index].split("-")
    line_number_start = int(line_number_start) if line_number_start != "None" else None
    line_number_end = int(line_number_end) if line_number_end != "None" else None
    return line_number_start, line_number_end

def overlaps(range_a: tuple, range_b: tuple):
    return range_a[0] <= range_b[1] and range_a[1] >= range_b[0]

def add_context_element_to_code_snippet(code_snippet: tuple, context_element: tuple):
    code_snippet, code_snippet_start_line, code_snippet_end_line = code_snippet
    context_element, context_element_start_line, context_element_end_line = context_element
    merged = code_snippet

    # if the context-element peaks out the top of the actual code snippet, prepend the uncontained parts
    if context_element_start_line < code_snippet_start_line:
        context_element_slice = "".join(context_element.splitlines(True)[:code_snippet_start_line-context_element_start_line])
        merged = context_element_slice + merged
    # if the context-element peaks out the bottom of the actual code snippet, append the uncontained parts
    if context_element_end_line > code_snippet_end_line:
        context_element_slice = "".join(context_element.splitlines(True)[-(context_element_end_line-code_snippet_end_line):])
        merged += context_element_slice

    return merged

def merge_line_ranges(line_start_a, line_end_a, line_start_b, line_end_b):
    new_line_start = choose_line_number(line_start_a, line_start_b, get_min=True)
    new_line_end = choose_line_number(line_end_a, line_end_b, get_min=False)
    return new_line_start, new_line_end

def choose_line_number(line_number_a, line_number_b, get_min: bool):
    if line_number_a is None and line_number_b is None: return None
    elif line_number_a is None: return line_number_b
    elif line_number_b is None: return line_number_a
    elif get_min: return min(line_number_a, line_number_b)
    else: return max(line_number_a, line_number_b)

def hunk_snapshots_equal(hunk_snapshots_a, hunk_snapshots_b):
    hunk_snapshots_equal = hunk_snapshots_a == hunk_snapshots_b
    if not hunk_snapshots_equal:
        pre_equals = hunk_snapshots_a[PRE] == hunk_snapshots_b[PRE]
        pre_is_empty = hunk_snapshots_a[PRE] is None or hunk_snapshots_b[PRE] is None
        post_equals = hunk_snapshots_a[POST] == hunk_snapshots_b[POST]
        post_is_empty = hunk_snapshots_a[POST] is None or hunk_snapshots_b[POST] is None
        hunk_snapshots_equal = (pre_equals and post_is_empty) or (pre_is_empty and post_equals)
    return hunk_snapshots_equal

def merge_hunk_line_range(line_range_a, line_range_b, snapshot_version):
    line_start_a_pre, line_end_a_pre = parse_hunk_line_range(line_range_a, snapshot_version)
    line_start_b_pre, line_end_b_pre = parse_hunk_line_range(line_range_b, snapshot_version)
    return merge_line_ranges(
        line_start_a_pre, line_end_a_pre,
        line_start_b_pre, line_end_b_pre
    )

def merge_hunk_line_ranges(line_range_a, line_range_b):
    new_line_start_pre, new_line_end_pre = merge_hunk_line_range(line_range_a, line_range_b, PRE)
    new_line_start_post, new_line_end_post = merge_hunk_line_range(line_range_a, line_range_b, POST)
    return f"{new_line_start_pre}-{new_line_end_pre}|{new_line_start_post}-{new_line_end_post}"

def get_changed_functions(commit_id, repository_path):
    #print(f"Extracting changed functions for commit {commit_id} from repository {repository_path}")
    
    # get the commit
    repo = Repo(repository_path)
    commit = repo.commit(commit_id)
    first_parent = commit.parents[0]
    diff = first_parent.diff(commit, create_patch=True, unified=0)

    hunks_per_file = {}
    # iterate over the changes
    num_files = sum(1 for _ in diff.iter_change_type("M"))
    if num_files > 200:
        print(f"Skipping commit {commit_id} because it has {num_files} (>200) changed files")
        return None

    for change in tqdm(diff.iter_change_type("M"), desc="Files", total=num_files):
        # get the file that the change is associated with
        _, file_extension = os.path.splitext(change.b_path)
        if (file_extension.lower() not in [".c", ".cc", ".cpp", ".cxx", ".cc", ".o", ".h", ".c++"]):
            SKIPPED_FILE_EXTENSIONS.add(file_extension.lower())
            continue

        #if (change.b_path != change.a_path):
        #    print(f"Commit {commit.hexsha}: file {change.a_path} was renamed to {change.b_path} or something")
        #    #exit()
        file_path = change.b_path


        # saves a version of the file before and after the commit
        pre_commit_snapshot_path, post_commit_snapshot_path = get_and_save_file_contents(commit, change.a_path, change.b_path) 
        
        # get the changes in this file
        patch = change.diff.decode("utf-8")
        #print(patch)

        hunks_per_file[file_path] = {
            #"<start_pre>-<end_pre>|<start_post>-<end_post>": <hunk_contents>,
            #"<start_pre>-<end_pre>|<start_post>-<end_post>": <hunk_contents>
        }
        # for each of the changed lines, get the name of the function that was changed
        hunk_regex = re.compile(r"@@ -(\d+),?(\d+)? \+(\d+),?(\d+)? @@")
        for match in hunk_regex.finditer(patch):
            deletion_start_line, deletion_end_line = get_start_and_endline(match.group(1), match.group(2))
            addition_start_line, addition_end_line = get_start_and_endline(match.group(3), match.group(4))
            is_deletion = deletion_start_line is not None and deletion_end_line is not None
            is_addition = addition_start_line is not None and addition_end_line is not None
            #print(f"Deletion: from line {deletion_start_line} to {deletion_end_line} {'=> no deletion' if not is_deletion else ''}")
            #print(f"Addition: from line {addition_start_line} to {addition_end_line} {'=> no addition' if not is_addition else ''}")
            
            hunk_contents = {
                # {"pre": "<code>", "post": "<code>"}
                PRE: {},
                POST: {}
            }
            hunks_per_file[file_path][f"{deletion_start_line}-{deletion_end_line}|{addition_start_line}-{addition_end_line}"] = hunk_contents

        hunks_per_file = extract_context(hunks_per_file, file_path, PRE, pre_commit_snapshot_path, include_doc_comments=True, num_context_lines=3)
        hunks_per_file = extract_context(hunks_per_file, file_path, POST, post_commit_snapshot_path, include_doc_comments=True, num_context_lines=3)

        checked_all = False
        while not checked_all:
            length = len(hunks_per_file[file_path].copy())
            num_checked = 0
            do_restart = False
            for line_range_a, hunk_snapshots_a in hunks_per_file[file_path].copy().items():
                num_checked += 1
                if do_restart:
                    break
                for line_range_b, hunk_snapshots_b in hunks_per_file[file_path].copy().items():
                    if line_range_a != line_range_b and hunk_snapshots_equal(hunk_snapshots_a, hunk_snapshots_b):
                        #print(f"PRE and POST hunks for {line_range_a} and {line_range_b} are identical. Merging them.")
                        new_line_range = merge_hunk_line_ranges(line_range_a, line_range_b)
                        #print(f"Merged to new key {new_line_range}")
                        # add new entry
                        hunks_per_file[file_path][new_line_range] = {
                            PRE: hunks_per_file[file_path][line_range_a][PRE] if hunks_per_file[file_path][line_range_a][PRE] is not None else hunks_per_file[file_path][line_range_b][PRE],
                            POST: hunks_per_file[file_path][line_range_a][POST] if hunks_per_file[file_path][line_range_a][POST] is not None else hunks_per_file[file_path][line_range_b][POST]
                        }
                        # remove old entries
                        del hunks_per_file[file_path][line_range_a]
                        del hunks_per_file[file_path][line_range_b]
                        # break loop and start over again, so the merged one can be merged as well
                        do_restart = True
                        break
            checked_all = num_checked == length

    return hunks_per_file

def show_processed_commit(commit_id, hunks_per_file):
    print("########################################################")
    print("########################################################")
    print(f"Commit: {commit_id}")
    print("# # # # # # # # # # # # # # # # # # # # # # # # # # # # ")
    for file_path, hunk_snapshots in hunks_per_file.items():
        print(f"File: '{file_path}'")
        for line_ranges, snapshots in hunk_snapshots.items():
            print("--------------------------------------------------------")
            print("--------------------------------------------------------")
            print(f"BEFORE/PRE: {line_ranges.split('|')[0]}")
            if snapshots["pre"] is not None:
                print(snapshots["pre"])
            else:
                print("Not found. Probably newly introduced.")
            print("--------------------------------------------------------")
            print(f"AFTER/POST: {line_ranges.split('|')[1]}")
            if snapshots["post"] is not None:
                print(snapshots["post"])
            else:
                print("Not found. Probably deleted.")
        print("# # # # # # # # # # # # # # # # # # # # # # # # # # # # ")

def show_processed(features_file_path: str):
    df = pd.read_csv(features_file_path)
    for _, row in df.iterrows():
        show_processed_commit(row["commit_sha"], ast.literal_eval(row["changed_functions"]))
        exit()

def process_dataset(dataset_path: str, save_to: str, repository_path: str, save_after: int):
    df_dataset = pd.read_csv(dataset_path)
    
    try:
        df_features = pd.read_csv(save_to)
    except FileNotFoundError:
        df_features = pd.DataFrame(columns=["commit_sha", "changed_functions"])

    num_processed = 0
    num_skipped = 0
    for _, row in tqdm(df_dataset.iterrows(), total=len(df_dataset)):
        if row["commit_sha"] in df_features["commit_sha"].values:
            num_skipped += 1
            continue

        try:
            changed_functions = get_changed_functions(row["commit_sha"], f"{repository_path}/{row['project']}")
        except Exception as e:
            print(f"Error while extracting functions for commit {row['commit_sha']}:")
            print(e)
            continue

        df_features = pd.concat([df_features, pd.DataFrame([{
            "commit_sha": row["commit_sha"],
            "changed_functions": changed_functions
        }])], ignore_index=True)
        num_processed += 1

        if num_processed % save_after == 0:
            df_features.to_csv(save_to, index=False)
        
    print(f"Processed {num_processed} commits (skipped {num_skipped}) of {len(df_dataset)} total")
    df_features.to_csv(save_to, index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-dataset-path", type=str, help="Path to the dataset file containing the commit-shas.")
    parser.add_argument("-save-path", type=str, help="Path to the file that the extracted features will be saved to.")
    parser.add_argument("-repo-path", type=str, help="Path to the folder, containing the cloned repos.")
    parser.add_argument("-save-after", type=int, default=100, help="Save results after every X extracted commits.")
    args = parser.parse_args()
    
    process_dataset(args.dataset_path, args.save_path, args.repo_path, args.save_after)
    exit()

    #commit_id = "8766dd516c535abf04491dca674d0ef6c95d814f"
    #commit_id = "88db6d1e4f6222d22c1c4b4d4d7166cfa9d2fe0e"
    commit_id = "39d637af5aa7577f655c58b9e55587566c63a0af"
    changed = get_changed_functions(commit_id, repository_path)
    show_processed_commit(commit_id, changed)

    #show_processed(save_to)