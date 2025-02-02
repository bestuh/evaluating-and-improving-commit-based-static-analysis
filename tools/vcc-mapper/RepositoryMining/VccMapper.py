from git import Repo, GitCommandError
from collections import defaultdict
import re
import time
import subprocess
import os
from multiprocessing import Process, current_process

class VccMapper:

    def __init__(self, repo_path, heuristic):
        self.repo = Repo(repo_path)
        if self.repo.bare:
            raise Exception('Found bare repository under \'{0}\'!'.format(repo_path))

        print('Repo at {} successfully loaded.'.format(repo_path))
        self.heuristic = heuristic

    def map_fixing_commit_to_vccs(self, fixing_commit, cve=None):
        fixing_commit = self.repo.commit(fixing_commit)
        vccs = self.heuristic.use_heuristic(self.repo, fixing_commit, cve)

        return vccs
