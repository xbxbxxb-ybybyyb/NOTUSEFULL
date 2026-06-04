import numpy as np
import os
from numba import jit
import polars as pl
import time
import copy
import ray
from xquant.xqutils.perf_profile import profile
import codon


def get_l3_data(symbol, date, base_dir="/dfs/group/800657/library/l3_data"):
    # base_dir = "/home/appadmin/l3_data"
    file_path = os.path.join(base_dir, f"{symbol}/{symbol}_{date}.parquet")
    if not os.path.exists(file_path):
        os.system("cd {} && python3 UpdateL3Data.py {} {}".format(base_dir, symbol, date))
    try:
        l3_df = pl.read_parquet(file_path)
    except:
        os.system("cd {} && python3 UpdateL3Data.py {} {}".format(base_dir, symbol, date))
        print("ERROR L3:", symbol, date)
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
    # .dt.cast_time_unit(time_unit="ms")
    l3_df = l3_df.with_columns(mdtime = pl.col("DateTime").dt.timestamp(time_unit = "ms") /1000.0,
                     recvtime = pl.col("recvtime").str.strptime(dtype=pl.Datetime, format="%Y%m%d%H%M%S%3f").dt.timestamp(time_unit="ms")/1000.0,
                     AskP0=pl.col('asks_price').list.first(),
                     BidP0=pl.col('bids_price').list.first(),
                     AskV0=pl.col('asks_qty').list.first(),
                     BidV0=pl.col('bids_qty').list.first()
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

def merge_one_order_trade(symbol, order_df, trade_df, tick_df):
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
        new_order_df = new_order_df.drop(columns="TradeType")
        new_order_df = new_order_df.with_columns(OrderType = pl.lit(2))
        new_order_df = new_order_df.select(order_columns)
        new_order_df = pl.concat([new_order_df, order_df])

        new_buy_order_df = new_order_df.filter(pl.col("BSFlag") == 1).group_by("msg_buy_no").agg(
            pl.last("Timestamp"), pl.last('OrderType'), pl.last('BSFlag'),
            pl.last('Price'), pl.sum('Volume'), pl.sum('Amount'),
            pl.last('SeqNo'), pl.last("recvtime"), pl.last("msg_sell_no"))
        new_buy_order_df = new_buy_order_df.with_columns(msg_buy_no = pl.lit(0))
        new_sell_order_df = new_order_df.filter(pl.col("BSFlag") == 2).group_by("msg_sell_no").agg(
            pl.last("Timestamp"), pl.last('OrderType'), pl.last('BSFlag'),
            pl.last('Price'), pl.sum('Volume'), pl.sum('Amount'),
            pl.last('SeqNo'), pl.last("recvtime"),pl.last("msg_buy_no"))
        new_sell_order_df = new_sell_order_df.with_columns(msg_buy_no = pl.lit(0))
        new_sell_order_df = new_sell_order_df.select(order_columns)
        new_buy_order_df = new_buy_order_df.select(order_columns)
        new_order_df = pl.concat([new_buy_order_df, new_sell_order_df], how="vertical").sort("SeqNo")

        new_tick_df = tick_df.filter(~pl.col("SeqNo").is_in(drop_dataindex))
    else:
        new_order_df = order_df
    # print(f"new_order_df: {new_order_df.shape}, new_trade_df: {new_trade_df.shape}, new_tick_df: {new_tick_df.shape}")
    return new_order_df, new_trade_df, new_tick_df

def get_l3_trade_order_date(symbol, date, merge_one_order = True, base_dir="/dfs/group/800657/library/l3_data"):
    try:
        l3_df = get_l3_data(symbol, date, base_dir)
    except Exception as e:
        print("ERROR： get_l3_data ", symbol, date, e)
        l3_df = pl.DataFrame()
    if len(l3_df) == 0:
        return pl.DataFrame(), pl.DataFrame(), pl.DataFrame(), pl.DataFrame()
    print(l3_df.columns)
    tick_df = l3_df.select([
        "mdtime", "last_price", "asks_price", "bids_price", "asks_qty", "bids_qty", "asks_count", "bids_count",
        "high_price", "low_price", "prev_close_price", "ttl_volume", "ttl_turn_over", "ttl_trade_num",
        "avg_ask_price", "avg_bid_price", "recvtime", "msg_order_type", "msg_trade_type", "msg_bsflag", "last_seq_num", "msg_price", "msg_qty",
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
        "last_seq_num": "SeqNo",
        'msg_order_type': 'OrderType',
        'msg_trade_type': 'TradeType',
        "mdtime": "Timestamp"
    })
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
        order_df, trade_df, tick_df = merge_one_order_trade(symbol, order_df, trade_df, tick_df)
    return tick_df, order_df, trade_df, cancel_df

@jit(nopython=True)
# @codon.jit#(pyvars=['np'])
def check_conditions(mdtimes, ask1_prices, bid1_prices, msg_trade_type, msg_bsflags, msg_prices, msg_qtys, seq_nos, vol1 = 400, vol2 = 600):
    n = len(mdtimes)
    # results_buy = np.zeros(n)#, dtype=np.int32)
    # results_sell = np.zeros(n)#, dtype=np.int32)
    # results_end_seqno = np.zeros(n) #dtype=np.float64
    results_buy = [0.0]*n
    results_sell = [0.0]*n
    results_end_seqno = [0.0]*n

    for i in range(n):
        ask1_price = ask1_prices[i]
        bid1_price = bid1_prices[i]

        if msg_trade_type[i] != -1:
            # 条件1: 判断买卖一档价差是否超过中间价的0.001
            mid_price = (ask1_price + bid1_price) / 2
            price_diff = abs(ask1_price-0.01-(bid1_price+0.01))
            if price_diff > 0.0012 * mid_price:
                # 满足条件1,开始计算买入总成交量
                buy_vol = 0.0
                buy_vol_weak = 0.0
                sell_vol = 0.0
                sell_vol_weak = 0.0
                start_time = mdtimes[i]
                flag_exceed_10s = False

                j = i + 1
                while j < n:
                    # if msg_trade_type[j] == -1:
                    #     # 非成交数据无需判断
                    #     j = j+1
                    #     continue
                    next_time = mdtimes[j]
                    msg_bsflag = msg_bsflags[j]
                    msg_price = msg_prices[j]
                    msg_qty = msg_qtys[j]
                    if results_buy[i] != 0 and results_sell[i] != 0:
                        results_end_seqno[i] = seq_nos[j-1]
                        break
                    # 判断时间差是否超过10秒
                    if next_time - start_time <= 10:
                        # 条件2: 判断下一条数据的买卖方向和成交价
                        if msg_bsflag == 1 and msg_price >= (bid1_price + 0.01) * 1.0008:
                            buy_vol += msg_qty
                        elif msg_bsflag == 2 and msg_price <= (ask1_price - 0.01) * 0.9992:
                            sell_vol += msg_qty
                        # 如果循环结束时buy_vol或sell_vol大于400,返回2
                        if buy_vol > vol1:
                            results_buy[i] = 2
                        if sell_vol > vol1:
                            results_sell[i] = -2
                    # else:
                    #     if not results_buy[i]:
                    #         results_buy[i] = -1
                    #     break
                    else:
                        if not flag_exceed_10s:
                            # 不包括t秒内>=a股的数量
                            flag_exceed_10s = True
                            buy_vol = 0
                            sell_vol = 0
                        # 条件2: 判断下一条数据的买卖方向和成交价
                        if msg_bsflag == 1:
                            if msg_price >= (bid1_price+0.01) * 1.0008:
                                buy_vol += msg_qty
                            else:
                                buy_vol_weak += msg_qty
                        elif msg_bsflag == 2:
                            if msg_price <= (ask1_price-0.01) * 0.9992:
                                sell_vol += msg_qty
                            else:
                                sell_vol_weak += msg_qty
                        if results_buy[i] == 0:
                            if buy_vol > vol1:
                                results_buy[i] = 1
                            elif buy_vol_weak > vol2:
                                results_buy[i] = -1
                        if results_sell[i] == 0:
                            if sell_vol > vol1:
                                results_sell[i] = -1
                            elif sell_vol_weak > vol2:
                                results_sell[i] = 1
                    j += 1
            else:
                results_end_seqno[i] = seq_nos[i]
                results_buy[i] = 0
                results_sell[i] = 0

    return results_buy, results_sell, results_end_seqno


# @profile
def calc(symbol, date):
    l3_df, order_df, trade_df, cancel_df = get_l3_trade_order_date(symbol, date, merge_one_order = True)
    l3_df = l3_df.join(trade_df, on = "SeqNo", how = "left")
    l3_df.write_parquet(f"{symbol}-{date}.parquet")
    #####################################################
    mdtimes = l3_df["Timestamp"].to_numpy()
    ask1_prices = l3_df["AskP0"].to_numpy()
    bid1_prices = l3_df["BidP0"].to_numpy()
    msg_trade_type = l3_df["TradeType"].to_numpy()
    msg_bsflags = l3_df["msg_bsflag"].to_numpy()
    msg_prices = l3_df["msg_price"].to_numpy()
    msg_qtys = l3_df["Volume"].to_numpy()# 注意：要用合并后的列
    seq_nos = l3_df["SeqNo"].to_numpy()
    print(seq_nos)

    results_buy, results_sell, results_end_seqno= check_conditions(mdtimes, ask1_prices, bid1_prices, msg_trade_type, msg_bsflags, msg_prices, msg_qtys, seq_nos)
    # print(results_buy)
    # print("results_buy shape:", results_buy[results_buy!=0].shape, "results_sell shape:",results_sell[results_sell!=0].shape)

    result_df = l3_df.select(["DateTime","Timestamp", "MDTime", "SeqNo"])
    result_df = result_df.with_columns(MDDate = pl.lit(date),
                        BuyActivePriceVolume_over_10_0012_400 = pl.Series("BuyActivePriceVolume_over_10_0012_400", results_buy),
                        SellActivePriceVolume_over_10_0012_400 = pl.Series("SellActivePriceVolume_over_10_0012_400", results_sell),
                        EndSeqNo=pl.Series("EndSeqNo", results_end_seqno)
                        )
    return result_df

if __name__=="__main__":
    t1 = time.time()
    date = "20230725"
    symbol = "688072.SH"
    sub_df = calc(symbol, date)
    # print(sub_df)
    # sub_df.write_parquet("/home/appadmin/df.pqt")
    print(time.time() - t1)

    # import ray
    # ray.init(num_cpus=10)
    # remote_func = ray.remote(calc)
    # tasks = [remote_func.remote() for i in  range(10)]
    # ray.get(tasks)
