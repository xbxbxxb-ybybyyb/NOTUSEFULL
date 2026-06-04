# USER ID
USER_ID = "015629"

# HBASE CELL_SIZE
CELL_SIZE = 200

# Data IO Date Range
MAX_FRAME_LENGTH = 20
MAX_DAILY_KLINE = 200
MAX_MINUTE_KLINE = 7
THIRD_MAX_FRAME_LENGTH = 20

# Data Suffix
DAILY_SUFFIX = "D"
MINUTE_SUFFIX = "M"
TICK_SUFFIX = "T"
TRANSACTION_SUFFIX = "TR"
ORDER_SUFFIX = "O"

# Stock Daily Data Columns
STOCK_RAW_DAILY_COLUMNS = ["close", "open", "high", "low", "pre_close", "volume", "amt", "free_turn", "total_shares", "free_float_shares", "adjfactor", "dealnum", "maxupordown", "stpt","trade_status",
                           "ev", "mkt_cap_ard", "a_mkt_cap", "pe_ttm", "pe_lyr", "s_val_pb_new", "s_price_div_dps", "ps_ttm", "ps_lyr", "pcf_ocf_ttm", "pcf_ncf_ttm", "pcf_ocflyr", "pcf_ncflyr", "net_assets_today",
                           "s_pq_adjhigh_52w", "s_pq_adjlow_52w", "net_profit_parent_comp_ttm", "net_profit_parent_comp_lyr", "net_cash_flows_oper_act_ttm", "net_cash_flows_oper_act_lyr", "oper_rev_ttm", "oper_rev_lyr",
                           "net_incr_cash_cash_equ_ttm", "net_incr_cash_cash_equ_lyr", "dyr_12"]
STOCK_CLEAN_DAILY_COLUMNS = ["date", "close", "open", "high", "low", "pre_close", "volume", "amt", "free_turn", "total_shares", "free_float_shares", "adjfactor", "dealnum", "maxupordown", "maxup", "maxdown", "trade_status",
                             "ev", "mkt_cap_ard", "a_mkt_cap", "pe_ttm", "pe_lyr", "s_val_pb_new", "s_price_div_dps", "ps_ttm", "ps_lyr", "pcf_ocf_ttm", "pcf_ncf_ttm", "pcf_ocflyr", "pcf_ncflyr", "net_assets_today",
                             "s_pq_adjhigh_52w", "s_pq_adjlow_52w", "net_profit_parent_comp_ttm", "net_profit_parent_comp_lyr", "net_cash_flows_oper_act_ttm", "net_cash_flows_oper_act_lyr", "oper_rev_ttm", "oper_rev_lyr",
                             "net_incr_cash_cash_equ_ttm", "net_incr_cash_cash_equ_lyr", "dyr_12" ]
STOCK_TARGET_DAILY_COLUMNS = ["Date", "ClosePrice", "OpenPrice", "HighPrice", "LowPrice", "PreviousClose", "Volume", "Amount", "FreeTurn", "TotalShares", "FreeFloatShares", "AdjFactor", "NumTrades", "MaxUpOrDown",
                              "MaxPrice", "MinPrice", "TradeStatus", "Ev", "MktCapArd", "AMktCap", "PeTTM", "PeLYR", "SValPbNew", "SPriceDivDps", "PsTTM", "PsLYR", "PcfOcfTTM", "PcfNcfTTM", "PcfOcfLYR", "PcfNcfLYR", "NetAssetsToday",
                              "SPqAdjhigh52w", "SPqAdjlow52w", "NetProfitParentCompTTM", "NetProfitParentCompLYR", "NetCashFlowsOperActTTM",
                              "NetCashFlowsOperActLYR", "OperRevTTM", "OperRevLYR", "NetIncrCashCashEquTTM", "NetIncrCashCashEquLYR", "Dyr12"]

# Stock Minute Data Columns
STOCK_RAW_MINUTE_COLUMNS = ["MDDate", "MDTime", "OpenPx", "ClosePx", "HighPx", "LowPx", "TotalVolumeTrade", "TotalValueTrade", "NumTrades"]
STOCK_CLEAN_MINUTE_COLUMNS = ["Timestamp", "MDDate", "MDTime", "OpenPx", "ClosePx", "HighPx", "LowPx", "TotalVolumeTrade", "TotalValueTrade", "NumTrades"]
STOCK_TARGET_MINUTE_COLUMNS = ["Timestamp", "Date", "Time", "OpenPrice", "ClosePrice", "HighPrice", "LowPrice", "Volume", "Amount", "NumTrades"]

# Stock Tick Data Columns
STOCK_RAW_TICK_COLUMNS = ["HTSCSecurityID", "MDDate", "MDTime",  "PreClosePx", "OpenPx", "HighPx", "LowPx", "MaxPx", "MinPx", "LastPx", "TotalVolumeTrade", "TotalValueTrade", "NumTrades",
                          "TotalBidQty", "TotalOfferQty", "WeightedAvgBidPx", "WeightedAvgOfferPx",
                          "Buy1Price", "Buy2Price", "Buy3Price", "Buy4Price", "Buy5Price", "Buy6Price", "Buy7Price", "Buy8Price", "Buy9Price", "Buy10Price",
                          "Sell1Price", "Sell2Price", "Sell3Price", "Sell4Price", "Sell5Price", "Sell6Price", "Sell7Price", "Sell8Price", "Sell9Price", "Sell10Price",
                          "Buy1OrderQty", "Buy2OrderQty", "Buy3OrderQty", "Buy4OrderQty", "Buy5OrderQty", "Buy6OrderQty", "Buy7OrderQty", "Buy8OrderQty", "Buy9OrderQty", "Buy10OrderQty",
                          "Sell1OrderQty", "Sell2OrderQty", "Sell3OrderQty", "Sell4OrderQty", "Sell5OrderQty", "Sell6OrderQty", "Sell7OrderQty", "Sell8OrderQty", "Sell9OrderQty", "Sell10OrderQty",
                          "Buy1NumOrders", "Buy2NumOrders", "Buy3NumOrders", "Buy4NumOrders", "Buy5NumOrders", "Buy6NumOrders", "Buy7NumOrders", "Buy8NumOrders", "Buy9NumOrders", "Buy10NumOrders",
                          "Sell1NumOrders", "Sell2NumOrders", "Sell3NumOrders", "Sell4NumOrders", "Sell5NumOrders", "Sell6NumOrders", "Sell7NumOrders", "Sell8NumOrders", "Sell9NumOrders", "Sell10NumOrders"]
STOCK_CLEAN_TICK_COLUMNS = ["HTSCSecurityID", "Timestamp", "MDDate", "MDTime", "PreClosePx", "OpenPx", "HighPx", "LowPx", "MaxPx", "MinPx", "LastPx", "VolumeTrade", "ValueTrade", "TotalVolumeTrade", "TotalValueTrade", "NumTrades",
                            "BidQty", "OfferQty", "WeightedAvgBidPx", "WeightedAvgOfferPx",
                            "Buy1Price", "Buy2Price", "Buy3Price", "Buy4Price", "Buy5Price", "Buy6Price", "Buy7Price", "Buy8Price", "Buy9Price", "Buy10Price",
                            "Sell1Price", "Sell2Price", "Sell3Price", "Sell4Price", "Sell5Price", "Sell6Price", "Sell7Price", "Sell8Price", "Sell9Price", "Sell10Price",
                            "Buy1OrderQty", "Buy2OrderQty", "Buy3OrderQty", "Buy4OrderQty", "Buy5OrderQty", "Buy6OrderQty", "Buy7OrderQty", "Buy8OrderQty", "Buy9OrderQty", "Buy10OrderQty",
                            "Sell1OrderQty", "Sell2OrderQty", "Sell3OrderQty", "Sell4OrderQty", "Sell5OrderQty", "Sell6OrderQty", "Sell7OrderQty", "Sell8OrderQty", "Sell9OrderQty", "Sell10OrderQty",
                            "Buy1NumOrders", "Buy2NumOrders", "Buy3NumOrders", "Buy4NumOrders", "Buy5NumOrders", "Buy6NumOrders", "Buy7NumOrders", "Buy8NumOrders", "Buy9NumOrders", "Buy10NumOrders",
                            "Sell1NumOrders", "Sell2NumOrders", "Sell3NumOrders", "Sell4NumOrders", "Sell5NumOrders", "Sell6NumOrders", "Sell7NumOrders", "Sell8NumOrders", "Sell9NumOrders", "Sell10NumOrders"]
STOCK_TARGET_TICK_COLUMNS = ["Code", "Timestamp", "Date", "Time", "PreviousClose", "OpenPrice", "HighPrice", "LowPrice", "MaxPrice", "MinPrice", "LastPrice", "Volume", "Amount", "TotalVolume", "TotalAmount", "NumTrades",
                             "BidQty", "OfferQty", "AvgBidPrice", "AvgOfferPrice",
                             "BidPrice1", "BidPrice2", "BidPrice3", "BidPrice4", "BidPrice5", "BidPrice6", "BidPrice7", "BidPrice8", "BidPrice9", "BidPrice10",
                             "AskPrice1", "AskPrice2", "AskPrice3", "AskPrice4", "AskPrice5", "AskPrice6", "AskPrice7", "AskPrice8", "AskPrice9", "AskPrice10",
                             "BidVolume1", "BidVolume2", "BidVolume3", "BidVolume4", "BidVolume5", "BidVolume6", "BidVolume7", "BidVolume8", "BidVolume9", "BidVolume10",
                             "AskVolume1", "AskVolume2", "AskVolume3", "AskVolume4", "AskVolume5", "AskVolume6", "AskVolume7", "AskVolume8", "AskVolume9", "AskVolume10",
                             "BidNum1", "BidNum2", "BidNum3", "BidNum4", "BidNum5", "BidNum6", "BidNum7", "BidNum8", "BidNum9", "BidNum10",
                             "AskNum1", "AskNum2", "AskNum3", "AskNum4", "AskNum5", "AskNum6", "AskNum7", "AskNum8", "AskNum9", "AskNum10"]

# Stock Transaction Data Columns
STOCK_RAW_TRANSACTION_COLUMNS = ["MDDate", "MDTime", "TradeIndex", "TradeBuyNo", "TradeSellNo", "TradeType", "TradeBSFlag", "TradePrice", "TradeQty", "TradeMoney"]
STOCK_CLEAN_TRANSACTION_COLUMNS = [ "Timestamp", "MDDate", "MDTime", "TradeIndex", "TradeBuyNo", "TradeSellNo", "TradeType", "TradeBSFlag", "TradePrice", "TradeQty", "TradeMoney"]
STOCK_TARGET_TRANSACTION_COLUMNS = [ "Timestamp", "Date", "Time", "TradeIndex", "BidOrder", "AskOrder", "TradeType", "BSFlag", "Price", "Volume", "Amount"]

# Stock Order Data Columns
STOCK_RAW_ORDER_COLUMNS = ["MDDate", "MDTime", "OrderIndex", "OrderType", "OrderPrice", "OrderQty", "OrderBSFlag"]
STOCK_CLEAN_ORDER_COLUMNS = ["Timestamp", "MDDate", "MDTime", "OrderIndex", "OrderType", "OrderPrice", "OrderQty", "OrderBSFlag"]
STOCK_TARGET_ORDER_COLUMNS = ["Timestamp", "Date", "Time", "OrderIndex", "OrderType", "Price", "Volume", "BSFlag"]

# Index Daily & Minute & Tick Data Columns
INDEX_RAW_DAILY_COLUMNS = ["close", "open", "high", "low", "pre_close", "volume", "amt"]
INDEX_CLEAN_DAILY_COLUMNS = ["date", "close", "open", "high", "low", "pre_close", "volume", "amt"]
INDEX_TARGET_DAILY_COLUMNS = ["Date", "ClosePrice", "OpenPrice", "HighPrice", "LowPrice", "PreviousClose", "Volume", "Amount"]

# 申万行业指数(Get From ThirdParty Interface) Daily Columns
SHENWAN_RAW_DAILY_COLUMNS = ["MDDate", "OpenPx", "HighPx", "LowPx", "ClosePx", "TotalVolumeTrade", "TotalValueTrade"]
SHENWAN_CLEAN_DAILY_COLUMNS = ["MDDate", "ClosePx", "OpenPx", "HighPx", "LowPx", "PreviousClose", "TotalVolumeTrade", "TotalValueTrade"]
SHENWAN_TARGET_DAILY_COLUMNS = INDEX_TARGET_DAILY_COLUMNS

INDEX_RAW_MINUTE_COLUMNS = ["MDDate", "MDTime", "OpenPx", "ClosePx", "HighPx", "LowPx", "TotalVolumeTrade", "TotalValueTrade"]
INDEX_CLEAN_MINUTE_COLUMNS = ["Timestamp", "MDDate", "MDTime", "OpenPx", "ClosePx", "HighPx", "LowPx", "TotalVolumeTrade", "TotalValueTrade"]
INDEX_TARGET_MINUTE_COLUMNS = ["Timestamp", "Date", "Time", "OpenPrice", "ClosePrice", "HighPrice", "LowPrice", "Volume", "Amount"]

INDEX_RAW_TICK_COLUMNS = ["HTSCSecurityID", "MDDate", "MDTime", "OpenPx", "HighPx", "LowPx", "LastPx", "TotalVolumeTrade", "TotalValueTrade", "PreClosePx"]
INDEX_CLEAN_TICK_COLUMNS = ["HTSCSecurityID", "Timestamp", "MDDate", "MDTime", "PreClosePx", "OpenPx", "HighPx", "LowPx", "LastPx", "VolumeTrade", "ValueTrade", "TotalVolumeTrade", "TotalValueTrade"]
INDEX_TARGET_TICK_COLUMNS = ["Code", "Timestamp", "Date", "Time",  "PreviousClose", "OpenPrice", "HighPrice", "LowPrice", "LastPrice", "Volume", "Amount", "TotalVolume", "TotalAmount"]

# CBond Daily & Minute & Tick & Transaction & Order Data Columns
CBOND_RAW_DAILY_COLUMNS = ["close", "open", "high", "low", "pre_close", "volume", "amount", "trade_status", "accrueddays", "accruedinterest", "ptm", "curyield",
                           "ytm", "strbvalue", "strbpremium", "strbpremiumratio", "convprice", "convratio", "convvalue", "convpremium", "convpremiumratio"]
CBOND_CLEAN_DAILY_COLUMNS = ["date", "close", "open", "high", "low", "pre_close", "maxup", "maxdown", "adjfactor", "volume", "amount", "trade_status", "accrueddays", "accruedinterest",
                             "ptm", "curyield", "ytm", "strbvalue", "strbpremium", "strbpremiumratio", "convprice", "convratio", "convvalue", "convpremium", "convpremiumratio"]
CBOND_TARGET_DAILY_COLUMNS = ["Date", "ClosePrice", "OpenPrice", "HighPrice", "LowPrice", "PreviousClose", "MaxPrice", "MinPrice", "AdjFactor", "Volume", "Amount", "TradeStatus", "Accrueddays",
                              "Accruedinterest", "Ptm", "Curyield", "Ytm", "Strbvalue", "Strbpremium", "Strbpremiumratio", "Convprice", "Convratio", "Convvalue", "Convpremium", "Convpremiumratio"]

CBOND_RAW_MINUTE_COLUMNS = STOCK_RAW_MINUTE_COLUMNS
CBOND_CLEAN_MINUTE_COLUMNS = STOCK_CLEAN_MINUTE_COLUMNS
CBOND_TARGET_MINUTE_COLUMNS = STOCK_TARGET_MINUTE_COLUMNS

CBOND_RAW_TICK_COLUMNS = STOCK_RAW_TICK_COLUMNS
CBOND_CLEAN_TICK_COLUMNS = STOCK_CLEAN_TICK_COLUMNS
CBOND_TARGET_TICK_COLUMNS = STOCK_TARGET_TICK_COLUMNS

CBOND_RAW_TRANSACTION_COLUMNS = STOCK_RAW_TRANSACTION_COLUMNS
CBOND_CLEAN_TRANSACTION_COLUMNS = STOCK_CLEAN_TRANSACTION_COLUMNS
CBOND_TARGET_TRANSACTION_COLUMNS = STOCK_TARGET_TRANSACTION_COLUMNS

CBOND_RAW_ORDER_COLUMNS = STOCK_RAW_ORDER_COLUMNS
CBOND_CLEAN_ORDER_COLUMNS = STOCK_CLEAN_ORDER_COLUMNS
CBOND_TARGET_ORDER_COLUMNS = STOCK_TARGET_ORDER_COLUMNS

# CBOND ShangHai Volume Adjustment
CBOND_SH_VOLUME_MULTIPLE = 10.
CBOND_SH_MINUTE_ADJUST_COLUMNS = ["Volume"]
CBOND_SH_TICK_ADJUST_COLUMNS = [v for v in CBOND_TARGET_TICK_COLUMNS if "Volume" in v ] #+ ["BidQty", "OfferQty"]
CBOND_SH_TRANSACTION_ADJUST_COLUMNS = ["Volume"]
CBOND_SH_ORDER_ADJUST_COLUMNS = ["Volume"]

# ETF / LOF Daily & Minute & Tick & Transaction & Order Columns
FUND_RAW_DAILY_COLUMNS = ["MDDate", "OpenPx", "HighPx", "LowPx", "ClosePx", "TotalVolumeTrade", "TotalValueTrade", "NumTrades"]
FUND_CLEAN_DAILY_COLUMNS = ["MDDate", "ClosePx", "OpenPx", "HighPx", "LowPx", "PreviousClose", "MaxPrice", "MinPrice", "AdjFactor", "TotalVolumeTrade", "TotalValueTrade", "NumTrades", "TradeStatus"]
FUND_TARGET_DAILY_COLUMNS = ["Date", "ClosePrice", "OpenPrice", "HighPrice", "LowPrice", "PreviousClose", "MaxPrice", "MinPrice", "AdjFactor", "Volume", "Amount", "NumTrades", "TradeStatus"]

FUND_RAW_MINUTE_COLUMNS = STOCK_RAW_MINUTE_COLUMNS
FUND_CLEAN_MINUTE_COLUMNS = STOCK_CLEAN_MINUTE_COLUMNS
FUND_TARGET_MINUTE_COLUMNS = STOCK_TARGET_MINUTE_COLUMNS

FUND_RAW_TICK_COLUMNS = STOCK_RAW_TICK_COLUMNS
FUND_CLEAN_TICK_COLUMNS = STOCK_CLEAN_TICK_COLUMNS
FUND_TARGET_TICK_COLUMNS = STOCK_TARGET_TICK_COLUMNS

FUND_RAW_TRANSACTION_COLUMNS = STOCK_RAW_TRANSACTION_COLUMNS
FUND_CLEAN_TRANSACTION_COLUMNS = STOCK_CLEAN_TRANSACTION_COLUMNS
FUND_TARGET_TRANSACTION_COLUMNS = STOCK_TARGET_TRANSACTION_COLUMNS

FUND_RAW_ORDER_COLUMNS = STOCK_RAW_ORDER_COLUMNS
FUND_CLEAN_ORDER_COLUMNS = STOCK_CLEAN_ORDER_COLUMNS
FUND_TARGET_ORDER_COLUMNS = STOCK_TARGET_ORDER_COLUMNS

# Index Future Daily & Minute & Minute Data Columns
FUTURE_RAW_DAILY_COLUMNS = ["MDDate", "OpenPx", "HighPx", "LowPx", "ClosePx", "TotalVolumeTrade", "TotalValueTrade", "OpenInterest", "SettlePrice"]
FUTURE_CLEAN_DAILY_COLUMNS = ["MDDate", "ClosePx", "OpenPx", "HighPx", "LowPx", "TotalVolumeTrade", "TotalValueTrade", "OpenInterest", "SettlePrice", "AdjFactor", "TradeStatus"]
FUTURE_TARGET_DAILY_COLUMNS = ["Date", "ClosePrice", "OpenPrice", "HighPrice", "LowPrice", "Volume", "Amount", "OpenInterest", "SettlePrice", "AdjFactor", "TradeStatus"]

FUTURE_RAW_MINUTE_COLUMNS = ["MDDate", "MDTime", "OpenPx", "ClosePx", "HighPx", "LowPx", "TotalVolumeTrade", "TotalValueTrade", "OpenInterest"]
FUTURE_CLEAN_MINUTE_COLUMNS = ["Timestamp", "MDDate", "MDTime", "OpenPx", "ClosePx", "HighPx", "LowPx", "TotalVolumeTrade", "TotalValueTrade", "OpenInterest"]
FUTURE_TARGET_MINUTE_COLUMNS = ["Timestamp", "Date", "Time", "OpenPrice", "ClosePrice", "HighPrice", "LowPrice", "Volume", "Amount", "OpenInterest"]

FUTURE_RAW_TICK_COLUMNS = ["HTSCSecurityID", "MDDate", "MDTime", "PreClosePx", "PreSettlePrice", "OpenPx", "HighPx", "LowPx", "MaxPx", "MinPx", "LastPx", "TotalVolumeTrade", "TotalValueTrade", "OpenInterest",
                          "Buy1Price", "Buy2Price", "Buy3Price", "Buy4Price", "Buy5Price", "Sell1Price", "Sell2Price", "Sell3Price", "Sell4Price", "Sell5Price",
                          "Buy1OrderQty", "Buy2OrderQty", "Buy3OrderQty", "Buy4OrderQty", "Buy5OrderQty", "Sell1OrderQty", "Sell2OrderQty", "Sell3OrderQty", "Sell4OrderQty", "Sell5OrderQty"]

FUTURE_CLEAN_TICK_COLUMNS = ["HTSCSecurityID", "Timestamp", "MDDate", "MDTime", "PreClosePx", "PreSettlePrice", "OpenPx", "HighPx", "LowPx", "MaxPx", "MinPx", "LastPx", "VolumeTrade", "ValueTrade", "TotalVolumeTrade", "TotalValueTrade", "OpenInterest",
                            "Buy1Price", "Buy2Price", "Buy3Price", "Buy4Price", "Buy5Price", "Sell1Price", "Sell2Price", "Sell3Price", "Sell4Price", "Sell5Price",
                            "Buy1OrderQty", "Buy2OrderQty", "Buy3OrderQty", "Buy4OrderQty", "Buy5OrderQty", "Sell1OrderQty", "Sell2OrderQty", "Sell3OrderQty", "Sell4OrderQty", "Sell5OrderQty"]

FUTURE_TARGET_TICK_COLUMNS = ["Code", "Timestamp", "Date", "Time",  "PreviousClose", "PreSettlePrice", "OpenPrice", "HighPrice", "LowPrice", "MaxPrice", "MinPrice", "LastPrice", "Volume", "Amount", "TotalVolume", "TotalAmount", "OpenInterest",
                             "BidPrice1", "BidPrice2", "BidPrice3", "BidPrice4", "BidPrice5", "AskPrice1", "AskPrice2", "AskPrice3", "AskPrice4", "AskPrice5",
                             "BidVolume1", "BidVolume2", "BidVolume3", "BidVolume4", "BidVolume5", "AskVolume1", "AskVolume2", "AskVolume3", "AskVolume4", "AskVolume5"]

# HBase Save Columns
ALIGN_STOCK_TICK_COLUMNS = ["Code", "Timestamp", "Date", "Time", "PreviousClose", "OpenPrice", "HighPrice", "LowPrice", "MaxPrice", "MinPrice", "LastPrice", "Volume", "Amount", "TotalVolume", "TotalAmount", "NumTrades",
                            "BidQty", "OfferQty", "AvgBidPrice", "AvgOfferPrice",
                            "BidPrice", "AskPrice", "BidVolume", "AskVolume", "BidNum", "AskNum", "TSIndex", "TEIndex", "OSIndex", "OEIndex", "IsMock"]
ALIGN_CBOND_TICK_COLUMNS = ALIGN_STOCK_TICK_COLUMNS
ALIGN_FUND_TICK_COLUMNS = ALIGN_STOCK_TICK_COLUMNS
ALIGN_INDEX_TICK_COLUMNS = ["Code", "Timestamp", "Date", "Time", "PreviousClose", "OpenPrice", "HighPrice", "LowPrice", "LastPrice", "Volume", "Amount", "TotalVolume", "TotalAmount", "IsMock"]

SUB_ALIGN_STOCK_COLUMNS = ["Code", "Timestamp", "Date", "Time", "PreviousClose", "OpenPrice", "HighPrice", "LowPrice", "MaxPrice", "MinPrice", "LastPrice", "Volume", "Amount", "TotalVolume", "TotalAmount", "NumTrades",
                           "BidQty", "OfferQty", "AvgBidPrice", "AvgOfferPrice"]
BID_PRICE_COLUMNS = ["BidPrice1", "BidPrice2", "BidPrice3", "BidPrice4", "BidPrice5", "BidPrice6", "BidPrice7", "BidPrice8", "BidPrice9", "BidPrice10"]
ASK_PRICE_COLUMNS = ["AskPrice1", "AskPrice2", "AskPrice3", "AskPrice4", "AskPrice5", "AskPrice6", "AskPrice7", "AskPrice8", "AskPrice9", "AskPrice10"]
BID_VOLUME_COLUMNS = ["BidVolume1", "BidVolume2", "BidVolume3", "BidVolume4", "BidVolume5", "BidVolume6", "BidVolume7", "BidVolume8", "BidVolume9", "BidVolume10"]
ASK_VOLUME_COLUMNS = ["AskVolume1", "AskVolume2", "AskVolume3", "AskVolume4", "AskVolume5", "AskVolume6", "AskVolume7", "AskVolume8", "AskVolume9", "AskVolume10"]
BID_NUM_COLUMNS = ["BidNum1", "BidNum2", "BidNum3", "BidNum4", "BidNum5", "BidNum6", "BidNum7", "BidNum8", "BidNum9", "BidNum10"]
ASK_NUM_COLUMNS = ["AskNum1", "AskNum2", "AskNum3", "AskNum4", "AskNum5", "AskNum6", "AskNum7", "AskNum8", "AskNum9", "AskNum10"]

ALIGN_FUTURE_TICK_COLUMNS = ["Code", "Timestamp", "Date", "Time", "PreviousClose", "PreSettlePrice", "OpenPrice", "HighPrice", "LowPrice", "MaxPrice", "MinPrice", "LastPrice",
                             "Volume", "Amount", "TotalVolume", "TotalAmount",  "OpenInterest", "BidPrice", "AskPrice", "BidVolume", "AskVolume", "IsMock"]
SUB_ALIGN_FUTURE_COLUMNS = ["Code", "Timestamp", "Date", "Time", "PreviousClose", "PreSettlePrice", "OpenPrice", "HighPrice", "LowPrice", "MaxPrice", "MinPrice", "LastPrice", "Volume", "Amount", "TotalVolume", "TotalAmount", "OpenInterest"]
FUTURE_BID_PRICE_COLUMNS = ["BidPrice1", "BidPrice2", "BidPrice3", "BidPrice4", "BidPrice5"]
FUTURE_ASK_PRICE_COLUMNS = ["AskPrice1", "AskPrice2", "AskPrice3", "AskPrice4", "AskPrice5"]
FUTURE_BID_VOLUME_COLUMNS = ["BidVolume1", "BidVolume2", "BidVolume3", "BidVolume4", "BidVolume5"]
FUTURE_ASK_VOLUME_COLUMNS = ["AskVolume1", "AskVolume2", "AskVolume3", "AskVolume4", "AskVolume5"]

ALIGN_STOCK_TRANSACTION_COLUMNS = STOCK_TARGET_TRANSACTION_COLUMNS
ALIGN_STOCK_ORDER_COLUMNS = STOCK_TARGET_ORDER_COLUMNS
DAILY_STOCK_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(DAILY_SUFFIX, x), STOCK_TARGET_DAILY_COLUMNS))
MINUTE_STOCK_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(MINUTE_SUFFIX, x), STOCK_TARGET_MINUTE_COLUMNS))
TICK_STOCK_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(TICK_SUFFIX, x), ALIGN_STOCK_TICK_COLUMNS))
TRANSACTION_STOCK_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(TRANSACTION_SUFFIX, x), ALIGN_STOCK_TRANSACTION_COLUMNS))
ORDER_STOCK_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(ORDER_SUFFIX, x), ALIGN_STOCK_ORDER_COLUMNS))

ALIGN_CBOND_TRANSACTION_COLUMNS = CBOND_TARGET_TRANSACTION_COLUMNS
ALIGN_CBOND_ORDER_COLUMNS = CBOND_TARGET_ORDER_COLUMNS
DAILY_CBOND_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(DAILY_SUFFIX, x), CBOND_TARGET_DAILY_COLUMNS))
MINUTE_CBOND_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(MINUTE_SUFFIX, x), CBOND_TARGET_MINUTE_COLUMNS))
TICK_CBOND_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(TICK_SUFFIX, x), ALIGN_CBOND_TICK_COLUMNS))
TRANSACTION_CBOND_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(TRANSACTION_SUFFIX, x), ALIGN_CBOND_TRANSACTION_COLUMNS))
ORDER_CBOND_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(ORDER_SUFFIX, x), ALIGN_CBOND_ORDER_COLUMNS))

ALIGN_FUND_TRANSACTION_COLUMNS = FUND_TARGET_TRANSACTION_COLUMNS
ALIGN_FUND_ORDER_COLUMNS = FUND_TARGET_ORDER_COLUMNS
DAILY_FUND_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(DAILY_SUFFIX, x), FUND_TARGET_DAILY_COLUMNS))
MINUTE_FUND_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(MINUTE_SUFFIX, x), FUND_TARGET_MINUTE_COLUMNS))
TICK_FUND_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(TICK_SUFFIX, x), ALIGN_FUND_TICK_COLUMNS))
TRANSACTION_FUND_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(TRANSACTION_SUFFIX, x), ALIGN_FUND_TRANSACTION_COLUMNS))
ORDER_FUND_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(ORDER_SUFFIX, x), ALIGN_FUND_ORDER_COLUMNS))

DAILY_INDEX_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(DAILY_SUFFIX, x), INDEX_TARGET_DAILY_COLUMNS))
MINUTE_INDEX_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(MINUTE_SUFFIX, x), INDEX_TARGET_MINUTE_COLUMNS))
TICK_INDEX_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(TICK_SUFFIX, x), ALIGN_INDEX_TICK_COLUMNS))

DAILY_FUTURE_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(DAILY_SUFFIX, x), FUTURE_TARGET_DAILY_COLUMNS))
MINUTE_FUTURE_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(MINUTE_SUFFIX, x), FUTURE_TARGET_MINUTE_COLUMNS))
TICK_FUTURE_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(TICK_SUFFIX, x), ALIGN_FUTURE_TICK_COLUMNS))

# Monitor HBase Columns
FLAG_COLUMNS = ["FlagDate", "FlagValue"]
DAILY_MONITOR_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(DAILY_SUFFIX, x), FLAG_COLUMNS))
MINUTE_MONITOR_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(MINUTE_SUFFIX, x), FLAG_COLUMNS))
TICK_MONITOR_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(TICK_SUFFIX, x), FLAG_COLUMNS))
TRANSACTION_MONITOR_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(TRANSACTION_SUFFIX, x), FLAG_COLUMNS))
ORDER_MONITOR_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(ORDER_SUFFIX, x), FLAG_COLUMNS))