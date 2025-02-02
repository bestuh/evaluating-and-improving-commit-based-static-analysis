import warnings
from datetime import datetime
from matplotlib import pyplot as plt
import numpy as np
from sklearn import datasets, linear_model
import powerlaw
from scipy.stats import norm, normaltest, percentileofscore, spearmanr, f_oneway, laplace
import scipy.stats as stats
import xmltodict
import math
import csv
import collections
from mlxtend.evaluate import permutation_test
import json
from sklearn.metrics import mean_squared_error
from tqdm import tqdm
import matplotlib.ticker as ticker
import statsmodels.api as sm
from pprint import pprint


cwe_xml_path = "./LifetimeAnalysis/cwe.xml"
regular_lifetime_path = "./LiftetimeAnalysis/codelifetimes.json"

class LifetimeEval:

    def __init__(self, path, is_ground_truth_data=False, only_stable_vuls=False, name='', **kwargs):
        self.path = path
        self.ground_truth = is_ground_truth_data
        self.name = name
        self.stable_vuls = only_stable_vuls

        with open(regular_lifetime_path, 'r+') as regular_lifetimes_file:
            self.regular_lifetimes = json.load(regular_lifetimes_file)

        with open('./LiftetimeAnalysis/cwe.xml', encoding='utf-8')as fd:
            doc = xmltodict.parse(fd.read())

        self.cwe_xml = doc['Weakness_Catalog']
        self.confidence_size = 30


        self.data = []
        self.__normalize(is_ground_truth_data)

        if 'additional_data' in kwargs:
            for additional_mapping in kwargs['additional_data']:
                path = additional_mapping[1]
                self.path = path
                self.__normalize(additional_mapping[0])

        print("Number of CVEs: {0}\n".format(len(self.data)))

        self.new_figure_required = False

    def __normalize(self, ground_truth=False):
        commits = 0
        path = self.path
        cves = {}

        with open(path, 'r+') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=';', quotechar='\'')

            headers_ = next(spamreader, None)
            index = 0
            headers = {}
            for item in headers_:
                headers[item] = index
                index += 1

            for row in spamreader:
                commits += 1

                cve = row[0]
                row_dict = {}
                if cve in cves:
                    #try:
                        if 'Fixing date' in headers and datetime.strptime(cves[cve]['Fixing date'][:16], "%Y-%m-%d %H:%M") < datetime.strptime(row[headers['Fixing date']][:16], "%Y-%m-%d %H:%M"):
                            cves[cve]['Fixing date'] = row[headers['Fixing date']]
                            cves[cve]['Fixing sha'] = row[headers['Fixing sha']]

                        if 'VCC-heuristic date' in headers and datetime.strptime(cves[cve]['VCC-heuristic date'][:16], "%Y-%m-%d %H:%M") > datetime.strptime(row[headers['VCC-heuristic date']][:16], "%Y-%m-%d %H:%M"):
                            cves[cve]['VCC-heuristic date'] = row[headers['VCC-heuristic date']]
                            cves[cve]['VCC-heuristic sha'] = row[headers['VCC-heuristic sha']]

                        if 'VCC-oldest date' in headers and datetime.strptime(cves[cve]['VCC-oldest date'][:16], "%Y-%m-%d %H:%M") > datetime.strptime(row[headers['VCC-oldest date']][:16], "%Y-%m-%d %H:%M"):
                            cves[cve]['VCC-oldest date'] = row[headers['VCC-heuristic date']]
                            cves[cve]['VCC-oldest sha'] = row[headers['VCC-heuristic sha']]

                        if 'VCC-newest date' in headers and datetime.strptime(cves[cve]['VCC-newest date'][:16], "%Y-%m-%d %H:%M") < datetime.strptime(row[headers['VCC-newest date']][:16], "%Y-%m-%d %H:%M"):
                            cves[cve]['VCC-newest date'] = row[headers['VCC-newest date']]
                            cves[cve]['VCC-newest sha'] = row[headers['VCC-newest sha']]

                        if 'Weighted Average date' in headers and datetime.strptime(cves[cve]['Weighted Average date'][:16], "%Y-%m-%d %H:%M") > datetime.strptime(row[headers['Weighted Average date']][:16], "%Y-%m-%d %H:%M"):
                            cves[cve]['Weighted Average date'] = row[headers['Weighted Average date']]

                        if ground_truth:
                            if datetime.strptime(cves[cve]['VCC date'][:16], "%Y-%m-%d %H:%M") > datetime.strptime(row[headers['VCC date']][:16], "%Y-%m-%d %H:%M"):
                                cves[cve]['VCC date'] = row[headers['VCC date']]
                                cves[cve]['VCC sha'] = row[headers['VCC sha']]

                        if 'Commits' in headers:
                            if cves[cve]['Commits'] < int(row[headers['Commits']] if row[headers['Commits']] != '' else '0'):
                                cves[cve]['Commits'] = int(row[headers['Commits']] if row[headers['Commits']] != '' else '0')

                        if 'Commits heuristic' in headers:
                            if cves[cve]['Commits heuristic'] < int(row[headers['Commits heuristic']]):
                                cves[cve]['Commits heuristic'] = int(row[headers['Commits heuristic']])

                        if 'Commmits newest' in headers:
                            if cves[cve]['Commmits newest'] > int(row[headers['Commmits newest']]):
                                cves[cve]['Commmits newest'] = int(row[headers['Commmits newest']])

                        if 'Commits oldest' in headers:
                            if cves[cve]['Commits oldest'] < int(row[headers['Commits oldest']]):
                                cves[cve]['Commits oldest'] = int(row[headers['Commits oldest']])

                        if 'Commits weighted' in headers:
                            if cves[cve]['Commits weighted'] < int(row[headers['Commits weighted']]):
                                cves[cve]['Commits weighted'] = int(row[headers['Commits weighted']])

                        if 'Confident' in headers:
                            cves[cve]['Confident'] = (cves[cve]['Confident'] and (row[headers['Confident']] == 'True'))
                    #except Exception as e:
                    #    warnings.warn('Unable to proccess line {0}:{1}'.format(cve, row[1]))
                else:
                    if self.stable_vuls:
                        stable = row[headers['Stable']]
                        if 'yes' in stable:
                            for header, index in headers.items():
                                row_dict[header] = row[index]
                                if header in ['Commits', 'Commits heuristic', 'Commmits newest', 'Commits oldest', 'Commits weighted']:
                                    try:
                                        row_dict[header] = int(row_dict[header] if row_dict[header] != '' else '0')
                                    except Exception as e:
                                        print("Converstion failed " + str(e))
                                if header in ['Confident']:
                                    try:
                                        row_dict[header] = bool(row_dict[header])
                                    except Exception as e:
                                        print("Converstion failed " + str(e))
                    else:
                        for header, index in headers.items():
                            row_dict[header] = row[index]
                            if header in ['Commits', 'Commits heuristic', 'Commmits newest', 'Commits oldest', 'Commits weighted']:
                                try:
                                    row_dict[header] = int(row_dict[header] if row_dict[header] != '' else '0')
                                except Exception as e:
                                    print("Converstion failed " + str(e))
                            if header in ['Confident']:
                                try:
                                    row_dict[header] = row_dict[header] == 'True'
                                except Exception as e:
                                    print("Converstion failed " + str(e))

                    if len(row_dict) > 0:
                        cves[cve] = row_dict

        print("Number of fixing-commits: {0}".format(commits))
        for key, value in cves.items():
            self.data.append(value)

    def override_data(self, new_data: list):
        self.data = new_data

    def plot_regular_lifetimes(self, config_code, vul_lifetimes = [], x_min=2000, x_max=2020, regressions=[], y_max=0):
        f = plt.figure()
        f.set_figwidth(6)
        f.set_figheight(3)
        self.new_figure_required = True

        x_axis = []
        y_axis = []
        for year_data, year_value in self.regular_lifetimes[config_code].items():
            x_axis.append(int(year_data))
            y_axis.append(year_value)

        i = 0
        for vul in vul_lifetimes:
            if i == 0:
                plt.plot(vul[0], [vul[1] for x in vul[0]], color=(0, 0, 1, 0.7), linewidth=3, label='Vul lifetime')
            else:
                plt.plot(vul[0], [vul[1] for x in vul[0]], color=(0, 0, 1, 0.7), linewidth=3)
            i += 1
        plt.plot(x_axis, y_axis, 'kx', color=(0.8, 0, 0.8, 1), label='Regular code age')

        plt.xticks(range(x_min, x_max, 2))
        plt.ylim(ymin=0)
        plt.xlim((x_min-0.5, x_max+0.5))
        if y_max > 0:
            plt.ylim(ymax=y_max)
        
        
        for reg in regressions:
            regr = linear_model.LinearRegression()
            min = reg[0]
            max = reg[1]
            x_axis = []
            y_axis = []
            for year_data, year_value in self.regular_lifetimes[config_code].items():
                year = int(year_data)
                if min <= year and year <= max:
                    x_axis.append(year)
                    y_axis.append(year_value)
            X = np.array(x_axis).reshape(-1, 1)
            Y = np.array(y_axis)

            regr.fit(X, Y)
            print("{0} - {1} | {2} {3}".format(min, max, regr.score(X, Y), regr.coef_[0]))
            plt.plot(X, regr.predict(X), "k--", color=(0.8, 0, 0.8, 0.6))
        plt.xlabel('Year of fixing commit')
        plt.ylabel('Lifetime in days')
        plt.legend()
        
        #plt.title(config_code)
        plt.savefig('./out/year_trend_regular_{0}.pdf'.format(self.name), bbox_inches='tight')

    def plot_year_trend_custom_buckets(self, bucket_number, plot_linear_fit=False, plot_regular_lifetimes=False):
        
        f = plt.figure()
        self.new_figure_required = True

        #f.set_size_inches(4, 5.2)
        #plt.margins(x=0.3)

        year_data = {}
        year_data_heuristic = {}
        year_data_heuristic_oldest = {}
        year_data_heuristic_newest = {}
        year_data_heuristic_w_average = {}


        diffs_average = []
        diffs_weighted_average = []
        diffs_heuristic = []
        earliest_year = 2100
        latest_year = 1900

        for year in range(1990, 2020):
            for item in self.data:

                fixing_date = datetime.strptime(item['Fixing date'][:16], "%Y-%m-%d %H:%M")

                if fixing_date.year != year:
                    continue

                if fixing_date.year > latest_year:
                    latest_year = fixing_date.year

                if fixing_date.year < earliest_year:
                    earliest_year = fixing_date.year

                #ignore correctly mapped CVEs
                #if item['VCC sha''] == item['VCC-heuristic sha']:
                #   continue
                if 'VCC date' in item:
                    vcc_date = datetime.strptime(item['VCC date'][:16], "%Y-%m-%d %H:%M")
                    delta = fixing_date - vcc_date
                else:
                    delta = None

                vcc_heuristic_date = datetime.strptime(item['VCC-heuristic date'][:16], "%Y-%m-%d %H:%M")
                delta_heuristic = fixing_date - vcc_heuristic_date

                vcc_heuristic_oldest_date = datetime.strptime(item['VCC-oldest date'][:16], "%Y-%m-%d %H:%M")
                delta_heuristic_oldest = fixing_date - vcc_heuristic_oldest_date

                vcc_heuristic_newest_date = datetime.strptime(item['VCC-newest date'][:16], "%Y-%m-%d %H:%M")
                delta_heuristic_newest = fixing_date - vcc_heuristic_newest_date

                if delta is not None and year in year_data:
                    year_data[year].append(delta.days)
                elif delta is not None:
                    year_data[year] = [delta.days]

                if year in year_data_heuristic:
                    year_data_heuristic[year].append(delta_heuristic.days)
                else:
                    year_data_heuristic[year] = [delta_heuristic.days]

                if year in year_data_heuristic_oldest:
                    year_data_heuristic_oldest[year].append(delta_heuristic_oldest.days)
                else:
                    year_data_heuristic_oldest[year] = [delta_heuristic_oldest.days]

                if year in year_data_heuristic_newest:
                    year_data_heuristic_newest[year].append(delta_heuristic_newest.days)
                else:
                    year_data_heuristic_newest[year] = [delta_heuristic_newest.days]

                weighted_average_date = datetime.strptime(item['Weighted Average date'][:16], "%Y-%m-%d %H:%M")
                life_time_weighted_average = fixing_date - weighted_average_date

                if year in year_data_heuristic_w_average:
                    year_data_heuristic_w_average[year].append(life_time_weighted_average.days)
                else:
                    year_data_heuristic_w_average[year] = [life_time_weighted_average.days]

        bucket_size = math.floor( (latest_year - earliest_year) / bucket_number)

        x_axis = []
        y_axis = []
        y_axis_upper = []
        y_axis_lower = []

        y_axis_regular = []

        bucket = 0
        data_points = []
        data_points_upper =[]
        data_points_lower = []

        data_points_regular = []
        x_lables = []

        config_code = self.name
        for key, items in year_data_heuristic_w_average.items():
            if bucket < bucket_size:
                data_points.extend(items)
                data_points_upper.extend(year_data_heuristic_oldest[key])
                data_points_lower.extend(year_data_heuristic_newest[key])

                if plot_regular_lifetimes:
                    data_points_regular.append(self.regular_lifetimes[config_code][str(key)])
                bucket += 1
            else:
                print('{1}-{0}: {2} - {3}'.format(key - 1, key-bucket_size - 1, len(data_points), np.mean(data_points)))
                x_axis.append(key)
                x_lables.append('{1}-{0}'.format(key - 1, key-bucket_size - 1))
                y_axis.append(np.mean(data_points))
                y_axis_upper.append(np.mean(data_points_upper))
                y_axis_lower.append(np.mean(data_points_lower))
                if plot_regular_lifetimes:
                    y_axis_regular.append(np.mean(data_points_regular))

                data_points = items
                data_points_upper = year_data_heuristic_oldest[key]
                data_points_lower = year_data_heuristic_newest[key]
                bucket = 0
            print('{0}: {1}'.format(key, len(items)))



        x_axis.append(key +1)
        y_axis.append(np.mean(data_points))
        y_axis_upper.append(np.mean(data_points_upper))
        y_axis_lower.append(np.mean(data_points_lower))

        y_axis_regular.append(np.mean(data_points_regular))
        x_lables.append('{1}-{0}'.format(key, x_axis[-2:-1][0]))
        print('{1}-{0}: {2} - {3}'.format(key, x_axis[-2:-1][0], len(data_points), np.mean(data_points)))



        plt.plot(x_axis, y_axis, 'b.', label='Weighted average')
        plt.plot(x_axis, y_axis_lower, 'g^', label='Heuristic lower bound')
        plt.plot(x_axis, y_axis_upper, 'rv', label='Heuristic upper bound')
        #plt.xlim((2003.5,2019.5))
        #self.__plot_dict(year_data_heuristic, 'y*', label='Heuristic most blamed')
        plt.xlabel('Year of fixing commit')
        plt.ylabel('Lifetime in days')

        plt.legend()
       # plt.title('Average Vulnerability lifetimes - {0}'.format(self.name))
        plt.xticks(x_axis, x_lables)
        plt.ylim(ymin=0)


        if plot_linear_fit:
            regr = linear_model.LinearRegression()
            X = np.array(x_axis).reshape(-1, 1)
            Y = np.array(y_axis)
            regr.fit(X, Y)
            print(regr.score(X, Y), regr.coef_[0])
            
            x_ = range(len(x_axis))
            pprint(x_)
            pprint(y_axis)
            X_ = sm.add_constant(x_)
            model = sm.OLS(y_axis,X_).fit()
            #predictions = model.predict(X_)
            #plt.plot(predictions)
            #plt.show()
            print(model.summary())
            #print(model.summary().as_latex())

            x_axis_fit = x_axis.copy()
            x_axis_fit.insert(0, x_axis_fit[0] -1)
            x_axis_fit.append(x_axis_fit[len(x_axis_fit)-1] + 1)
            X_fit = np.array(x_axis_fit).reshape(-1, 1)

            plt.plot(x_axis_fit, regr.predict(X_fit), 'k--', color=(0.1, 0.1, 0.1, 0.4))

        if plot_regular_lifetimes:
            plt.plot(x_axis, y_axis_regular, 'kx', color=(0.8, 0, 0.8, 1), label='Regular code age')
            if plot_linear_fit:
                regr_reg = linear_model.LinearRegression()
                Y_reg = np.array(y_axis_regular)

                regr_reg.fit(X, Y_reg)
                print(regr_reg.score(X, Y_reg), regr_reg.coef_[0])

                plt.plot(x_axis_fit, regr_reg.predict(X_fit), color=(0.8, 0.0, 0.8, 0.4))
        f.set_figwidth(9)
        f.set_figheight(6)
        plt.savefig('./out/year_trend_{0}{1}.pdf'.format(self.name, "_with_regular" if plot_regular_lifetimes else ""), bbox_inches='tight')

    def plot_year_trend(self, linear_fit=False, use_commit_numbers=False,  plot_regular_lifetimes=False, restrict_categorie=None, lower_limit=1980, upper_limit=2020, xmin=0, xmax=0, ymax=0, bounds=False, lw=0):

        
        f = plt.figure()
        f.set_figwidth(6)
        f.set_figheight(3)

        
        
        year_data = {}
        year_data_heuristic = {}
        year_data_heuristic_oldest = {}
        year_data_heuristic_newest = {}
        year_data_heuristic_w_average = {}

        year_data_combined = {}
        gt_heuristic_ratio = {}

        diffs_average = []
        diffs_weighted_average = []
        diffs_heuristic = []
        for year in range(lower_limit, upper_limit):
            for item in self.data:

                fixing_date = datetime.strptime(item['Fixing date'][:16], "%Y-%m-%d %H:%M")
                vcc_heuristic_date = datetime.strptime(item['VCC-heuristic date'][:16], "%Y-%m-%d %H:%M")

                if fixing_date.year != year:
                #if vcc_heuristic_date.year != year:
                    continue

                if restrict_categorie is not None:
                    if self.__manual_cve_mappings(item['CWE'].replace('CWE-', '')) != restrict_categorie:
                        continue

                #ignore correctly mapped CVEs
                #if item['VCC sha''] == item['VCC-heuristic sha']:
                #   continue
                if 'VCC date' in item:
                    vcc_date = datetime.strptime(item['VCC date'][:16], "%Y-%m-%d %H:%M")
                    delta = fixing_date - vcc_date
                else:
                    delta = None

                #vcc_heuristic_date = datetime.strptime(item['VCC-heuristic date'][:16], "%Y-%m-%d %H:%M")
                delta_heuristic = fixing_date - vcc_heuristic_date
                if use_commit_numbers:
                    commits_heuristic = item['Commits heuristic']
                    commits_upper = item['Commits oldest']
                    commits_lower = item['Commmits newest']
                    commits_w_average = item['Commits weighted']
                    commit_correct = item['Commits weighted']

                vcc_heuristic_oldest_date = datetime.strptime(item['VCC-oldest date'][:16], "%Y-%m-%d %H:%M")
                delta_heuristic_oldest = fixing_date - vcc_heuristic_oldest_date

                vcc_heuristic_newest_date = datetime.strptime(item['VCC-newest date'][:16], "%Y-%m-%d %H:%M")
                delta_heuristic_newest = fixing_date - vcc_heuristic_newest_date

                if delta is not None and year in year_data:
                    year_data[year].append(delta.days if not use_commit_numbers else commit_correct)
                    year_data_combined[year].append(delta.days if not use_commit_numbers else commit_correct)
                    if year in gt_heuristic_ratio:
                        gt_heuristic_ratio[year][0] += 1
                    else:
                        gt_heuristic_ratio[year] = [1, 0]
                elif delta is not None:
                    year_data[year] = [delta.days if not use_commit_numbers else commit_correct]
                    if year in year_data_combined:
                        year_data_combined[year].append(delta.days if not use_commit_numbers else commit_correct)
                    else:
                        year_data_combined[year] = [delta.days if not use_commit_numbers else commit_correct]
                    if year in gt_heuristic_ratio:
                        gt_heuristic_ratio[year][0] += 1
                    else:
                        gt_heuristic_ratio[year] = [1, 0]

                if year in year_data_heuristic:
                    year_data_heuristic[year].append(delta_heuristic.days if not use_commit_numbers else commits_heuristic)
                else:
                    year_data_heuristic[year] = [delta_heuristic.days if not use_commit_numbers else commits_heuristic]

                if year in year_data_heuristic_oldest:
                    year_data_heuristic_oldest[year].append(delta_heuristic_oldest.days if not use_commit_numbers else commits_upper)
                else:
                    year_data_heuristic_oldest[year] = [delta_heuristic_oldest.days if not use_commit_numbers else commits_upper]

                if year in year_data_heuristic_newest:
                    year_data_heuristic_newest[year].append(delta_heuristic_newest.days if not use_commit_numbers else commits_lower)
                else:
                    year_data_heuristic_newest[year] = [delta_heuristic_newest.days if not use_commit_numbers else commits_lower]

                weighted_average_date = datetime.strptime(item['Weighted Average date'][:16], "%Y-%m-%d %H:%M")
                life_time_weighted_average = fixing_date - weighted_average_date

                if year in year_data_heuristic_w_average:
                    year_data_heuristic_w_average[year].append(life_time_weighted_average.days if not use_commit_numbers else commits_w_average)
                    if delta is None:
                        year_data_combined[year].append(life_time_weighted_average.days if not use_commit_numbers else commits_w_average)
                        if year in gt_heuristic_ratio:
                            gt_heuristic_ratio[year][1] += 1
                        else:
                            gt_heuristic_ratio[year] = [0, 1]
                else:
                    year_data_heuristic_w_average[year] = [life_time_weighted_average.days if not use_commit_numbers else commits_w_average]
                    if delta is None:
                        if year in year_data_combined:
                            year_data_combined[year].append(life_time_weighted_average.days if not use_commit_numbers else commits_w_average)
                        else:
                            year_data_combined[year] = [life_time_weighted_average.days if not use_commit_numbers else commits_w_average]
                        if year in gt_heuristic_ratio:
                            gt_heuristic_ratio[year][1] += 1
                        else:
                            gt_heuristic_ratio[year] = [0, 1]

        #self.__plot_dict(year_data, 'kx',  label='Correct lifetime')
        if bounds:
            #self.__plot_dict(year_data_heuristic_oldest, 'rv', label='Heuristic upper bound')
            self.__plot_dict(year_data_heuristic_newest, 'g^', label='Heuristic lower bound')
        #self.__plot_dict(year_data_heuristic, 'y*', label='Heuristic most blamed')

        self.__plot_dict(year_data_combined, 'bx', True, gt_heuristic_ratio,  label='Vul lifetime')
        
        if lw > 0:
            plt.axvline(0, color='grey', lw=10, alpha=0.5, label='Insufficient data')
            plt.axvline(xmin, color='grey', lw=lw, alpha=0.5)
        if(linear_fit):
            #Fit

            self.__plot_linear_fit(year_data_combined, left_shift=False)


        plt.xlabel('Year of fixing commit')
        plt.ylabel('Lifetime in days' if not use_commit_numbers else 'Lifetime in commits')
        plt.ylim(ymin=0)
        if xmin > 0:
            plt.xlim(xmin=xmin)
        if xmax > 0:
            plt.xlim(xmax=xmax)
        if ymax > 0:
            plt.ylim(ymax=ymax)

        #plt.xlim((2013.5, 2018.5))
        #plt.xticks([2014, 2015, 2016, 2017, 2018], [2014, 2015, 2016, 2017, 2018])
        #plt.xlim(xmax=2018.5)
        #plt.xlim(xmin=2013.5)

        #plt.title('Average Vulnerability lifetimes - {0}'.format(self.name))

        if plot_regular_lifetimes:
            x_axis = []
            y_axis = []
            for year, data in year_data_heuristic_w_average.items():
                if len(data) >= self.confidence_size:
                    x_axis.append(year)
                    y_axis.append(self.regular_lifetimes[self.name][str(year)])

            plt.plot(x_axis, y_axis, 'kx', color=(0.8, 0, 0.8, 1), label="Regular code age")

            regr = linear_model.LinearRegression()
            X = np.array(x_axis).reshape(-1, 1)
            Y = np.array(y_axis)
            regr.fit(X, Y)

            x_axis.append(year + 1)
            x_axis.insert(0, x_axis[0] - 1)
            print(regr.score(X, Y), regr.coef_[0])
            X = np.array(x_axis).reshape(-1, 1)
            if linear_fit:
                plt.plot(x_axis, regr.predict(X), 'k--', color=(0.8, 0, 0.8, 0.6))

        plt.legend()
        plt.savefig('./out/year_trend_{0}{1}.pdf'.format(self.name, "_with_regular" if plot_regular_lifetimes else ""), bbox_inches='tight')

    def plot_box_plot(self, field, confidence=True, use_commit_numbers=False):
        if self.new_figure_required:
            plt.figure()
        self.new_figure_required = True

        year_data_heuristic_w_average = {}

        for year in range(1990, 2020):
            for item in self.data:

                fixing_date = datetime.strptime(item['Fixing date'][:16], "%Y-%m-%d %H:%M")
                if fixing_date.year != year:
                    continue

                date = datetime.strptime(item[self.__map_fields(field)][:16], "%Y-%m-%d %H:%M")
                life_time_weighted_average = fixing_date - date
                if use_commit_numbers:
                    commits = item[self.__map_fields_commits(field)]

                if year in year_data_heuristic_w_average:
                    year_data_heuristic_w_average[year].append(life_time_weighted_average.days if not use_commit_numbers else commits)
                else:
                    year_data_heuristic_w_average[year] = [life_time_weighted_average.days if not use_commit_numbers else commits]
        box_plot_data = []
        years = []
        avgs = []
        conf = []
        for key, items in year_data_heuristic_w_average.items():
            if confidence and len(items) >= self.confidence_size:
                mean = np.mean(items)
                box_plot_data.append(items)
                avgs.append(mean)
                years.append(key)
                conf.append([mean + mean * 0.15, mean - mean*0.15])

        plt.boxplot(box_plot_data, labels=years, sym='', usermedians=avgs)#, notch=True, conf_intervals=conf)

        plt.xlabel('Year of fixing commit')
        plt.ylabel('Lifetime in days' if not use_commit_numbers else "Lifetime in commits")

        #plt.title('Boxplot Vulnerability lifetimes - {0}'.format(self.name))

        plt.savefig('./out/box_plot_{0}.pdf'.format(self.name),  bbox_inches='tight')

    def plot_historic_inaccuracies(self, eval_field, percentage=True):
        if self.new_figure_required:
            plt.figure()
        self.new_figure_required = True

        diffs = {}
        avg ={}
        lower = {}
        for year in range(1990, 2020):
            for item in self.data:

                fixing_date = datetime.strptime(item['Fixing date'][:16], "%Y-%m-%d %H:%M")
                if fixing_date.year != year:
                    continue

                if 'VCC date' in item:
                    vcc_date = datetime.strptime(item['VCC date'][:16], "%Y-%m-%d %H:%M")
                    delta = fixing_date - vcc_date
                else:
                    delta = None
                    vcc_date = None
                lower_date = datetime.strptime(item[self.__map_fields('lower')][:16], "%Y-%m-%d %H:%M")
                date = datetime.strptime(item[self.__map_fields(eval_field)][:16], "%Y-%m-%d %H:%M")
                if vcc_date is not None:
                    delta_date = vcc_date - date
                    lifetime = fixing_date - vcc_date

                    delta_lower = vcc_date - lower_date
                    if year in diffs:
                        diffs[year].append(delta_date.days)
                        avg[year].append(lifetime.days)

                        lower[year].append(delta_lower.days)
                    else:
                        diffs[year] = [delta_date.days]
                        avg[year] = [lifetime.days]

                        lower[year] = [delta_lower.days]

        x_axis = []
        y_axis_1 = []
        y_axis_2 = []

        y_axis_3 = []
        res = []

        for key, items in diffs.items():
            if len(items) >= self.confidence_size:
                x_axis.append(key)
                res.append([key, np.mean(items)])
                print(str(key) + ': ' + str(len(items)))
                if percentage:
                    y_axis_1.append(np.mean(items) / np.mean(avg[key]) * 100)
                    y_axis_2.append(len(items))

                    y_axis_3.append(np.mean(lower[key]) / np.mean(avg[key]) * 100)
                else:
                    y_axis_1.append(np.mean(items))
                    y_axis_2.append(len(items))

                    y_axis_3.append(np.mean(lower[key]))

        plt.plot(x_axis, y_axis_1, 'rv', label='heuristic uppper bound')
        plt.plot(x_axis, y_axis_3, 'g^', label='heuristic lower bound')
        plt.xlabel('Year of fixing commit')
        plt.ylabel('Difference lifetime - %')
        #plt.legend()
        x_axis_2 = range(2010, 2021)

        plt.plot(x_axis_2, [0 for i in x_axis_2], 'k--', color=(0, 0, 0, 0.5))

        print(np.mean(y_axis_1))
        print(np.mean(y_axis_3))
        # fig, ax1 = plt.subplots()
        plt.xlim((2010.5,2019.5))
        # ax2 = ax1.twinx()
        # ax1.bar(x_axis, y_axis_2, label='Percentage', fc=(0, 0, 1, 0.5))
        # # print(y_axis_1)
        # ax2.plot(x_axis,y_axis_1, 'rx')
        # ax2.plot(x_axis_2, [0 for i in x_axis_2], color=(0, 0, 0, 0.5))
        #
        # #plt.title('Historic change in lifetime error - {0}'.format(self.name))
        # ax1.set_xlabel('Year of fixing commit')
        # ax2.set_ylabel('Difference in lifetime - %', color='r')
        # #
        # ax1.set_ylabel('Number of datapoints', color='b')
        print(spearmanr(res))
        plt.savefig('./out/heuristic_historic_error_upper_lower.pdf',  bbox_inches='tight')

    def plot_miss_distribution(self, eval_field, only_misses=True, in_percentage=False, only_correct=False, only_confident=False, check_data:dict=None, use_merge_vcc=False):
        if self.new_figure_required:
            plt.figure()
        self.new_figure_required = True

        data_points = []
        confident = {}
        if only_misses and only_correct:
            raise AttributeError()

        for item in self.data:

            if only_misses and item['VCC sha'] == item['VCC-heuristic sha']:
                continue
            if only_correct and item['VCC sha'] != item['VCC-heuristic sha']:
                continue
            if only_confident and item['Confident']:
                continue
            elif only_confident and not item['Confident']:
                if item['CVE'] in confident:
                    confident[item['CVE']][item['Fixing sha']] = True
                else:
                    confident[item['CVE']] = {item['Fixing sha']: True}


            if check_data is not None:
                if item['CVE'] not in check_data:
                    continue
                else:
                    if item['Fixing sha'] not in check_data[item['CVE']]:
                        continue
            if use_merge_vcc:
                vcc_date = datetime.strptime(item['VCC Merge Date'][:16], "%Y-%m-%d %H:%M")
            else:
                vcc_date = datetime.strptime(item['VCC date'][:16], "%Y-%m-%d %H:%M")

            date = datetime.strptime(item[self.__map_fields(eval_field)][:16], "%Y-%m-%d %H:%M")
            if in_percentage:
                fixing_date = datetime.strptime(item['Fixing date'][:16], "%Y-%m-%d %H:%M")
                lifetime = fixing_date - vcc_date
                date_lifetime = fixing_date - date
                if lifetime.days > 0:
                    percentage = (date_lifetime.days - lifetime.days) / lifetime.days * 100
                    print(percentage)
                    data_points.append(percentage)
            else:
                delta_date = vcc_date - date
                data_points.append(delta_date.days)


        Y_, X_, patches = plt.hist(data_points, 1000, density=True,  histtype='step',
                                   cumulative=True, label="Cumulated values", zorder= 10, range=[-6000, 6000] )
        X_ = self._moving_average(X_, 2)
        #plt.title('Distribution of inaccuracies in lifetimes - {0}'.format(self.name))
        plt.xlabel('Lifetime difference in {0}'.format('days' if not in_percentage else '%'))
        plt.ylabel('Percentage')
        X = np.arange(-6000, 6000, 10)


        mean = np.mean(data_points)

        print()
        print('Samplesize: {0}'.format(len(data_points)))

        #fit_function, parameters, loss = self._find_best_fit_function(X=X_, y_true= Y_, loss_function=mean_squared_error, data_points=data_points)

        #print('Function with least loss: ' + fit_function.name + ' MSE:' + str(loss))
        #print('Function parameters: ' +  str(parameters))

        #plt.plot(X, fit_function.cdf(X, *parameters), label=fit_function.name)
        #print(normaltest(normtest_data))
        print(np.mean(data_points))
        print(np.std(data_points))
        print(np.mean(np.abs(data_points)))
        print()
        #plt.text(2500, 40, 'Mean: ' + str(np.mean(data_points)) + '\n Median '+ str(np.median(data_points)) + '\n 1st Quartile: '+ str(np.quantile(data_points, 0.25)) + '\n 2nd Quartile: ' + str(np.quantile(data_points, 0.75)) + '\n Deviation: ' + str(np.mean(np.absolute(data_points))))
        plt.xlim([-5500, 5550])
        plt.legend()
        plt.savefig('./out/heuristic_miss_distribution_cdf{0}.pdf'.format(self.name),  bbox_inches='tight')
        plt.figure()
        plt.hist(data_points, 60, density=True,  label="Histogram values", range=[-6000, 6000] )
        plt.savefig('./out/heuristic_miss_distribution_pdf{0}.pdf'.format(self.name),  bbox_inches='tight')
        #plt.plot(X, fit_function.pdf(X, *parameters), label=fit_function.name)
        return data_points

    def plot_lifetime_distribution(self, eval_field: str, cut_off: list = None, use_commit_numbers: bool = False, cdf: bool = False, xmax: float = 7600, bins: int = 100, seperate_figs = False, fit_only = False, data_only = False, x_min_fit=None):

        if self.new_figure_required:
            plt.figure()
        self.new_figure_required = True
        data_points_1 = []
        cut_off_data = {}

        for item in self.data:

            fixing_date = datetime.strptime(item['Fixing date'][:16], "%Y-%m-%d %H:%M")


            date = datetime.strptime(item[self.__map_fields(eval_field)][:16], "%Y-%m-%d %H:%M")
            delta_date = fixing_date - date
            if use_commit_numbers:
                commits = item[self.__map_fields_commits(eval_field)]

            data_points_1.append(delta_date.days if not use_commit_numbers else commits)

            if cut_off is not None:
                for year in cut_off:
                    if fixing_date.year <= year:
                        if year in cut_off_data:
                            cut_off_data[year].append(delta_date.days if not use_commit_numbers else commits)
                        else:
                            cut_off_data[year] = [delta_date.days if not use_commit_numbers else commits]
                        break
        a, b = stats.expon.fit(data_points_1)
        np.random.seed(987654321)


        print(stats.kstest(data_points_1, stats.expon.cdf, (a,b), ))
        print(stats.kstest(data_points_1, stats.norm.cdf))


        fit = powerlaw.Fit(data_points_1, discrete=True, xmin=x_min_fit)
        comp = fit.distribution_compare('stretched_exponential', 'power_law')
        print('powerlaw')
        print(comp)
        comp = fit.distribution_compare('stretched_exponential', 'lognormal')
        print('lognormal')
        print(comp)
        comp = fit.distribution_compare('stretched_exponential', 'truncated_power_law')
        print('truncated_power_law')
        print(comp)
        comp = fit.distribution_compare('stretched_exponential', 'lognormal_positive')
        print('lognormal_positive')
        print(comp)
        pprint(fit.stretched_exponential.parameters)


        #comp = fit.distribution_compare('exponential', 'normal')
        #print(comp)

        X = np.arange(0, xmax + 1000, 10)

        if cut_off is None:

            if cdf and not fit_only:
                n_log, bins_log, patches_log = plt.hist(data_points_1, bins, density=True, histtype='step',
                                                   cumulative=True, label="Cumulated values {0}".format("< " + str(cut_off)  if cut_off is not None else ""), zorder= 10, range=[0, 15000])

            elif not fit_only:
                n_log, bins_log, patches_log = plt.hist(data_points_1, bins, density=True)
                plt.axvline(np.mean(data_points_1), color='orange', lw=2, alpha=0.5, label='Mean')
                plt.axvline(np.median(data_points_1), color='red', lw=2, alpha=0.5, label='Median')

            a_, b_, c_, d_ = stats.powerlognorm.fit(data_points_1)
                                                    

            a, b = stats.expon.fit(data_points_1)
            
            if cdf:
                Y = stats.expon.cdf(X, a, b)
                Y_ = stats.powerlognorm.cdf(X, a_, b_, c_, d_)
            else:
                Y = stats.expon.pdf(X, a, b)
                Y_ = stats.powerlognorm.pdf(X, a_, b_, c_, d_)

            if not data_only:
                plt.plot(X, Y, label="Exponential fit {0}".format("< " + str(cut_off)  if cut_off is not None else ""))
                
                #plt.plot(X, Y_, label="Lognormal fit {0}".format("< " + str(cut_off)  if cut_off is not None else ""))
            
            #fig = sm.qqplot(np.array(data_points_1), dist=stats.expon, loc=a, scale=b, line='45')
            #plt.xlabel('Exponential theoretical quantiles')
            #plt.ylabel('Data quantiles')
            #plt.xlim((0, xmax))
            #plt.savefig("./out/qq_plot.pdf")


            print('Mean: ' + str(np.mean(data_points_1)) + '\n 1st Quartile: '+ str(np.quantile(data_points_1, 0.25)) + '\n 2nd Quartile: ' + str(np.quantile(data_points_1, 0.75)) + '\n Deviation: ' + str(np.mean(np.absolute([x - np.mean(data_points_1) for x in data_points_1]))))
            print('{0}% are below {1} | {2} data points'.format(percentileofscore(data_points_1, np.mean(data_points_1)), np.mean(data_points_1), len(data_points_1)))
            print('Median: {0}'.format(np.median(data_points_1)))
           

        plt.xlabel('Lifetime in days' if not use_commit_numbers else 'Lifetime in commits')
        plt.ylabel('Density')
        plt.xlim((0, xmax))
        plt.legend(loc='lower right')
        plt.savefig("./out/distribution_{0}_{1}.pdf".format(self.name, "cdf" if cdf else "pdf"), bbox_inches='tight')
        if cut_off is not None:
            for year, data in cut_off_data.items():
                if seperate_figs:
                    plt.figure()
                if not fit_only:
                    n_log, bins_log, patches_log = plt.hist(data, bins, density=True, histtype='step',
                                                        cumulative=True, label="Cumulated values <= {0}".format(year), zorder= 10, range=[0, 8000])
                a, b = stats.expon.fit(data)
                Y = stats.expon.cdf(X, a, b)
                if not data_only:
                    if cdf:
                        plt.plot(X, Y, label="Exponential fit <= {0}".format(year))
                    else:
                        Y = stats.expon.pdf(X, a, b)
                        plt.plot(X, Y, label="Exponential fit <= {0}".format(year))
                # plt.axvline(np.mean(data_points_2), color='orange', linestyle='-', linewidth=1)
                #plt.title('Distribution of vulnerability lifetimes - {0} {1}'.format(self.name, "After {0}".format(cut_off) if cut_off is not None and cut_off > 0 else ""))
                plt.xlabel('Lifetime in days')
                plt.ylabel('Number of CVEs')

                print("<={0}".format(year))
                print('Mean: ' + str(np.mean(data)) + '\n 1st Quartile: '+ str(np.quantile(data, 0.25)) + '\n 2nd Quartile: ' + str(np.quantile(data, 0.75)) + '\n Deviation: ' + str(np.mean(np.absolute([x - np.mean(data) for x in data]))))

                print('{0}% are below {1}| {2} data points'.format(percentileofscore(data, np.mean(data)), np.mean(data), len(data)))
                plt.legend()
                plt.savefig("./out/distribution_{0}_second.pdf".format(self.name), bbox_inches='tight')

    def constant_factor_comparison(self, split):
        perfect_c = 0
        perfect_p = 0
        first_half = []
        second_half = []

        for item in self.data:
            fixing_date = datetime.strptime(item['Fixing date'][:16], "%Y-%m-%d %H:%M")
            if fixing_date.year < split:
                first_half.append(item)
            else:
                second_half.append(item)

        print('Datapoints in first sample: {0}'.format(len(first_half)))
        print('Datapoints in second sample: {0}'.format(len(second_half)))

        for item in first_half:
            vcc_date = datetime.strptime(item['VCC date'][:16], "%Y-%m-%d %H:%M")
            lower_bound_date = datetime.strptime(item['VCC-oldest date'][:16], "%Y-%m-%d %H:%M")

            fixing_date = datetime.strptime(item['Fixing date'][:16], "%Y-%m-%d %H:%M")

            lifetime = (fixing_date - lower_bound_date).days
            if lifetime != 0:
                perfect_p += (vcc_date - lower_bound_date).days / lifetime
            perfect_c += (vcc_date - lower_bound_date).days

        perfect_c /= len(first_half)
        perfect_p /= len(first_half)



        print('Perfect factor first sample: {0} days'.format(perfect_c))
        print('Perfect factor first sample: {0} % of lifetime'.format(perfect_p * 100))

        error_weighted_average = 0
        error_perfect_constant = 0
        error_perfect_percentage = 0


        for item in second_half:
            vcc_date = datetime.strptime(item['VCC date'][:16], "%Y-%m-%d %H:%M")
            lower_bound_date = datetime.strptime(item['VCC-oldest date'][:16], "%Y-%m-%d %H:%M")
            w_average_date = datetime.strptime(item['Weighted Average date'][:16], "%Y-%m-%d %H:%M")
            fixing_date = datetime.strptime(item['Fixing date'][:16], "%Y-%m-%d %H:%M")

            lifetime_lower = (fixing_date - lower_bound_date).days
            lifetime_ = (fixing_date - vcc_date).days

            error_weighted_average += (vcc_date - w_average_date).days
            error_perfect_constant += (vcc_date - lower_bound_date).days - perfect_c

            error_perfect_percentage += lifetime_ - (lifetime_lower + (perfect_p * lifetime_lower))

        error_weighted_average /= len(second_half)
        error_perfect_constant /= len(second_half)
        error_perfect_percentage /= len(second_half)

        print("Error in second half using w average: {0}".format(error_weighted_average))
        print("Error in second half using perfect constant: {0}".format(error_perfect_constant))
        print("Error in second half using perfect percentage: {0}".format(error_perfect_percentage))

    def get_root_cwe(self, cwe_id):
        try:
            try:
                node = [x for x in self.cwe_xml['Weaknesses']['Weakness']if x['@ID'] == str(cwe_id)][0]
            except:
                return self.__map_old_cves(str(cwe_id))
            try:
                parent = [x for x in node['Related_Weaknesses']['Related_Weakness'] if x['@Nature'] == 'ChildOf' and '@Ordinal' in x and x['@Ordinal'] == 'Primary'][0]

            except:
                parent = node['Related_Weaknesses']['Related_Weakness']
                if parent['@Nature'] == 'ChildOf' and parent['@Ordinal'] == 'Primary':
                    return self.get_root_cwe(parent['@CWE_ID'])
                else:
                    return cwe_id
            return self.get_root_cwe(parent['@CWE_ID'])
        except:
            return cwe_id

    def get_cwe_description(self, cwe_id):
        try:
            node = [x for x in self.cwe_xml['Weaknesses']['Weakness']if x['@ID'] == str(cwe_id)][0]
            return node['@Name']
        except:
            return "Unknown CWE"

    def cwe_lifetimes(self, own_categories=True):
        cwes = {}
        for item in self.data:
            try:
                cwe_id = item['CWE'].replace('CWE-', '')
            except:

                print('{0} defines no cwe'.format(item['CVE']))
                continue

            fixing_date = datetime.strptime(item['Fixing date'][:16], "%Y-%m-%d %H:%M")
            date = datetime.strptime(item[self.__map_fields('weighted')][:16], "%Y-%m-%d %H:%M")
            delta = fixing_date - date

            if own_categories:
                root_cwe = self.__manual_cve_mappings(cwe_id)
            else:
                root_cwe = cwe_id

            if root_cwe in cwes:
                cwes[root_cwe].append(delta.days)
            else:
                cwes[root_cwe] = [delta.days]

        od = collections.OrderedDict([(k, v) for k, v in sorted(cwes.items(), key=lambda k: len(k[1]), reverse=True)])

        top1 = []
        top2 = []
        top3 = []
        top4 = []
        top5 = []
        top6 = []
        top7 = []
        top8 = []
        top9 = []
        top10 = []

        it = 1
        for key, value in od.items():
            if key is None:
                continue
            print('{0} - {4}: {1} days - {2} datapoints | {3}'.format(key, np.mean(value), len(value), np.median(value), self.get_cwe_description(key)))

            if it == 1 :
               top1 = value
            if it == 2 :
               top2 = value
            if it == 3 :
               top3 = value
            if it == 4 :
               top4 = value
            if it == 5 :
               top5 = value
            if it == 6 :
               top6 = value
            if it == 7 :
               top7 = value
            if it == 8 :
               top8 = value
            if it == 9 :
               top9 = value
            if it == 10 :
               top10 = value
            it +=1
        #     if str(key) == str(693):
        #         sample_693 = value
        #     if str(key) == str(682):
        #         sample_682 = value
        #     if str(key) == str(707):
        #         sample_707 = value
        #     if str(key) == str(664):
        #         sample_664 = value
        #     if str(key) == str(691):
        #         sample_691 = value
        #     if str(key) == str(118):
        #         sample_118 = value
        #     if str(key) == str(710):
        #         sample_710 = value
        #
        self.__pairwise_comparison([['1', top1], ['4', top2], ['2', top3]
                                      ,   ['5', top4]
                                     , ['3', top5]
                                        , ['6', top6]
        #                               , ['CWE-118', sample_118]
                                     ])
        if own_categories:
            print(stats.kruskal(top1, top2, top3, top4, top5, top6))
        else:
            print(stats.kruskal(top1, top2, top3, top4, top5, top6, top7, top8, top9, top10))

    def score_lifetimes(self):
        scores = {}
        for item in self.data:
            try:
                cvss_score = float(item['CVSS-Score'])
            except:
                print('{0} defines no cvss'.format(item['CVE']))
            fixing_date = datetime.strptime(item['Fixing date'][:16], "%Y-%m-%d %H:%M")
            date = datetime.strptime(item[self.__map_fields('weighted')][:16], "%Y-%m-%d %H:%M")
            delta = fixing_date - date

            normalized_score = (round(cvss_score * 1, 0) / 1.0)
            if normalized_score in scores:
                scores[normalized_score].append(delta.days)
            else:
                scores[normalized_score] = [delta.days]

        res = []
        x_axis = []
        y_axis = []
        for key, value in scores.items():
            if len(value) > self.confidence_size:
                res.append([key, np.mean(value)])
                x_axis.append(key)
                y_axis.append(np.mean(value))
                print('{0}: {1} days - {2} datapoints'.format(key, np.mean(value), len(value)))
            else:
                print('Ignored: {0}: {1} days - {2} datapoints'.format(key, np.mean(value), len(value)))
        plt.plot(x_axis, y_axis, 'k.')
        print(spearmanr(res))

    def __map_fields(self, field):
        mapping = {'average': 'Average date',
                   'upper': 'VCC-oldest date',
                   'lower': 'VCC-newest date',
                   'heuristic': 'VCC-heuristic date',
                   'weighted': 'Weighted Average date',
                   'correct': 'VCC date'
                   }
        return mapping[field.lower()]

    def __map_fields_commits(self, field):
        mapping =  {'upper': 'Commits oldest',
                    'lower': 'Commmits newest',
                    'heuristic': 'Commits heuristic',
                    'weighted': 'Commits weighted',
                    'correct': 'Commits'}
        return mapping[field.lower()]

    def __pairwise_comparison(self, input):
        print()
        for i in range(len(input)):
            cwe_1 = input[i][0]
            data_1 = input[i][1]

            for x in range(i + 1, len(input)):
                cwe_2 = input[x][0]
                data_2 = input[x][1]
                #print("{0} vs {1}: {2}".format(cwe_1, cwe_2, stats.mannwhitneyu(data_1, data_2, alternative='two-sided')))
                #print("{0} vs {1}: {2}".format(cwe_1, cwe_2, p_test.permutationtest(data_1, data_2)))
                print("{0} vs {1}: {2}".format(cwe_1, cwe_2, permutation_test(data_1, data_2,
                                                                              method='approximate',
                                                                              num_rounds=100000,
                                                                              seed=0)))
            print()

    def __plot_dict(self, data, point='kx', print_=False, gt_heuristic_ratio = {}, **kwargs):
        x_axis = []
        y_axis = []
        for key, items in data.items():
            if print_:
                print('{0}: {1} {2} - {3} days'.format(key, len(items), "  {0} | {1} -> {2}%".format(gt_heuristic_ratio[key][0], gt_heuristic_ratio[key][1], gt_heuristic_ratio[key][0] / len(items) * 100) if key in gt_heuristic_ratio else "", np.mean(items)))
            if len(items) >= self.confidence_size:
                x_axis.append(key)
                y_axis.append(np.mean(items))


        plt.plot(x_axis, y_axis, point, **kwargs)

    def __plot_linear_fit(self, data, confidence=True, left_shift=True):
        x_axis = []
        y_axis = []
        for key, items in data.items():
            if confidence and len(items) >= self.confidence_size:
                x_axis.append(key)
                y_axis.append(np.mean(items))

        regr = linear_model.LinearRegression()
        X = np.array(x_axis).reshape(-1, 1)
        Y = np.array(y_axis)
        regr.fit(X, Y)
        
        x_ = range(len(x_axis))
        X_ = sm.add_constant(x_)
        model = sm.OLS(y_axis,X_).fit()
        predictions = model.predict(X_)
        #plt.plot(predictions)
        #plt.show()
        print(model.summary())
        print(model.summary().as_latex())
        
        x_axis.append(key + 1)
        x_axis.insert(0, x_axis[0] - 1)
        if left_shift:
            x_axis.insert(0, x_axis[0] - 1)
        print(regr.score(X, Y), regr.coef_[0])

        X = np.array(x_axis).reshape(-1, 1)
        plt.plot(x_axis, regr.predict(X), 'k--', color=(0.0, 0.0, 1, 0.6))

        #plt.text(x_axis[0], 2000, 'r={0}\ncoef={1}'.format(regr.score(X, Y), regr.coef_[0]))

    def __map_old_cves(self, cve):
        mappings= {'264': '693', '189': '682', '399': '664', '16': '710', '254': '693', '310': '693', '255': '693', '19': '707', '199': '707', '316':'664', '275': '693', '388': '703', '361': '664', '417': '693'}
        return mappings[cve]

    def __manual_cve_mappings(self, cve: str) -> int:
        """Mapps CWE-ID to a top-level category.
        1 - Memory and Resource Management
        2 - Input Validation and Sanitization
        3 - Code Development Quality
        4 - Security Measures
        5 - Others
        6 - Concurrency
        CWEs that are not included return None, as well as the CWE \'NVD-noinfo\'"""
        mappings = {'20': 2, '189': 4, '119': 1, '125': 1, '399': 1, 'NVD-Other': 5, '200': 4, '476': 1, '264': 4,
                    '416': 1, '835': 3, 'NVD-noinfo': None, '362': 6, '400': 1, '787': 1, '772': 1, '310': 4, '190': 1,
                    '74': 2, '17': 3, '284': 4, '415': 1, '369': 3, '19': 5, '834': 3, '79': 4, '754': 5, '674': 3,
                    '120': 1, '94': 2, '388': 5, '269': 4, '254': 4, '129': 2, '287': 4, '617': 3, '276': 4, '404': 1,
                    '134': 5, '862': 4, '320': 4, '89': 2, '347': 4, '682': 3, '16': 5, '665': 5, '755': 5, '732': 4,
                    '311': 4, '770': 1, '252': 5, '534': 5, '704': 5, '22': 2, '532': 5, '193': 3, '843': 5, '391': 5,
                    '191': 1, '59': 2, '763': 1, '358': 4, '285': 4, '863': 4, '77': 2, '327': 4, '330': 5, '295': 5,
                    '352': 5, '92': 4, '664': 1, '93': 2, '275': 4, '434': 5, '707': 2, '668': 4, '361': 6, '319': 4,
                    '255': 4, '824': 1, '1187': 1, '426': 4, '417': 5, '427': 5, '610': 5, '522': 4, '345': 5, '354': 5,
                    '91': 2, '918': 5, '922': 4, '706': 5, '538': 4, '290': 4, '601': 4, '346': 5, '502': 2, '1021': 5,
                    '78': 2, '199': 5, '829': 5, '281': 4}
        try:
            return mappings[cve]
        except:
            print(cve)
            return None

    def _find_best_fit_function(self, loss_function, X, y_true, data_points):
        # Distributions to check
        DISTRIBUTIONS = [
            stats.alpha,stats.anglit,stats.arcsine,stats.beta,stats.betaprime,stats.bradford,stats.burr,stats.cauchy,stats.chi,stats.chi2,stats.cosine,
            stats.dgamma,stats.dweibull,stats.erlang,stats.expon,stats.exponnorm,stats.exponweib,stats.exponpow,stats.f,stats.fatiguelife,stats.fisk,
            stats.foldcauchy,stats.foldnorm,stats.frechet_r,stats.frechet_l,stats.genlogistic,stats.genpareto,stats.gennorm,stats.genexpon,
            stats.foldcauchy,stats.foldnorm,stats.frechet_r,stats.frechet_l,stats.genlogistic,stats.genpareto,stats.gennorm,stats.genexpon,
            stats.genextreme,stats.gausshyper,stats.gamma,stats.gengamma,stats.genhalflogistic,stats.gilbrat,stats.gompertz,stats.gumbel_r,
            stats.gumbel_l,stats.halfcauchy,stats.halflogistic,stats.halfnorm,stats.halfgennorm,stats.hypsecant,stats.invgamma,stats.invgauss,
            stats.invweibull,stats.johnsonsb,stats.johnsonsu,stats.ksone,stats.kstwobign,stats.laplace,stats.levy,stats.levy_l,stats.levy_stable,
            stats.logistic,stats.loggamma,stats.loglaplace,stats.lognorm,stats.lomax,stats.maxwell,stats.mielke,stats.nakagami,stats.ncx2,stats.ncf,
            stats.nct,stats.norm,stats.pareto,stats.pearson3,stats.powerlaw,stats.powerlognorm,stats.powernorm,stats.rdist,stats.reciprocal,
            stats.rayleigh,stats.rice,stats.recipinvgauss,stats.semicircular,stats.t,stats.triang,stats.truncexpon,stats.truncnorm,stats.tukeylambda,
            stats.uniform,stats.vonmises,stats.vonmises_line,stats.wald,stats.weibull_min,stats.weibull_max,stats.wrapcauchy
        ]

        # Best holders
        best_distribution = stats.norm
        best_params = (0.0, 1.0)
        best_loss = np.inf

        # Estimate distribution parameters from data
        for distribution in tqdm(DISTRIBUTIONS):
            if distribution.name == 'levy_stable':
                continue
            # Try to fit the distribution
            try:
                # Ignore warnings from data that can't be fit
                with warnings.catch_warnings():
                    warnings.filterwarnings('ignore')

                    # fit dist to data
                    params = distribution.fit(data_points)

                    # Separate parts of parameters
                    arg = params[:-2]
                    loc = params[-2]
                    scale = params[-1]

                    # Calculate fitted PDF and error with fit in distribution
                    y_pred = distribution.cdf(X, loc=loc, scale=scale, *arg)
                    loss = loss_function(y_true=y_true, y_pred=y_pred)

                    # if axis pass in add to plot


                    # identify if this distribution is better
                    if best_loss > loss > 0:
                        best_distribution = distribution
                        best_params = params
                        best_loss = loss

            except Exception:
                pass

        return (best_distribution, best_params, best_loss)

    def _moving_average(self, a, n=3) :
        ret = np.cumsum(a, dtype=float)
        ret[n:] = ret[n:] - ret[:-n]
        return ret[n - 1:] / n