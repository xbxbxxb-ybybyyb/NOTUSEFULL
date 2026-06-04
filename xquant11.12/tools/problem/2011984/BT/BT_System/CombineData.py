"""下载原始行情数据————update @2021.6.30"""

import os
import time
import json
import pickle
import numpy as np
import pandas as pd
import sklearn.cluster as skclust
from DataAPI.ARootPath import RootPath
from DataAPI.TradingDay import trading_day_code, trading_day
from Utils.MultiTasks import main_multiprocess
from Utils.UtilsCode import get_code_status
from xquant.factordata import FactorData
from xquant.xqutils.xqfile import Pyfile


class CombineData:
    def __init__(self, portfolio, code_list, start_date, end_date, is_calc_vol_limit=False):
        self.portfolio = portfolio
        self.code_list = code_list
        self.start_date = str(start_date)
        self.end_date = str(end_date)
        self.__is_calc_vol_limit = is_calc_vol_limit

        self.origin_data_path = RootPath().get_origin_data_path(portfolio)
        self.__hdfs_path = ''
        self.__combine_path = ''

        # 设置计算Vol Limit的参数
        self.order_capacity_percentile = [0.25, 0.75]
        self.look_back = 20
        self.lag = 200
        self.method = 'Cluster'

    def start(self, multi_process_nums):
        hdfs_path_list = get_origin_data_list(self.portfolio, self.start_date, self.end_date)
        for hdfs_path in hdfs_path_list:
            self.__hdfs_path = hdfs_path
            self.__combine_path = f'/data/user/011668/{self.__hdfs_path}'
            os.makedirs(self.__combine_path, exist_ok=True)
            all_codes2 = self.get_non_existing_codes(self.code_list)
            while len(all_codes2) > 0:
                main_multiprocess(self.single_task, all_codes2, multi_process_nums, is_sum_result=False)
                Pyfile().upload(self.__hdfs_path, self.__combine_path)  # NAS传到HDFS上
                all_codes2 = self.get_non_existing_codes(self.code_list)

    def get_non_existing_codes(self, all_codes):
        py = Pyfile()
        codes_non_existing = []
        for code in all_codes:
            if (not py.exists(f'{self.__hdfs_path}/{code}/Data.pickle')) or \
                    (not os.path.exists(f'{self.__combine_path}/{code}/Data.pickle')) or \
                    (self.__is_calc_vol_limit and not py.exists(f'{self.__hdfs_path}/{code}/OrderCapacity.json')):
                codes_non_existing.append(code)
        print('Combine Data: {} stocks need to combine'.format(len(codes_non_existing)))
        return codes_non_existing

    def single_task(self, code_list):
        for code in code_list:
            self.combine_data(code)
            if self.__is_calc_vol_limit:
                self.calc_vol_limit(code)

    def combine_data(self, code):
        os.makedirs('{}/{}'.format(self.__combine_path, code), exist_ok=True)
        tick_data = []
        transaction_data = []
        valid_dates = []
        all_trading_days = self.__get_trading_days()
        for date in all_trading_days:
            code_data_path = '{}/{}/{}/Data.pickle'.format(self.origin_data_path, code, date)
            if not os.path.exists(code_data_path):
                print("Data.pickle not found for {} on {}.".format(code, date))
            else:
                with open(code_data_path, 'rb') as f:
                    data = pickle.load(f)
                tick_data.append(data[0])
                transaction_data.append(data[1])
                valid_dates.append(date)

        with open(f'{self.__combine_path}/{code}/Dates.pickle', "wb") as f:
            pickle.dump(valid_dates, f)
        with open(f'{self.__combine_path}/{code}/Data.pickle', 'wb') as f:
            pickle.dump((tick_data, transaction_data), f)

    def calc_vol_limit(self, code):
        start = time.perf_counter()
        tick_volume_dict = self.get_tick_vol(code)
        order_capacity_index = self.calc_order_capacity(tick_volume_dict)
        high_vol_index = self.calc_high_vol(tick_volume_dict)

        # 存储文件
        order_capacity_file = "{}/{}/OrderCapacity.json".format(self.__combine_path, code)
        if os.path.exists(order_capacity_file):
            with open(order_capacity_file, "r") as f:
                order_capacity = json.load(f)
            order_capacity["OrderCapacity"].update(order_capacity_index)
            order_capacity["OrderCapacity"] = dict(sorted(order_capacity["OrderCapacity"].items(), key=lambda x: x[0]))
            order_capacity["HighVol"].update(high_vol_index)
            order_capacity["HighVol"] = dict(sorted(order_capacity["HighVol"].items(), key=lambda x: x[0]))
        else:
            order_capacity = {"code": code, "OrderCapacity": order_capacity_index, "HighVol": high_vol_index}
        with open(order_capacity_file, "w") as f:
            json.dump(order_capacity, f)
        print("{} {}-{} ,train time: {}".format(code, self.start_date, self.end_date, round((time.perf_counter() - start) / 60, 2)))

    def get_tick_vol(self, code):
        date_list = self.get_valid_dates(code)
        tick_volume_dict = dict()
        for trade_date in date_list:
            try:
                fd = FactorData()
                tick_df = fd.get_factor_value("ZeusDataLib", code, str(trade_date), ["T_Date", "T_Time", "T_Volume"])
                tick_df.columns = list(map(lambda x: x.replace("T_", ""), list(tick_df.columns)))
                tick_volume_dict[trade_date] = tick_df
            except:
                continue
        return tick_volume_dict

    def calc_order_capacity(self, tick_volume_dict):
        all_trading_days = self.__get_trading_days()
        if len(tick_volume_dict) == 0:
            return {}.fromkeys(all_trading_days, 0)
        code_order_capacity = dict()
        for trade_date in all_trading_days:
            volume_df = pd.concat(self.get_dict_select(tick_volume_dict, trade_date))
            day_volume = sorted(list(volume_df['Volume']))
            filter_day_volume = day_volume[int(self.order_capacity_percentile[0] * len(day_volume)):
                                           int(self.order_capacity_percentile[1] * len(day_volume))]
            vol_mean = int(np.nanmean(np.array(filter_day_volume)))
            code_order_capacity.update({trade_date: vol_mean})
        return code_order_capacity

    def calc_high_vol(self, tick_volume_dict):
        all_trading_days = self.__get_trading_days()
        if len(tick_volume_dict) == 0:
            return {}.fromkeys(all_trading_days, 0)
        volume_holder = {}
        date_list = sorted(list(tick_volume_dict.keys()))
        for date in date_list:
            tick_df = tick_volume_dict[date]
            ma_volume = np.log(tick_df["Volume"].astype(np.float64) + 100).rolling(self.lag).mean()[self.lag:]
            volume_holder.update({date: ma_volume.values[None].T})

        code_high_vol = dict()
        for trade_date in all_trading_days:
            volume_array = np.vstack(self.get_dict_select(volume_holder, trade_date))
            high_vol = 0.
            if self.method == "Cluster":
                a = skclust.KMeans(n_clusters=2).fit(volume_array)
                ub = volume_array[a.labels_ == a.cluster_centers_.argmax()].min()
                lb = volume_array[a.labels_ == a.cluster_centers_.argmin()].max()
                high_vol = int((ub + lb) / 2 * 10) / 10
            elif self.method == "Median":
                median = np.nanmedian(volume_array)
                high_vol = int(median * 10) / 10
            code_high_vol.update({trade_date: high_vol})
        return code_high_vol

    def get_valid_dates(self, code):
        """获取某一只股票，所有回测的日期（剔除停牌日期）"""
        date_list = np.array(trading_day_code(code, int(self.start_date) - 10000, int(self.end_date)))
        date_list1 = date_list[date_list < int(self.start_date)][-self.look_back:].tolist()
        date_list2 = date_list[date_list >= int(self.start_date)].tolist()
        valid_days = [str(x) for x in sorted(date_list1 + date_list2)]
        return valid_days

    def get_dict_select(self, tick_vol_dict, trade_date):
        date_list = sorted(list(tick_vol_dict.keys()))
        date_select = list(np.array(date_list)[np.array(date_list) < trade_date])[-self.look_back:]
        out_list = []
        for date in date_select:
            out_list.append(tick_vol_dict[date])
        return out_list

    def reset_origin_data_path(self, origin_data_path):
        """重新设置原始数据路径（比如level 2 plus数据）"""
        self.origin_data_path = origin_data_path

    def __get_trading_days(self):
        # 根据hdfs_path拆解交易日期
        date_str = self.__hdfs_path.split('/')[-1]
        if '-' not in date_str:
            return [date_str]
        else:
            st_date, ed_date = date_str.split('-')
            return trading_day(st_date, ed_date)


def get_origin_data_list(portfolio, start_date, end_date):
    # 按月拆解存储的月份
    year, month, day = start_date[0:4], start_date[4:6], start_date[6:8]
    end_year, end_month, end_day = end_date[0:4], end_date[4:6], end_date[6:8]
    last_day_dict = {'01': '31', '02': '28', '03': '31', '04': '30', '05': '31', '06': '30',
                     '07': '31', '08': '31', '09': '30', '10': '31', '11': '30', '12': '31'}

    hdfs_path_list = []
    while not (year == end_year and month == end_month):
        if int(year) % 4 == 0:
            last_day_dict['02'] = '29'
        if day != '01':
            hdfs_path = f'BT_Data/{portfolio}/{year}{month}{day}-{year}{month}{last_day_dict[month]}'
            hdfs_path_list.append(hdfs_path)
            day = '01'
        else:
            hdfs_path = f'BT_Data/{portfolio}_store/{year}{month}{day}-{year}{month}{last_day_dict[month]}'
            hdfs_path_list.append(hdfs_path)
        if month != '12':
            month = list(last_day_dict.keys())[int(month)]
        else:
            month = '01'
            year = str(int(year) + 1)
    if end_day == day:
        hdfs_path = f'BT_Data/{portfolio}/{year}{month}{day}'
    elif end_day != last_day_dict[month]:
        hdfs_path = f'BT_Data/{portfolio}/{year}{month}{day}-{year}{month}{end_day}'
    else:
        hdfs_path = f'BT_Data/{portfolio}_store/{year}{month}{day}-{year}{month}{end_day}'
    hdfs_path_list.append(hdfs_path)
    # print(f'{portfolio} 回测日期：{start_date}-{end_date}, {hdfs_path_list}')
    return hdfs_path_list


def check_non_existing_codes(all_codes, trade_date, portfolio):
    origin_data_path = RootPath().get_origin_data_path(portfolio)
    existing_codes, non_existing_codes, tp_codes = [], [], []
    for code in all_codes:
        code_data_path = f'{origin_data_path}/{code}/{trade_date}/Data.pickle'
        if not os.path.exists(code_data_path):
            code_status = get_code_status(code, trade_date)
            if code_status[code] == '停牌':
                tp_codes.append(code)
            else:
                non_existing_codes.append(code)
        else:
            existing_codes.append(code)
    if len(tp_codes) > 0:
        print(f'{origin_data_path}, {" " * (50-len(origin_data_path))}{len(existing_codes)}/{len(all_codes)}, 停牌{len(tp_codes)}只{tp_codes}')
    else:
        print(f'{origin_data_path}, {" " * (50 - len(origin_data_path))}{len(existing_codes)}/{len(all_codes)}')
    if len(non_existing_codes) > 0:
        print(f'缺失{len(non_existing_codes)}只Data.pickle ', non_existing_codes)
