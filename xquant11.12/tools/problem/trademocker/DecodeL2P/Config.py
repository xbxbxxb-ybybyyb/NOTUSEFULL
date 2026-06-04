#-*- coding:utf-8 -*-
# author: 015629
# datetime:2021/2/24 9:58
CELL_SIZE = 200

LOG_TICK_SUFFIX = "T"
LOG_NUMERICAL_COLUMNS = ["TotalVolume", "TotalAmount", "Volume", "Amount", "LastPrice", "NumTrades", "HighPrice", "LowPrice"]
LOG_ALIGN_COLUMNS = ["Code", "Timestamp", "Date", "Time", "HighPrice", "LowPrice", "LastPrice",
                     "TotalVolume", "TotalAmount", "Volume", "Amount", "NumTrades", "BidPrice", "AskPrice", "BidVolume", "AskVolume", "IsMock"]
LOG_TICK_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(LOG_TICK_SUFFIX, x), LOG_ALIGN_COLUMNS))

