# BreakingP0NumOrders
import numpy as np
import pandas as pd
import polars as pl
import datetime as dt
import os
import copy
import time
from xquant.xqutils.perf_profile import profile

debug = False

# @profile
def get_l3_data(symbol, date, use_pandas=False, base_dir="/dfs/group/800657/library/l3_data"):
    # base_dir = "/home/appadmin/l3_data"
    file_path = os.path.join(base_dir, f"{symbol}/{symbol}_{date}.parquet")
    if not os.path.exists(file_path):
        os.system("cd {} && python3 UpdateL3Data.py {} {}".format(base_dir, symbol, date))
    if use_pandas:
        try:
            l3_df = pd.read_parquet(file_path)
        except Exception as e:
            os.system("cd {} && python3 UpdateL3Data.py {} {}".format(base_dir, symbol, date))
            print("ERROR L3:", symbol, date, e)
            time.sleep(3)
            l3_df = pd.read_parquet(file_path)
        l3_df = l3_df[
            (l3_df["mdtime"] >= int(date + '093000000')) & (l3_df["mdtime"] <= int(date + '113000000')) | (
                    l3_df["mdtime"] >= int(date + '130000000')) & (l3_df["mdtime"] <= int(date + '145700000'))]
        if len(l3_df)==0:
            return pd.DataFrame()
        l3_df["mdtime"] = l3_df["mdtime"].astype(str)
        l3_df["recvtime"] = l3_df["recvtime"].astype(str)
        # l3_df["MDDate"] = l3_df["mdtime"].astype(str).apply(lambda x: int(x[:8]))
        l3_df["MDTime"] = l3_df["mdtime"].astype(str).apply(lambda x: int(x[8:]))
        l3_df["DateTime"] = pd.to_datetime(l3_df["mdtime"], format="%Y%m%d%H%M%S%f")
        l3_df["mdtime"] = l3_df["DateTime"].apply(lambda x: x.timestamp())
        l3_df["recvtime"] = pd.to_datetime(l3_df["recvtime"], format="%Y%m%d%H%M%S%f")
        l3_df["recvtime"] = l3_df["recvtime"].apply(lambda x: x.timestamp())
        l3_df['AskP0'] = l3_df["asks_price"].apply(lambda x: x[0])
        l3_df['BidP0'] = l3_df["bids_price"].apply(lambda x: x[0])
        l3_df['AskV0'] = l3_df["asks_qty"].apply(lambda x: x[0])
        l3_df['BidV0'] = l3_df["bids_qty"].apply(lambda x: x[0])
        l3_df['LastAskP0'] = l3_df["AskP0"].shift(1)
        l3_df['LastBidP0'] = l3_df["BidP0"].shift(1)
        l3_df['LastAskV0'] = l3_df["AskV0"].shift(1)
        l3_df['LastBidV0'] = l3_df["BidV0"].shift(1)
        l3_df["LevelOneChange"] = (l3_df['LastAskP0'] != l3_df["AskP0"]) | \
                                              (l3_df['LastBidP0'] != l3_df["BidP0"]) | \
                                              (l3_df['LastAskV0'] != l3_df["AskV0"]) | \
                                              (l3_df['LastBidV0'] != l3_df["BidV0"])
        l3_df["LevelOneChange"] = l3_df["LevelOneChange"].astype(float)
    else:
        try:
            l3_df = pl.read_parquet(file_path)
        except Exception as e:
            os.system("cd {} && python3 UpdateL3Data.py {} {}".format(base_dir, symbol, date))
            print("ERROR L3:", symbol, date, e)
            l3_df = pl.read_parquet(file_path)
        if len(l3_df)==0:
            return pl.DataFrame()
        l3_df = l3_df.filter(
            (l3_df["mdtime"] >= int(date + '093000000')) & (l3_df["mdtime"] <= int(date + '113000000')) |
            (l3_df["mdtime"] >= int(date + '130000000')) & (l3_df["mdtime"] <= int(date + '145700000')))

        l3_df = l3_df.cast({"mdtime":pl.String,"recvtime":pl.String}).\
            with_columns(
                MDTime=pl.col("mdtime").str.slice(8),
                DateTime=pl.col("mdtime").str.strptime(dtype=pl.Datetime, format="%Y%m%d%H%M%S%3f")
                # MDDate=pl.col("mdtime").str.slice(0, 8),
            )

        l3_df = l3_df.with_columns(mdtime = pl.col("DateTime").dt.timestamp(time_unit = "ms") /1000.0,
                         recvtime = pl.col("recvtime").str.strptime(dtype=pl.Datetime, format="%Y%m%d%H%M%S%3f").dt.replace_time_zone("Asia/Shanghai").dt.timestamp(time_unit="ms")/1000.0,
                         AskP0=pl.col('asks_price').list.first(),
                         BidP0=pl.col('bids_price').list.first(),
                         AskV0=pl.col('asks_qty').list.first(),
                         BidV0=pl.col('bids_qty').list.first(),
                         asks_price = pl.col('asks_price').list.slice(0, 10),
                         bids_price = pl.col('bids_price').list.slice(0, 10),
                         asks_qty = pl.col('asks_qty').list.slice(0, 10),
                         bids_qty = pl.col('bids_qty').list.slice(0, 10)
                         # BidV0=pl.col('bids_qty').map_elements(lambda x: x[0])# 慢
                         )
        # ActivePriceVolume_df = ActivePriceVolume_df.with_columns(pl.col("Timestamp")*1000.0)
        # ActivePriceVolume_df = ActivePriceVolume_df.with_columns(timestamp = pl.from_epoch("Timestamp",time_unit = "ms"))
        # ActivePriceVolume_df.with_columns(MDTime = pl.col("timestamp").dt.strftime("%H%M%S"))
        l3_df = l3_df.with_columns(LevelOneChange= ((pl.col('AskP0') != pl.col("AskP0").shift(1)) |
                        (pl.col('BidP0') != pl.col("BidP0").shift(1)) |
                        (pl.col('AskV0') != pl.col("AskV0").shift(1)) |
                        (pl.col('BidV0') != pl.col("BidV0").shift(1)))).cast({"LevelOneChange":pl.Float32})
    return l3_df


def merge_one_order_trade(symbol, order_df, trade_df, cancel_df, tick_df, use_pandas=False):
    if use_pandas:
        order_columns = order_df.columns
        trade_columns = trade_df.columns
        # 将同一个委托的成交单合并, 便于识别大单
        buy_trade_df = trade_df[trade_df["BSFlag"] == 1].groupby("msg_buy_no").agg({
            "Timestamp": "last", 'TradeType': 'last', 'BSFlag': 'last',
            'Price': 'last', 'Volume': 'sum', 'Amount': 'sum',
            'SeqNo': 'last', "recvtime": "last"}).reset_index()
        sell_trade_df = trade_df[trade_df["BSFlag"] == 2].groupby("msg_sell_no").agg({
            "Timestamp": "last", 'TradeType': 'last', 'BSFlag': 'last',
            'Price': 'last', 'Volume': 'sum', 'Amount': 'sum',
            'SeqNo': 'last', "recvtime": "last"}).reset_index()
        new_trade_df = pd.concat([buy_trade_df, sell_trade_df]).sort_values(by="SeqNo")
        drop_index = trade_df[~trade_df["SeqNo"].isin(new_trade_df["SeqNo"]).values]["SeqNo"]
        new_tick_df = tick_df[~tick_df["SeqNo"].isin(drop_index)]
        if symbol.endswith("SH"):
            # 还原原始委托
            new_order_df = copy.deepcopy(trade_df)
            new_order_df = new_order_df.drop("TradeType")
            new_order_df["OrderType"] = 2
            new_order_df = pd.concat([new_order_df, order_df])
            new_buy_order_df = new_order_df[new_order_df['BSFlag'] == 1].groupby("msg_buy_no").agg(
                {'Timestamp': "last", 'OrderType': "last", 'BSFlag': "last", 'Price': "last",
                 'Volume': "sum", 'Amount': "sum", 'msg_buy_no': "last",
                 'msg_sell_no': "last", 'SeqNo': "last", 'recvtime': "last"}
            )
            new_buy_order_df["msg_sell_no"] = 0
            new_sell_order_df = new_order_df[new_order_df['BSFlag'] == 2].groupby("msg_sell_no").agg(
                {'Timestamp': "last", 'OrderType': "last", 'BSFlag': "last", 'Price': "last",
                 'Volume': "sum", 'Amount': "sum", 'msg_buy_no': "last",
                 'msg_sell_no': "last", 'SeqNo': "last", 'recvtime': "last"}
            )
            new_buy_order_df["msg_buy_no"] = 0

            new_order_df = pd.concat([new_buy_order_df, new_sell_order_df]).sort_values(by="SeqNo")
            new_order_df = new_order_df.reindex(columns = order_columns)
            new_trade_df = new_trade_df.reindex(columns = trade_columns)
        else:
            new_order_df = order_df
    else:
        order_columns = order_df.columns
        trade_columns = trade_df.columns
        # 将同一个委托的成交单合并, 便于识别大单
        buy_trade_df = trade_df.filter(pl.col("BSFlag") == 1).group_by("msg_buy_no").agg(
            pl.last("Timestamp"), pl.last('TradeType'), pl.last('BSFlag'),
            pl.last('Price'), pl.sum('Volume'), pl.sum('Amount'),
            pl.last('SeqNo'), pl.last("recvtime"), pl.last("msg_sell_no"))
        sell_trade_df = trade_df.filter(pl.col("BSFlag") == 2).group_by("msg_sell_no").agg(
            pl.last("Timestamp"), pl.last('TradeType'), pl.last('BSFlag'),
            pl.last('Price'), pl.sum('Volume'), pl.sum('Amount'),
            pl.last('SeqNo'), pl.last("recvtime"),pl.last("msg_buy_no"))

        buy_trade_df = buy_trade_df.select(trade_columns)
        sell_trade_df = sell_trade_df.select(trade_columns)
        new_trade_df = pl.concat([buy_trade_df, sell_trade_df], how="vertical").sort("SeqNo")
        new_trade_df_dataindex = new_trade_df.select("SeqNo")
        # 方式一：保留单笔委托连续成交的最后一一条成交数据
        drop_dataindex = trade_df.filter(~pl.col("SeqNo").is_in(new_trade_df_dataindex)).select("SeqNo")
        new_tick_df = tick_df.filter(~pl.col("SeqNo").is_in(drop_dataindex))

        # 根据成交数据还原原始委托
        if symbol.endswith("SH"):
            new_order_df = copy.deepcopy(trade_df)
            new_order_df = new_order_df.drop("TradeType").with_columns(OrderType = pl.lit(-1))
            new_order_df = new_order_df.select(order_columns)
            # 成交在前，委托在后
            new_order_df = pl.concat([new_order_df, order_df]).sort("SeqNo")
            # 数量取成交和委托的累计数量，取最后一条的委托价
            # 统计Trade类型的数量作为成交量
            new_buy_order_df = new_order_df.filter(pl.col("BSFlag") == 1).group_by("msg_buy_no").agg(
                pl.last("Timestamp"), pl.last('OrderType'), pl.last('BSFlag'),
                pl.last('Price'), pl.sum('Volume'), pl.sum('Amount'), pl.col("Volume").where((pl.col("Volume")!=0) & (pl.col("OrderType")==-1)).sum().alias("TradeVolume"),
                pl.last('SeqNo'), pl.last("recvtime"), pl.last("msg_sell_no"))
            new_buy_order_df = new_buy_order_df.with_columns(msg_sell_no = pl.lit(0)).cast({"msg_sell_no":pl.Int64})
            new_sell_order_df = new_order_df.filter(pl.col("BSFlag") == 2).group_by("msg_sell_no").agg(
                pl.last("Timestamp"), pl.last('OrderType'), pl.last('BSFlag'),
                pl.last('Price'), pl.sum('Volume'), pl.sum('Amount'), pl.col("Volume").where((pl.col("Volume")!=0) & (pl.col("OrderType")==-1)).sum().alias("TradeVolume"),
                pl.last('SeqNo'), pl.last("recvtime"),pl.last("msg_buy_no"))
            new_sell_order_df = new_sell_order_df.with_columns(msg_buy_no = pl.lit(0)).cast({"msg_buy_no":pl.Int64})
            new_sell_order_df = new_sell_order_df.select(order_columns+["TradeVolume"])
            new_buy_order_df = new_buy_order_df.select(order_columns+["TradeVolume"])
            new_order_df = pl.concat([new_buy_order_df, new_sell_order_df], how="vertical").sort(by = "SeqNo")
            # 将Trade还原出的OrderType类型置为限价单
            new_order_df = new_order_df.with_columns(OrderType = pl.when(pl.col("OrderType")==-1).then(pl.lit(2)).otherwise(pl.col("OrderType")))
        else:
            new_order_df = copy.deepcopy(trade_df)
            new_order_df = new_order_df.drop("TradeType")
            new_order_df = new_order_df.with_columns(OrderType = pl.lit(2))
            new_order_df = new_order_df.select(order_columns)
            # 委托在前，成交在后
            new_order_df = pl.concat([order_df, new_order_df]).sort("SeqNo")

            # 数量取第一条委托的数量，第一条的委托价, 最后一笔成交的ApplSeqNum
            new_buy_order_df = new_order_df.filter(pl.col("BSFlag") == 1).group_by("msg_buy_no").agg(
                pl.last("Timestamp"), pl.last('OrderType'), pl.last('BSFlag'),
                pl.first('Price'), pl.first('Volume'), pl.sum('Amount'), (pl.sum("Volume")-pl.first('Volume')).cast(pl.Float64).alias("TradeVolume"),
                pl.last('SeqNo'), pl.last("recvtime"), pl.last("msg_sell_no"))
            new_buy_order_df = new_buy_order_df.with_columns(msg_sell_no = pl.lit(0)).cast({"msg_sell_no":pl.Int64})
            new_sell_order_df = new_order_df.filter(pl.col("BSFlag") == 2).group_by("msg_sell_no").agg(
                pl.last("Timestamp"), pl.last('OrderType'), pl.last('BSFlag'),
                pl.first('Price'), pl.first('Volume'), pl.sum('Amount'), (pl.sum("Volume")-pl.first('Volume')).cast(pl.Float64).alias("TradeVolume"),
                pl.last('SeqNo'), pl.last("recvtime"),pl.last("msg_buy_no"))
            new_sell_order_df = new_sell_order_df.with_columns(msg_buy_no = pl.lit(0)).cast({"msg_buy_no":pl.Int64})
            new_sell_order_df = new_sell_order_df.select(order_columns+["TradeVolume"])
            new_buy_order_df = new_buy_order_df.select(order_columns+["TradeVolume"])
            new_order_df = pl.concat([new_buy_order_df, new_sell_order_df], how="vertical").sort("SeqNo")
            # 删除原始委托的SeqNo
            new_order_df_dataindex = new_order_df.select("SeqNo")
            drop_dataindex = order_df.filter(~pl.col("SeqNo").is_in(new_order_df_dataindex)).select("SeqNo")
            new_tick_df = new_tick_df.filter(~pl.col("SeqNo").is_in(drop_dataindex))
    if debug:
        print(f"new_order_df: {new_order_df.shape}, new_trade_df: {new_trade_df.shape}, new_tick_df: {new_tick_df.shape}")
    # BUG: 一笔原始委托成交之后有剩余，还原原始委托groupby msg_buy_no只会保留一笔，但是Tick数据中同时有成交和委托多条记录。导致无法根据两条tick之间成交量的差推断该笔委托的成交；
    # 解决办法，tick_df只保留order对应的数据

    # 主要耗时在这
    new_tick_df = new_tick_df.filter((pl.col("SeqNo").is_in(new_order_df.select("SeqNo"))) | (pl.col("SeqNo").is_in(cancel_df.select("SeqNo"))))
    return new_order_df, new_trade_df, new_tick_df

def get_l3_trade_order_date(symbol, date, merge_one_order = True, use_pandas=False, base_dir="/dfs/group/800657/library/l3_data"):
    try:
        l3_df = get_l3_data(symbol, date, use_pandas, base_dir)
    except Exception as e:
        print("ERROR： get_l3_data ", symbol, date, e)
        l3_df = pd.DataFrame()
    if len(l3_df) == 0:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    if use_pandas:
        tick_df = l3_df[['mdtime', 'last_price', 'asks_price', 'bids_price', 'asks_qty',
                          'bids_qty', 'asks_count', 'bids_count', 'high_price', 'low_price',
                          'prev_close_price', 'ttl_volume', 'ttl_turn_over', 'ttl_trade_num',
                          'avg_ask_price', 'avg_bid_price', 'recvtime', 'msg_order_type', 'msg_trade_type',"msg_bsflag",
                          'last_seq_num',  "AskP0", "BidP0", "AskV0", "BidV0", "LevelOneChange", "MDTime", "DateTime"
                          ]]
        order_df = l3_df[["mdtime", 'msg_order_type', 'msg_bsflag', 'msg_price',
                           'msg_qty', 'msg_amt', 'msg_buy_no', 'msg_sell_no', "last_seq_num", "recvtime", "DateTime"]]
        trade_df = l3_df[["mdtime", 'msg_trade_type', 'msg_bsflag', 'msg_price',
                           'msg_qty', 'msg_amt', 'msg_buy_no', 'msg_sell_no', "last_seq_num", "recvtime", "DateTime"]]
        order_df = order_df.rename(columns={"msg_order_type": "OrderType",
                                            "msg_bsflag": "BSFlag", "msg_price": "Price",
                                            "msg_qty": "Volume", "last_seq_num": "SeqNo",
                                            "mdtime": "Timestamp", "msg_amt": "Amount"})
        trade_df = trade_df.rename(columns={"msg_trade_type": "TradeType",
                                            "msg_bsflag": "BSFlag", "msg_price": "Price",
                                            "msg_qty": "Volume", "last_seq_num": "SeqNo",
                                            "mdtime": "Timestamp", "msg_amt": "Amount"})
        tick_df = tick_df.rename(columns={
            'asks_price': 'AskPrice', 'bids_price': 'BidPrice',
            'asks_qty': 'AskVolume', 'bids_qty': 'BidVolume',
            'asks_count': 'AskNum', 'bids_count': 'BidNum',
            "last_seq_num": "SeqNo",
            'msg_order_type': 'OrderType',
            'msg_trade_type': 'TradeType',
            "mdtime": "Timestamp"
        })

        if symbol.endswith("SH"):
            order_df = order_df[order_df["OrderType"] != -1]
            trade_df = trade_df[trade_df["TradeType"] != -1]
            cancel_df = order_df[order_df["OrderType"] == 10]
            order_df = order_df[order_df["OrderType"] != 10]
        else:
            order_df = order_df[order_df["OrderType"] != -1]
            trade_df = trade_df[trade_df["TradeType"] != -1]
            cancel_df = trade_df[trade_df["TradeType"] == 1]
            trade_df = trade_df[trade_df["TradeType"] != 1]

        if merge_one_order:
            order_df, trade_df, tick_df = merge_one_order_trade(symbol, order_df, trade_df, cancel_df, tick_df, use_pandas)
    else:
        tick_df = l3_df.select([
            "mdtime", "last_price", "asks_price", "bids_price", "asks_qty", "bids_qty", "asks_count", "bids_count",
            "high_price", "low_price", "prev_close_price", "ttl_volume", "ttl_turn_over", "ttl_trade_num",
            "avg_ask_price", "avg_bid_price", "recvtime", "msg_order_type", "msg_trade_type", "msg_bsflag", "last_seq_num",
            "AskP0", "BidP0", "AskV0", "BidV0", "LevelOneChange", "MDTime", "DateTime"
        ])
        order_df = l3_df.select([
            "mdtime", "msg_order_type", "msg_bsflag", "msg_price", "msg_qty", "msg_amt", "msg_buy_no",
            "msg_sell_no",
            "last_seq_num", "recvtime"
        ]).rename({"msg_order_type": "OrderType",
                   "msg_bsflag": "BSFlag", "msg_price": "Price",
                   "msg_qty": "Volume", "last_seq_num": "SeqNo",
                   "mdtime": "Timestamp", "msg_amt": "Amount"})
        trade_df = l3_df.select([
            "mdtime", "msg_trade_type", "msg_bsflag", "msg_price", "msg_qty", "msg_amt", "msg_buy_no",
            "msg_sell_no",
            "last_seq_num", "recvtime"
        ]).rename({"msg_trade_type": "TradeType",
                   "msg_bsflag": "BSFlag", "msg_price": "Price",
                   "msg_qty": "Volume", "last_seq_num": "SeqNo",
                   "mdtime": "Timestamp", "msg_amt": "Amount"})
        tick_df = tick_df.rename({
            'asks_price': 'AskPrice', 'bids_price': 'BidPrice',
            'asks_qty': 'AskVolume', 'bids_qty': 'BidVolume',
            'asks_count': 'AskNum', 'bids_count': 'BidNum',
            "last_seq_num": "SeqNo",
            'msg_order_type': 'OrderType',
            'msg_trade_type': 'TradeType',
            "mdtime": "Timestamp"
        })
        # tick_df = tick_df.with_columns(AskPrice=pl.col("AskPrice").list.to_array(10),
        #                                BidPrice=pl.col("BidPrice").list.to_array(10),
        #                                AskVolume=pl.col("AskVolume").list.to_array(10),
        #                                BidVolume=pl.col("BidVolume").list.to_array(10),
        #                                AskNum=pl.col("AskNum").list.to_array(10),
        #                                BidNum=pl.col("BidNum").list.to_array(10)
        #                                )
        if symbol.endswith("SH"):
            order_df = order_df.filter(pl.col("OrderType") != -1)
            trade_df = trade_df.filter(pl.col("TradeType") != -1)
            cancel_df = order_df.filter(pl.col("OrderType") == 10)
            order_df = order_df.filter(pl.col("OrderType") != 10)
        else:
            order_df = order_df.filter(pl.col("OrderType") != -1)
            trade_df = trade_df.filter(pl.col("TradeType") != -1)
            cancel_df = trade_df.filter(pl.col("TradeType") == 1)
            trade_df = trade_df.filter(pl.col("TradeType") != 1)

        if merge_one_order:
            order_df, trade_df, tick_df = merge_one_order_trade(symbol, order_df, trade_df, cancel_df, tick_df, use_pandas)
    return tick_df, order_df, trade_df, cancel_df


class MarketDataManager:
    # @profile
    def __init__(self, symbol, date, base_dir="/dfs/group/800657/library/l3_data") -> None:
        self.base_dir = base_dir
        self.symbol = symbol
        self.date = date
        use_pandas = False
        tick_df, order_df, trade_df, cancel_df = get_l3_trade_order_date(symbol, date, merge_one_order=True,
                                                                          use_pandas=use_pandas, base_dir=base_dir)
        if use_pandas:
            tick_array = tick_df.values
            order_array = order_df.values
            trade_array = trade_df.values
            cancel_array = cancel_df.values
        else:
            tick_df = tick_df.with_columns(sample_1s_flag = pl.lit(0))# 是否为1s内的第一条数据
            tick_array = tick_df.to_numpy()
            order_array = order_df.to_numpy()
            trade_array = trade_df.to_numpy()
            cancel_array = cancel_df.to_numpy()


        self.last_sample_1s_timestamp = 0
        self.tick_array = tick_array
        self.tick_colidx = {col: cidx for cidx, col in enumerate(tick_df.columns)}
        self.order_array = order_array
        self.order_colidx = {col: cidx for cidx, col in enumerate(order_df.columns)}
        self.trade_array = trade_array
        self.trade_colidx = {col: cidx for cidx, col in enumerate(trade_df.columns)}
        self.cancel_array = cancel_array
        self.cancel_colidx = {col: cidx for cidx, col in enumerate(cancel_df.columns)}
        self.order_len = len(self.order_array)
        self.trade_len = len(self.trade_array)
        self.cancel_len = len(self.cancel_array)
        self.order_idx = -1
        self.trade_idx = -1
        self.cancel_idx = -1
        self.idx = -1
        self.dataindex = -1
        try:
            self.next_order_idx = 0
            self.next_order_seq_num = self.order_array[self.next_order_idx, self.order_colidx["SeqNo"]]
            self.next_trade_idx = 0
            self.next_trade_seq_num = self.trade_array[self.next_trade_idx, self.trade_colidx["SeqNo"]]
            self.next_cancel_idx = 0
            self.next_cancel_seq_num = self.cancel_array[self.next_cancel_idx, self.cancel_colidx["SeqNo"]]
        except:
            self.next_order_idx = 0
            self.next_order_seq_num = 0
            self.next_trade_idx = 0
            self.next_trade_seq_num = 0
            self.next_cancel_idx = 0
            self.next_cancel_seq_num = 0

    def broadcast(self):
        self.idx = self.idx + 1
        self.dataindex = self.tick_array[self.idx, self.tick_colidx["SeqNo"]]
        now_timestamp = self.tick_array[self.idx, self.tick_colidx["Timestamp"]]
        self.last_timestamp = now_timestamp
        if int(now_timestamp) > int(self.last_sample_1s_timestamp):
            # 当前数据为1s内的第一条数据
            self.last_sample_1s_timestamp = now_timestamp
            self.tick_array[self.idx, self.tick_colidx["sample_1s_flag"]] = 1

        if self.dataindex >= self.next_order_seq_num and self.next_order_idx < self.order_len-1:
            self.order_idx += 1
            self.next_order_idx += 1
            self.next_order_seq_num = self.order_array[self.next_order_idx, self.order_colidx["SeqNo"]]

        if self.dataindex >= self.next_trade_seq_num and self.next_trade_idx < self.trade_len-1:
                # 有问题：深交所委托的ApplSeqNum替换为了最后一条成交的ApplSeqNum，所以成交不再回放，避免重复播放
                self.trade_idx += 1
                self.next_trade_idx += 1
                self.next_trade_seq_num = self.trade_array[self.next_trade_idx, self.trade_colidx["SeqNo"]]
        if self.dataindex >= self.next_cancel_seq_num and self.next_cancel_idx < self.cancel_len-1:
            self.cancel_idx += 1
            self.next_cancel_idx += 1
            self.next_cancel_seq_num = self.cancel_array[self.next_cancel_idx, self.cancel_colidx["SeqNo"]]

        # 在上交所生成原始委托后，以下逻辑有问题，因为原始委托的DataIndex要么不在Tick_df中存在，要么和Tick_df中的Trade的DataIndex重合
        # if self.symbol.endswith("SH"):
        #     if self.tick_array[self.idx, self.tick_colidx["TradeType"]] == -1:
        #         if self.tick_array[self.idx, self.tick_colidx["OrderType"]] == 10:
        #             self.cancel_idx += 1
        #         else:
        #             # Order类型
        #             self.order_idx += 1
        #     else:
        #         self.trade_idx += 1
        # else:
        #     if self.tick_array[self.idx, self.tick_colidx["TradeType"]] == -1:
        #         self.order_idx += 1
        #     else:
        #         if self.tick_array[self.idx, self.tick_colidx["TradeType"]] == 1:
        #             self.cancel_idx += 1
        #         else:
        #             self.trade_idx += 1

    def getSymbol(self):
        return self.symbol

    def getDate(self):
        return self.date

    def getPrevTick(self, field):
        return self.tick_array[self.idx, self.tick_colidx[field]]

    def getPrevOrder(self, field):
        return self.order_array[self.order_idx, self.order_colidx[field]]

    def getPrevCancel(self, field):
        return self.cancel_array[self.cancel_idx, self.cancel_colidx[field]]

    def getPrevTrade(self, field):
        return self.trade_array[self.trade_idx, self.trade_colidx[field]]

    def getPrevNTick(self, field, slide):
        return self.tick_array[max(0, self.idx + 1 - slide):self.idx + 1, self.tick_colidx[field]]

    def getPrevNOrder(self, field, slide):
        return self.order_array[max(0, self.order_idx + 1 - slide):self.order_idx + 1, self.order_colidx[field]]

    def getPrevNTrade(self, field, slide):
        return self.trade_array[max(0, self.trade_idx + 1 - slide):self.trade_idx + 1, self.trade_colidx[field]]

    def getPrevNCancel(self, field, slide):
        return self.cancel_array[max(0, self.cancel_idx + 1 - slide):self.cancel_idx + 1, self.cancel_colidx[field]]

    def getPrevSecTick(self, field, n_seconds):
        if n_seconds >= 0:
            timestamp = self.tick_array[0:self.idx+1, self.tick_colidx["Timestamp"]]
            startIndex = np.searchsorted(timestamp, self.last_timestamp - n_seconds, side="left")
            return self.tick_array[startIndex:self.idx+1, self.tick_colidx[field]]
        else:
            # 查询未来数据
            timestamp = self.tick_array[self.idx+1:, self.tick_colidx["Timestamp"]]
            endindex = np.searchsorted(timestamp, self.last_timestamp - n_seconds, side="right")
            return self.tick_array[self.idx+1: self.idx+endindex+1, self.tick_colidx[field]]

    def getPrevSecOrder(self, field, n_seconds):
        if False:
            mask = self.order_array[:, self.order_colidx["Timestamp"]] > self.last_timestamp - dt.timedelta(
                n_seconds) & self.order_array[:, self.order_colidx["Timestamp"]] <= self.last_timestamp
            return self.order_array[mask][:, self.order_colidx[field]]
        else:
            if n_seconds>=0:
                timestamp = self.order_array[0:self.order_idx+1, self.order_colidx["Timestamp"]]
                # 【？是否需要right】
                startIndex = np.searchsorted(timestamp, self.last_timestamp - n_seconds, side="left")
                return self.order_array[startIndex:self.order_idx+1, self.order_colidx[field]]
            else:
                # 查询未来数据(不包括当前, 右闭)
                timestamp = self.order_array[self.order_idx+1:, self.order_colidx["Timestamp"]]
                endindex = np.searchsorted(timestamp, self.last_timestamp - n_seconds, side="right")
                return self.order_array[self.order_idx+1:self.order_idx+endindex+1, self.order_colidx[field]]


    def getPrevSecTrade(self, field, n_seconds):
        if False:
            mask = self.trade_array[:, self.trade_colidx["Timestamp"]] > self.last_timestamp - dt.timedelta(
                n_seconds) & self.trade_array[:, self.trade_colidx["Timestamp"]] <= self.last_timestamp
            return self.trade_array[mask][:, self.trade_colidx[field]]
        else:
            if n_seconds>=0:
                timestamp = self.trade_array[0:self.trade_idx+1, self.trade_colidx["Timestamp"]]
                startIndex = np.searchsorted(timestamp, self.last_timestamp - n_seconds, side="left")
                return self.trade_array[startIndex:self.trade_idx+1, self.trade_colidx[field]]
            else:
                # 查询未来数据(不包括当前)
                timestamp = self.trade_array[self.trade_idx+1:, self.trade_colidx["Timestamp"]]
                endindex = np.searchsorted(timestamp, self.last_timestamp - n_seconds, side="right")
                return self.trade_array[self.trade_idx+1:self.trade_idx+endindex+1, self.trade_colidx[field]]

    def getPrevSecCancel(self, field, n_seconds):
        if False:
            mask = self.cancel_array[:, self.cancel_colidx["Timestamp"]] > self.last_timestamp - dt.timedelta(
                n_seconds) & self.cancel_array[:, self.cancel_colidx["Timestamp"]] <= self.last_timestamp
            return self.cancel_array[mask][:, self.cancel_colidx[field]]
        else:
            if n_seconds>=0:
                timestamp = self.cancel_array[0:self.cancel_idx+1, self.cancel_colidx["Timestamp"]]
                startIndex = np.searchsorted(timestamp, self.last_timestamp - n_seconds, side="left")
                return self.cancel_array[startIndex:self.cancel_idx+1, self.cancel_colidx[field]]
            else:
                # 查询未来数据(不包括当前)
                timestamp = self.cancel_array[self.cancel_array+1:, self.cancel_colidx["Timestamp"]]
                endindex = np.searchsorted(timestamp, self.last_timestamp - n_seconds, side="right")
                return self.cancel_array[self.cancel_idx+1:self.cancel_idx+endindex+1, self.cancel_colidx[field]]

