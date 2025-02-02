# vcc-mapper

This repository contains tools to identify commits that fixed vulnerabilities (fixing commits), tools to map fixing commits to possible Vulnerability Contributing Commits (VCCs), as well as tools to study the lifetime of such vulnerabilities. These tools were created over the course of Manuel Bracks and Jan Philipp Wagners Bachelor Thesis that can be found in the Thesis directory.

## Table of Contents
- [Heuristic](#heuristic)
- [Authors](#authors)

## Heuristic
### VccMapper class
A simple example of how this class is used can be found in main.
```
VccMapper(repo_path, heuristic)
```
repo_path - Path to the git repository of the examined vulnerability\
heuristic - The heuristic used for mapping a fixing commit to VCCs. Different heuristics can be found in the RepositoryMining directory. The most relevant heuristics are VuldiggerHeuristic2 (used for Manuels thesis and the paper) and OwnHeuristic (used for Jans thesis). Other heuristics would need a little bit of tweaking to work with the current setup of the VccMapper class, let me know if they are of interest.

#### The map_fixing_commit_to_vccs Method
```
map_fixing_commit_to_vccs(self, fixing_commit, cve)
```
fixing_commit - The/one of the fixing commit(s) of the examined vulnerability\
cve - The CVE-ID of the examined vulnerability

Returns a dictonary containing possible VCCs as values and how many times these commits were blamed as keys (as well as a confidence value when using OwnHeuristic).


## Authors
* Manuel Brack - Initial work - [manuelbrack](https://github.com/manuelbrack)
* Jan Philipp Wagner - Initial work - [jpwagner](https://github.com/jp-wagner)