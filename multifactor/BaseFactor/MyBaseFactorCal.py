# -*- coding: utf-8 -*-

from abc import abstractmethod
import pandas as pd
import numpy as np
import datetime as dt
from xquant.factordata import FactorData

fa = FactorData()

def convert_date_time_to_datetime(date_list_int: list, time_int: int):
    # if time_int == 1500:
    #     hour = 0
    #     minute = 0
    # else:
    hour = divmod(time_int, 100)[0]
    minute = divmod(time_int, 100)[1]
    result_list = [dt.datetime(int(str(i_date)[0:4]), int(str(i_date)[4:6]), int(str(i_date)[6:8]), hour, minute).strftime("%Y%m%d%H%M") for
                   i_date in date_list_int]
    # result_list = [i.timestamp() for i in result_list] #index变成时间戳，股票组做法
    return result_list


def convert_df(factor_df: pd.DataFrame, time_int: int):
    dateint_list = list(factor_df.index)
    factor_df.index = convert_date_time_to_datetime(dateint_list, time_int)
    return factor_df


# def convert_index(factor_df: pd.DataFrame):
#     index_datetime = list(factor_df.index)
#     index_int = [int(dt.datetime.strftime(x, '%Y%m%d')) for x in index_datetime]
#     factor_df['date'] = index_int
#     factor_df.index = index_int
#     factor_df = factor_df.set_index(['date'])
#     return factor_df


def get_complete_minute_list():
    complete_minute_list = [925, 930, 931, 932, 933, 934, 935, 936, 937, 938, 939, 940, 941, 942, 943, 944, 945, 946,
                            947, 948, 949, 950, 951, 952, 953, 954, 955, 956, 957, 958, 959, 1000, 1001, 1002, 1003,
                            1004, 1005, 1006, 1007, 1008, 1009, 1010, 1011, 1012, 1013, 1014, 1015, 1016, 1017, 1018,
                            1019, 1020, 1021, 1022, 1023, 1024, 1025, 1026, 1027, 1028, 1029, 1030, 1031, 1032, 1033,
                            1034, 1035, 1036, 1037, 1038, 1039, 1040, 1041, 1042, 1043, 1044, 1045, 1046, 1047, 1048,
                            1049, 1050, 1051, 1052, 1053, 1054, 1055, 1056, 1057, 1058, 1059, 1100, 1101, 1102, 1103,
                            1104, 1105, 1106, 1107, 1108, 1109, 1110, 1111, 1112, 1113, 1114, 1115, 1116, 1117, 1118,
                            1119, 1120, 1121, 1122, 1123, 1124, 1125, 1126, 1127, 1128, 1129, 1300, 1301, 1302, 1303,
                            1304, 1305, 1306, 1307, 1308, 1309, 1310, 1311, 1312, 1313, 1314, 1315, 1316, 1317, 1318,
                            1319, 1320, 1321, 1322, 1323, 1324, 1325, 1326, 1327, 1328, 1329, 1330, 1331, 1332, 1333,
                            1334, 1335, 1336, 1337, 1338, 1339, 1340, 1341, 1342, 1343, 1344, 1345, 1346, 1347, 1348,
                            1349, 1350, 1351, 1352, 1353, 1354, 1355, 1356, 1357, 1358, 1359, 1400, 1401, 1402, 1403,
                            1404, 1405, 1406, 1407, 1408, 1409, 1410, 1411, 1412, 1413, 1414, 1415, 1416, 1417, 1418,
                            1419, 1420, 1421, 1422, 1423, 1424, 1425, 1426, 1427, 1428, 1429, 1430, 1431, 1432, 1433,
                            1434, 1435, 1436, 1437, 1438, 1439, 1440, 1441, 1442, 1443, 1444, 1445, 1446, 1447, 1448,
                            1449, 1450, 1451, 1452, 1453, 1454, 1455, 1456, 1457, 1458, 1459, 1500]
    return complete_minute_list


class DailyFactorPlayerBase(object):
    def __init__(self, alpha_factor_root_path, stock_list, start_date, end_date, params):
        self.alpha_factor_root_path = alpha_factor_root_path
        self.stock_list = stock_list
        self.params = params
        # self.trading_day_list = Dtk.get_trading_day(start_date, end_date)
        self.trading_day_list = fa.tradingday(start_date, end_date)

        self.start_date = self.trading_day_list[0]
        self.end_date = self.trading_day_list[-1]
        self.ans_df = pd.DataFrame(columns=stock_list)
        self.type = self.params['type']  # 如果是日间因子，参数设置为1500，如果是fix因子设置为对应时间点
        self.play_day_lag = self.params['play_day_lag']  # 计算T日的日间因子时，播放时带有play_day前缀的数据会传入generator_lag日（包括T日）的数据，计算T日的fix因子时，播放时带有play_day前缀的数据会传入generator_lag-1日（不包括T日）的数据
        self.play_min_lag = self.params['play_min_lag']  # 计算T日的因子时，播放时带有play_minute前缀的数据会传入generator_lag日（包括T日，如果是fix因子，T日的数据只会有截至固定时点之前的数据）的数据
        self.generator_lag = self.params['generator_lag']  # 在factor_generator中传入的data会向前多传入generator_lag-1日的数据，并且play_intermediate也会多生成generator_lag-1日的返回值
        self.data_base_str = self.params['Data_Base']
        self.data_base = {}
        self.data_base_play = {}
        self.type_all = [1000, 1030, 1100, 1300, 1330, 1400, 1430, 1500]
        self.temp_start_date = None
        self.temp_end_date = None

    @abstractmethod
    def factor_generator(self):
        return None

    def play_intermediate(self, func):
        start_date = self.temp_start_date
        end_date = self.temp_end_date
        start_date = fa.tradingday(start_date, -self.generator_lag)[0]
        trading_day_list = fa.tradingday(start_date, end_date)
        intermediate = pd.DataFrame(columns=self.stock_list)
        for temp_end_date in trading_day_list:
            for data_name_str in self.data_base_str:
                if data_name_str[:4] == 'play':
                    if not self.type in self.type_all:
                        print('error type')
                        exit()
                    if self.type == 1500:
                        if data_name_str[5:11] == 'minute':
                            start_date2 = fa.tradingday(temp_end_date, -self.play_min_lag)[0]
                            end_date2 = temp_end_date
                        elif data_name_str[5:8] == 'day':
                            start_date2 = fa.tradingday(temp_end_date, -self.play_day_lag)[0]
                            end_date2 = temp_end_date
                        else:
                            print('error play_data name!')
                            start_date2 = start_date
                            end_date2 = temp_end_date
                            exit()
                    else:
                        if data_name_str[5:11] == 'minute':
                            start_date2 = fa.tradingday(temp_end_date, -self.play_min_lag)[0]
                            idx = get_complete_minute_list().index(self.type) - 1
                            end_date2 = temp_end_date * 10000 + get_complete_minute_list()[idx]
                        elif data_name_str[5:8] == 'day':
                            if self.play_day_lag >= 2:
                                start_date2 = fa.tradingday(temp_end_date, -self.play_day_lag)[0]
                                end_date2 = fa.tradingday(temp_end_date, -2)[0]
                            else:
                                start_date2 = start_date
                                end_date2 = temp_end_date
                                print('error play_day_lag, need > 1!')
                                exit()
                        else:
                            print('error play_data name!')
                            start_date2 = start_date
                            end_date2 = temp_end_date
                            exit()
                    if isinstance(start_date2, int):
                        start_date2 = str(start_date2)
                    if isinstance(end_date2, int):
                        end_date2 = str(end_date2)
                    temp_data = self.data_base[data_name_str].loc[start_date2:end_date2]
                    self.data_base_play.update({data_name_str: temp_data})
            temp_intermediate = func()
            self.data_base_play = {}
            if isinstance(temp_intermediate, pd.DataFrame):
                temp_intermediate = temp_intermediate.iloc[-1]
                temp_intermediate = temp_intermediate.to_frame().T
                temp_intermediate.index = [dt.datetime.strptime(str(temp_end_date), '%Y%m%d')]
            if isinstance(temp_intermediate, pd.Series):
                temp_intermediate = temp_intermediate.to_frame().T
                temp_intermediate.index = [dt.datetime.strptime(str(temp_end_date), '%Y%m%d')]
            # print(temp_intermediate)
            # print(temp_intermediate.columns)
            intermediate = pd.concat([intermediate, temp_intermediate], axis=0)
        return intermediate

    def load_data_management(self, start_date, end_date):
        data_base = {}
        for data_name_str in self.data_base_str:
            if data_name_str[:4] == 'play':
                if data_name_str[5:11] == 'minute':
                    start_date2 = fa.tradingday(start_date, -(self.generator_lag+self.play_min_lag-1))[0]
                elif data_name_str[5:8] == 'day':
                    start_date2 = fa.tradingday(start_date, -(self.generator_lag+self.play_day_lag-1))[0]
                else:
                    print('error play_data name!')
                    start_date2 = start_date
                    exit()
            else:
                start_date2 = fa.tradingday(start_date, -self.generator_lag)[0]
            temp_data = self.load_data(data_name_str, start_date2, end_date)
            data_base.update({data_name_str: temp_data})
        return data_base

    @abstractmethod
    def load_data(self, data_name_str, start_date, end_date):
        return None

    def single_task(self, start_date, end_date):
        self.temp_start_date = start_date
        self.temp_end_date = end_date
        self.data_base = self.load_data_management(start_date, end_date)
        if isinstance(start_date, int):
            start_date = str(start_date)
        if isinstance(end_date, int):
            end_date = str(end_date)
        factor_data = self.factor_generator()[start_date:end_date]
        return factor_data

    def factor_calc(self):
        trading_day_list = self.trading_day_list
        date_split_list = self.date_split(trading_day_list, 100)
        # 分时间段计算因子值
        for start_date, end_date in date_split_list:
            print("{}-{} factor is calculating.".format(start_date, end_date))
            sub_factor_value = self.single_task(start_date, end_date)
            # sub_factor_value = convert_index(sub_factor_value)
            sub_trading_day_list = fa.tradingday(start_date, end_date)
            sub_factor_value = sub_factor_value.reindex(sub_trading_day_list)
            self.ans_df = pd.concat([self.ans_df, sub_factor_value], axis=0, sort=True)

        # print(self.ans_df)
        self.ans_df = convert_df(self.ans_df, self.type)
        return self.ans_df

    @staticmethod
    def date_split(date_list: list, num_date: int=50):
        date_len = date_list.__len__()
        num_group = int(np.ceil(date_len/num_date))
        group_list = []
        for i in range(num_group):
            i_group = i + 1
            if i_group < num_group:
                start = date_list[i*num_date]
                end = date_list[(i+1)*num_date-1]
            else:
                start = date_list[i*num_date]
                end = date_list[-1]
            group_list.append([start, end])
        return group_list
