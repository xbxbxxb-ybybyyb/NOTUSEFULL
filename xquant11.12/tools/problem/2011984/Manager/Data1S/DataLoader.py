import pandas as pd
from xquant.factordata import FactorData
from Manager.Data1S.StaticInfo import StaticInfo

TICK_SUFFIX = "T"
TRANSACTION_SUFFIX = "TR"
TICK_TARGET_COLUMNS = ["Date", "Time", "Timestamp", "PreviousClose", "OpenPrice", "HighPrice", "LowPrice", "MaxPrice", "MinPrice", "LastPrice", "TotalVolume", "TotalAmount", "Volume", "Amount",
                       "BidP1", "BidP2", "BidP3", "BidP4", "BidP5", "BidP6", "BidP7", "BidP8", "BidP9", "BidP10",
                       "AskP1", "AskP2", "AskP3", "AskP4", "AskP5", "AskP6", "AskP7", "AskP8", "AskP9", "AskP10",
                       "BidV1", "BidV2", "BidV3", "BidV4", "BidV5", "BidV6", "BidV7", "BidV8", "BidV9", "BidV10",
                       "AskV1", "AskV2", "AskV3", "AskV4", "AskV5", "AskV6", "AskV7", "AskV8", "AskV9", "AskV10"
                      ]
ALIGN_TICK_COLUMNS = ["Timestamp", "Date", "Time", "PreviousClose", "OpenPrice", "HighPrice", "LowPrice", "MaxPrice", "MinPrice", "LastPrice",
                      "Volume", "Amount", "TotalVolume", "TotalAmount", "BidPrice", "AskPrice", "BidVolume", "AskVolume"]
TICK_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(TICK_SUFFIX, x), ALIGN_TICK_COLUMNS))

TRANSACTION_CLEAN_COLUMNS = ["MDDate", "MDTime", "Timestamp", "TradeIndex", "TradeBuyNo", "TradeSellNo", "TradeType", "TradeBSFlag", "TradePrice", "TradeQty", "TradeMoney"]
TRANSACTION_TARGET_COLUMNS = ["Date", "Time", "Timestamp", "TradeIndex", "BidOrder", "AskOrder", "TradeType", "BSFlag", "Price", "Volume", "Amount"]
TRANSACTION_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(TRANSACTION_SUFFIX, x), TRANSACTION_TARGET_COLUMNS))


class DataLoader(object):
    """"""
    def __init__(self, code, start_date, end_date, tick_hbase_library=None, tran_hbase_library=None):
        self.code = code
        self.start_date = start_date
        self.end_date = end_date
        self.tick_hbase_library = tick_hbase_library
        self.tran_hbase_library = tran_hbase_library

        self.fa = FactorData()
        self.static_info = StaticInfo(self.code, self.start_date, self.end_date)
        self.valid_date_list = self.static_info.load_valid_dates()
        self.pre_close_dict = self.static_info.load_pre_close_dict()

    def load_valid_dates(self):
        return self.valid_date_list

    def load_pre_close_dict(self):
        return self.pre_close_dict

    def load_tick_data(self):
        sub_ticks_list = []
        for date in self.valid_date_list:
            try:
                sub_tick_df = self.fa.get_factor_value(self.tick_hbase_library, self.code, date, TICK_HBASE_COLUMNS + ["{}_IsMock".format(TICK_SUFFIX)])
                sub_tick_df.columns = list(map(lambda x: x.replace("{0}_".format(TICK_SUFFIX), ""), sub_tick_df.columns.to_list()))
                # sub_tick_df = sub_tick_df[sub_tick_df["IsMock"] == 0].reset_index(drop=True)
                sub_tick_df = sub_tick_df.reindex(columns=ALIGN_TICK_COLUMNS + ["IsMock"])
                sub_tick_df.columns = ALIGN_TICK_COLUMNS + ["IsMock"]
            except:
                sub_tick_df = pd.DataFrame(columns=ALIGN_TICK_COLUMNS + ["IsMock"])

            sub_ticks_list.append(sub_tick_df)

        if len(sub_ticks_list) == 0:
            ticks_df = pd.DataFrame(columns=TICK_TARGET_COLUMNS + ["IsMock"])
        else:
            ticks_df = pd.concat(sub_ticks_list, axis=0)

            for level in range(1, 11):
                ticks_df["AskP{}".format(level)] = ticks_df["AskPrice"].apply(lambda x: x.tolist()[level - 1]).values
                ticks_df["AskV{}".format(level)] = ticks_df["AskVolume"].apply(lambda x: x.tolist()[level - 1]).values
                ticks_df["BidP{}".format(level)] = ticks_df["BidPrice"].apply(lambda x: x.tolist()[level - 1]).values
                ticks_df["BidV{}".format(level)] = ticks_df["BidVolume"].apply(lambda x: x.tolist()[level - 1]).values

        ticks_df = ticks_df.reindex(columns=TICK_TARGET_COLUMNS + ["IsMock"])
        ticks_df.columns = TICK_TARGET_COLUMNS + ["IsMock"]

        return ticks_df

    def load_transaction_data(self):
        sub_transactions_list = []
        for date in self.valid_date_list:
            try:
                sub_transactions_df = self.fa.get_factor_value(self.tran_hbase_library, self.code, date, TRANSACTION_HBASE_COLUMNS)
                sub_transactions_df.columns = list(map(lambda x: x.replace("{0}_".format(TRANSACTION_SUFFIX), ""), sub_transactions_df.columns.to_list()))
                sub_transactions_df = sub_transactions_df.reindex(columns=TRANSACTION_TARGET_COLUMNS)
                sub_transactions_df.columns = TRANSACTION_TARGET_COLUMNS
            except:
                sub_transactions_df = pd.DataFrame(columns=TRANSACTION_TARGET_COLUMNS)

            sub_transactions_list.append(sub_transactions_df)

        if len(sub_transactions_list) == 0:
            transactions_df = pd.DataFrame(columns=TRANSACTION_CLEAN_COLUMNS)
        else:
            transactions_df = pd.concat(sub_transactions_list, axis=0)

        return transactions_df

    def load_target_timestamp_dict(self, date_list):
        target_timestamp_dict = dict()
        for date in date_list:
            try:
                df = self.fa.get_factor_value(self.tick_hbase_library, self.code, date, ["T_Timestamp", "T_TargetTimestamp"])
            except:
                df = pd.DataFrame()
            if not df.empty:
                target_timestamp_dict.update(df.set_index("T_Timestamp")["T_TargetTimestamp"].to_dict())
        return target_timestamp_dict





