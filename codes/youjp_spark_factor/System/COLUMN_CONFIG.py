# ####################################################### Stock ########################################################

TICK_COLUMN_NAMES1 = [
    "Date", "Time", "Timestamp",
    "PreviousClose", "LastPrice", "OpenPrice", "HighPrice", "LowPrice", "MaxPrice", "MinPrice", "Volume", "Amount",
    "TotalVolume", "TotalAmount"
]
TICK_COLUMN_NAMES2 = [
    "BidPrice", "BidVolume", "AskPrice", "AskVolume", "Transactions"
]
TRANSACTION_COLUMN_NAMES = [
    "BidOrder", "AskOrder", "TradeType", "BSFlag", "Price", "Volume", "Timestamp"
]
MINUTE_COLUMN_NAMES = [
    "Date", "Time", "Timestamp",
    "OpenPrice", "HighPrice", "LowPrice", "ClosePrice", "Volume", "Amount"
]
DAILY_COLUMN_NAMES = [
    "Date", "TotalShares", "FreeFloatShares", "AdjFactor", "TradeStatus",
    "PreviousClose", "OpenPrice", "HighPrice", "LowPrice", "ClosePrice", "Volume", "Amount", "MaxPrice", "MinPrice",
    "FreeTurn", "NetCashFlowsOperActLYR", "NetProfitParentCompTTM", "NetProfitParentCompLYR", "PcfOcfLYR", "PcfNcfLYR",
    "OperRevLYR", "MaxUpOrDown", "SPqAdjlow52w", "PcfNcfTTM", "SPqAdjhigh52w", "NetCashFlowsOperActTTM", "AMktCap",
    "SPriceDivDps", "SValPbNew", "PeTTM", "OperRevTTM", "PsLYR", "Dyr12", "DealNum", "NetIncrCashCashEquLYR", "Ev",
    "PsTTM", "NetIncrCashCashEquTTM", "PeLYR", "NetAssetsToday", "PcfOcfTTM", "MktCapArd"
]

TICK_COLUMN_INDEX_DICT1 = {k: v for v, k in enumerate(TICK_COLUMN_NAMES1)}
TICK_COLUMN_INDEX_DICT2 = {k: v for v, k in enumerate(TICK_COLUMN_NAMES2)}
TRANSACTION_COLUMN_INDEX_DICT = {k: v for v, k in enumerate(TRANSACTION_COLUMN_NAMES)}
MINUTE_COLUMN_INDEX_DICT = {k: v for v, k in enumerate(MINUTE_COLUMN_NAMES)}
DAILY_COLUMN_INDEX_DICT = {k: v for v, k in enumerate(DAILY_COLUMN_NAMES)}

# ############################################# UnderLying Asset Index #################################################

INDEX_TICK_COLUMN_NAMES = [
    "Date", "Time", "Timestamp", "OpenPrice", "HighPrice", "LowPrice", "LastPrice", "Volume", "Amount", "TotalVolume",
    "TotalAmount", "PreviousClose"
]
INDEX_MINUTE_COLUMN_NAMES = [
    "Date", "Time", "Timestamp", "OpenPrice", "ClosePrice", "HighPrice", "LowPrice", "Volume", "Amount"
]
INDEX_DAILY_COLUMN_NAMES = [
    "Date", "ClosePrice", "OpenPrice", "HighPrice", "LowPrice", "PreviousClose", "Volume", "Amount"
]

INDEX_TICK_COLUMN_INDEX_DICT = {k: v for v, k in enumerate(INDEX_TICK_COLUMN_NAMES)}
INDEX_MINUTE_COLUMN_INDEX_DICT = {k: v for v, k in enumerate(INDEX_MINUTE_COLUMN_NAMES)}
INDEX_DAILY_COLUMN_INDEX_DICT = {k: v for v, k in enumerate(INDEX_DAILY_COLUMN_NAMES)}

# ################################################## Convertible Bond ##################################################

CB_TICK_COLUMN_NAMES1 = [
    "Date", "Time", "Timestamp",
    "PreviousClose", "LastPrice", "OpenPrice", "HighPrice", "LowPrice", "MaxPrice", "MinPrice", "Volume", "Amount",
    "TotalVolume", "TotalAmount"
]
CB_TICK_COLUMN_NAMES2 = [
    "BidPrice", "BidVolume", "AskPrice", "AskVolume", "Transactions"
]
CB_TRANSACTION_COLUMN_NAMES = [
    "BidOrder", "AskOrder", "TradeType", "BSFlag", "Price", "Volume", "Timestamp"
]
CB_MINUTE_COLUMN_NAMES = [
    "Date", "Time", "Timestamp",
    "OpenPrice", "HighPrice", "LowPrice", "ClosePrice", "Volume", "Amount"
]
CB_DAILY_COLUMN_NAMES = [
    "Date", "TradeStatus",
    "PreviousClose", "OpenPrice", "HighPrice", "LowPrice", "ClosePrice", "Volume", "Amount", "MaxPrice", "MinPrice",
    "Accrueddays", "Accruedinterest", "Ptm", "Curyield", "Ytm", "Strbvalue", "Strbpremium", "Strbpremiumratio",
    "Convprice", "Convratio", "Convvalue", "Convpremium", "Convpremiumratio"
]

CB_TICK_COLUMN_INDEX_DICT1 = {k: v for v, k in enumerate(CB_TICK_COLUMN_NAMES1)}
CB_TICK_COLUMN_INDEX_DICT2 = {k: v for v, k in enumerate(CB_TICK_COLUMN_NAMES2)}
CB_TRANSACTION_COLUMN_INDEX_DICT = {k: v for v, k in enumerate(CB_TRANSACTION_COLUMN_NAMES)}
CB_MINUTE_COLUMN_INDEX_DICT = {k: v for v, k in enumerate(CB_MINUTE_COLUMN_NAMES)}
CB_DAILY_COLUMN_INDEX_DICT = {k: v for v, k in enumerate(CB_DAILY_COLUMN_NAMES)}

# ######################################################## ETF #########################################################

ETF_TICK_COLUMN_NAMES1 = [
    "Date", "Time", "Timestamp",
    "PreviousClose", "LastPrice", "OpenPrice", "HighPrice", "LowPrice", "MaxPrice", "MinPrice", "Volume", "Amount",
    "TotalVolume", "TotalAmount"
]
ETF_TICK_COLUMN_NAMES2 = [
    "BidPrice", "BidVolume", "AskPrice", "AskVolume", "Transactions"
]
ETF_TRANSACTION_COLUMN_NAMES = [
    "BidOrder", "AskOrder", "TradeType", "BSFlag", "Price", "Volume", "Timestamp"
]
ETF_MINUTE_COLUMN_NAMES = [
    "Date", "Time", "Timestamp",
    "OpenPrice", "HighPrice", "LowPrice", "ClosePrice", "Volume", "Amount"
]
ETF_DAILY_COLUMN_NAMES = [
    "Date", "ClosePrice", "OpenPrice", "HighPrice", "LowPrice", "PreviousClose", "MaxPrice", "MinPrice", "AdjFactor",
    "Volume", "Amount", "DealNum", "TradeStatus"
]

ETF_TICK_COLUMN_INDEX_DICT1 = {k: v for v, k in enumerate(ETF_TICK_COLUMN_NAMES1)}
ETF_TICK_COLUMN_INDEX_DICT2 = {k: v for v, k in enumerate(ETF_TICK_COLUMN_NAMES2)}
ETF_TRANSACTION_COLUMN_INDEX_DICT = {k: v for v, k in enumerate(ETF_TRANSACTION_COLUMN_NAMES)}
ETF_MINUTE_COLUMN_INDEX_DICT = {k: v for v, k in enumerate(ETF_MINUTE_COLUMN_NAMES)}
ETF_DAILY_COLUMN_INDEX_DICT = {k: v for v, k in enumerate(ETF_DAILY_COLUMN_NAMES)}


# ###################################################### Future ######################################################

FUTURE_TICK_COLUMN_NAMES1 = [
    "Date", "Time", "Timestamp",
    "PreviousClose", "PreSettlePrice", "LastPrice", "OpenPrice", "HighPrice", "LowPrice", "MaxPrice",
    "MinPrice", "Volume", "Amount", "TotalVolume", "TotalAmount", "OpenInterest"
]
FUTURE_TICK_COLUMN_NAMES2 = [
    "BidPrice", "BidVolume", "AskPrice", "AskVolume"
]
FUTURE_MINUTE_COLUMN_NAMES = [
    "Date", "Time", "Timestamp",
    "OpenPrice", "HighPrice", "LowPrice", "ClosePrice", "Volume", "Amount", "OpenInterest"
]
FUTURE_DAILY_COLUMN_NAMES = [
    "Date", "ClosePrice", "OpenPrice", "HighPrice", "LowPrice", "SettlePrice", "AdjFactor",
    "Volume", "Amount", "OpenInterest", "TradeStatus"
]

FUTURE_TICK_COLUMN_INDEX_DICT1 = {k: v for v, k in enumerate(FUTURE_TICK_COLUMN_NAMES1)}
FUTURE_TICK_COLUMN_INDEX_DICT2 = {k: v for v, k in enumerate(FUTURE_TICK_COLUMN_NAMES2)}
FUTURE_MINUTE_COLUMN_INDEX_DICT = {k: v for v, k in enumerate(FUTURE_MINUTE_COLUMN_NAMES)}
FUTURE_DAILY_COLUMN_INDEX_DICT = {k: v for v, k in enumerate(FUTURE_DAILY_COLUMN_NAMES)}


# #################################################### Asset Index #####################################################

CINDEX_TICK_COLUMN_NAMES1 = [
    "Date", "Time", "Timestamp",
    "PreviousClose", "LastPrice", "OpenPrice", "HighPrice", "LowPrice", "Volume", "Amount", "TotalVolume", "TotalAmount"
]
CINDEX_MINUTE_COLUMN_NAMES = [
    "Date", "Time", "Timestamp", "OpenPrice", "HighPrice", "LowPrice", "ClosePrice", "Volume", "Amount"
]
CINDEX_DAILY_COLUMN_NAMES = [
    "Date", "ClosePrice", "OpenPrice", "HighPrice", "LowPrice", "PreviousClose", "AdjFactor",
    "Volume", "Amount",  "TradeStatus"
]

CINDEX_TICK_COLUMN_INDEX_DICT1 = {k: v for v, k in enumerate(CINDEX_TICK_COLUMN_NAMES1)}
CINDEX_MINUTE_COLUMN_INDEX_DICT = {k: v for v, k in enumerate(CINDEX_MINUTE_COLUMN_NAMES)}
CINDEX_DAILY_COLUMN_INDEX_DICT = {k: v for v, k in enumerate(CINDEX_DAILY_COLUMN_NAMES)}
