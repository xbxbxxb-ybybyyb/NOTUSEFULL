import os
import sys

sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../.."))
import numpy as np
import System.TradingDay as GD
import System.GetValidTradingDay as GTD
from xquant.bonddata import BondData
from xquant.factordata import FactorData
import datetime as dt
fd = FactorData()
bd = BondData()


def convert_2_timestamp(date):
    return dt.datetime.strptime(str(date), "%Y%m%d").timestamp()

def getVolMeanRaw(stockCode, keyDate, NDaysOff):
    keyDateList = GD.getTradingDay(keyDate - 10000, keyDate)
    keyDateList = list(map(str, keyDateList))
    df1 = fd.get_factor_value("Basic_factor", [stockCode], keyDateList, ["trade_status"], category="bond")
    df1 = df1.reset_index()
    df2 = df1[~df1["trade_status"].isnull()]
    df2 = df2[df2["trade_status"] != "停牌"]
    df2 = df2[df2["trade_status"] != "待核查"]
    dateList = np.array(df2["mddate"])
    dateList.sort()
    dateList = dateList[-NDaysOff:].tolist()
    recent_day_list = GD.getNDaysOff(keyDate, 7)
    for d in recent_day_list:
        dateList.append(str(d))
    dateList = list(set(dateList))
    dateList.sort()

    stockData = None
    start_date = dateList[0]
    limit = 20 * 3600 * 24
    for i in range(1, len(dateList)):
        if convert_2_timestamp(dateList[i]) - convert_2_timestamp(start_date) <= limit:
            if i == len(dateList) - 1:
                end_date = dateList[i]
                data = bd.get_bond_data(stockCode, str(start_date) + " 093000000", str(end_date) + " 150000000", "TICK")
                if stockData is None:
                    stockData = data
                else:
                    stockData = stockData.append(data)
            continue
    
        end_date = dateList[i - 1]
        data = bd.get_bond_data(stockCode, str(start_date) + " 093000000", str(end_date) + " 150000000", "TICK")
        if stockData is None:
            stockData = data
        else:
            stockData = stockData.append(data)  
            
        if i == len(dateList) - 1:
            start_date = dateList[i]
            end_date = dateList[i]
            data = bd.get_bond_data(stockCode, str(start_date) + " 093000000", str(end_date) + " 150000000", "TICK")
            stockData = stockData.append(data)
        else:
            start_date = dateList[i] 
        
    day_volume = []
    dateList = list(reversed(dateList))
    count = 0
    for d in dateList:
        if count >= NDaysOff:
            break
        d_str = str(d)        
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
    
    # filter_day_volume = day_volume[int(1.5 * len(day_volume) / 10): int(8.5 * len(day_volume) / 10)]
    # filter_day_volume = day_volume[int(2.5 * len(day_volume) / 10): int(7.5 * len(day_volume) / 10)]
    filter_day_volume = day_volume[int(4.5 * len(day_volume) / 10): int(5.5 * len(day_volume) / 10)]
    volMean = np.mean(np.array(filter_day_volume))
    volMean *= 0.8
        
    return volMean

def getVolMeanRawGroup(stockCode, keyDate, NDaysOff):
    dateList = list(map(str, GTD.getValidTradingDayList(stockCode, keyDate[0] - 10000, keyDate[-1])))
    recent_day_list = GD.getTradingDay(GD.getNDaysOff(keyDate[-1], 7), keyDate[-1])
    
    total_dates = GTD.getValidTradingDayList(stockCode, keyDate[0], keyDate[-1])
    dateList = dateList[-(NDaysOff + len(total_dates)):]
    for d in recent_day_list:
        dateList.append(str(d))
    dateList = list(set(dateList))
    dateList.sort()
  
    stockData = None
    start_date = dateList[0]
    limit = 60 * 3600 * 24
    for i in range(1, len(dateList)):
        if convert_2_timestamp(dateList[i]) - convert_2_timestamp(start_date) <= limit:
            if i == len(dateList) - 1:
                end_date = dateList[i]
                data = bd.get_bond_data(stockCode, str(start_date) + " 093000000", str(end_date) + " 150000000", "TICK")
                if stockData is None:
                    stockData = data
                else:
                    stockData = stockData.append(data)
            continue
    
        end_date = dateList[i - 1]
        data = bd.get_bond_data(stockCode, str(start_date) + " 093000000", str(end_date) + " 150000000", "TICK")
        if stockData is None:
            stockData = data
        else:
            stockData = stockData.append(data)  
            
        if i == len(dateList) - 1:
            start_date = dateList[i]
            end_date = dateList[i]
            data = bd.get_bond_data(stockCode, str(start_date) + " 093000000", str(end_date) + " 150000000", "TICK")
            stockData = stockData.append(data)
        else:
            start_date = dateList[i] 
    # for d in dateList:
        # data = mdp.get_data_by_time_frame("Stock", stockCode, str(d) + " 093112000", str(d) + " 145500000", ["3"])
        # if stockData is None:
            # stockData = data
        # else:
            # stockData = stockData.append(data)  
    volMeanList = []
    dateList = list(reversed(dateList))
    for date in keyDate:    
        day_volume = []
        count = 0
        for d in dateList:
            if d > str(date):
                continue
            if count >= NDaysOff:
                break
            d_str = str(d)        
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
        if stockCode.endswith("SH"):
            day_volume = [x *10 for x in day_volume if x > 0]

        filter_day_volume = day_volume[int(2.5 * len(day_volume) / 10): int(7.5 * len(day_volume) / 10)]
        volMean = np.mean(np.array(filter_day_volume))
        volMeanList.append(volMean)
        # volMeanList.append(np.mean(np.array(day_volume)) / 1000)
    return volMeanList  

# getVolMeanRawGroup("110030.SH", [20191101, 20191231], 20)