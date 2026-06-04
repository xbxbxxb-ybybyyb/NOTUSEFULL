import pickle
from System.SliceData import SliceData
from typing import Dict


class SimpleDataConverter:
    __slots__ = ['__data_dict']

    def __init__(self, stock_data):
        self.__data_dict = {}
        for stockData in stock_data:
            if stockData is not None:
                code = stockData['Code'][0]
                for i in range(len(stockData['TimeStamp'])):
                    bidPrice = [stockData['BidP1'][i], stockData['BidP2'][i],
                                stockData['BidP3'][i], stockData['BidP4'][i],
                                stockData['BidP5'][i], stockData['BidP6'][i],
                                stockData['BidP7'][i], stockData['BidP8'][i],
                                stockData['BidP9'][i], stockData['BidP10'][i]]
                    askPrice = [stockData['AskP1'][i], stockData['AskP2'][i],
                                stockData['AskP3'][i], stockData['AskP4'][i],
                                stockData['AskP5'][i], stockData['AskP6'][i],
                                stockData['AskP7'][i], stockData['AskP8'][i],
                                stockData['AskP9'][i], stockData['AskP10'][i]]
                    bidVolume = [stockData['BidV1'][i], stockData['BidV2'][i],
                                 stockData['BidV3'][i], stockData['BidV4'][i],
                                 stockData['BidV5'][i], stockData['BidV6'][i],
                                 stockData['BidV7'][i], stockData['BidV8'][i],
                                 stockData['BidV9'][i], stockData['BidV10'][i]]
                    askVolume = [stockData['AskV1'][i], stockData['AskV2'][i],
                                 stockData['AskV3'][i], stockData['AskV4'][i],
                                 stockData['AskV5'][i], stockData['AskV6'][i],
                                 stockData['AskV7'][i], stockData['AskV8'][i],
                                 stockData['AskV9'][i], stockData['AskV10'][i]]
                    lastPrice = stockData['Price'][i]
                    maxPrice = stockData['MaxP'][i]
                    minPrice = stockData['MinP'][i]
                    highPrice = stockData['High'][i]
                    lowPrice = stockData['Low'][i]
                    volume = stockData['Volume'][i]
                    amount = stockData['Turover'][i]
                    totalVolume = stockData['AccVolume'][i]
                    totalAmt = stockData['AccTurover'][i]
                    preClose = stockData['PreClose'][i]
                    timeStamp = stockData['TimeStamp'][i]
                    if i != len(stockData['TimeStamp']) - 1:
                        nextTimeStamp = stockData['TimeStamp'][i + 1]
                    else:
                        nextTimeStamp = stockData['TimeStamp'][-1]
                    time = stockData['Time'][i]
                    sliceData = SliceData(code=code, timeStamp=timeStamp, nextTimeStamp=nextTimeStamp, time=time,
                                          bidPrice=bidPrice, askPrice=askPrice, bidVolume=bidVolume,
                                          askVolume=askVolume, lastPrice=lastPrice, maxPrice=maxPrice,
                                          minPrice=minPrice, volume=volume, amount=amount, totalVolume=totalVolume,
                                          totalAmount=totalAmt, previousClosingPrice=preClose, highPrice=highPrice, lowPrice=lowPrice)
                    self.__data_dict.update({timeStamp: sliceData})

    def get_data_dict(self) -> Dict[float, 'SliceData']:
        return self.__data_dict
