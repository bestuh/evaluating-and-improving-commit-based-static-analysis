import warnings
from datetime import datetime
from matplotlib import pyplot as plt
import numpy as np
from sklearn import datasets, linear_model
import powerlaw
from scipy.stats import norm, normaltest, percentileofscore, spearmanr, f_oneway
import scipy.stats as stats
import xmltodict
import math

cwe_xml_path = "LifetimeAnalysis/cwe.xml"

class LifetimeEval:

    def __init__(self, path, is_ground_truth_data=False, only_stable_vuls=False, name='', **kwargs):
        self.path = path
        self.ground_truth = is_ground_truth_data
        self.name = name
        self.stable_vuls = only_stable_vuls

        with open('./LiftetimeAnalysis/cwe.xml', encoding='utf-8')as fd:
            doc = xmltodict.parse(fd.read())

        self.cwe_xml = doc['Weakness_Catalog']
        self.confidence_size = 20

        if self.ground_truth:
            with open(path, 'r+') as f:
                commits = 0
                self.data = []
                cves = {}
                for line in f.readlines()[1:]:
                    splits = line.split(';')
                    cve = splits[0]
                    commits += 1
                    if cve in cves:
                        try:
                            cwe = cves[cve][13]
                            cvss_score = cves[cve][14]
                            fixing = cves[cve][0:2] if datetime.strptime(cves[cve][1][:16], "%Y-%m-%d %H:%M") >= datetime.strptime(splits[2][:16], "%Y-%m-%d %H:%M") else splits[1:3]
                            vcc_heuristic = cves[cve][4:6] if datetime.strptime(cves[cve][5][:16], "%Y-%m-%d %H:%M") <= datetime.strptime(splits[4][:16], "%Y-%m-%d %H:%M") else splits[3:5]
                            vcc_oldest = cves[cve][6:8] if datetime.strptime(cves[cve][7][:16], "%Y-%m-%d %H:%M") <= datetime.strptime(splits[6][:16], "%Y-%m-%d %H:%M") else splits[5:7]
                            vcc_newest = cves[cve][8:10] if datetime.strptime(cves[cve][9][:16], "%Y-%m-%d %H:%M") >= datetime.strptime(splits[8][:16], "%Y-%m-%d %H:%M") else splits[7:9]
                            vcc_average = cves[cve][10] if datetime.strptime(cves[cve][10][:16], "%Y-%m-%d %H:%M") <= datetime.strptime(splits[9][:16], "%Y-%m-%d %H:%M") else splits[9]
                            vcc_weighted_average = cves[cve][11] if datetime.strptime(cves[cve][11][:16], "%Y-%m-%d %H:%M") <= datetime.strptime(splits[10][:16], "%Y-%m-%d %H:%M") else splits[10]
                            vcc_heuristic_average = cves[cve][12] if datetime.strptime(cves[cve][12][:16], "%Y-%m-%d %H:%M") <= datetime.strptime(splits[11][:16], "%Y-%m-%d %H:%M") else splits[11]
                            vcc = cves[cve][2:4] if datetime.strptime(cves[cve][3][:16], "%Y-%m-%d %H:%M") <= datetime.strptime(splits[2][:16], "%Y-%m-%d %H:%M") else splits[1:3]
                            cves[cve] = fixing + vcc + vcc_heuristic + vcc_oldest  + vcc_newest + [vcc_average, vcc_weighted_average, vcc_heuristic_average, cwe, cvss_score]
                        except Exception as e:
                            warnings.warn('Unable to proccess line {0}:{1}'.format(cve, splits[1]))
                    else:
                        if self.stable_vuls:
                            stable = splits[17]
                            if 'yes' in stable:
                                cves[cve] = splits[1:]
                        else:
                            cves[cve] = splits[1:]
            print("Number of fixing-commits: {0}".format(commits))
            for key, value in cves.items():
                self.data.append([key] + value)
        else:
            self.data = []
            self.__normalize()

        if 'additional_data' in kwargs:
            for additional_mapping in kwargs['additional_data']:
                path = additional_mapping[1]
                if additional_mapping[0]:
                    cves = {}
                    with open(path, 'r+') as f:
                        for line in f.readlines()[1:]:
                            cve = splits[0]
                            if cve in cves:
                                try:
                                    cwe = cves[cve][13]
                                    cvss_score = cves[cve][14]
                                    fixing = cves[cve][0:2] if datetime.strptime(cves[cve][1][:16], "%Y-%m-%d %H:%M") >= datetime.strptime(splits[2][:16], "%Y-%m-%d %H:%M") else splits[1:3]
                                    vcc_heuristic = cves[cve][4:6] if datetime.strptime(cves[cve][5][:16], "%Y-%m-%d %H:%M") <= datetime.strptime(splits[4][:16], "%Y-%m-%d %H:%M") else splits[3:5]
                                    vcc_oldest = cves[cve][6:8] if datetime.strptime(cves[cve][7][:16], "%Y-%m-%d %H:%M") <= datetime.strptime(splits[6][:16], "%Y-%m-%d %H:%M") else splits[5:7]
                                    vcc_newest = cves[cve][8:10] if datetime.strptime(cves[cve][9][:16], "%Y-%m-%d %H:%M") >= datetime.strptime(splits[8][:16], "%Y-%m-%d %H:%M") else splits[7:9]
                                    vcc_average = cves[cve][10] if datetime.strptime(cves[cve][10][:16], "%Y-%m-%d %H:%M") <= datetime.strptime(splits[9][:16], "%Y-%m-%d %H:%M") else splits[9]
                                    vcc_weighted_average = cves[cve][11] if datetime.strptime(cves[cve][11][:16], "%Y-%m-%d %H:%M") <= datetime.strptime(splits[10][:16], "%Y-%m-%d %H:%M") else splits[10]
                                    vcc_heuristic_average = cves[cve][12] if datetime.strptime(cves[cve][12][:16], "%Y-%m-%d %H:%M") <= datetime.strptime(splits[11][:16], "%Y-%m-%d %H:%M") else splits[11]
                                    vcc = cves[cve][2:4] if datetime.strptime(cves[cve][3][:16], "%Y-%m-%d %H:%M") <= datetime.strptime(splits[2][:16], "%Y-%m-%d %H:%M") else splits[1:3]
                                    cves[cve] = fixing + vcc + vcc_heuristic + vcc_oldest  + vcc_newest + [vcc_average, vcc_weighted_average, vcc_heuristic_average, cwe, cvss_score]
                                except Exception as e:
                                    warnings.warn('Unable to proccess line {0}:{1}'.format(cve, splits[1]))
                            else:
                                if self.stable_vuls:
                                    stable = splits[17]
                                    if 'yes' in stable:
                                        cves[cve] = splits[1:]
                                else:
                                    cves[cve] = splits[1:]
                    for key, value in cves.items():
                        self.data.append([key] + value)
                else:
                    self.path = path
                    self.__normalize()

        print("Number of CVEs: {0}\n".format(len(self.data)))

        self.new_figure_required = False

    def __normalize(self, ground_truth=False):
        commits = 0
        path = self.path
        cves = {}
        with open(path, 'r+') as f:

            for line in f.readlines()[1:]:
                commits += 1
                splits = line.split(';')
                cve = splits[0]
                if cve in cves:
                    try:
                        cwe = cves[cve][13]
                        cvss_score = cves[cve][14]
                        fixing = cves[cve][0:2] if datetime.strptime(cves[cve][1][:16], "%Y-%m-%d %H:%M") >= datetime.strptime(splits[2][:16], "%Y-%m-%d %H:%M") else splits[1:3]
                        vcc_heuristic = cves[cve][4:6] if datetime.strptime(cves[cve][5][:16], "%Y-%m-%d %H:%M") <= datetime.strptime(splits[4][:16], "%Y-%m-%d %H:%M") else splits[3:5]
                        vcc_oldest = cves[cve][6:8] if datetime.strptime(cves[cve][7][:16], "%Y-%m-%d %H:%M") <= datetime.strptime(splits[6][:16], "%Y-%m-%d %H:%M") else splits[5:7]
                        vcc_newest = cves[cve][8:10] if datetime.strptime(cves[cve][9][:16], "%Y-%m-%d %H:%M") >= datetime.strptime(splits[8][:16], "%Y-%m-%d %H:%M") else splits[7:9]
                        vcc_average = cves[cve][10] if datetime.strptime(cves[cve][10][:16], "%Y-%m-%d %H:%M") <= datetime.strptime(splits[9][:16], "%Y-%m-%d %H:%M") else splits[9]
                        vcc_weighted_average = cves[cve][11] if datetime.strptime(cves[cve][11][:16], "%Y-%m-%d %H:%M") <= datetime.strptime(splits[10][:16], "%Y-%m-%d %H:%M") else splits[10]
                        vcc_heuristic_average = cves[cve][12] if datetime.strptime(cves[cve][12][:16], "%Y-%m-%d %H:%M") <= datetime.strptime(splits[11][:16], "%Y-%m-%d %H:%M") else splits[11]
                        cves[cve] = fixing + [None, None] + vcc_heuristic + vcc_oldest  + vcc_newest + [vcc_average, vcc_weighted_average, vcc_heuristic_average, cwe, cvss_score]
                    except Exception as e:
                        warnings.warn('Unable to proccess line {0}:{1}'.format(cve, splits[1]))
                else:
                    if self.stable_vuls:
                        stable = splits[15]
                        if 'yes' in stable:
                            cves[cve] = splits[1:3] + [None, None] + splits[3:]
                    else:
                        cves[cve] = splits[1:3] + [None, None] + splits[3:]
        data = []
        for key, value in cves.items():
            data.append([key] + value)
        print("Number of fixing-commits: {0}".format(commits))
        self.data.extend(data)

    def plot_year_trend_custom_buckets(self, bucket_number, plot_linear_fit=False):
        if self.new_figure_required:
            f = plt.figure()
        self.new_figure_required = True

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

                fixing_date = datetime.strptime(item[2][:16], "%Y-%m-%d %H:%M")

                if fixing_date.year != year:
                    continue

                if fixing_date.year > latest_year:
                    latest_year = fixing_date.year

                if fixing_date.year < earliest_year:
                    earliest_year = fixing_date.year

                #ignore correctly mapped CVEs
                #if item[3] == item[5]:
                #   continue
                if item[4] is not None:
                    vcc_date = datetime.strptime(item[4][:16], "%Y-%m-%d %H:%M")
                    delta = fixing_date - vcc_date
                else:
                    delta = None

                vcc_heuristic_date = datetime.strptime(item[6][:16], "%Y-%m-%d %H:%M")
                delta_heuristic = fixing_date - vcc_heuristic_date

                vcc_heuristic_oldest_date = datetime.strptime(item[8][:16], "%Y-%m-%d %H:%M")
                delta_heuristic_oldest = fixing_date - vcc_heuristic_oldest_date

                vcc_heuristic_newest_date = datetime.strptime(item[10][:16], "%Y-%m-%d %H:%M")
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

                weighted_average_date = datetime.strptime(item[12][:16], "%Y-%m-%d %H:%M")
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
        bucket = 0
        data_points = []
        data_points_upper =[]
        data_points_lower = []
        x_lables = []
        for key, items in year_data_heuristic_w_average.items():
            if bucket < bucket_size:
                data_points.extend(items)
                data_points_upper.extend(year_data_heuristic_oldest[key])
                data_points_lower.extend(year_data_heuristic_newest[key])
                bucket += 1
            else:
                print('{1}-{0}: {2}'.format(key - 1, key-bucket_size - 1, len(data_points)))
                x_axis.append(key)
                x_lables.append('{1}-{0}'.format(key - 1, key-bucket_size - 1))
                y_axis.append(np.mean(data_points))
                y_axis_upper.append(np.mean(data_points_upper))
                y_axis_lower.append(np.mean(data_points_lower))
                data_points = items
                data_points_upper = year_data_heuristic_oldest[key]
                data_points_lower = year_data_heuristic_newest[key]
                bucket = 0
            print('{0}: {1}'.format(key, len(items)))



        x_axis.append(key +1)
        y_axis.append(np.mean(data_points))
        y_axis_upper.append(np.mean(data_points_upper))
        y_axis_lower.append(np.mean(data_points_lower))
        x_lables.append('{1}-{0}'.format(key, x_axis[-2:-1][0]))
        print('{1}-{0}: {2}'.format(key, x_axis[-2:-1][0], len(data_points)))

        plt.plot(x_axis, y_axis, 'b.', label='Weighted average')
        plt.plot(x_axis, y_axis_lower, 'g^', label='Heuristic lower bound')
        plt.plot(x_axis, y_axis_upper, 'rv', label='Heuristic upper bound')
        #self.__plot_dict(year_data_heuristic, 'y*', label='Heuristic most blamed')
        plt.xlabel('Year of fixing commit')
        plt.ylabel('Lifetime in days')

        plt.legend()
        plt.title('Average Vulnerability lifetimes - {0}'.format(self.name))
        plt.xticks(x_axis, x_lables)
        #f.savefig('year_trend_{0}.pdf'.format(self.name), bbox_inches='tight')

        if plot_linear_fit:
            regr = linear_model.LinearRegression()
            X = np.array(x_axis).reshape(-1, 1)
            Y = np.array(y_axis)
            regr.fit(X, Y)
            plt.plot(x_axis, regr.predict(X), '--k')
            print(regr.score(X, Y), regr.coef_[0])

    def plot_year_trend(self, linear_fit=False):

        if self.new_figure_required:
            f = plt.figure()
        self.new_figure_required = True

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
        for year in range(1990, 2020):
            for item in self.data:

                fixing_date = datetime.strptime(item[2][:16], "%Y-%m-%d %H:%M")
                if fixing_date.year != year:
                    continue

                #ignore correctly mapped CVEs
                #if item[3] == item[5]:
                #   continue
                if item[4] is not None:
                    vcc_date = datetime.strptime(item[4][:16], "%Y-%m-%d %H:%M")
                    delta = fixing_date - vcc_date
                else:
                    delta = None

                vcc_heuristic_date = datetime.strptime(item[6][:16], "%Y-%m-%d %H:%M")
                delta_heuristic = fixing_date - vcc_heuristic_date

                vcc_heuristic_oldest_date = datetime.strptime(item[8][:16], "%Y-%m-%d %H:%M")
                delta_heuristic_oldest = fixing_date - vcc_heuristic_oldest_date

                vcc_heuristic_newest_date = datetime.strptime(item[10][:16], "%Y-%m-%d %H:%M")
                delta_heuristic_newest = fixing_date - vcc_heuristic_newest_date

                if delta is not None and year in year_data:
                    year_data[year].append(delta.days)
                    year_data_combined[year].append(delta.days)
                    if year in gt_heuristic_ratio:
                        gt_heuristic_ratio[year][0] += 1
                    else:
                        gt_heuristic_ratio[year] = [1, 0]
                elif delta is not None:
                    year_data[year] = [delta.days]
                    year_data_combined[year] = [delta.days]
                    if year in gt_heuristic_ratio:
                        gt_heuristic_ratio[year][0] += 1
                    else:
                        gt_heuristic_ratio[year] = [1, 0]

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

                weighted_average_date = datetime.strptime(item[12][:16], "%Y-%m-%d %H:%M")
                life_time_weighted_average = fixing_date - weighted_average_date

                if year in year_data_heuristic_w_average:
                    year_data_heuristic_w_average[year].append(life_time_weighted_average.days)
                    if item[4] is None:
                        year_data_combined[year].append(life_time_weighted_average.days)
                        if year in gt_heuristic_ratio:
                            gt_heuristic_ratio[year][1] += 1
                        else:
                            gt_heuristic_ratio[year] = [0, 1]
                else:
                    year_data_heuristic_w_average[year] = [life_time_weighted_average.days]
                    if item[4] is None:
                        year_data_combined[year] = [life_time_weighted_average.days]
                        if year in gt_heuristic_ratio:
                            gt_heuristic_ratio[year][1] += 1
                        else:
                            gt_heuristic_ratio[year] = [0, 1]

        #self.__plot_dict(year_data, 'kx',  label='Correct lifetime')
        self.__plot_dict(year_data_heuristic_oldest, 'rv', True, gt_heuristic_ratio, label='Heuristic upper bound')
        self.__plot_dict(year_data_heuristic_newest, 'g^', label='Heuristic lower bound')
        #self.__plot_dict(year_data_heuristic, 'y*', label='Heuristic most blamed')
        self.__plot_dict(year_data_combined, 'b.', label='Combined average')

        if(linear_fit):
            #Fit
            if len(year_data) > 0:
                self.__plot_linear_fit(year_data_combined)
            else:
                self.__plot_linear_fit(year_data_heuristic_w_average)


        plt.xlabel('Year of fixing commit')
        plt.ylabel('Lifetime in days')

        plt.legend()
        plt.title('Average Vulnerability lifetimes - {0}'.format(self.name))

        plt.savefig('year_trend_{0}.pdf'.format(self.name), bbox_inches='tight')

    def plot_box_plot(self, field, confidence=True):
        if self.new_figure_required:
            plt.figure()
        self.new_figure_required = True

        year_data_heuristic_w_average = {}

        for year in range(1990, 2020):
            for item in self.data:

                fixing_date = datetime.strptime(item[2][:16], "%Y-%m-%d %H:%M")
                if fixing_date.year != year:
                    continue

                date = datetime.strptime(item[self.__map_fields(field)][:16], "%Y-%m-%d %H:%M")
                life_time_weighted_average = fixing_date - date

                if year in year_data_heuristic_w_average:
                    year_data_heuristic_w_average[year].append(life_time_weighted_average.days)
                else:
                    year_data_heuristic_w_average[year] = [life_time_weighted_average.days]
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
        plt.ylabel('Lifetime in days')

        plt.title('Boxplot Vulnerability lifetimes - {0}'.format(self.name))

        plt.savefig('box_plot_{0}.pdf'.format(self.name),  bbox_inches='tight')

    def plot_historic_inaccuracies(self, eval_field, percentage=True):
        if self.new_figure_required:
            plt.figure()
        self.new_figure_required = True

        diffs = {}
        avg ={}
        lower = {}
        for year in range(1990, 2020):
            for item in self.data:

                fixing_date = datetime.strptime(item[2][:16], "%Y-%m-%d %H:%M")
                if fixing_date.year != year:
                    continue

                if item[4] is not None:
                    vcc_date = datetime.strptime(item[4][:16], "%Y-%m-%d %H:%M")
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
        for key, items in diffs.items():
            if len(items) >= self.confidence_size:
                x_axis.append(key)
                print(str(key) + ': ' + str(len(items)))
                if percentage:
                    y_axis_1.append(np.mean(items) / np.mean(avg[key]) * 100)
                    y_axis_2.append(len(items))

                    y_axis_3.append(np.mean(lower[key]) / np.mean(avg[key]) * 100)
                else:
                    y_axis_1.append(np.mean(items))
                    y_axis_2.append(len(items))

                    y_axis_3.append(np.mean(lower[key]))

        plt.plot(x_axis, y_axis_1, 'kx', label='heuristic uppper bound')
        #plt.plot(x_axis, y_axis_3, 'g^', label='heuristic lower bound')
        plt.xlabel('Year of fixing commit')
        plt.ylabel('Difference lifetime in days')

        x_axis_2 = range(2011, 2020)

        #plt.plot(x_axis_2, [0 for i in x_axis_2], 'k--')

        print(np.mean(y_axis_1))
        print(np.mean(y_axis_3))
        # fig, ax1 = plt.subplots()
        # ax2 = ax1.twinx()
        # ax1.bar(x_axis, y_axis_2, label='Percentage', fc=(0, 0, 1, 0.5))
        # print(y_axis_1)
        # ax2.plot(x_axis,y_axis_1, 'rx')
        # plt.title('Historic change in lifetime error - {0}'.format(self.name))
        # ax2.set_xlabel('Year of fixing commit')
        # ax2.set_ylabel('Difference in lifetime - %', color='r')
        #
        # ax1.set_ylabel('Number of datapoints', color='b')
        #plt.savefig('heuristic_error_weighted.pdf',  bbox_inches='tight')

    def plot_miss_distribution(self, eval_field, only_misses=True, in_percentage=False, only_correct=False):
        if self.new_figure_required:
            plt.figure()
        self.new_figure_required = True

        data_points = []
        if only_misses and only_correct:
            raise AttributeError()
        for item in self.data:

            if only_misses and item[3] == item[5]:
                continue
            if only_correct and item[3] != item[5]:
                continue
            vcc_date = datetime.strptime(item[4][:16], "%Y-%m-%d %H:%M")

            date = datetime.strptime(item[self.__map_fields(eval_field)][:16], "%Y-%m-%d %H:%M")
            if in_percentage:
                fixing_date = datetime.strptime(item[2][:16], "%Y-%m-%d %H:%M")
                lifetime = fixing_date - vcc_date
                date_lifetime = fixing_date - date
                if lifetime.days > 0:
                    percentage = (date_lifetime.days - lifetime.days) / lifetime.days * 100
                    print(percentage)
                    data_points.append(percentage)
            else:
                delta_date = vcc_date - date
                data_points.append(delta_date.days)


        n, bin, patches = plt.hist(data_points, 60, density=True)
        #plt.title('Distribution of inaccuracies in lifetimes - {0}'.format(self.name))
        plt.xlabel('Lifetime difference in {0}'.format('days' if not in_percentage else '%'))
        plt.ylabel('Percentage')
        X = np.arange(-4000, 4000, 10)
        Y = norm.pdf(X, np.mean(data_points), np.std(data_points))

        plt.plot(X, Y)
        mean = np.mean(data_points)
        normtest_data = [x - mean for x in data_points]
        print()
        print(normaltest(normtest_data))
        print(np.mean(data_points))
        print(np.std(data_points))
        print()
        #plt.text(2500, 40, 'Mean: ' + str(np.mean(data_points)) + '\n Median '+ str(np.median(data_points)) + '\n 1st Quartile: '+ str(np.quantile(data_points, 0.25)) + '\n 2nd Quartile: ' + str(np.quantile(data_points, 0.75)) + '\n Deviation: ' + str(np.mean(np.absolute(data_points))))
        plt.savefig('heuristic_miss_distribution.pdf',  bbox_inches='tight')

    def plot_lifetime_distribution(self, eval_field, cut_off=None):

        if self.new_figure_required:
            plt.figure()
        self.new_figure_required = True
        data_points_1 = []
        data_points_2 = []

        for item in self.data:

            fixing_date = datetime.strptime(item[2][:16], "%Y-%m-%d %H:%M")


            date = datetime.strptime(item[self.__map_fields(eval_field)][:16], "%Y-%m-%d %H:%M")
            delta_date = fixing_date - date
            if cut_off is not None and 0 < cut_off < fixing_date.year:
                data_points_2.append(delta_date.days)
            else:
                data_points_1.append(delta_date.days)

        fit = powerlaw.Fit(data_points_1)
        comp = fit.distribution_compare('lognormal', 'power_law')
        print(comp)
        comp = fit.distribution_compare('lognormal', 'exponential')
        print(comp)
        comp = fit.distribution_compare('lognormal', 'truncated_power_law')
        print(comp)

        n_log, bins_log, patches_log = plt.hist(data_points_1, 40, density=False)
        plt.axvline(np.mean(data_points_1), color='orange', linestyle='-', linewidth=1)

        plt.title('Distribution of vulnerability lifetimes - {0} {1}'.format(self.name, "<= {0}".format(cut_off) if cut_off is not None and cut_off > 0 else ""))
        plt.xlabel('Lifetime in days')
        plt.ylabel('Number of CVEs')

        print('Mean: ' + str(np.mean(data_points_1)) + '\n 1st Quartile: '+ str(np.quantile(data_points_1, 0.25)) + '\n 2nd Quartile: ' + str(np.quantile(data_points_1, 0.75)) + '\n Deviation: ' + str(np.mean(np.absolute([x - np.mean(data_points_1) for x in data_points_1]))))
        print('{0}% are below {1} | {2} data points'.format(percentileofscore(data_points_1, np.mean(data_points_1)), np.mean(data_points_1), len(data_points_1)))
        plt.savefig("distribution_{0}.pdf".format(self.name), bbox_inches='tight')

        if cut_off is not None and cut_off > 0:
            plt.figure()
            n_log, bins_log, patches_log = plt.hist(data_points_2, 40, density=False)
            plt.axvline(np.mean(data_points_2), color='orange', linestyle='-', linewidth=1)
            plt.title('Distribution of vulnerability lifetimes - {0} {1}'.format(self.name, "After {0}".format(cut_off) if cut_off is not None and cut_off > 0 else ""))
            plt.xlabel('Lifetime in days')
            plt.ylabel('Number of CVEs')

            print('Mean: ' + str(np.mean(data_points_2)) + '\n 1st Quartile: '+ str(np.quantile(data_points_2, 0.25)) + '\n 2nd Quartile: ' + str(np.quantile(data_points_2, 0.75)) + '\n Deviation: ' + str(np.mean(np.absolute([x - np.mean(data_points_2) for x in data_points_2]))))
            print('{0}% are below {1}| {2} data points'.format(percentileofscore(data_points_2, np.mean(data_points_2)), np.mean(data_points_2), len(data_points_2)))
            plt.savefig("distribution_{0}_second.pdf".format(self.name), bbox_inches='tight')

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

    def cwe_lifetimes(self):
        cwes = {}
        for item in self.data:
            try:
                cwe_id = item[14].replace('CWE-', '')
            except:
                print('{0} defines no cwe'.format(item[0]))
            fixing_date = datetime.strptime(item[2][:16], "%Y-%m-%d %H:%M")
            date = datetime.strptime(item[self.__map_fields('weighted')][:16], "%Y-%m-%d %H:%M")
            delta = fixing_date - date

            root_cwe = self.get_root_cwe(cwe_id)
            if root_cwe in cwes:
                cwes[root_cwe].append(delta.days)
            else:
                cwes[root_cwe] = [delta.days]

        sample_693 = []
        sample_682 = []
        sample_707 = []
        sample_664 = []
        sample_691 = []
        sample_118 = []
        sample_710 = []
        for key, value in cwes.items():
            print('CWE-{0}: {1} days - {2} datapoints - {3}'.format(key, np.mean(value), len(value), self.get_cwe_description(key)))
            if str(key) == str(693):
                sample_693 = value
            if str(key) == str(682):
                sample_682 = value
            if str(key) == str(707):
                sample_707 = value
            if str(key) == str(664):
                sample_664 = value
            if str(key) == str(691):
                sample_691 = value
            if str(key) == str(118):
                sample_118 = value
            if str(key) == str(710):
                sample_710 = value

        self.__pairwise_comparison([['CWE-693', sample_693], ['CWE-682', sample_682], ['CWE-664', sample_664]
                                       , ['CWE-710', sample_710]
                                    , ['CWE-691', sample_691]
                                       , ['CWE-707', sample_707]
                                      , ['CWE-118', sample_118]
                                    ])
        print(stats.kruskal(sample_693, sample_682, sample_707, sample_664, sample_691, sample_118, sample_710))

    def score_lifetimes(self):
        scores = {}
        for item in self.data:
            try:
                cvss_score = float(item[15])
            except:
                print('{0} defines no cwe'.format(item[0]))
            fixing_date = datetime.strptime(item[2][:16], "%Y-%m-%d %H:%M")
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
        mapping = {'average': 11,
                   'upper': 8,
                   'lower': 10,
                   'heuristic': 6,
                   'weighted': 12,
                   'correct': 4}
        return mapping[field.lower()]

    def __pairwise_comparison(self, input):
        print()
        for i in range(len(input)):
            cwe_1 = input[i][0]
            data_1 = input[i][1]

            for x in range(i + 1, len(input)):
                cwe_2 = input[x][0]
                data_2 = input[x][1]
                print("{0} vs {1}: {2}".format(cwe_1, cwe_2, stats.mannwhitneyu(data_1, data_2, alternative='two-sided')))
            print()

    def __plot_dict(self, data, point='kx', print_=False, gt_heuristic_ratio = {}, **kwargs):
        x_axis = []
        y_axis = []
        for key, items in data.items():
            if print_:
                print('{0}: {1} {2}'.format(key, len(items), "  {0} | {1} -> {2}%".format(gt_heuristic_ratio[key][0], gt_heuristic_ratio[key][1], gt_heuristic_ratio[key][0] / len(items) * 100) if key in gt_heuristic_ratio else ""))
            if len(items) >= self.confidence_size:
                x_axis.append(key)
                y_axis.append(np.mean(items))

        plt.plot(x_axis, y_axis, point, **kwargs)

    def __plot_linear_fit(self, data, confidence=True):
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
        plt.plot(x_axis, regr.predict(X), '--k')
        print(regr.score(X, Y), regr.coef_[0])
        #plt.text(x_axis[0], 2000, 'r={0}\ncoef={1}'.format(regr.score(X, Y), regr.coef_[0]))

    def __map_old_cves(self, cve):
        mappings= {'264': '693', '189': '682', '399': '664', '16': '710', '254': '693', '310': '693', '255': '693', '19': '707', '199': '707', '316':'664', '275': '693', '388': '703', '361': '664', '417': '693'}
        return mappings[cve]
