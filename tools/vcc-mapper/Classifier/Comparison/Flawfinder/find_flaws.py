import glob
import subprocess
import os

commits = [x[-45:-5] for x in glob.glob("/home/rappy/Uni/WS1920/Bachelorarbeit/vcc-mapper/Classifier/Testing/unclassified/linux/*.json")]
vc = open("unclassified.txt", "w+")

count = 0
for commit in commits:
    print(str(count)+"/"+str(len(commits)))
    vulnerable = False
    output = subprocess.check_output(["./find_flaws.sh", commit])
    if ":" in str(output):
        vulnerable = True
    if vulnerable:
        vc.write(str(commit) + " is vulnerable.\n")
    count += 1

