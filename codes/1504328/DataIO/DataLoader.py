#-*- coding:utf-8 -*-
# author: 015629
# datetime:2021/11/11 14:57
import numpy as np
import datetime as dt
import pandas as pd
from xquant.factordata import FactorData
from xquant.thirdpartydata.marketdata import MarketData as ThirdMarketData
from xquant.marketdata import MarketData
from xquant.bonddata import BondData
from DataIO.StaticInfo import StaticInfo
from DataIO.Utils import get_code_type, split_calc_date_into_group, tick_data_zero_price_filter, tick_data_circuit_filter

MAX_FRAME_LENGTH = 20

TICK_RAW_COLUMNS = ["MDDate", "MDTime", "PreClosePx", "OpenPx", "HighPx", "LowPx", "MaxPx", "MinPx", "LastPx", "TotalVolumeTrade", "TotalValueTrade",
                    "Buy1Price", "Buy2Price", "Buy3Price", "Buy4Price", "Buy5Price", "Buy6Price", "Buy7Price", "Buy8Price", "Buy9Price", "Buy10Price",
                    "Sell1Price", "Sell2Price", "Sell3Price", "Sell4Price", "Sell5Price", "Sell6Price", "Sell7Price", "Sell8Price", "Sell9Price", "Sell10Price",
                    "Buy1OrderQty", "Buy2OrderQty", "Buy3OrderQty", "Buy4OrderQty", "Buy5OrderQty", "Buy6OrderQty", "Buy7OrderQty", "Buy8OrderQty", "Buy9OrderQty", "Buy10OrderQty",
                    "Sell1OrderQty", "Sell2OrderQty", "Sell3OrderQty", "Sell4OrderQty", "Sell5OrderQty", "Sell6OrderQty", "Sell7OrderQty", "Sell8OrderQty", "Sell9OrderQty", "Sell10OrderQty"
                    ]
TICK_CLEAN_COLUMNS = ["MDDate", "MDTime", "Timestamp", "PreClosePx", "OpenPx", "HighPx", "LowPx", "MaxPx", "MinPx", "LastPx", "TotalVolumeTrade", "TotalValueTrade", "Volume", "Amount",
                      "Buy1Price", "Buy2Price", "Buy3Price", "Buy4Price", "Buy5Price", "Buy6Price", "Buy7Price", "Buy8Price", "Buy9Price", "Buy10Price",
                      "Sell1Price", "Sell2Price", "Sell3Price", "Sell4Price", "Sell5Price", "Sell6Price", "Sell7Price", "Sell8Price", "Sell9Price", "Sell10Price",
                      "Buy1OrderQty", "Buy2OrderQty", "Buy3OrderQty", "Buy4OrderQty", "Buy5OrderQty", "Buy6OrderQty", "Buy7OrderQty", "Buy8OrderQty", "Buy9OrderQty", "Buy10OrderQty",
                      "Sell1OrderQty", "Sell2OrderQty", "Sell3OrderQty", "Sell4OrderQty", "Sell5OrderQty", "Sell6OrderQty", "Sell7OrderQty", "Sell8OrderQty", "Sell9OrderQty", "Sell10OrderQty"
                     ]
TICK_TARGET_COLUMNS = ["Date", "Time", "Timestamp", "PreviousClose", "OpenPrice", "HighPrice", "LowPrice", "MaxPrice", "MinPrice", "LastPrice", "TotalVolume", "TotalAmount", "Volume", "Amount",
                       "BidP1", "BidP2", "BidP3", "BidP4", "BidP5", "BidP6", "BidP7", "BidP8", "BidP9", "BidP10",
                       "AskP1", "AskP2", "AskP3", "AskP4", "AskP5", "AskP6", "AskP7", "AskP8", "AskP9", "AskP10",
                       "BidV1", "BidV2", "BidV3", "BidV4", "BidV5", "BidV6", "BidV7", "BidV8", "BidV9", "BidV10",
                       "AskV1", "AskV2", "AskV3", "AskV4", "AskV5", "AskV6", "AskV7", "AskV8", "AskV9", "AskV10"
                      ]

TRANSACTION_RAW_COLUMNS = ["MDDate", "MDTime", "TradeIndex", "TradeBuyNo", "TradeSellNo", "TradeType", "TradeBSFlag", "TradePrice", "TradeQty", "TradeMoney"]
TRANSACTION_CLEAN_COLUMNS = ["MDDate", "MDTime", "Timestamp", "TradeIndex", "TradeBuyNo", "TradeSellNo", "TradeType", "TradeBSFlag", "TradePrice", "TradeQty", "TradeMoney"]
TRANSACTION_TARGET_COLUMNS = ["Date", "Time", "Timestamp", "TradeIndex", "BidOrder", "AskOrder", "TradeType", "BSFlag", "Price", "Volume", "Amount"]

ORDER_RAW_COLUMNS = ["MDDate", "MDTime", "OrderIndex", "OrderType", "OrderPrice", "OrderQty", "OrderBSFlag"]
SH_ORDER_RAW_COLUMNS = ["MDDate", "MDTime", "OrderNo", "OrderType", "OrderPrice", "OrderQty", "OrderBSFlag"]
ORDER_CLEAN_COLUMNS = ["MDDate", "MDTime", "Timestamp", "OrderIndex", "OrderType", "OrderPrice", "OrderQty", "OrderBSFlag"]
ORDER_TARGET_COLUMNS = ["Date", "Time", "Timestamp", "OrderIndex", "OrderType", "Price", "Volume", "BSFlag"]

CBOND_SH_VOLUME_MULTIPLE = 10
CBOND_SH_TICK_ADJUST_COLUMNS = [v for v in TICK_TARGET_COLUMNS if "Volume" in v] + ["BidQty", "OfferQty"]
CBOND_SH_TRANSACTION_ADJUST_COLUMNS = ["TradeQty"]
CBOND_SH_ORDER_ADJUST_COLUMNS = ["OrderQty"]

TICK_SUFFIX = "T"
TRANSACTION_SUFFIX = "TR"
ORDER_SUFFIX = "O"
TRANSACTION_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(TRANSACTION_SUFFIX, x), TRANSACTION_TARGET_COLUMNS))
ORDER_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(ORDER_SUFFIX, x), ORDER_TARGET_COLUMNS))

ALIGN_TICK_COLUMNS = ["Timestamp", "Date", "Time", "PreviousClose", "OpenPrice", "HighPrice", "LowPrice", "MaxPrice", "MinPrice", "LastPrice",
                      "Volume", "Amount", "TotalVolume", "TotalAmount", "BidPrice", "AskPrice", "BidVolume", "AskVolume"]
TICK_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(TICK_SUFFIX, x), ALIGN_TICK_COLUMNS))


class DataLoader(object):
    """"""
    def __init__(self,
                 code, start_date, end_date,
                 tick_data_source=None, tick_hbase_library=None,
                 tran_data_source=None, tran_hbase_library=None,
                 order_data_source=None, order_hbase_librray=None
    ):
        self.code = code
        self.code_type = get_code_type(self.code)
        self.start_date = start_date
        self.end_date = end_date
        self.tick_data_source = tick_data_source
        self.tick_hbase_library = tick_hbase_library
        self.tran_data_source = tran_data_source
        self.tran_hbase_library = tran_hbase_library
        self.order_data_source = order_data_source
        self.order_hbase_library = order_hbase_librray

        self.fa = FactorData()
        self.mdp, self.tma, self.bd = None, None, None
        data_source = [self.tick_data_source, self.tran_data_source, self.order_data_source]
        if self.code_type == "CBOND" and "mdp" in data_source:
            self.bd = BondData()
        if "third" in data_source:
            self.tma = ThirdMarketData()
        if self.code_type == "STOCK" and "mdp" in data_source:
            self.mdp = MarketData()

        self.static_info = StaticInfo(self.code, self.start_date, self.end_date)
        self.valid_date_list = self.static_info.load_valid_dates()

    def load_valid_dates(self):
        return self.valid_date_list

    def load_tick_data(self):
        """"""
        if self.tick_data_source == "mdp":
            ticks_df = self.load_mdp_tick_data()
        elif self.tick_data_source == "third":
            ticks_df = self.load_third_tick_data()
        elif self.tick_data_source == "hbase":
            ticks_df = self.load_hbase_tick_data(hbase_library=self.tick_hbase_library)
        else:
            raise Exception(" Only Support mdp/third/hbase Tick Data Source ")
        return ticks_df

    def load_transaction_data(self):
        """"""
        if self.tran_data_source == "mdp":
            transactions_df = self.load_mdp_transaction_data()
        elif self.tran_data_source == "third":
            transactions_df = self.load_third_transaction_data()
        elif self.tran_data_source == "hbase":
            transactions_df = self.load_hbase_transaction_data(hbase_library=self.tran_hbase_library)
        else:
            raise Exception(" Only Support mdp/third/hbase Transaction Data Source ")
        return transactions_df

    def load_order_data(self):
        if self.order_data_source == "mdp":
            orders_df = self.load_mdp_order_data()
        elif self.order_data_source == "third":
            orders_df = self.load_third_order_data()
        elif self.order_data_source == "hbase":
            orders_df = self.load_hbase_order_data(hbase_library=self.order_hbase_library)
        else:
            raise Exception(" Only Support mdp/third/hbase Order Data Source ")
        return orders_df

    def load_mdp_tick_data(self):
        calc_time_groups = split_calc_date_into_group(self.valid_date_list, MAX_FRAME_LENGTH)
        sub_ticks_list = []
        for group in calc_time_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            # 读取股票逐笔数据
            start_date_time = "{0} {1}".format(sub_start_date, "000001000")
            end_date_time = "{0} {1}".format(sub_end_date, "235959000")
            if self.code_type == "STOCK":
                sub_tick_df = self.mdp.get_data_by_time_frame("Stock", self.code, start_date_time, end_date_time, ['1','2','3','4','5'])
            elif self.code_type == "CBOND":
                sub_tick_df = self.bd.get_bond_data(self.code, start_date_time, end_date_time, "TICK")

            if sub_tick_df.empty:
                sub_tick_df = pd.DataFrame(columns=TICK_RAW_COLUMNS)
            else:
                sub_tick_df = sub_tick_df[TICK_RAW_COLUMNS]
                sub_tick_df = sub_tick_df.replace({"PreClosePx": 0.0}, np.nan)  # 如遇PreClose为0的，以前值填充之
                sub_tick_df = sub_tick_df.fillna(method="ffill")
                # 将连续竞价期间OpenPrice, HighPrice和LowPrice为0的条目删掉
                sub_tick_df = tick_data_zero_price_filter(sub_tick_df)
                # 剔除临停期间数据
                sub_tick_df = tick_data_circuit_filter(sub_tick_df)

            sub_ticks_list.append(sub_tick_df)

        if len(sub_ticks_list) == 0:
            tick_df = pd.DataFrame()
        else:
            tick_df = pd.concat(sub_ticks_list, axis=0)

        if tick_df.empty:
            tick_df = pd.DataFrame(columns=TICK_TARGET_COLUMNS)
        else:
            tick_df["Timestamp"] = (tick_df["MDDate"] + tick_df["MDTime"]).apply(
                                              lambda x: dt.datetime.strptime(x + "000", "%Y%m%d%H%M%S%f").timestamp())
            daily_tick_df_list = []

            for trading_day in self.valid_date_list:
                daily_tick_df = tick_df[tick_df["MDDate"] == trading_day]
                if not daily_tick_df.empty:
                    daily_tick_df = daily_tick_df.reset_index(drop=True)
                    first_tick_volume = daily_tick_df.TotalVolumeTrade.iloc[0]
                    first_tick_amount = daily_tick_df.TotalValueTrade.iloc[0]
                    daily_tick_df["VolumeTrade"] = daily_tick_df["TotalVolumeTrade"].diff()
                    daily_tick_df["ValueTrade"] = daily_tick_df["TotalValueTrade"].diff()
                    # 每日第1行的成交额、成交量等于累计成交额、累计成交量
                    daily_tick_df.loc[0, "VolumeTrade"] = first_tick_volume
                    daily_tick_df.loc[0, "ValueTrade"] = first_tick_amount
                    daily_tick_df["VolumeTrade"] = daily_tick_df["VolumeTrade"].clip_lower(0)
                    daily_tick_df["ValueTrade"] = daily_tick_df["ValueTrade"].clip_lower(0)

                    daily_tick_df_list.append(daily_tick_df)

            tick_df = pd.concat(daily_tick_df_list, axis=0)

            tick_df = tick_df.reindex(columns=TICK_CLEAN_COLUMNS)
            tick_df.columns = TICK_TARGET_COLUMNS

        if self.code_type == "CBOND" and self.code.endswith(".SH"):
            tick_df[CBOND_SH_TICK_ADJUST_COLUMNS] = tick_df[CBOND_SH_TICK_ADJUST_COLUMNS] * CBOND_SH_VOLUME_MULTIPLE

        return tick_df

    def load_mdp_transaction_data(self):
        calc_time_groups = split_calc_date_into_group(self.valid_date_list, MAX_FRAME_LENGTH)
        sub_transactions_list = []
        for group in calc_time_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            # 读取股票逐笔数据
            start_date_time = "{0} {1}".format(sub_start_date, "000001000")
            end_date_time = "{0} {1}".format(sub_end_date, "235959000")
            if self.code_type == "STOCK":
                sub_transactions_df = self.mdp.get_data_by_time_frame("Transaction", self.code, start_date_time,
                                                                       end_date_time, ['1','2','3','4','5'])
            elif self.code_type == "CBOND":
                sub_transactions_df = self.bd.get_bond_data(self.code, start_date_time, end_date_time, "TRANSACTION")

            if sub_transactions_df.empty:
                sub_transactions_df = pd.DataFrame(columns=TRANSACTION_RAW_COLUMNS)
            else:
                sub_transactions_df = sub_transactions_df[TRANSACTION_RAW_COLUMNS]

            sub_transactions_list.append(sub_transactions_df)

        if len(sub_transactions_list) == 0:
            transactions_df = pd.DataFrame()
        else:
            transactions_df = pd.concat(sub_transactions_list, axis=0)

        if transactions_df.empty:
            transactions_df = pd.DataFrame(columns=TRANSACTION_CLEAN_COLUMNS)
        else:
            # 保留撤单数据 TradeType == 1
            transactions_df["Timestamp"] = (transactions_df["MDDate"] + transactions_df["MDTime"]).apply(
                                            lambda x: dt.datetime.strptime(x + "000", "%Y%m%d%H%M%S%f").timestamp())

        transactions_df = transactions_df.reindex(columns=TRANSACTION_CLEAN_COLUMNS)
        transactions_df.columns = TRANSACTION_TARGET_COLUMNS

        if self.code_type == "CBOND" and self.code.endswith(".SH"):
            transactions_df[CBOND_SH_TRANSACTION_ADJUST_COLUMNS] = transactions_df[CBOND_SH_TRANSACTION_ADJUST_COLUMNS] * CBOND_SH_VOLUME_MULTIPLE

        return transactions_df

    def load_mdp_order_data(self):
        order_raw_columns = SH_ORDER_RAW_COLUMNS if self.code.endswith(".SH") else ORDER_RAW_COLUMNS
        calc_time_groups = split_calc_date_into_group(self.valid_date_list, MAX_FRAME_LENGTH)
        sub_orders_list = []
        for group in calc_time_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            # 读取股票逐笔数据
            start_date_time = "{0} {1}".format(sub_start_date, "000001000")
            end_date_time = "{0} {1}".format(sub_end_date, "235959000")
            if self.code_type == "STOCK":
                sub_orders_df = self.mdp.get_data_by_time_frame("Order", self.code, start_date_time, end_date_time, ['1', '2', '3', '4', '5'])
            elif self.code_type == "CBOND":
                sub_orders_df = self.bd.get_bond_data(self.code, start_date_time, end_date_time, "ORDER")

            if sub_orders_df.empty:
                sub_orders_df = pd.DataFrame(columns=order_raw_columns)
            else:
                sub_orders_df = sub_orders_df[order_raw_columns]

            sub_orders_list.append(sub_orders_df)

        if len(sub_orders_list) == 0:
            orders_df = pd.DataFrame()
        else:
            orders_df = pd.concat(sub_orders_list, axis=0)

        if orders_df.empty:
            orders_df = pd.DataFrame(columns=ORDER_CLEAN_COLUMNS)
        else:
            if self.code.endswith(".SH"):
                orders_df = orders_df.rename(columns={"OrderNo": "OrderIndex"})
            orders_df["Timestamp"] = (orders_df["MDDate"] + orders_df["MDTime"]).apply(
                                      lambda x: dt.datetime.strptime(x + "000", "%Y%m%d%H%M%S%f").timestamp())

        orders_df = orders_df.reindex(columns=ORDER_CLEAN_COLUMNS)
        orders_df.columns = ORDER_TARGET_COLUMNS

        if self.code_type == "CBOND" and self.code.endswith(".SH"):
            orders_df[CBOND_SH_ORDER_ADJUST_COLUMNS] = orders_df[CBOND_SH_ORDER_ADJUST_COLUMNS] * CBOND_SH_VOLUME_MULTIPLE

        return orders_df

    def load_third_tick_data(self):
        calc_time_groups = split_calc_date_into_group(self.valid_date_list, MAX_FRAME_LENGTH)
        sub_ticks_list = []
        for group in calc_time_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            # 读取股票逐笔数据
            start_date_time = "{0}{1}".format(sub_start_date, "000001")
            end_date_time = "{0}{1}".format(sub_end_date, "235959")
            sub_tick_df = self.tma.getMDSecurityTickDataFrame(self.code, start_date_time, end_date_time, QueryType=1)

            if sub_tick_df.empty:
                sub_tick_df = pd.DataFrame(columns=TICK_RAW_COLUMNS)
            else:
                sub_tick_df = sub_tick_df[TICK_RAW_COLUMNS]
                sub_tick_df = sub_tick_df.replace({"PreClosePx": 0.0}, np.nan)  # 如遇PreClose为0的，以前值填充之
                sub_tick_df = sub_tick_df.fillna(method="ffill")
                # 将连续竞价期间OpenPrice, HighPrice和LowPrice为0的条目删掉
                sub_tick_df = tick_data_zero_price_filter(sub_tick_df)
                # 剔除临停期间数据
                sub_tick_df = tick_data_circuit_filter(sub_tick_df)

            sub_ticks_list.append(sub_tick_df)

        if len(sub_ticks_list) == 0:
            tick_df = pd.DataFrame()
        else:
            tick_df = pd.concat(sub_ticks_list, axis=0)

        if tick_df.empty:
            tick_df = pd.DataFrame(columns=TICK_TARGET_COLUMNS)
        else:
            tick_df["Timestamp"] = (tick_df["MDDate"] + tick_df["MDTime"]).apply(
                                              lambda x: dt.datetime.strptime(x + "000", "%Y%m%d%H%M%S%f").timestamp())
            daily_tick_df_list = []

            for trading_day in self.valid_date_list:
                daily_tick_df = tick_df[tick_df["MDDate"] == trading_day]
                if not daily_tick_df.empty:
                    daily_tick_df = daily_tick_df.reset_index(drop=True)
                    first_tick_volume = daily_tick_df.TotalVolumeTrade.iloc[0]
                    first_tick_amount = daily_tick_df.TotalValueTrade.iloc[0]
                    daily_tick_df["VolumeTrade"] = daily_tick_df["TotalVolumeTrade"].diff()
                    daily_tick_df["ValueTrade"] = daily_tick_df["TotalValueTrade"].diff()
                    # 每日第1行的成交额、成交量等于累计成交额、累计成交量
                    daily_tick_df.loc[0, "VolumeTrade"] = first_tick_volume
                    daily_tick_df.loc[0, "ValueTrade"] = first_tick_amount
                    daily_tick_df["VolumeTrade"] = daily_tick_df["VolumeTrade"].clip_lower(0)
                    daily_tick_df["ValueTrade"] = daily_tick_df["ValueTrade"].clip_lower(0)

                    daily_tick_df_list.append(daily_tick_df)

            tick_df = pd.concat(daily_tick_df_list, axis=0)

            tick_df = tick_df.reindex(columns=TICK_CLEAN_COLUMNS)
            tick_df.columns = TICK_TARGET_COLUMNS

        if self.code_type == "CBOND" and self.code.endswith(".SH"):
            tick_df[CBOND_SH_TICK_ADJUST_COLUMNS] = tick_df[CBOND_SH_TICK_ADJUST_COLUMNS] * CBOND_SH_VOLUME_MULTIPLE

        return tick_df

    def load_third_transaction_data(self):
        calc_time_groups = split_calc_date_into_group(self.valid_date_list, 1)
        sub_transactions_list = []
        for group in calc_time_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            # 读取股票逐笔数据
            start_date_time = "{0}{1}".format(sub_start_date, "000001")
            end_date_time = "{0}{1}".format(sub_end_date, "235959")
            sub_transactions_df = self.tma.getMDTransactionDataFrame(self.code, start_date_time, end_date_time)
            if sub_transactions_df.empty:
                sub_transactions_df = pd.DataFrame(columns=TRANSACTION_RAW_COLUMNS)
            else:
                sub_transactions_df = sub_transactions_df[TRANSACTION_RAW_COLUMNS]

            sub_transactions_list.append(sub_transactions_df)

        if len(sub_transactions_list) == 0:
            transactions_df = pd.DataFrame()
        else:
            transactions_df = pd.concat(sub_transactions_list, axis=0)

        if transactions_df.empty:
            transactions_df = pd.DataFrame(columns=TRANSACTION_CLEAN_COLUMNS)
        else:
            # 保留撤单数据 TradeType == 1
            transactions_df["Timestamp"] = (transactions_df["MDDate"] + transactions_df["MDTime"]).apply(
                                            lambda x: dt.datetime.strptime(x + "000", "%Y%m%d%H%M%S%f").timestamp())

        transactions_df = transactions_df.reindex(columns=TRANSACTION_CLEAN_COLUMNS)
        transactions_df.columns = TRANSACTION_TARGET_COLUMNS

        if self.code_type == "CBOND" and self.code.endswith(".SH"):
            transactions_df[CBOND_SH_TRANSACTION_ADJUST_COLUMNS] = transactions_df[CBOND_SH_TRANSACTION_ADJUST_COLUMNS] * CBOND_SH_VOLUME_MULTIPLE

        return transactions_df

    def load_third_order_data(self):
        order_raw_columns = SH_ORDER_RAW_COLUMNS if self.code.endswith(".SH") else ORDER_RAW_COLUMNS
        calc_time_groups = split_calc_date_into_group(self.valid_date_list, 1)
        sub_orders_list = []
        for group in calc_time_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            # 读取股票逐笔数据
            start_date_time = "{0}{1}".format(sub_start_date, "000001")
            end_date_time = "{0}{1}".format(sub_end_date, "235959")
            sub_orders_df = self.tma.getMDOrderDataFrame(self.code, start_date_time, end_date_time)
            if sub_orders_df.empty:
                sub_orders_df = pd.DataFrame(columns=order_raw_columns)
            else:
                sub_orders_df = sub_orders_df[order_raw_columns]

            sub_orders_list.append(sub_orders_df)

        if len(sub_orders_list) == 0:
            orders_df = pd.DataFrame()
        else:
            orders_df = pd.concat(sub_orders_list, axis=0)

        if orders_df.empty:
            orders_df = pd.DataFrame(columns=ORDER_CLEAN_COLUMNS)
        else:
            if self.code.endswith(".SH"):
                orders_df = orders_df.rename(columns={"OrderNo": "OrderIndex"})
            orders_df["Timestamp"] = (orders_df["MDDate"] + orders_df["MDTime"]).apply(
                                      lambda x: dt.datetime.strptime(x + "000", "%Y%m%d%H%M%S%f").timestamp())

        orders_df = orders_df.reindex(columns=ORDER_CLEAN_COLUMNS)
        orders_df.columns = ORDER_TARGET_COLUMNS

        if self.code_type == "CBOND" and self.code.endswith(".SH"):
            orders_df[CBOND_SH_ORDER_ADJUST_COLUMNS] = orders_df[CBOND_SH_ORDER_ADJUST_COLUMNS] * CBOND_SH_VOLUME_MULTIPLE

        return orders_df

    def load_hbase_tick_data(self, hbase_library):
        sub_ticks_list = []
        for date in self.valid_date_list:
            try:
                sub_tick_df = self.fa.get_factor_value(hbase_library, self.code, date, TICK_HBASE_COLUMNS + ["{}_IsMock".format(TICK_SUFFIX)])
                sub_tick_df.columns = list(map(lambda x: x.replace("{0}_".format(TICK_SUFFIX), ""), sub_tick_df.columns.to_list()))
                sub_tick_df = sub_tick_df[sub_tick_df["IsMock"] == 0].reset_index(drop=True)
                sub_tick_df = sub_tick_df.reindex(columns=ALIGN_TICK_COLUMNS)
                sub_tick_df.columns = ALIGN_TICK_COLUMNS
            except Exception as e:
                sub_tick_df = pd.DataFrame(columns=ALIGN_TICK_COLUMNS)

            sub_ticks_list.append(sub_tick_df)

        if len(sub_ticks_list) == 0:
            ticks_df = pd.DataFrame(columns=TICK_TARGET_COLUMNS)
        else:
            ticks_df = pd.concat(sub_ticks_list, axis=0)

            for level in range(1, 11):
                ticks_df["AskP{}".format(level)] = ticks_df["AskPrice"].apply(lambda x: x.tolist()[level - 1]).values
                ticks_df["AskV{}".format(level)] = ticks_df["AskVolume"].apply(lambda x: x.tolist()[level - 1]).values
                ticks_df["BidP{}".format(level)] = ticks_df["BidPrice"].apply(lambda x: x.tolist()[level - 1]).values
                ticks_df["BidV{}".format(level)] = ticks_df["BidVolume"].apply(lambda x: x.tolist()[level - 1]).values

        ticks_df = ticks_df.reindex(columns=TICK_TARGET_COLUMNS)
        ticks_df.columns = TICK_TARGET_COLUMNS

        # 数据保存至HBASE时已经进行了乘数处理
        # if self.code_type == "CBOND" and self.code.endswith(".SH"):
        #     ticks_df[CBOND_SH_TICK_ADJUST_COLUMNS] = ticks_df[CBOND_SH_TICK_ADJUST_COLUMNS] * CBOND_SH_VOLUME_MULTIPLE

        return ticks_df

    def load_hbase_transaction_data(self, hbase_library):
        sub_transactions_list = []
        for date in self.valid_date_list:
            try:
                sub_transactions_df = self.fa.get_factor_value(hbase_library, self.code, date, TRANSACTION_HBASE_COLUMNS)
                sub_transactions_df.columns = list(map(lambda x: x.replace("{0}_".format(TRANSACTION_SUFFIX), ""), sub_transactions_df.columns.to_list()))
                sub_transactions_df = sub_transactions_df.reindex(columns=TRANSACTION_TARGET_COLUMNS)
                sub_transactions_df.columns = TRANSACTION_TARGET_COLUMNS
            except Exception as e:
                sub_transactions_df = pd.DataFrame(columns=TRANSACTION_TARGET_COLUMNS)

            sub_transactions_list.append(sub_transactions_df)

        if len(sub_transactions_list) == 0:
            transactions_df = pd.DataFrame(columns=TRANSACTION_CLEAN_COLUMNS)
        else:
            transactions_df = pd.concat(sub_transactions_list, axis=0)

        # 数据保存至HBASE时已经进行了乘数处理
        # if self.code_type == "CBOND" and self.code.endswith(".SH"):
        #     transactions_df[CBOND_SH_TRANSACTION_ADJUST_COLUMNS] = transactions_df[CBOND_SH_TRANSACTION_ADJUST_COLUMNS] * CBOND_SH_VOLUME_MULTIPLE

        return transactions_df

    def load_hbase_order_data(self, hbase_library):
        sub_orders_list = []
        for date in self.valid_date_list:
            try:
                sub_orders_df = self.fa.get_factor_value(hbase_library, self.code, date, ORDER_HBASE_COLUMNS)
                sub_orders_df.columns = list(map(lambda x: x.replace("{0}_".format(ORDER_SUFFIX), ""), sub_orders_df.columns.to_list()))
                sub_orders_df = sub_orders_df.reindex(columns=ORDER_TARGET_COLUMNS)
                sub_orders_df.columns = ORDER_TARGET_COLUMNS
            except Exception as e:
                sub_orders_df = pd.DataFrame(columns=ORDER_TARGET_COLUMNS)

            sub_orders_list.append(sub_orders_df)

        if len(sub_orders_list) == 0:
            orders_df = pd.DataFrame(columns=ORDER_TARGET_COLUMNS)
        else:
            orders_df = pd.concat(sub_orders_list, axis=0)

        # 数据保存至HBASE时已经进行了乘数处理
        # if self.code_type == "CBOND" and self.code.endswith(".SH"):
        #     orders_df[CBOND_SH_ORDER_ADJUST_COLUMNS] = orders_df[CBOND_SH_ORDER_ADJUST_COLUMNS] * CBOND_SH_VOLUME_MULTIPLE

        return orders_df

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


if __name__ == "__main__":
    code = "000001.SZ"
    start_date = "20211112"
    end_date = "20211112"
    data_source = "third"
    hbase_library = "ZeusDataLib"
    dl = DataLoader(code, start_date, end_date)
    tick = dl.load_tick_data(data_source, hbase_library)
    print(tick.iloc[1000:].head())





