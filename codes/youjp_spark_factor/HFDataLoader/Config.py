### USER ID
USER_ID = "015629"

###HBase info ###
STANDARD_LIB = "XHFDataLib"

### HBASE CELL_SIZE
CELL_SIZE = 100

### parameter config ###
MAX_FRAME_LENGTH = 20
MAX_DAILY_KLINE = 200
MAX_MINUTE_KLINE = 7

### CBOND InterFace TimeRange
THIRD_MAX_FRAME_LENGTH = 20

### Stock daily data columns ###
STOCK_RAW_DAILY_COLUMNS = ['close', 'open', 'high', 'low', 'pre_close', 'volume', 'amt', 'free_turn', 'total_shares', 'free_float_shares', 'adjfactor', 'dealnum', 'maxupordown', 'stpt','trade_status',
                           'ev', 'mkt_cap_ard', 'a_mkt_cap', 'pe_ttm', 'pe_lyr', 's_val_pb_new', 's_price_div_dps', 'ps_ttm', 'ps_lyr', 'pcf_ocf_ttm',
                           'pcf_ncf_ttm', 'pcf_ocflyr', 'pcf_ncflyr', 'net_assets_today', 's_pq_adjhigh_52w', 's_pq_adjlow_52w', 'net_profit_parent_comp_ttm',
                           'net_profit_parent_comp_lyr', 'net_cash_flows_oper_act_ttm', 'net_cash_flows_oper_act_lyr', 'oper_rev_ttm', 'oper_rev_lyr',
                           'net_incr_cash_cash_equ_ttm', 'net_incr_cash_cash_equ_lyr', 'dyr_12']
STOCK_CLEAN_DAILY_COLUMNS = ['date', 'close', 'open', 'high', 'low', 'pre_close', 'volume', 'amt', 'free_turn', 'total_shares', 'free_float_shares', 'adjfactor', 'dealnum', 'maxupordown', 'maxup', 'maxdown', 'trade_status',
                             'ev', 'mkt_cap_ard', 'a_mkt_cap', 'pe_ttm', 'pe_lyr', 's_val_pb_new', 's_price_div_dps', 'ps_ttm', 'ps_lyr', 'pcf_ocf_ttm',
                             'pcf_ncf_ttm', 'pcf_ocflyr', 'pcf_ncflyr', 'net_assets_today', 's_pq_adjhigh_52w', 's_pq_adjlow_52w', 'net_profit_parent_comp_ttm',
                             'net_profit_parent_comp_lyr', 'net_cash_flows_oper_act_ttm', 'net_cash_flows_oper_act_lyr', 'oper_rev_ttm', 'oper_rev_lyr',
                             'net_incr_cash_cash_equ_ttm', 'net_incr_cash_cash_equ_lyr', 'dyr_12' ]
STOCK_TARGET_DAILY_COLUMNS = ['Date', 'ClosePrice', 'OpenPrice', 'HighPrice', 'LowPrice', 'PreviousClose', 'Volume', 'Amount', 'FreeTurn', 'TotalShares', 'FreeFloatShares', 'AdjFactor',
                              'DealNum', 'MaxUpOrDown', 'MaxPrice', 'MinPrice', 'TradeStatus',
                              'Ev', 'MktCapArd', 'AMktCap', 'PeTTM', 'PeLYR', 'SValPbNew', 'SPriceDivDps', 'PsTTM', 'PsLYR', 'PcfOcfTTM',
                              'PcfNcfTTM', 'PcfOcfLYR', 'PcfNcfLYR', 'NetAssetsToday', 'SPqAdjhigh52w', 'SPqAdjlow52w', 'NetProfitParentCompTTM',
                              'NetProfitParentCompLYR', 'NetCashFlowsOperActTTM', 'NetCashFlowsOperActLYR', 'OperRevTTM', 'OperRevLYR',
                              'NetIncrCashCashEquTTM', 'NetIncrCashCashEquLYR', 'Dyr12']

### Stock minute data columns ###
STOCK_RAW_MINUTE_COLUMNS = ['MDDate', 'MDTime', 'OpenPx', 'ClosePx', 'HighPx', 'LowPx', 'TotalVolumeTrade', 'TotalValueTrade','NumTrades']
STOCK_CLEAN_MINUTE_COLUMNS = ['Timestamp', 'MDDate', 'MDTime', 'OpenPx', 'ClosePx', 'HighPx', 'LowPx', 'TotalVolumeTrade', 'TotalValueTrade','NumTrades']
STOCK_TARGET_MINUTE_COLUMNS = ["Timestamp", "Date", "Time", "OpenPrice", "ClosePrice", "HighPrice", "LowPrice", "Volume", "Amount", 'NumTrades']

### Stock tick data columns ###
STOCK_RAW_TICK_COLUMNS = ["HTSCSecurityID", "MDDate", "MDTime",
                          "Buy1Price", "Buy2Price", "Buy3Price", "Buy4Price", "Buy5Price", "Buy6Price", "Buy7Price", "Buy8Price", "Buy9Price", "Buy10Price",
                          "Sell1Price", "Sell2Price", "Sell3Price", "Sell4Price", "Sell5Price", "Sell6Price", "Sell7Price", "Sell8Price", "Sell9Price", "Sell10Price",
                          "Buy1OrderQty", "Buy2OrderQty", "Buy3OrderQty", "Buy4OrderQty", "Buy5OrderQty", "Buy6OrderQty", "Buy7OrderQty", "Buy8OrderQty", "Buy9OrderQty", "Buy10OrderQty",
                          "Sell1OrderQty", "Sell2OrderQty", "Sell3OrderQty", "Sell4OrderQty", "Sell5OrderQty", "Sell6OrderQty", "Sell7OrderQty", "Sell8OrderQty", "Sell9OrderQty", "Sell10OrderQty",
                          "OpenPx", "HighPx", "LowPx", "MaxPx", "MinPx", "LastPx", "TotalVolumeTrade", "TotalValueTrade", "PreClosePx"]
STOCK_CLEAN_TICK_COLUMNS = ["HTSCSecurityID", "Timestamp", "MDDate", "MDTime",
                            "Buy1Price", "Buy2Price", "Buy3Price", "Buy4Price", "Buy5Price", "Buy6Price", "Buy7Price", "Buy8Price", "Buy9Price", "Buy10Price",
                            "Sell1Price", "Sell2Price", "Sell3Price", "Sell4Price", "Sell5Price", "Sell6Price", "Sell7Price", "Sell8Price", "Sell9Price", "Sell10Price",
                            "Buy1OrderQty", "Buy2OrderQty", "Buy3OrderQty", "Buy4OrderQty", "Buy5OrderQty", "Buy6OrderQty", "Buy7OrderQty", "Buy8OrderQty", "Buy9OrderQty", "Buy10OrderQty",
                            "Sell1OrderQty", "Sell2OrderQty", "Sell3OrderQty", "Sell4OrderQty", "Sell5OrderQty", "Sell6OrderQty", "Sell7OrderQty", "Sell8OrderQty", "Sell9OrderQty", "Sell10OrderQty",
                            "OpenPx", "HighPx", "LowPx", "MaxPx", "MinPx", "LastPx", "VolumeTrade", "ValueTrade", "TotalVolumeTrade", "TotalValueTrade", "PreClosePx"]
STOCK_TARGET_TICK_COLUMNS = ["Code", "Timestamp", "Date", "Time",
                             "BidPrice1", "BidPrice2", "BidPrice3", "BidPrice4", "BidPrice5", "BidPrice6", "BidPrice7", "BidPrice8", "BidPrice9", "BidPrice10",
                             "AskPrice1", "AskPrice2", "AskPrice3", "AskPrice4", "AskPrice5", "AskPrice6", "AskPrice7", "AskPrice8", "AskPrice9", "AskPrice10",
                             "BidVolume1", "BidVolume2", "BidVolume3", "BidVolume4", "BidVolume5", "BidVolume6", "BidVolume7", "BidVolume8", "BidVolume9", "BidVolume10",
                             "AskVolume1", "AskVolume2", "AskVolume3", "AskVolume4", "AskVolume5", "AskVolume6", "AskVolume7", "AskVolume8", "AskVolume9", "AskVolume10",
                             "OpenPrice", "HighPrice", "LowPrice", "MaxPrice", "MinPrice", "LastPrice", "Volume", "Amount", "TotalVolume", "TotalAmount", "PreviousClose"]

 ### Stock transaction data columns ###
STOCK_RAW_TRANSACTIONS_COLUMNS = ['MDDate', 'MDTime', 'TradeBuyNo', 'TradeSellNo', 'TradeType', 'TradeBSFlag', 'TradePrice', 'TradeQty']
STOCK_CLEAN_TRANSACTIONS_COLUMNS = ['MDDate', 'MDTime', 'TradeBuyNo', 'TradeSellNo', 'TradeType', 'TradeBSFlag', 'TradePrice', 'TradeQty', 'Timestamp']
STOCK_TARGET_TRANSACTIONS_COLUMNS = ['Date', 'Time', 'BidOrder', 'AskOrder', 'TradeType', 'BSFlag', 'Price', 'Volume', 'Timestamp']

### Stock order data columns ###
STOCK_RAW_ORDER_COLUMNS = ["MDDate", "MDTime", "OrderBSFlag", "OrderPrice", "OrderQty", "OrderType", "OrderIndex"]


#######################################################################################################################################################################
### index daily data columns ###
INDEX_RAW_DAILY_COLUMNS = ['close', 'open', 'high', 'low', 'pre_close', 'volume', 'amt']
INDEX_CLEAN_DAILY_COLUMNS = ['date', 'close', 'open', 'high', 'low', 'pre_close', 'volume', 'amt']
INDEX_TARGET_DAILY_COLUMNS = ['Date', 'ClosePrice', 'OpenPrice', 'HighPrice', 'LowPrice', 'PreviousClose', 'Volume', 'Amount']

### index minute data columns ###
INDEX_RAW_MINUTE_COLUMNS = ['MDDate', 'MDTime', 'OpenPx', 'ClosePx', 'HighPx', 'LowPx', 'TotalVolumeTrade', 'TotalValueTrade']
INDEX_CLEAN_MINUTE_COLUMNS = ['Timestamp', 'MDDate', 'MDTime', 'OpenPx', 'ClosePx', 'HighPx', 'LowPx', 'TotalVolumeTrade', 'TotalValueTrade']
INDEX_TARGET_MINUTE_COLUMNS = ['Timestamp', "Date", "Time", "OpenPrice", "ClosePrice", "HighPrice", "LowPrice", "Volume", "Amount"]

### index tick data columns ###
INDEX_RAW_TICK_COLUMNS = ["HTSCSecurityID", "MDDate", "MDTime", "OpenPx", "HighPx", "LowPx", "LastPx", "TotalVolumeTrade", "TotalValueTrade", "PreClosePx"]
INDEX_CLEAN_TICK_COLUMNS = ["HTSCSecurityID", "Timestamp", "MDDate", "MDTime", "OpenPx", "HighPx", "LowPx", "LastPx", "VolumeTrade", "ValueTrade", "TotalVolumeTrade", "TotalValueTrade", "PreClosePx"]
INDEX_TARGET_TICK_COLUMNS = ["Code", "Timestamp", "Date", "Time", "OpenPrice", "HighPrice", "LowPrice", "LastPrice", "Volume", "Amount", "TotalVolume", "TotalAmount", "PreviousClose"]


### daily cbond data columns
CBOND_RAW_DAILY_COLUMNS = ["close", "open", "high", "low", "pre_close", "volume", "amount", "trade_status", "accrueddays", "accruedinterest", "ptm", "curyield", "ytm", "strbvalue",
                           "strbpremium", "strbpremiumratio", "convprice", "convratio", "convvalue", "convpremium", "convpremiumratio"]
CBOND_CLEAN_DAILY_COLUMNS = ["date", "close", "open", "high", "low", "pre_close", "maxup", "maxdown", "adjfactor", "volume", "amount", "trade_status", "accrueddays", "accruedinterest", "ptm", "curyield", "ytm", "strbvalue",
                           "strbpremium", "strbpremiumratio", "convprice", "convratio", "convvalue", "convpremium", "convpremiumratio"]
CBOND_TARGET_DAILY_COLUMNS = ["Date", "ClosePrice", "OpenPrice", "HighPrice", "LowPrice", "PreviousClose", "MaxPrice", "MinPrice", "AdjFactor", "Volume", "Amount", "TradeStatus",
                              "Accrueddays", "Accruedinterest", "Ptm", "Curyield", "Ytm", "Strbvalue", "Strbpremium", "Strbpremiumratio", "Convprice", "Convratio", "Convvalue", "Convpremium", "Convpremiumratio"]

### minute cbond data columns
CBOND_RAW_MINUTE_COLUMNS = STOCK_RAW_MINUTE_COLUMNS
CBOND_CLEAN_MINUTE_COLUMNS = STOCK_CLEAN_MINUTE_COLUMNS
CBOND_TARGET_MINUTE_COLUMNS = STOCK_TARGET_MINUTE_COLUMNS

### cbond tick data columns
CBOND_RAW_TICK_COLUMNS = STOCK_RAW_TICK_COLUMNS
CBOND_CLEAN_TICK_COLUMNS = STOCK_CLEAN_TICK_COLUMNS
CBOND_TARGET_TICK_COLUMNS = STOCK_TARGET_TICK_COLUMNS

### cbond transaction data columns
CBOND_RAW_TRANSACTIONS_COLUMNS = STOCK_RAW_TRANSACTIONS_COLUMNS
CBOND_CLEAN_TRANSACTIONS_COLUMNS = STOCK_CLEAN_TRANSACTIONS_COLUMNS
CBOND_TARGET_TRANSACTIONS_COLUMNS = STOCK_TARGET_TRANSACTIONS_COLUMNS

### CBOND ShangHai Volume Adjustment
CBOND_SH_VOLUME_MULTIPLE = 10.
CBOND_SH_MINUTE_ADJUST_COLUMNS = ["Volume"]
CBOND_SH_TICK_ADJUST_COLUMNS = [v for v in CBOND_TARGET_TICK_COLUMNS if "Volume" in v ]
CBOND_SH_TRANSACTIONS_ADJUST_COLUMNS = ["Volume"]

### ETF or LOF daily columns
FUND_RAW_DAILY_COLUMNS = ["MDDate", "OpenPx", "HighPx", "LowPx", "ClosePx", "TotalVolumeTrade", "TotalValueTrade", "NumTrades"]
FUND_CLEAN_DAILY_COLUMNS = ["MDDate", "ClosePx", "OpenPx", "HighPx", "LowPx", "PreviousClose", "MaxPrice", "MinPrice", "AdjFactor", "TotalVolumeTrade", "TotalValueTrade", "NumTrades", "TradeStatus"]
FUND_TARGET_DAILY_COLUMNS = ['Date', 'ClosePrice', 'OpenPrice', 'HighPrice', 'LowPrice', 'PreviousClose', "MaxPrice", "MinPrice", "AdjFactor", 'Volume', 'Amount', 'DealNum', 'TradeStatus']

FUND_RAW_MINUTE_COLUMNS = STOCK_RAW_MINUTE_COLUMNS
FUND_CLEAN_MINUTE_COLUMNS = STOCK_CLEAN_MINUTE_COLUMNS
FUND_TARGET_MINUTE_COLUMNS = STOCK_TARGET_MINUTE_COLUMNS

### cbond tick data columns
FUND_RAW_TICK_COLUMNS = STOCK_RAW_TICK_COLUMNS
FUND_CLEAN_TICK_COLUMNS = STOCK_CLEAN_TICK_COLUMNS
FUND_TARGET_TICK_COLUMNS = STOCK_TARGET_TICK_COLUMNS

### cbond transaction data columns
FUND_RAW_TRANSACTIONS_COLUMNS = STOCK_RAW_TRANSACTIONS_COLUMNS
FUND_CLEAN_TRANSACTIONS_COLUMNS = STOCK_CLEAN_TRANSACTIONS_COLUMNS
FUND_TARGET_TRANSACTIONS_COLUMNS = STOCK_TARGET_TRANSACTIONS_COLUMNS

### 申万行业指数 daily columns
SHENWAN_RAW_DAILY_COLUMNS = ["MDDate", "OpenPx", "HighPx", "LowPx", "ClosePx", "TotalVolumeTrade", "TotalValueTrade"]
SHENWAN_CLEAN_DAILY_COLUMNS = ["MDDate", "ClosePx", "OpenPx", "HighPx", "LowPx", "PreviousClose", "TotalVolumeTrade", "TotalValueTrade"]
SHENWAN_TARGET_DAILY_COLUMNS = INDEX_TARGET_DAILY_COLUMNS

### 期货数据
FUTURE_RAW_DAILY_COLUMNS = ["MDDate", "OpenPx", "HighPx", "LowPx", "ClosePx", "TotalVolumeTrade", "TotalValueTrade", "OpenInterest", "SettlePrice"]
FUTURE_CLEAN_DAILY_COLUMNS = ["MDDate", "ClosePx", "OpenPx", "HighPx", "LowPx", "TotalVolumeTrade", "TotalValueTrade", "OpenInterest", "SettlePrice", "AdjFactor", "TradeStatus"]
FUTURE_TARGET_DAILY_COLUMNS = ['Date', 'ClosePrice', 'OpenPrice', 'HighPrice', 'LowPrice', 'Volume', 'Amount', "OpenInterest", "SettlePrice", "AdjFactor", "TradeStatus"]

FUTURE_RAW_MINUTE_COLUMNS = ['MDDate', 'MDTime', 'OpenPx', 'ClosePx', 'HighPx', 'LowPx', 'TotalVolumeTrade', 'TotalValueTrade', "OpenInterest"]
FUTURE_CLEAN_MINUTE_COLUMNS = ['Timestamp', 'MDDate', 'MDTime', 'OpenPx', 'ClosePx', 'HighPx', 'LowPx', 'TotalVolumeTrade', 'TotalValueTrade', "OpenInterest"]
FUTURE_TARGET_MINUTE_COLUMNS = ['Timestamp', "Date", "Time", "OpenPrice", "ClosePrice", "HighPrice", "LowPrice", "Volume", "Amount", "OpenInterest"]

FUTURE_RAW_TICK_COLUMNS = ["HTSCSecurityID", "MDDate", "MDTime",
                          "Buy1Price", "Buy2Price", "Buy3Price", "Buy4Price", "Buy5Price", "Sell1Price", "Sell2Price", "Sell3Price", "Sell4Price", "Sell5Price",
                          "Buy1OrderQty", "Buy2OrderQty", "Buy3OrderQty", "Buy4OrderQty", "Buy5OrderQty", "Sell1OrderQty", "Sell2OrderQty", "Sell3OrderQty", "Sell4OrderQty", "Sell5OrderQty",
                          "OpenPx", "HighPx", "LowPx", "MaxPx", "MinPx", "LastPx", "TotalVolumeTrade", "TotalValueTrade", "PreClosePx", "PreSettlePrice", "OpenInterest"]
FUTURE_CLEAN_TICK_COLUMNS = ["HTSCSecurityID", "Timestamp", "MDDate", "MDTime",
                            "Buy1Price", "Buy2Price", "Buy3Price", "Buy4Price", "Buy5Price", "Sell1Price", "Sell2Price", "Sell3Price", "Sell4Price", "Sell5Price",
                            "Buy1OrderQty", "Buy2OrderQty", "Buy3OrderQty", "Buy4OrderQty", "Buy5OrderQty", "Sell1OrderQty", "Sell2OrderQty", "Sell3OrderQty", "Sell4OrderQty", "Sell5OrderQty",
                            "OpenPx", "HighPx", "LowPx", "MaxPx", "MinPx", "LastPx", "VolumeTrade", "ValueTrade", "TotalVolumeTrade", "TotalValueTrade", "PreClosePx", "PreSettlePrice", "OpenInterest"]
FUTURE_TARGET_TICK_COLUMNS = ["Code", "Timestamp", "Date", "Time",
                             "BidPrice1", "BidPrice2", "BidPrice3", "BidPrice4", "BidPrice5", "AskPrice1", "AskPrice2", "AskPrice3", "AskPrice4", "AskPrice5",
                             "BidVolume1", "BidVolume2", "BidVolume3", "BidVolume4", "BidVolume5", "AskVolume1", "AskVolume2", "AskVolume3", "AskVolume4", "AskVolume5",
                             "OpenPrice", "HighPrice", "LowPrice", "MaxPrice", "MinPrice", "LastPrice", "Volume", "Amount", "TotalVolume", "TotalAmount", "PreviousClose", "PreSettlePrice", "OpenInterest"]

#######################################################################################################################################################################
ALIGN_STOCK_COLUMNS = ["Code", "Timestamp", "Date", "Time", "OpenPrice", "HighPrice", "LowPrice", "MaxPrice", "MinPrice", "LastPrice", "Volume", "Amount", "TotalVolume", "TotalAmount", "PreviousClose",
                       "BidPrice", "AskPrice", "BidVolume", "AskVolume", "Transactions", "IsMock"]
ALIGN_INDEX_COLUMNS = ["Code", "Timestamp", "Date", "Time", "OpenPrice", "HighPrice", "LowPrice", "LastPrice", "Volume", "Amount", "TotalVolume", "TotalAmount", "PreviousClose", "IsMock"]
ALIGN_CBOND_COLUMNS = ALIGN_STOCK_COLUMNS
ALIGN_FUND_COLUMNS = ALIGN_STOCK_COLUMNS

SUB_ALIGN_STOCK_COLUMNS = ["Code", "Timestamp", "Date", "Time", "OpenPrice", "HighPrice", "LowPrice", "MaxPrice", "MinPrice", "LastPrice", "Volume", "Amount", "TotalVolume", "TotalAmount", "PreviousClose"]
BID_PRICE_COLUMNS = ["BidPrice1", "BidPrice2", "BidPrice3", "BidPrice4", "BidPrice5", "BidPrice6", "BidPrice7", "BidPrice8", "BidPrice9", "BidPrice10"]
ASK_PRICE_COLUMNS = ["AskPrice1", "AskPrice2", "AskPrice3", "AskPrice4", "AskPrice5", "AskPrice6", "AskPrice7", "AskPrice8", "AskPrice9", "AskPrice10"]
BID_VOLUME_COLUMNS = ["BidVolume1", "BidVolume2", "BidVolume3", "BidVolume4", "BidVolume5", "BidVolume6", "BidVolume7", "BidVolume8", "BidVolume9", "BidVolume10"]
ASK_VOLUME_COLUMNS = ["AskVolume1", "AskVolume2", "AskVolume3", "AskVolume4", "AskVolume5", "AskVolume6", "AskVolume7", "AskVolume8", "AskVolume9", "AskVolume10"]

ALIGN_FUTURE_COLUMNS = ["Code", "Timestamp", "Date", "Time", "OpenPrice", "HighPrice", "LowPrice", "MaxPrice", "MinPrice", "LastPrice", "Volume", "Amount", "TotalVolume", "TotalAmount", "PreviousClose",
                       "PreSettlePrice", "OpenInterest", "BidPrice", "AskPrice", "BidVolume", "AskVolume", "IsMock"]
SUB_ALIGN_FUTURE_COLUMNS = ["Code", "Timestamp", "Date", "Time", "OpenPrice", "HighPrice", "LowPrice", "MaxPrice", "MinPrice", "LastPrice", "Volume", "Amount", "TotalVolume", "TotalAmount", "PreviousClose", "PreSettlePrice", "OpenInterest"]
FUTURE_BID_PRICE_COLUMNS = ["BidPrice1", "BidPrice2", "BidPrice3", "BidPrice4", "BidPrice5"]
FUTURE_ASK_PRICE_COLUMNS = ["AskPrice1", "AskPrice2", "AskPrice3", "AskPrice4", "AskPrice5"]
FUTURE_BID_VOLUME_COLUMNS = ["BidVolume1", "BidVolume2", "BidVolume3", "BidVolume4", "BidVolume5"]
FUTURE_ASK_VOLUME_COLUMNS = ["AskVolume1", "AskVolume2", "AskVolume3", "AskVolume4", "AskVolume5"]


DAILY_SUFFIX = "D"
MINUTE_SUFFIX = "M"
TICK_SUFFIX = "T"
MOCK_TICK_SUFFIX = "MT"

DAILY_STOCK_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(DAILY_SUFFIX, x), STOCK_TARGET_DAILY_COLUMNS))
MINUTE_STOCK_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(MINUTE_SUFFIX, x), STOCK_TARGET_MINUTE_COLUMNS))
TICK_STOCK_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(TICK_SUFFIX, x), ALIGN_STOCK_COLUMNS))
MOCK_TICK_STOCK_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(MOCK_TICK_SUFFIX, x), ALIGN_STOCK_COLUMNS))

DAILY_INDEX_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(DAILY_SUFFIX, x), INDEX_TARGET_DAILY_COLUMNS))
MINUTE_INDEX_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(MINUTE_SUFFIX, x), INDEX_TARGET_MINUTE_COLUMNS))
TICK_INDEX_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(TICK_SUFFIX, x), ALIGN_INDEX_COLUMNS))

DAILY_CBOND_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(DAILY_SUFFIX, x), CBOND_TARGET_DAILY_COLUMNS))
MINUTE_CBOND_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(MINUTE_SUFFIX, x), CBOND_TARGET_MINUTE_COLUMNS))
TICK_CBOND_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(TICK_SUFFIX, x), ALIGN_CBOND_COLUMNS))

DAILY_FUND_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(DAILY_SUFFIX, x), FUND_TARGET_DAILY_COLUMNS))
MINUTE_FUND_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(MINUTE_SUFFIX, x), FUND_TARGET_MINUTE_COLUMNS))
TICK_FUND_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(TICK_SUFFIX, x), ALIGN_FUND_COLUMNS))

DAILY_FUTURE_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(DAILY_SUFFIX, x), FUTURE_TARGET_DAILY_COLUMNS))
MINUTE_FUTURE_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(MINUTE_SUFFIX, x), FUTURE_TARGET_MINUTE_COLUMNS))
TICK_FUTURE_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(TICK_SUFFIX, x), ALIGN_FUTURE_COLUMNS))

################################################# Data Monitor #########################################################
FLAG_COLUMNS = ["FlagDate", "FlagValue"]
DAILY_MONITOR_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(DAILY_SUFFIX, x), FLAG_COLUMNS))
MINUTE_MONITOR_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(MINUTE_SUFFIX, x), FLAG_COLUMNS))
TICK_MONITOR_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(TICK_SUFFIX, x), FLAG_COLUMNS))
MOCK_TICK_MONITOR_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(MOCK_TICK_SUFFIX, x), FLAG_COLUMNS))

from enum import Enum, unique

@unique
class DailyMonitor(Enum):
    NORMAL = 0
    MISSING = 1
    EMPTY = 2
    UNKOWN = 3

@unique
class MinuteMonitor(Enum):
    NORMAL = 0
    MISSING = 1
    EMPTY = 2
    UNKOWN = 3

@unique
class TickMonitor(Enum):
    NORMAL = 0
    MISSING = 1
    EMPTY = 2
    POSTPONE_NORMAL = 3
    POSTPONE_MISSING = 4
    UNKOWN = 5
