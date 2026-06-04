from Manager.UtilsModel.SliceData import SliceData
from typing import Dict


class SimpleDataConverter:
    __slots__ = ['__data_dict']

    def __init__(self, stock_data):
        self.__data_dict = {}
        for stockData in stock_data:
            if stockData is not None:
                code = stockData['Code'][0]
                for i in range(len(stockData['TimeStamp'])):
                    bid_price = [stockData['BidP1'][i], stockData['BidP2'][i],
                                 stockData['BidP3'][i], stockData['BidP4'][i],
                                 stockData['BidP5'][i], stockData['BidP6'][i],
                                 stockData['BidP7'][i], stockData['BidP8'][i],
                                 stockData['BidP9'][i], stockData['BidP10'][i]]
                    ask_price = [stockData['AskP1'][i], stockData['AskP2'][i],
                                 stockData['AskP3'][i], stockData['AskP4'][i],
                                 stockData['AskP5'][i], stockData['AskP6'][i],
                                 stockData['AskP7'][i], stockData['AskP8'][i],
                                 stockData['AskP9'][i], stockData['AskP10'][i]]
                    bid_vol = [stockData['BidV1'][i], stockData['BidV2'][i],
                               stockData['BidV3'][i], stockData['BidV4'][i],
                               stockData['BidV5'][i], stockData['BidV6'][i],
                               stockData['BidV7'][i], stockData['BidV8'][i],
                               stockData['BidV9'][i], stockData['BidV10'][i]]
                    ask_vol = [stockData['AskV1'][i], stockData['AskV2'][i],
                               stockData['AskV3'][i], stockData['AskV4'][i],
                               stockData['AskV5'][i], stockData['AskV6'][i],
                               stockData['AskV7'][i], stockData['AskV8'][i],
                               stockData['AskV9'][i], stockData['AskV10'][i]]
                    last_price = stockData['Price'][i]
                    max_price = stockData['MaxP'][i]
                    min_price = stockData['MinP'][i]
                    high_price = stockData['High'][i]
                    low_price = stockData['Low'][i]
                    volume = stockData['Volume'][i]
                    amount = stockData['Turover'][i]
                    total_vol = stockData['AccVolume'][i]
                    total_amt = stockData['AccTurover'][i]
                    pre_close = stockData['PreClose'][i]
                    timestamp = round(stockData['TimeStamp'][i], 3)
                    if i != len(stockData['TimeStamp']) - 1:
                        next_timestamp = round(stockData['TimeStamp'][i + 1], 3)
                    else:
                        next_timestamp = round(stockData['TimeStamp'][-1], 3)
                    time = stockData['Time'][i]
                    date = stockData['Date'][i]
                    slice_data = SliceData(code=code, timestamp=timestamp, next_timestamp=next_timestamp, time=time, date=date,
                                           bid_price=bid_price, ask_price=ask_price, bid_vol=bid_vol,
                                           ask_vol=ask_vol, last_price=last_price, max_price=max_price,
                                           min_price=min_price, volume=volume, amount=amount, total_vol=total_vol,
                                           total_amt=total_amt, pre_close=pre_close,
                                           high_price=high_price, low_price=low_price)
                    self.__data_dict.update({timestamp: slice_data})

    def get_data_dict(self) -> Dict[float, 'SliceData']:
        return self.__data_dict
