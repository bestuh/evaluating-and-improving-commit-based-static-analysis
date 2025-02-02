import git

class CommitMapping:
    def __init__(self, commit: git.Commit, mapping_type: str) -> None:
        self.id = commit.hexsha
        self.commit = commit
        self.cves = []
        self.vccs = []
        self.mapping_type = mapping_type
