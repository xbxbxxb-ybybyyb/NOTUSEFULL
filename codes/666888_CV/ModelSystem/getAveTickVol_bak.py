import sys
import os
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../.."))

from MDCDataProvider.DataProvider import DataProvider
import numpy as np
import System.GetTradingDay as GD
import xquant.quant as xq
from xquant.marketdata import MarketData
import datetime as dt
from xquant.factor import FactorData
from xquant.factor.FactorEnum import *
import datetime as dt
fd = FactorData()
mdp = DataProvider()
# def getVolMeanRaw(stockCode, keyDate, NDaysOff):
    # dateList = GD.getNDaysOff(keyDate, NDaysOff)
    # [factorData, _, _] = xq.hfactor([stockCode], [xq.Factors.volume], dateList)
    # factorData = factorData[0][1][0]
    # if len(factorData) > 2:
        # volMean = 100 * (sum(factorData) - max(factorData) - min(factorData)) / (len(factorData) - 2) / 4750
    # else:
        # volMean = 100 * sum(factorData) / len(factorData) / 4750    
    # return volMean
# def getVolMeanRaw(stockCode, keyDate, NDaysOff):
    # # dateList = GD.getNDaysOff(keyDate, NDaysOff)
    # df1 = fd.getData(['filter_suspend'],(keyDate - 10000, keyDate),[stockCode])
    # df1 = df1.reset_index()
    # df2 = df1[df1.filter_suspend == True]
    # dateList = np.array(df2["date"])
    # dateList.sort()
    # dateList = dateList[-NDaysOff:]
    # stockData = mdp.get_data_by_time_frame("Stock", stockCode, str(dateList[0]) + " 093112000", str(dateList[-1]) + " 145500000", ["3"])
    # day_tick_num = []
    # day_volume = []
    # for d in dateList:
        # d_str = str(d)        
        # data = stockData[stockData['MDDate'] == d_str]

        # filter_data_morning = data[((data['MDTime'] >= "093112000") & (data['MDTime'] <= "112857000"))]
        # filter_data_afternoon = data[((data['MDTime'] >= "130112000") & (data['MDTime'] <= "145500000"))]
        # if filter_data_morning.empty and filter_data_afternoon.empty:
            # continue
        # # max_px = np.max(np.array(data['HighPx']))
        # # min_px = np.min(np.array(data['LowPx']))
        # # pre_close_px = np.array(data['PreClosePx'])[0]
        # # if (max_px / pre_close_px - 1) >= 0.095 or (min_px / pre_close_px - 1) <= -0.095:
            # # continue
        # acc_tick_num = 0
        # acc_vol = 0
        # if not filter_data_morning.empty:
            # volume_list = np.array(filter_data_morning['TotalVolumeTrade'])
            # acc_vol = acc_vol + volume_list[-1] - volume_list[0]
            # acc_tick_num = 2355
        # if not filter_data_afternoon.empty:
            # volume_list = np.array(filter_data_afternoon['TotalVolumeTrade'])
            # acc_vol = acc_vol + volume_list[-1] - volume_list[0]
            # acc_tick_num = acc_tick_num + 2275
        # day_tick_num.append(acc_tick_num)
        # day_volume.append(acc_vol)
    
    # if len(day_volume) > 2:
        # max_vol = max(day_volume)
        # min_vol = min(day_volume)
        # day_vol_array = np.array(day_volume)
        # day_tick_num_array = np.array(day_tick_num)
        # max_day_tick_num = day_tick_num_array[day_vol_array == max_vol][-1] 
        # min_day_tick_num = day_tick_num_array[day_vol_array == min_vol][-1]
        # volMean = (sum(day_volume) - max_vol - min_vol) / (sum(day_tick_num) - max_day_tick_num - min_day_tick_num)
    # else:
        # volMean = sum(day_volume) / sum(day_tick_num)     
    # return volMean
def convert_2_timestamp(date):
    return dt.datetime.strptime(str(date), "%Y%m%d").timestamp()  
                               
# def getVolMeanRaw(stockCode, keyDate, NDaysOff):
    # # dateList = GD.getNDaysOff(keyDate, NDaysOff)
    # df1 = fd.getData(['filter_suspend'],(keyDate - 10000, keyDate),[stockCode])
    # df1 = df1.reset_index()
    # df2 = df1[df1.filter_suspend == True]
    # dateList = np.array(df2["date"])
    # dateList.sort()
    # dateList = dateList[-NDaysOff:]
    # # stockData = mdp.get_data_by_time_frame("Stock", stockCode, str(dateList[0]) + " 093112000", str(dateList[-1]) + " 145500000", ["3"])
    # stockData = None
    # start_date = dateList[0]
    # limit = 60 * 3600 * 24
    # for i in range(1, len(dateList)):
        # if convert_2_timestamp(dateList[i]) - convert_2_timestamp(start_date) <= limit:
            # if i == len(dateList) - 1:
                # end_date = dateList[i]
                # data = mdp.get_data_by_time_frame("Stock", stockCode, str(start_date) + " 093000000", str(end_date) + " 150000000", ["3"])
                # if stockData is None:
                    # stockData = data
                # else:
                    # stockData = stockData.append(data)
            # continue
    
        # end_date = dateList[i - 1]
        # data = mdp.get_data_by_time_frame("Stock", stockCode, str(start_date) + " 093000000", str(end_date) + " 150000000", ["3"])
        # if stockData is None:
            # stockData = data
        # else:
            # stockData = stockData.append(data)  
            
        # if i == len(dateList) - 1:
            # start_date = dateList[i]
            # end_date = dateList[i]
            # data = mdp.get_data_by_time_frame("Stock", stockCode, str(start_date) + " 093000000", str(end_date) + " 150000000", ["3"])
            # stockData = stockData.append(data)
        # else:
            # start_date = dateList[i] 
    # # for d in dateList:
        # # data = mdp.get_data_by_time_frame("Stock", stockCode, str(d) + " 093112000", str(d) + " 145500000", ["3"])
        # # if stockData is None:
            # # stockData = data
        # # else:
            # # stockData = stockData.append(data)  
        
    # day_volume = []
    # for d in dateList:
        # d_str = str(d)        
        # data = stockData[stockData['MDDate'] == d_str]

        # filter_data_morning = data[((data['MDTime'] >= "093112000") & (data['MDTime'] <= "112857000"))]
        # filter_data_afternoon = data[((data['MDTime'] >= "130112000") & (data['MDTime'] <= "145500000"))]
        # if filter_data_morning.empty and filter_data_afternoon.empty:
            # print (d)
            # continue
        # # max_px = np.max(np.array(data['HighPx']))
        # # min_px = np.min(np.array(data['LowPx']))
        # # pre_close_px = np.array(data['PreClosePx'])[0]
        # # if (max_px / pre_close_px - 1) >= 0.095 or (min_px / pre_close_px - 1) <= -0.095:
            # # continue
        # if not filter_data_morning.empty:
            # volume_list = np.array(filter_data_morning['TotalVolumeTrade'])
            # for i in range(1, len(volume_list)):
                # day_volume.append(volume_list[i] - volume_list[i - 1])
        # if not filter_data_afternoon.empty:
            # volume_list = np.array(filter_data_afternoon['TotalVolumeTrade'])
            # for i in range(1, len(volume_list)):
                # day_volume.append(volume_list[i] - volume_list[i - 1])
        
    # day_volume.sort()
    
    # filter_day_volume = day_volume[int(len(day_volume) / 4): int(3 * len(day_volume) / 4)]
    # volMean = np.mean(np.array(filter_day_volume))
        
    # return volMean
    
def getVolMeanRaw(stockCode, keyDate, NDaysOff):
    print("bb", keyDate)
    df1 = fd.getData(['filter_suspend'],(keyDate - 10000, keyDate),[stockCode])
    print(df1)
    df1 = df1.reset_index()
    df2 = df1[df1.filter_suspend == True]
    dateList = np.array(df2["date"])
    print("ccc", dateList)
    dateList.sort()
    dateList = dateList[-NDaysOff:].tolist()
    
    recent_day_list = GD.getNDaysOff(keyDate, 7)
    for d in recent_day_list:
        dateList.append(str(d))
    dateList = list(set(dateList))
    dateList.sort()
    print(dateList)
    # dateList = GD.getNDaysOff(keyDate, NDaysOff)
    # stockData = mdp.get_data_by_time_frame("Stock", stockCode, str(dateList[0]) + " 093112000", str(dateList[-1]) + " 145500000", ["3"])
    stockData = None
    start_date = dateList[0]
    limit = 60 * 3600 * 24
    for i in range(1, len(dateList)):
        if convert_2_timestamp(dateList[i]) - convert_2_timestamp(start_date) <= limit:
            if i == len(dateList) - 1:
                end_date = dateList[i]
                data = mdp.get_data_by_time_frame("Stock", stockCode, str(start_date) + " 093000000", str(end_date) + " 150000000", ["3"])
                if stockData is None:
                    stockData = data
                else:
                    stockData = stockData.append(data)
            continue
    
        end_date = dateList[i - 1]
        data = mdp.get_data_by_time_frame("Stock", stockCode, str(start_date) + " 093000000", str(end_date) + " 150000000", ["3"])
        if stockData is None:
            stockData = data
        else:
            stockData = stockData.append(data)  
            
        if i == len(dateList) - 1:
            start_date = dateList[i]
            end_date = dateList[i]
            data = mdp.get_data_by_time_frame("Stock", stockCode, str(start_date) + " 093000000", str(end_date) + " 150000000", ["3"])
            stockData = stockData.append(data)
        else:
            start_date = dateList[i] 
    # for d in dateList:
        # data = mdp.get_data_by_time_frame("Stock", stockCode, str(d) + " 093112000", str(d) + " 145500000", ["3"])
        # if stockData is None:
            # stockData = data
        # else:
            # stockData = stockData.append(data)  
        
    day_volume = []
    dateList = list(reversed(dateList))
    count = 0
    for d in dateList:
        if count >= NDaysOff:
            break
        d_str = str(d)
        print(d_str)        
        data = stockData[stockData['MDDate'] == d_str]

        filter_data_morning = data[((data['MDTime'] >= "093112000") & (data['MDTime'] <= "112857000"))]
        filter_data_afternoon = data[((data['MDTime'] >= "130112000") & (data['MDTime'] <= "145500000"))]
        if filter_data_morning.empty and filter_data_afternoon.empty:
            print (d)
            continue
        count = count + 1
        # max_px = np.max(np.array(data['HighPx']))
        # min_px = np.min(np.array(data['LowPx']))
        # pre_close_px = np.array(data['PreClosePx'])[0]
        # if (max_px / pre_close_px - 1) >= 0.095 or (min_px / pre_close_px - 1) <= -0.095:
            # continue
        if not filter_data_morning.empty:
            volume_list = np.array(filter_data_morning['TotalVolumeTrade'])
            for i in range(1, len(volume_list)):
                day_volume.append(volume_list[i] - volume_list[i - 1])
        if not filter_data_afternoon.empty:
            volume_list = np.array(filter_data_afternoon['TotalVolumeTrade'])
            for i in range(1, len(volume_list)):
                day_volume.append(volume_list[i] - volume_list[i - 1])
        
    day_volume.sort()
    
    filter_day_volume = day_volume[int(1.5 * len(day_volume) / 10): int(8.5 * len(day_volume) / 10)]
    # filter_day_volume = day_volume[int(2.5 * len(day_volume) / 10): int(7.5 * len(day_volume) / 10)]
    volMean = np.mean(np.array(filter_day_volume))
        
    return volMean
        
def getVolMean(stockCode, keyDate, NDaysOff):
    """
    取stockCode这只股票，从keyDate回看NDaysOff天（包含keyDate），每天连续竞价期间的平均每Tick的成交量，单位是股
    """
    dateList = GD.getNDaysOff(keyDate, NDaysOff)
    tempStockData = mdp.get_data_by_time_frame("Stock", stockCode, str(dateList[0]) + " 093000000",
                                               str(dateList[-1]) + " 150000000", ["3"])
    tempStockData = tickDataAppendVolume(tempStockData)  # 新增成交量和成交额列
    volMean = tempStockData['Volume'].mean()
    return volMean


def tickDataAppendVolume(df):
    """
    这个函数处理的情况：从XQuant接口的mdp读取了跨日的Tick数据（格式为DataFrame），但数据中没有成交量字段，且数据索引不连续
    函数的功能1：通过累计成交量的差分，算出成交量；另外每日第1行的成交量直接用累计成交量代替
    函数的功能2：重建索引，将索引变为连续的
    函数最后仍返回DataFrame格式的数据
    """
    df = df.copy()
    df['Date2'] = df['MDDate'].astype(int)  # 将日期转为int，以便后续计算
    dateList = np.array(df['Date2'])
    del df['Date2']
    dateListDiff = np.diff(dateList)  # 对日期进行差分
    dateListDiffLogic = dateListDiff != 0
    changeDayInx = np.argwhere(dateListDiffLogic)  # 若为True，则表示这行到了新的一天；找到行号
    changeDayInx = (changeDayInx + 1).tolist()  # 差分后会少一行，所以行号需要+1
    changeDayInx = [y for x in changeDayInx for y in x]  # np.argwhere会给结果带上[]，把括号去掉
    changeDayInx.insert(0, 0)  # 第1天的第1行也必然因为差分而丢失了，需补上
    df = df.reset_index(drop=True)  # 需要重塑index，因为从XQuant取到的原始行情，索引不是连续的（因为只取了连续竞价期间数据）
    df['Volume'] = df['TotalVolumeTrade'].diff()
    for i in changeDayInx:
        df.loc[i, 'Volume'] = df.loc[i, 'TotalVolumeTrade']
    return df

stockCode = "000001.SZ"
keyDate = 20191023

a = getVolMeanRaw(stockCode, keyDate, 20)
print(a)
