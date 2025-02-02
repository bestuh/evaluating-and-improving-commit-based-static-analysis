from git import Repo

repo = Repo("~/Repos/FFmpeg")

com = ""
length = 0
with open("ffmpeg_mappings.txt", "r+") as m:
    for mapping in m.readlines():
        commit = mapping.split("  ")[1]
        commit = repo.commit(commit)
        print(commit.hexsha)
        if length < len(repo.git.show(commit).split("\n")):
            length = len(repo.git.show(commit).split("\n"))
            com = commit.hexsha
print(length)
print(com)
