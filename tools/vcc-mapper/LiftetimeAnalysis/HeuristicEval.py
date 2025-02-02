from datetime import datetime
import numpy as np
path = 'X:/OneDrive/Encrypted/Dokumente/Uni/Master/Semester_1/Paper/heuristic_eval/\heuristic_comparison/lowerbound_httpd.csv'
#path = 'X:/OneDrive/Encrypted/Dokumente/Uni/Master/Semester_1/Paper/heuristic_eval/vuldigger2_httpd.csv'

if __name__ == "__main__":
    with open(path, 'r+') as f:
        fixing_commits_set = set()
        data = []
        for line in f.readlines()[1:]:
            splits = line.split(';')
            data.append(splits)

    correct = 0
    upper_bound = 0
    lower_bound = 0
    vcc_weighted = []
    vcc_most_blamed = []
    for item in data:
        fixing_date = datetime.strptime(item[2][:16], "%Y-%m-%d %H:%M")
        vcc_heuristic_date = datetime.strptime(item[6][:16], "%Y-%m-%d %H:%M")
        #vcc_weighted_date = datetime.strptime(item[12][:16], "%Y-%m-%d %H:%M")
        #vcc_heuristic_oldest_date = datetime.strptime(item[8][:16], "%Y-%m-%d %H:%M")
        #vcc_heuristic_newest_date = datetime.strptime(item[10][:16], "%Y-%m-%d %H:%M")
        vcc_date = datetime.strptime(item[4][:16], "%Y-%m-%d %H:%M")

        lifetime = fixing_date - vcc_date




        # if vcc_heuristic_oldest_date <= vcc_date:
        #     upper_bound += 1
        # else:
        #     print(item[0])
        # if vcc_heuristic_newest_date >= vcc_date:
        #     lower_bound += 1

        if item[3] == item[5]:
            correct += 1
        #
        # if lifetime.days > 0:
        #     delta_b = vcc_date - vcc_heuristic_date
        #     vcc_most_blamed.append(delta_b.days)
        #
        #     delta_w = vcc_date - vcc_weighted_date
        #     vcc_weighted.append(delta_w.days )

    print ("{0} out of {1} mappings correct: {2}%".format(correct, len(data), correct/len(data) * 100))
    print ("{0} out of {1} upper-bounds hold: {2}%".format(upper_bound, len(data), upper_bound/len(data) * 100))
    print ("{0} out of {1} lower-bounds hold: {2}%".format(lower_bound, len(data), lower_bound/len(data) * 100))

    print("W average miss: {0}".format(np.mean(np.abs(vcc_weighted))))
    print("Most blamed miss: {0}".format(np.mean(np.abs(vcc_most_blamed))))
