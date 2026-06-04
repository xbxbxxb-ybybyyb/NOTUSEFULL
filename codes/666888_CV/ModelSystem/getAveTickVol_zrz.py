"""
created on 2018/12/18 by 006566 -- 通过量化平台查询VolMean
updated on 2018/12/19 -- 删除全部volume中首25%的tick和尾25%的tick; 以50天为跨度、将日期切分;
                         提取volume的数据源切换为wind落地数据库
"""

import System.GetTradingDay as GTD
import platform
import os
from MDCDataProvider.DataProvider import DataProvider
import xquant.quant as xq
import numpy as np
import datetime as dt
import pandas as pd
from xquant.multifactor.IO import IO
from xquant.multifactor.IO.IO_enums import *

mdp = DataProvider()


def get_complete_stock_list() -> list:
    # 获取所有股票的并集（从2013年至今），返回一个股票代码list，其中含有退市股票；为了简化起见，股票列表固定为3542只
    # 2018年8月14日以后的新股也不更新
    complete_stock_list = []
    if platform.system() == "Windows":
        complete_stock_list_path = "S:\\Apollo\\StockList20181130.csv"
    else:
        complete_stock_list_path = "/app/data/006566/Apollo/StockList20181130.csv"
    if os.path.exists(complete_stock_list_path):
        with open(complete_stock_list_path) as file:
            for line in file:
                complete_stock_list.append(line[0:9])
        file.close()
    else:
        print("Error: cannot find the CompleteStockList file")
    return complete_stock_list


class StockVolMean:
    def __init__(self):
        self.complete_stock_list = get_complete_stock_list()
        self.date_code_volume_dict = {}
        self.trading_date_list = []

    def getStockVolume(self, keyDate, stock_list, source='xqplatform'):
        # 获得所有股票上溯一年的数据
        year, monthday = divmod(keyDate, 10000)
        self.trading_date_list = GTD.getTradingDay((year-1) * 10000 + monthday, keyDate)  # 往前上溯一年、获得交易日
        key_date_code_volume_dict = {}
        if source == 'xqplatform':
            if stock_list.__len__() == 0:
                factorData = xq.hfactor(self.complete_stock_list, [xq.Factors.volume], self.trading_date_list)
            elif stock_list.__len__() == 1:
                factorData = xq.hfactor([stock_list], [xq.Factors.volume], self.trading_date_list)
            else:
                factorData = xq.hfactor(stock_list, [xq.Factors.volume], self.trading_date_list)
            volume_list = factorData[0][0][1]
            stock_code_output_list = factorData[2]
            key_date_code_volume_dict = dict(zip(stock_code_output_list, volume_list))
        elif source == 'winddb':
            data_df = IO.read_data([self.trading_date_list[0], self.trading_date_list[-1]],
                                   columns=['S_DQ_VOLUME'], alt='WIND/AShareEODPrices')
            data_df = data_df.unstack()
            key_date_code_volume_dict = {}
            stock_code_output_list = list(data_df.columns)
            df_array = data_df.values
            for i in range(stock_code_output_list.__len__()):
                key_date_code_volume_dict.update({stock_code_output_list[i][1]: list(df_array[:, i])})
        self.date_code_volume_dict.update({keyDate: key_date_code_volume_dict})

    @staticmethod
    def datesSegment(startDate, endDate, n):
        # 因为取XQuant的MDP接口所能取的最大时间跨度是180(?)天，若原函数输入的日期跨度较大，则需拆分为多段分别获取数据
        # 本函数将起止日期的拆分为每n天一组
        # 虽然输入的类型是dt.date，但为了后续使用方便，输出的最小元素转为8位数字的字符串
        daysDiff = (endDate - startDate).days
        if divmod(daysDiff, n)[1] > 0 or daysDiff == 0:
            datesPeriod = divmod(daysDiff, n)[0] + 1
        else:
            datesPeriod = divmod(daysDiff, n)[0]
        if datesPeriod == 1:
            startEndDatesList = [[startDate, endDate]]
        else:
            startEndDatesList = [None for _ in range(datesPeriod)]
            for i in range(datesPeriod - 1):
                startEndDatesList[i] = [startDate, startDate + dt.timedelta(n)]
                startDate = startDate + dt.timedelta(n+1)
            startEndDatesList[-1] = [startDate, endDate]
        # 截至到此，startEndDatesList的最小元素全部是dt.date类型，以下转化为8位数字的字符串，例如'20180101'
        startEndDatesList2 = [None for _ in range(datesPeriod)]
        for iPeriod in range(startEndDatesList.__len__()):
            startEndDatesList2[iPeriod] = [str(iDate.year * 10000 + iDate.month * 100 + iDate.day) for iDate in
                                           startEndDatesList[iPeriod]]
        return startEndDatesList2

    def getVolMean(self, stockCode, keyDate, NDaysOff):
        if keyDate in self.date_code_volume_dict.keys():
            if stockCode in self.date_code_volume_dict[keyDate].keys():
                volume_list = self.date_code_volume_dict[keyDate][stockCode]
            else:
                self.getStockVolume(keyDate, [stockCode], 'winddb')
                volume_list = self.date_code_volume_dict[keyDate][stockCode]
        else:
            if stockCode in self.complete_stock_list:
                self.getStockVolume(keyDate, self.complete_stock_list, 'winddb')
            else:
                self.complete_stock_list.append(stockCode)
                self.getStockVolume(keyDate, self.complete_stock_list, 'winddb')
            volume_list = self.date_code_volume_dict[keyDate][stockCode]
        valid_date_count = 0
        reverse_idx_count = 0
        valid_date_list = []
        while valid_date_count < NDaysOff:
            if reverse_idx_count <= volume_list.__len__():
                pass
            else:
                break
            if volume_list[-1 * (reverse_idx_count + 1)] > 0:
                valid_date_count += 1
                reverse_idx_count += 1
                valid_date_list.append(self.trading_date_list[-1 * reverse_idx_count])
            else:
                reverse_idx_count += 1
        valid_date_list.sort()  # 有交易日的日期、按升序排序

        start_date_int = valid_date_list[0]
        end_date_int = valid_date_list[-1]

        start_date_dt = dt.date(int(str(start_date_int)[0:4]), int(str(start_date_int)[4:6]),
                                int(str(start_date_int)[6:8]))
        end_date_dt = dt.date(int(str(end_date_int)[0:4]), int(str(end_date_int)[4:6]), int(str(end_date_int)[6:8]))
        date_list2 = self.datesSegment(start_date_dt, end_date_dt, 58)  # 将日期分段
        data_df = pd.DataFrame()
        for i_date_list in date_list2:
            temp_data_df = mdp.get_data_by_time_frame("Stock", stockCode, str(i_date_list[0]) + " 093112000",
                                                      str(i_date_list[-1]) + " 145500000", ["3"])
            data_df = data_df.append(temp_data_df)

        day_volume = []
        for d in valid_date_list:
            d_str = str(d)
            data = data_df[data_df['MDDate'] == d_str]

            filter_data_morning = data[((data['MDTime'] >= "093112000") & (data['MDTime'] <= "112857000"))]
            filter_data_afternoon = data[((data['MDTime'] >= "130112000") & (data['MDTime'] <= "145500000"))]
            if filter_data_morning.empty and filter_data_afternoon.empty:
                continue
            if not filter_data_morning.empty:
                volume_list = np.array(filter_data_morning['TotalVolumeTrade'])
                for i in range(1, len(volume_list)):
                    day_volume.append(volume_list[i] - volume_list[i - 1])
            if not filter_data_afternoon.empty:
                volume_list = np.array(filter_data_afternoon['TotalVolumeTrade'])
                for i in range(1, len(volume_list)):
                    day_volume.append(volume_list[i] - volume_list[i - 1])

        day_volume.sort()
        # volume_list_25p_idx = int(day_volume.__len__() * 0.25)
        # volume_list_75p_idx = int(day_volume.__len__() * 0.75)
        # valid_volume_list = day_volume[volume_list_25p_idx: volume_list_75p_idx]
        volume_list_10p_idx = int(day_volume.__len__() * 0.15)
        volume_list_90p_idx = int(day_volume.__len__() * 0.85)
        valid_volume_list = day_volume[volume_list_10p_idx: volume_list_90p_idx]
        vol_mean = np.mean(valid_volume_list)
        return vol_mean
