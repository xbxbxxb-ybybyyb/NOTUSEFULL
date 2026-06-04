#-*- coding:utf-8 -*-
# author: 015629
# datetime:2021/11/11 14:54
import pandas as pd
from Manager.Data1S.SliceData import SliceData
from Manager.Data1S.DecimalUtil import myRound
from typing import Dict, List


class Tick2SliceData(object):
    def __init__(self, code: str):
        self.code = code
        self.data_dict = dict()

    def convert_tick_data(self, tick_data: List[pd.DataFrame]):
        """"""
        for daily_data in tick_data:
            for i in range(len(daily_data['Timestamp'])):
                if daily_data["IsMock"][i] != 0:
                    continue
                bidPrice = [myRound(daily_data['BidP{}'.format(level)][i], 2) for level in range(1, 11)]
                askPrice = [myRound(daily_data['AskP{}'.format(level)][i], 2) for level in range(1, 11)]
                bidVolume = [daily_data['BidV{}'.format(level)][i] for level in range(1, 11)]
                askVolume = [daily_data['AskV{}'.format(level)][i] for level in range(1, 11)]
                lastPrice = daily_data['LastPrice'][i]
                maxPrice = daily_data['MaxPrice'][i]
                minPrice = daily_data['MinPrice'][i]
                volume = daily_data['Volume'][i]
                amount = daily_data['Amount'][i]
                totalVolume = daily_data['TotalVolume'][i]
                totalAmt = daily_data['TotalAmount'][i]
                preClose = daily_data['PreviousClose'][i]
                timeStamp = daily_data['Timestamp'][i]
                if i != len(daily_data['Timestamp']) - 1:
                    nextTimeStamp = daily_data['Timestamp'][i + 1]
                else:
                    nextTimeStamp = daily_data['Timestamp'][-1]
                time = daily_data['Time'][i]
                sliceData = SliceData(code=self.code, timeStamp=timeStamp, nextTimeStamp=nextTimeStamp, time=time,
                                      bidPrice=bidPrice, askPrice=askPrice, bidVolume=bidVolume,
                                      askVolume=askVolume, lastPrice=lastPrice, maxPrice=maxPrice,
                                      minPrice=minPrice, volume=volume, amount=amount, totalVolume=totalVolume,
                                      totalAmount=totalAmt, previousClosingPrice=preClose)
                self.data_dict.update({timeStamp: sliceData})

    def get_data_dict(self) -> Dict[float, 'SliceData']:
        return self.data_dict
