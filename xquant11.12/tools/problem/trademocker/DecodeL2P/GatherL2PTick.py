#-*- coding:utf-8 -*-
# author: 015629
# datetime:2021/1/26 19:08
from DataInterface.Config import TICK_STOCK_HBASE_COLUMNS, ALIGN_STOCK_TICK_COLUMNS
from DataLoader.StockDataLoader import StockDataLoader
from DecodeL2P.DataCleanUtil import daily_align_tick_tran_order_data
from Utils.HelpFunc import my_print
from DecodeL2P.Config import CELL_SIZE, LOG_TICK_SUFFIX, LOG_TICK_HBASE_COLUMNS

import numpy as np
import pandas as pd
import datetime as dt
from xquant.factordata import FactorData
from xquant.marketdata import MarketData
from xquant.bonddata import BondData


class GatherL2PTickData(object):
    def __init__(self, l2pLibrary, stock, cbond, save, saveLibrary):
        self.l2pLibrary = l2pLibrary
        self.stock = stock
        self.cbond = cbond
        self.save = save
        self.saveLibrary = saveLibrary

        self.symbol = "{}{}".format(self.stock[:6], self.cbond[:6])

        self.fa = FactorData()
        self.sd = StockDataLoader(self.stock)
        self.mdp = MarketData()
        self.bd = BondData()

    def load_level2plus_tick_data(self, date, map_col=True):
        """"""
        HBASE_COLUMNS = LOG_TICK_HBASE_COLUMNS
        try:
            tick_df = self.fa.get_factor_value(self.l2pLibrary, self.symbol, date, HBASE_COLUMNS)
        except:
            tick_df = pd.DataFrame(columns=HBASE_COLUMNS)

        if map_col:
            tick_df.columns = list(map(lambda x: x.replace("{0}_".format(LOG_TICK_SUFFIX), ""), tick_df.columns.to_list()))
        if not tick_df.empty:
            tick_df.index = tick_df["Date"].astype(np.int64)

        return tick_df

    def load_market_tick_transaction_data(self, date):
        """加载Tick和逐笔成交、逐笔委托行情数据"""
        tick, _ = self.sd.load_tick_data(date, date)
        transaction, _ = self.sd.load_transaction_data(date, date)
        order, _ = self.sd.load_order_data(date, date)

        return tick, transaction, order

    def clean_stock_level2plus_tick(self, l2p_tick, tick):
        """"""
        l2p_tick["OpenPrice"] = 0
        l2p_tick["BidQty"] = 0
        l2p_tick["OfferQty"] = 0
        l2p_tick["AvgBidPrice"] = 0
        l2p_tick["AvgOfferPrice"] = 0

        for level in range(1, 11):
            l2p_tick["AskPrice{}".format(level)] = l2p_tick["AskPrice"].apply(lambda x: x.tolist()[level - 1]).values
            l2p_tick["AskVolume{}".format(level)] = l2p_tick["AskVolume"].apply(lambda x: x.tolist()[level - 1]).values
            l2p_tick["AskNum{}".format(level)] = 0
            l2p_tick["BidPrice{}".format(level)] = l2p_tick["BidPrice"].apply(lambda x: x.tolist()[level - 1]).values
            l2p_tick["BidVolume{}".format(level)] = l2p_tick["BidVolume"].apply(lambda x: x.tolist()[level - 1]).values
            l2p_tick["BidNum{}".format(level)] = 0

        # 清洗掉无效Tick，判断条件: 盘口是否全为零
        price_columns = ["AskPrice{}".format(level) for level in range(1, 11)] + ["BidPrice{}".format(level) for level in range(1, 11)]
        l2p_tick = l2p_tick[~(l2p_tick[price_columns].sum(axis=1) == 0)].reset_index(drop=True)

        first = tick.iloc[0]
        pre_close, max_price, min_price = first.PreviousClose, first.MaxPrice, first.MinPrice
        l2p_tick["PreviousClose"] = pre_close
        l2p_tick["MaxPrice"] = max_price
        l2p_tick["MinPrice"] = min_price

        l2p_tick = l2p_tick.reindex(columns=tick.columns.tolist())

        return l2p_tick

    def load_receive_time(self, date):
        """"""
        start_date_time = "{0} {1}".format(date, "000001000")
        end_date_time = "{0} {1}".format(date, "235959000")
        tick = self.mdp.get_data_by_time_frame("Stock", self.stock, start_date_time, end_date_time, ["1", "2", "3", "4", "5"])
        tick["Timestamp"] = (tick["MDDate"] + tick["MDTime"]).apply(lambda x: dt.datetime.strptime(x + "000", "%Y%m%d%H%M%S%f").timestamp())
        tick["ReceiveTimestamp"] = tick["ReceiveDateTime"].apply(lambda x: dt.datetime.strptime(str(x) + "000", "%Y%m%d%H%M%S%f").timestamp())
        tick = tick[["Timestamp", "ReceiveTimestamp"]]

        transaction = self.mdp.get_data_by_time_frame("Transaction", self.stock, start_date_time, end_date_time, ["1", "2", "3", "4", "5"])
        transaction["Timestamp"] = (transaction["MDDate"] + transaction["MDTime"]).apply(lambda x: dt.datetime.strptime(x + "000", "%Y%m%d%H%M%S%f").timestamp())
        transaction["ReceiveTimestamp"] = transaction["ReceiveDateTime"].apply(lambda x: dt.datetime.strptime(str(x) + "000", "%Y%m%d%H%M%S%f").timestamp())
        transaction = transaction[["Timestamp", "ReceiveTimestamp"]]

        cbond_tick = self.bd.get_bond_data(self.cbond, start_date_time, end_date_time, "TICK")
        cbond_tick["Timestamp"] = (cbond_tick["MDDate"] + cbond_tick["MDTime"]).apply(lambda x: dt.datetime.strptime(x + "000", "%Y%m%d%H%M%S%f").timestamp())
        cbond_tick["ReceiveTimestamp"] = cbond_tick["ReceiveDateTime"].apply(lambda x: dt.datetime.strptime(str(x) + "000", "%Y%m%d%H%M%S%f").timestamp())
        cbond_tick = cbond_tick[["Timestamp", "ReceiveTimestamp"]]
        cbond_tick_dict = cbond_tick.set_index("Timestamp")["ReceiveTimestamp"].to_dict()

        return tick, transaction, cbond_tick_dict

    def run(self, date):
        """"""
        l2p_tick = self.load_level2plus_tick_data(date)

        tick, transaction, order = self.load_market_tick_transaction_data(date)
        receive_tick, receive_transaction, receive_cbond_tick_dict = self.load_receive_time(date)

        l2p_tick = self.clean_stock_level2plus_tick(l2p_tick, tick)

        gather_tick = daily_align_tick_tran_order_data(self.stock, date, l2p_tick, transaction, order, receive_tick, receive_transaction, receive_cbond_tick_dict)

        if self.save:
            self.save_level2plus_tick(date, gather_tick)

        return gather_tick

    def save_level2plus_tick(self, date, gather_tick):
        """"""
        if not gather_tick.empty:
            gather_tick = gather_tick.reindex(columns=ALIGN_STOCK_TICK_COLUMNS)
            gather_tick.columns = TICK_STOCK_HBASE_COLUMNS

            self.fa.update_factor_value(self.saveLibrary, gather_tick, self.symbol, date, cell_size=CELL_SIZE)

        my_print(" Gather Level2Plus Tick Data with Market Tick Data Done : {}-{} ".format(self.stock, date))


if __name__ == "__main__":
    l2pLibrary = "ZGLevel2PlusTicks"
    stock = "000761.SZ"
    cbond = "127018.SZ"
    date = "20210511"
    save = True
    saveLibrary = "ZGLevel2PlusDataLib"
    gtd = GatherL2PTickData(l2pLibrary, stock, cbond, save, saveLibrary)
    gather_tick = gtd.run(date)
    print(gather_tick[["Time", "TSIndex", "TEIndex"]].head())
