from DataInterface.Config import SUB_ALIGN_STOCK_COLUMNS, BID_PRICE_COLUMNS, ASK_PRICE_COLUMNS, BID_VOLUME_COLUMNS, ASK_VOLUME_COLUMNS, BID_NUM_COLUMNS, ASK_NUM_COLUMNS
from DataInterface.Config import ALIGN_STOCK_TICK_COLUMNS

import copy
import numpy as np
import pandas as pd
import datetime as dt

def generate_timestamp(trading_day, time):
    return dt.datetime.strptime("{0} {1}".format(trading_day, time), "%Y%m%d %H%M%S").timestamp()

def generate_daily_key_timestamp(trading_day):
    morning_start_timestamp = generate_timestamp(trading_day, "093015")
    morning_end_timestamp = generate_timestamp(trading_day, "112959")
    afternoon_start_timestamp = generate_timestamp(trading_day, "130015")
    afternoon_end_timestamp = generate_timestamp(trading_day, "145659")
    return morning_start_timestamp, morning_end_timestamp, afternoon_start_timestamp, afternoon_end_timestamp

def fill_none_tick_with_help_df(fill_df, help_df):
    # Code, Date, MinPrice, MaxPrice, PreviousClose字段一天中保持不变，直接复制
    # fill_df: 传入一个空DataFrame，列名给定
    fill_df.loc[0, :] = copy.deepcopy(help_df.values)
    fill_nan_columns = ["OpenPrice", "HighPrice", "LowPrice", "LastPrice", "AvgBidPrice", "AvgOfferPrice"]
    fill_zero_columns = ["Volume", "Amount", "TotalVolume", "TotalAmount", "NumTrades", "BidQty", "OfferQty", "TSIndex", "TEIndex", "OSIndex", "OEIndex"]
    fill_none_columns = ["BidPrice", "AskPrice", "BidVolume", "AskVolume", "BidNum", "AskNum"]
    fill_df.loc[0, fill_nan_columns] = [np.nan for _ in range(len(fill_nan_columns))]
    fill_df.loc[0, fill_zero_columns] = [0 for _ in range(len(fill_zero_columns))]
    fill_df.loc[0, fill_none_columns] = [None for _ in range(len(fill_none_columns))]
    fill_df.loc[0, "IsMock"] = 1
    return fill_df

def get_start_end_not_fill_tick(tick_timestamp_list, fill_tick_timestamp_list):
    start_no_fill_tick_timestamp = None
    end_no_fill_tick_timestamp = None
    if len(tick_timestamp_list):
        for tick_timestamp in tick_timestamp_list:
            if tick_timestamp not in fill_tick_timestamp_list:
                start_no_fill_tick_timestamp = tick_timestamp
                break
        for tick_timestamp in tick_timestamp_list[::-1]:
            if tick_timestamp not in fill_tick_timestamp_list:
                end_no_fill_tick_timestamp = tick_timestamp
                break
    return start_no_fill_tick_timestamp, end_no_fill_tick_timestamp

def daily_align_tick_tran_order_data(code, trading_day, l2p_tick, transaction, order, receive_tick, receive_transaction, receive_cbond_tick_dict):
    """
    （1）对齐Tick & Transaction & Order 数据，获取每个Tick对应的Transaction/Order开始结束的Index
    (2）后面每个Tick计算时向前补齐
    """
    ALIGN_TICK_COLUMNS = ALIGN_STOCK_TICK_COLUMNS

    morning_start_timestamp = generate_timestamp(trading_day, "093015")
    morning_end_timestamp = generate_timestamp(trading_day, "112959")
    afternoon_start_timestamp = generate_timestamp(trading_day, "130015")
    afternoon_end_timestamp = generate_timestamp(trading_day, "145659")

    # 为了优化效率加速，提取出Numpy矩阵，以及各个列名idx
    tick_array = l2p_tick.values
    sub_align_stock_idx = [l2p_tick.columns.get_loc(k) for k in SUB_ALIGN_STOCK_COLUMNS]
    bid_price_idx = [l2p_tick.columns.get_loc(k) for k in BID_PRICE_COLUMNS]
    ask_price_idx = [l2p_tick.columns.get_loc(k) for k in ASK_PRICE_COLUMNS]
    bid_volume_idx = [l2p_tick.columns.get_loc(k) for k in BID_VOLUME_COLUMNS]
    ask_volume_idx = [l2p_tick.columns.get_loc(k) for k in ASK_VOLUME_COLUMNS]
    bid_num_idx = [l2p_tick.columns.get_loc(k) for k in BID_NUM_COLUMNS]
    ask_num_idx = [l2p_tick.columns.get_loc(k) for k in ASK_NUM_COLUMNS]

    # 为了加速运行，提取出逐笔交易数据时间戳列表、数值矩阵
    order_start_idx, order_end_idx = 0, 0
    tran_index_list = transaction["Timestamp"].to_list()
    receive_tran_index_list = receive_transaction["ReceiveTimestamp"].tolist()
    if code.endswith(".SZ"):
        order_index_list = order["Timestamp"].tolist()

    timestamp_tick_values_list = []
    fill_tick_timestamp_list = []
    for i in range(tick_array.shape[0]):

        # 当前Tick信息
        base_cols = tick_array[i, sub_align_stock_idx].tolist()
        bid_price_col = tick_array[i, bid_price_idx].reshape(len(BID_PRICE_COLUMNS),).astype(np.float64)
        ask_price_col = tick_array[i, ask_price_idx].reshape(len(ASK_PRICE_COLUMNS),).astype(np.float64)
        bid_volume_col = tick_array[i, bid_volume_idx].reshape(len(BID_VOLUME_COLUMNS),).astype(np.float64)
        ask_volume_col = tick_array[i, ask_volume_idx].reshape(len(ASK_VOLUME_COLUMNS),).astype(np.float64)
        bid_num_col = tick_array[i, bid_num_idx].reshape(len(BID_NUM_COLUMNS),).astype(np.int)
        ask_num_col = tick_array[i, ask_num_idx].reshape(len(ASK_NUM_COLUMNS),).astype(np.int)

        tick_timestamp = base_cols[1]
        receive_tick_timestamp = receive_cbond_tick_dict.get(tick_timestamp)

        # 确定每个Tick逐笔成交 & 逐笔委托数据的 Start & End Index
        before_transaction = receive_transaction[(receive_transaction["ReceiveTimestamp"] < receive_tick_timestamp ) &
                                                 (receive_transaction["Timestamp"] < tick_timestamp )]
        mock_tran_end_idx = before_transaction.shape[0]

        before_real_tick = receive_tick[(receive_tick["ReceiveTimestamp"] < receive_tick_timestamp) &
                                        (receive_tick["Timestamp"] < tick_timestamp)]
        if len(before_real_tick) > 0:
            mock_tick_start_timestamp = before_real_tick.iloc[-1].Timestamp
            mock_transaction = before_transaction[before_transaction["Timestamp"] >= mock_tick_start_timestamp]
            mock_tran_start_idx = mock_tran_end_idx - mock_transaction.shape[0]
        else:
            mock_tran_start_idx = mock_tran_end_idx

        if code.endswith(".SZ"):
            order_start_idx = order_end_idx
            while order_end_idx < len(order_index_list):
                if order_index_list[order_end_idx] < tick_timestamp:
                    order_end_idx += 1
                else:
                    break

        timestamp_tick_values = base_cols + [bid_price_col, ask_price_col, bid_volume_col, ask_volume_col, bid_num_col, ask_num_col,
                                             mock_tran_start_idx, mock_tran_end_idx, order_start_idx, order_end_idx] + [0]

        # 把当前Tick数据加入到align_daily_stock_tick_df中
        timestamp_tick_values_list.append(timestamp_tick_values)

    # 汇总已有数据
    align_tick = pd.DataFrame(timestamp_tick_values_list, columns=ALIGN_TICK_COLUMNS)

    # 加入093012 TICK数据
    first_tick_timestamp = generate_timestamp(trading_day, "093012")
    first_tick = align_tick[align_tick["Timestamp"] <= first_tick_timestamp]
    help_df = align_tick[align_tick["Timestamp"] > first_tick_timestamp].head(1)

    # 检查是否存在093012 TICK数据
    align_am_first_tick = pd.DataFrame(columns=ALIGN_TICK_COLUMNS)
    if first_tick.empty:
        align_am_first_tick = fill_none_tick_with_help_df(align_am_first_tick, help_df)
    else:
        align_am_first_tick.loc[0, ALIGN_TICK_COLUMNS] = first_tick[ALIGN_TICK_COLUMNS].tail(1).values
    align_am_first_tick.loc[0, "Timestamp"] = first_tick_timestamp

    # 处理上午数据，开始和结束均从第一个非补齐TICK开始
    am_tick_timestamp_list = align_tick[(align_tick["Timestamp"] >= morning_start_timestamp) &
                                        (align_tick["Timestamp"] <= morning_end_timestamp)]["Timestamp"].values.tolist()
    am_start_timestamp, am_end_timestamp = get_start_end_not_fill_tick(am_tick_timestamp_list, fill_tick_timestamp_list)
    if am_start_timestamp is None or am_end_timestamp is None:
        align_am_tick = pd.DataFrame(columns=ALIGN_TICK_COLUMNS)
    else:
        am_start_timestamp = max(am_start_timestamp, morning_start_timestamp)
        am_end_timestamp = min(am_end_timestamp, morning_end_timestamp)
        align_am_tick = align_tick[(align_tick["Timestamp"] >= am_start_timestamp) & (align_tick["Timestamp"] <= am_end_timestamp)]

    # 处理下午时刻数据，开始和结束均从第一个非补齐TICK开始
    pm_tick_timestamp_list = align_tick[(align_tick["Timestamp"] >= afternoon_start_timestamp) &
                                        (align_tick["Timestamp"] <= afternoon_end_timestamp)]["Timestamp"].values.tolist()
    pm_start_timestamp, pm_end_timestamp = get_start_end_not_fill_tick(pm_tick_timestamp_list, fill_tick_timestamp_list)
    if pm_start_timestamp is None or pm_end_timestamp is None:
        align_pm_tick = pd.DataFrame(columns=ALIGN_TICK_COLUMNS)
    else:
        pm_start_timestamp = max(pm_start_timestamp, afternoon_start_timestamp)
        pm_end_timestamp = min(pm_end_timestamp, afternoon_end_timestamp)
        align_pm_tick = align_tick[(align_tick["Timestamp"] >= pm_start_timestamp) & (align_tick["Timestamp"] <= pm_end_timestamp)]

    # 合并上下午数据
    align_tick = pd.concat([align_am_first_tick, align_am_tick, align_pm_tick], axis=0)

    align_tick["Time"] = align_tick["Timestamp"].apply(lambda x: dt.datetime.fromtimestamp(x).strftime("%Y%m%d %H%M%S%f").split(" ")[1][:-3])
    align_tick = align_tick.reset_index(drop=True)

    return align_tick

def daily_align_tick_tran_order_data_old(code, trading_day, l2p_tick, tick, transaction, order):
    """
    （1）对齐Tick & Transaction & Order 数据，获取每个Tick对应的Transaction/Order开始结束的Index
    (2）后面每个Tick计算时向前补齐
    """
    ALIGN_TICK_COLUMNS = ALIGN_STOCK_TICK_COLUMNS

    morning_start_timestamp = generate_timestamp(trading_day, "093015")
    morning_end_timestamp = generate_timestamp(trading_day, "112959")
    afternoon_start_timestamp = generate_timestamp(trading_day, "130015")
    afternoon_end_timestamp = generate_timestamp(trading_day, "145659")

    # 为了优化效率加速，提取出Numpy矩阵，以及各个列名idx
    tick_array = l2p_tick.values
    sub_align_stock_idx = [l2p_tick.columns.get_loc(k) for k in SUB_ALIGN_STOCK_COLUMNS]
    bid_price_idx = [l2p_tick.columns.get_loc(k) for k in BID_PRICE_COLUMNS]
    ask_price_idx = [l2p_tick.columns.get_loc(k) for k in ASK_PRICE_COLUMNS]
    bid_volume_idx = [l2p_tick.columns.get_loc(k) for k in BID_VOLUME_COLUMNS]
    ask_volume_idx = [l2p_tick.columns.get_loc(k) for k in ASK_VOLUME_COLUMNS]
    bid_num_idx = [l2p_tick.columns.get_loc(k) for k in BID_NUM_COLUMNS]
    ask_num_idx = [l2p_tick.columns.get_loc(k) for k in ASK_NUM_COLUMNS]

    # 为了加速运行，提取出逐笔交易数据时间戳列表、数值矩阵
    real_tick_timestamp_array = tick["Timestamp"].values
    tran_start_idx, tran_end_idx = 0, 0
    order_start_idx, order_end_idx = 0, 0
    tran_index_list = transaction["Timestamp"].to_list()
    if code.endswith(".SZ"):
        order_index_list = order["Timestamp"].tolist()

    timestamp_tick_values_list = []
    fill_tick_timestamp_list = []
    for i in range(tick_array.shape[0]):

        # 当前Tick信息
        base_cols = tick_array[i, sub_align_stock_idx].tolist()
        bid_price_col = tick_array[i, bid_price_idx].reshape(len(BID_PRICE_COLUMNS),).astype(np.float64)
        ask_price_col = tick_array[i, ask_price_idx].reshape(len(ASK_PRICE_COLUMNS),).astype(np.float64)
        bid_volume_col = tick_array[i, bid_volume_idx].reshape(len(BID_VOLUME_COLUMNS),).astype(np.float64)
        ask_volume_col = tick_array[i, ask_volume_idx].reshape(len(ASK_VOLUME_COLUMNS),).astype(np.float64)
        bid_num_col = tick_array[i, bid_num_idx].reshape(len(BID_NUM_COLUMNS),).astype(np.int)
        ask_num_col = tick_array[i, ask_num_idx].reshape(len(ASK_NUM_COLUMNS),).astype(np.int)

        tick_timestamp = base_cols[1]

        # 确定每个Tick逐笔成交 & 逐笔委托数据的Start & End Index
        # tran_start_idx = tran_end_idx
        while tran_end_idx < len(tran_index_list):
            if tran_index_list[tran_end_idx] < tick_timestamp:
                tran_end_idx += 1
            else:
                break

        before_real_tick_timestamp_array = real_tick_timestamp_array[real_tick_timestamp_array < tick_timestamp]
        if len(before_real_tick_timestamp_array) != 0:
            mock_tick_start_timestamp = before_real_tick_timestamp_array[-1]
            tran_slice = [tt for tt in tran_index_list if mock_tick_start_timestamp <= tt < tick_timestamp]
            if len(tran_slice) > 0:
                mock_tick_start_timestamp = tran_slice[0]
                mock_tran_start_idx = tran_index_list.index(mock_tick_start_timestamp)
            else:
                mock_tran_start_idx = tran_end_idx
        else:
            mock_tran_start_idx = tran_end_idx

        if code.endswith(".SZ"):
            order_start_idx = order_end_idx
            while order_end_idx < len(order_index_list):
                if order_index_list[order_end_idx] < tick_timestamp:
                    order_end_idx += 1
                else:
                    break

        timestamp_tick_values = base_cols + [bid_price_col, ask_price_col, bid_volume_col, ask_volume_col, bid_num_col, ask_num_col,
                                             mock_tran_start_idx, tran_end_idx, order_start_idx, order_end_idx] + [0]

        # 把当前Tick数据加入到align_daily_stock_tick_df中
        timestamp_tick_values_list.append(timestamp_tick_values)

    # 汇总已有数据
    align_tick = pd.DataFrame(timestamp_tick_values_list, columns=ALIGN_TICK_COLUMNS)

    # 加入093012 TICK数据
    first_tick_timestamp = generate_timestamp(trading_day, "093012")
    first_tick = align_tick[align_tick["Timestamp"] <= first_tick_timestamp]
    help_df = align_tick[align_tick["Timestamp"] > first_tick_timestamp].head(1)

    # 检查是否存在093012 TICK数据
    align_am_first_tick = pd.DataFrame(columns=ALIGN_TICK_COLUMNS)
    if first_tick.empty:
        align_am_first_tick = fill_none_tick_with_help_df(align_am_first_tick, help_df)
    else:
        align_am_first_tick.loc[0, ALIGN_TICK_COLUMNS] = first_tick[ALIGN_TICK_COLUMNS].tail(1).values
    align_am_first_tick.loc[0, "Timestamp"] = first_tick_timestamp

    # 处理上午数据，开始和结束均从第一个非补齐TICK开始
    am_tick_timestamp_list = align_tick[(align_tick["Timestamp"] >= morning_start_timestamp) &
                                        (align_tick["Timestamp"] <= morning_end_timestamp)]["Timestamp"].values.tolist()
    am_start_timestamp, am_end_timestamp = get_start_end_not_fill_tick(am_tick_timestamp_list, fill_tick_timestamp_list)
    if am_start_timestamp is None or am_end_timestamp is None:
        align_am_tick = pd.DataFrame(columns=ALIGN_TICK_COLUMNS)
    else:
        am_start_timestamp = max(am_start_timestamp, morning_start_timestamp)
        am_end_timestamp = min(am_end_timestamp, morning_end_timestamp)
        align_am_tick = align_tick[(align_tick["Timestamp"] >= am_start_timestamp) & (align_tick["Timestamp"] <= am_end_timestamp)]

    # 处理下午时刻数据，开始和结束均从第一个非补齐TICK开始
    pm_tick_timestamp_list = align_tick[(align_tick["Timestamp"] >= afternoon_start_timestamp) &
                                        (align_tick["Timestamp"] <= afternoon_end_timestamp)]["Timestamp"].values.tolist()
    pm_start_timestamp, pm_end_timestamp = get_start_end_not_fill_tick(pm_tick_timestamp_list, fill_tick_timestamp_list)
    if pm_start_timestamp is None or pm_end_timestamp is None:
        align_pm_tick = pd.DataFrame(columns=ALIGN_TICK_COLUMNS)
    else:
        pm_start_timestamp = max(pm_start_timestamp, afternoon_start_timestamp)
        pm_end_timestamp = min(pm_end_timestamp, afternoon_end_timestamp)
        align_pm_tick = align_tick[(align_tick["Timestamp"] >= pm_start_timestamp) & (align_tick["Timestamp"] <= pm_end_timestamp)]

    # 合并上下午数据
    align_tick = pd.concat([align_am_first_tick, align_am_tick, align_pm_tick], axis=0)

    align_tick["Time"] = align_tick["Timestamp"].apply(lambda x: dt.datetime.fromtimestamp(x).strftime("%Y%m%d %H%M%S%f").split(" ")[1][:-3])
    align_tick = align_tick.reset_index(drop=True)

    return align_tick
