import re
import random

commits = []
with open("log.txt", "rb") as history:
        lines = history.readlines()
        for line in lines:
            try:
                line = line.decode()
            except:
                continue
            if re.match(r'commit \b[0-9a-f]{5,40}\b', str(line)):
                commits.append(line[-41:])


with open("unclassified.txt", "a+") as u:
    for x in range(0, 1000):
        u.write(random.choice(commits))
