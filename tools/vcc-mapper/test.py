from git import Repo, GitCommandError, BadName
from db_repository import DBRepository
from RepositoryMining.CommitMappingClass import CommitMapping
from datetime import datetime
from matplotlib import pyplot as plt
from scipy.stats import norm, lognorm
import numpy as np
import math
import statistics
import warnings
from sklearn import datasets, linear_model
import powerlaw
import xml.etree.ElementTree as ET
import xmltodict

from LiftetimeAnalysis.LifetimeEval import LifetimeEval

confidence_size = 20
ground_truth = False

path_kernel_gt = 'C:/Users/manue/OneDrive/Dokumente/Uni/Semester_7/Thesis/Data/V2/kernel_gt_mapped_stable_commitcount.csv'
path_kernel_add = 'C:/Users/manue/OneDrive/Dokumente/Uni/Semester_7/Thesis/Data/V2/kernel_mapped_stable_commitcount.csv'
name = 'kernel'
path_firefox =  'C:/Users/manue/OneDrive/Dokumente/Uni/Semester_7/Thesis/Data/V2/firefox_complete.csv'
#name = 'firefox'
path_chrome =  'C:/Users/manue/OneDrive/Dokumente/Uni/Semester_7/Thesis/Data/V2/chrome_complete.csv'
name = 'chrome'
path_thunderbird =  'C:/Users/manue/OneDrive/Dokumente/Uni/Semester_7/Thesis/Data/V2/thunderbird-mapped.csv'
path_wireshark =  'C:/Users/manue/OneDrive/Dokumente/Uni/Semester_7/Thesis/Data/V2/wireshark_complete.csv'
#name = 'wireshark'
path_openssl =  'C:/Users/manue/OneDrive/Dokumente/Uni/Semester_7/Thesis/Data/V2/openssl_complete.csv'
name = 'openssl'
path_ffmpeg =  'C:/Users/manue/OneDrive/Dokumente/Uni/Semester_7/Thesis/Data/V2/ffmpeg_complete.csv'
name = 'ffmpeg'
path_postgres =  'C:/Users/manue/OneDrive/Dokumente/Uni/Semester_7/Thesis/Data/V2/postgres_complete.csv'
#name = 'postgres'
path_tcpdump = 'C:/Users/manue/OneDrive/Dokumente/Uni/Semester_7/Thesis/Data/V2/tcpdump_complete.csv'
#name = 'TCP Dump'
path_httpd = 'C:/Users/manue/OneDrive/Dokumente/Uni/Semester_7/Thesis/Data/V2/httpd_complete.csv'
name = 'httpd'
#name = 'all'


gt_kernel = 'X:/OneDrive/Encrypted/Dokumente/Uni/Master/Semester_1/Paper/heuristic_eval/heuristic_comparison/vccfinder_kernel.csv'
gt_http = 'X:/OneDrive/Encrypted/Dokumente/Uni/Master/Semester_1/Paper/heuristic_eval/heuristic_comparison/vccfinder_httpd.csv'
gt_chromium = 'X:/OneDrive/Encrypted/Dokumente/Uni/Master/Semester_1/Paper/heuristic_eval/heuristic_comparison/vccfinder_chromium.csv'

gt_kernel = 'X:/OneDrive/Encrypted/Dokumente/Uni/Master/Semester_1/Paper/heuristic_eval/heuristic_comparison/vul2_kernel.csv'
gt_http = 'X:/OneDrive/Encrypted/Dokumente/Uni/Master/Semester_1/Paper/heuristic_eval/heuristic_comparison/vul2_httpd.csv'
gt_chromium = 'X:/OneDrive/Encrypted/Dokumente/Uni/Master/Semester_1/Paper/heuristic_eval/heuristic_comparison/vul2_chromium.csv'

gt_tomcat = 'X:/OneDrive/Encrypted/Dokumente/Uni/Master/Semester_1/Paper/heuristic_eval/vul2_tomcat.csv'
gt_struts = 'X:/OneDrive/Encrypted/Dokumente/Uni/Master/Semester_1/Paper/heuristic_eval/vul2_struts.csv'


path_chrome = './Data/chrome.csv'
path_ffmpeg = './Data/ffmpeg.csv'
path_firefox = './Data/firefox.csv'
path_httpd = './Data/httpd.csv'
path_openssl = './Data/openssl.csv'
path_php = './Data/php.csv'
path_postgres = './Data/postgres.csv'
path_qemu = './Data/qemu.csv'
path_tcpdump = './Data/tcpdump.csv'
path_wireshark = './Data/wireshark.csv'

path_kernel_gt = './Data/kernel_gt_final.csv'
path_kernel = './Data/kernel_add.csv'

if __name__ == "__main__":

    eval_all = LifetimeEval(path_chrome, is_ground_truth_data=False, name='All', only_stable_vuls=False
                            , additional_data=[[False, path_ffmpeg], [False, path_firefox],
                                               [False, path_httpd], [True, path_kernel_gt],
                                               [False, path_kernel], [False, path_openssl],
                                               [False, path_php], [False, path_postgres],
                                               [False, path_qemu], [False, path_tcpdump],
                                               [False, path_wireshark]])
    eval_all.plot_year_trend(lower_limit=2007)
    plt.show()