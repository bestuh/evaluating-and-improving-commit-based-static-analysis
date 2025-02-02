from RepositoryMining.VccMapper import VccMapper
from RepositoryMining.VuldiggerHeuristic2 import VuldiggerHeuristic2
from RepositoryMining.OwnHeuristic import OwnHeuristic

def main():
    heuristic = VuldiggerHeuristic2()
    mapper = VccMapper("/path/to/repositories/FFmpeg", heuristic)

    vccs_cve20122798 = mapper.map_fixing_commit_to_vccs("d05f72c75445969cd7bdb1d860635c9880c67fb6", "CVE-2012-2798")
    print(vccs_cve20122798)

if __name__ == "__main__":
    main()
