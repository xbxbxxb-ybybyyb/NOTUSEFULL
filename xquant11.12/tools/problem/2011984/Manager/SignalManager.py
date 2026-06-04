"""信号管理模块——update @2021.6.30"""

import pandas as pd
from Utils.UtilsCode import code_classify
from xquant.factordata import FactorData
from Manager.UtilsModel.VotingTriggers import split_col_names


class SignalManager:
    def __init__(self, code, date_list, signal_lib, tag_lib=None, mock_lib=None, vt_name='8min', signal_col_names=None,
                 is_add_tag=False, is_get_valid=False, is_add_mock=True, is_add_pct=False, is_add_pv1=False):
        # signal_col_names为制定输出的列明（None为输出ave_long和ave_short
        # is_add_tag为是否输出结果加入tag列，默认False为不加入
        # is_get_valid为是否剔除午盘（11:25-11:30）和尾盘（14:50-15:00）数据，默认False为不剔除
        # is_add_mock为是否加入补的tick数据，默认True为包括
        # is_add_pct 为是否加入涨跌幅数据，默认False为不加入
        self.code = code
        self.signal_lib = signal_lib
        self.__date_list = date_list
        self.__tag_lib = tag_lib
        self.__mock_lib = mock_lib
        self.__vt_name = vt_name
        self.__signal_col_names = ['Timestamp', 'ave_long', 'ave_short'] if signal_col_names is None else signal_col_names
        if is_add_tag:
            self.__signal_col_names += ['tag1minLong', 'tag2minLong', 'tag5minLong', 'tag1minShort', 'tag2minShort', 'tag5minShort']
        self.__is_add_tag = is_add_tag  # 是否加入tag数据
        self.__is_add_mock = is_add_mock  # 是否加入补的tick数据
        self.__is_add_pct = is_add_pct  # 是否加入涨跌幅数据
        self.__is_add_pv1 = is_add_pv1  # 是否加入一档买卖盘口数据
        self.__is_add_sec = float(self.__vt_name[:-3]) % 1 in [0.25, 0.5, 0.75]  # 是否加入秒频（15s和30s）信号预测值
        self.__valid_date_list, self.__signal_data_list = self.__load_signal_data(is_get_valid)

    def __load_signal_data(self, is_get_valid):
        signal_data_list = []
        valid_date_list = []
        for trade_date in self.__date_list:
            fa = FactorData()
            try:
                prediction_names = ['timestamp', 'ticktime', 'prediction1minLong', 'prediction2minLong', 'prediction5minLong',
                                    'prediction1minShort', 'prediction2minShort', 'prediction5minShort']
                if self.__is_add_sec:
                    prediction_names += ['prediction15secLong', 'prediction15secShort', 'prediction30secLong', 'prediction30secShort']
                data = fa.get_factor_value(self.signal_lib, self.code, trade_date, prediction_names)
                rename_dict = {'timestamp': 'Timestamp', 'ticktime': 'Ticktime'}
                rename_dict.update(dict([(x, x.replace('prediction', '').replace('All', '')) for x in prediction_names[2:]]))
                data = data.rename(columns=rename_dict)

                column_long = data[[x + 'Long' for x in split_col_names(self.__vt_name)]].mean(axis=1)
                data = data.assign(ave_long=column_long)
                column_short = data[[x + 'Short' for x in split_col_names(self.__vt_name)]].mean(axis=1)
                data = data.assign(ave_short=column_short)

                if is_get_valid:
                    data = data[(('09:30:00' < data['Ticktime']) & (data['Ticktime'] < '11:25:00')) |
                                ('13:00:00' < data['Ticktime']) & (data['Ticktime'] < '14:50:00')]
                elif code_classify(self.code) != 'cb' and self.__vt_name == '8min':
                    data = self.average_special_time(data, '11:25:00', '11:28:00', '11:30:00')
                    data = self.average_special_time(data, '14:52:00', '14:55:00', '14:57:00')

                if self.__is_add_tag:
                    tag_names = ['timestamp'] + [x.replace('prediction', 'tag').replace('All', '')
                                                 for x in prediction_names if x.startswith('prediction')]
                    if self.__tag_lib is not None:
                        tag_lib = self.__tag_lib
                    else:
                        tag_lib = 'Factor_Zeus_Plus' if code_classify(self.code) != 'cb' else 'CBFactor_Zeus_Super'
                    data_tag = fa.get_factor_value(tag_lib, self.code, trade_date, tag_names).rename(columns={'timestamp': 'Timestamp'})
                    data = pd.concat([data.set_index('Timestamp'), data_tag.set_index('Timestamp') * 1000], axis=1).reset_index()

                if not self.__is_add_mock:  # 剔除补的数据
                    col_names = ['T_Timestamp', 'T_IsMock']
                    if self.__is_add_pct:
                        col_names += ['T_LastPrice', 'T_PreviousClose']
                    if self.__is_add_pv1:
                        col_names += ['T_AskPrice', 'T_BidPrice', 'T_AskVolume', 'T_BidVolume']
                    mock_lib = 'ZeusDataLib' if self.__mock_lib is None else self.__mock_lib
                    data2 = fa.get_factor_value(mock_lib, self.code, trade_date, col_names). \
                        rename(columns={'T_Timestamp': 'Timestamp'}).set_index('Timestamp')
                    data2_col_name = ['T_IsMock']
                    if self.__is_add_pct:
                        data2['pct'] = data2['T_LastPrice'] / data2['T_PreviousClose'] - 1
                        data2_col_name += ['pct', 'T_LastPrice']
                    if self.__is_add_pv1:
                        data2['bid_p0'] = [x[0] if x is not None else 0 for x in data2['T_BidPrice']]
                        data2['ask_p0'] = [x[0] if x is not None else 0 for x in data2['T_AskPrice']]
                        data2['bid_v0'] = [x[0] if x is not None else 0 for x in data2['T_BidVolume']]
                        data2['ask_v0'] = [x[0] if x is not None else 0 for x in data2['T_AskVolume']]
                        data2_col_name += ['bid_p0', 'ask_p0', 'bid_v0', 'ask_v0']
                    data2 = data2[data2_col_name]
                    data = pd.concat([data.set_index('Timestamp'), data2], axis=1).reset_index()
                    data = data[data['T_IsMock'] == 0]

                valid_date_list.append(trade_date)
                signal_data_list.append(data)
            except:
                continue
        return valid_date_list, signal_data_list

    @staticmethod
    def average_special_time(data, time1, time2, time3):
        """临近午盘和尾盘收盘时的信号平均特殊处理"""
        filter1 = (data['Ticktime'] >= time1) & (data['Ticktime'] < time2)
        index1 = data.loc[filter1, 'Ticktime'].index
        ave_long1 = (data.loc[index1, '1minLong'] + data.loc[index1, '2minLong']) / 2
        ave_short1 = (data.loc[index1, '1minShort'] + data.loc[index1, '2minShort']) / 2
        data.loc[index1, 'ave_long'] = ave_long1
        data.loc[index1, 'ave_short'] = ave_short1

        filter2 = (data['Ticktime'] >= time2) & (data['Ticktime'] < time3)
        index2 = data.loc[filter2, 'Ticktime'].index
        ave_long2 = data.loc[index2, '1minLong']
        ave_short2 = data.loc[index2, '1minShort']
        data.loc[index2, 'ave_long'] = ave_long2
        data.loc[index2, 'ave_short'] = ave_short2
        return data

    def get_signals(self):
        if len(self.__signal_data_list) > 0:
            signals = pd.concat(self.__signal_data_list, axis=0)[self.__signal_col_names].dropna(axis=0)
            signals.index = range(signals.shape[0])
            return signals

    def get_signals_split(self):
        if len(self.__signal_data_list) > 1:
            half = int(len(self.__signal_data_list) / 2)
            signals_first = pd.concat(self.__signal_data_list[:half], axis=0)[self.__signal_col_names]
            signals_second = pd.concat(self.__signal_data_list[half:], axis=0)[self.__signal_col_names]
            return signals_first, signals_second
        else:
            return None, None

    def get_signal_dict(self):
        # 获取按天来汇总的信号矩阵（输出为字典，key为日期，value为当日的信号矩阵）
        return dict(zip(self.__valid_date_list, self.__signal_data_list))
