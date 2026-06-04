from DataInterface.Config import SUB_ALIGN_STOCK_COLUMNS, BID_PRICE_COLUMNS, ASK_PRICE_COLUMNS, BID_VOLUME_COLUMNS, ASK_VOLUME_COLUMNS, BID_NUM_COLUMNS, ASK_NUM_COLUMNS
from DataInterface.Config import ALIGN_STOCK_TICK_COLUMNS, ALIGN_INDEX_TICK_COLUMNS, ALIGN_CBOND_TICK_COLUMNS, ALIGN_FUND_TICK_COLUMNS
from DataInterface.Config import SUB_ALIGN_FUTURE_COLUMNS, FUTURE_BID_PRICE_COLUMNS, FUTURE_ASK_PRICE_COLUMNS, FUTURE_BID_VOLUME_COLUMNS, FUTURE_ASK_VOLUME_COLUMNS
from DataInterface.Config import ALIGN_FUTURE_TICK_COLUMNS
from DataMonitor.Monitor import TickMonitor

import copy
import numpy as np
import pandas as pd
import datetime as dt


def tick_data_zero_price_filter(tick: pd.DataFrame):
    # 本函数将连续竞价期间OpenPrice, HighPrice和LowPrice为0的条目删掉
    filter_tick = tick[((True^tick["OpenPx"].isin([0])) & (True^tick["HighPx"].isin([0])) & (True^tick["LowPx"].isin([0])))].copy()
    return filter_tick

def tick_data_circuit_filter(cbond_tick: pd.DataFrame):
    # 本函数将可转债盘中临停时间段内TICK行情删掉，判断条件为: 十档买卖盘口价格均为0
    price_columns = ["Buy1Price", "Buy2Price", "Buy3Price", "Buy4Price", "Buy5Price", "Buy6Price", "Buy7Price", "Buy8Price", "Buy9Price", "Buy10Price",
                     "Sell1Price", "Sell2Price", "Sell3Price", "Sell4Price", "Sell5Price", "Sell6Price", "Sell7Price", "Sell8Price", "Sell9Price", "Sell10Price"]
    cbond_filter_tick = cbond_tick[~(cbond_tick[price_columns].sum(axis=1) == 0)].reset_index(drop=True).copy()
    return cbond_filter_tick

def daily_clean_GEM_stock(tick: pd.DataFrame, transaction: pd.DataFrame):
    tick = copy.deepcopy(tick)
    transaction = copy.deepcopy(transaction)

    if tick.empty or transaction.empty:
        return tick, TickMonitor.EMPTY

    tick_amount = tick["Amount"].tolist()
    tick_time = tick["Timestamp"].tolist()
    trans_amount = transaction["Amount"]
    trans_amount.index = transaction["Timestamp"]

    amount_diff_threshold = 10       # amount difference less than 10 yuan
    postpone_times_threshold = 20    # abnormal appears 20 times, then postpone

    wrong_counter = 0
    for i in range(1, len(tick) - 1):
        if wrong_counter > postpone_times_threshold:
            break
        amount_diff = trans_amount.loc[tick_time[i-1]: tick_time[i]].sum() - tick_amount[i]
        if np.abs(amount_diff) > amount_diff_threshold:
            wrong_counter += 1
    if wrong_counter == 0:
        return tick, TickMonitor.NORMAL
    elif wrong_counter <= postpone_times_threshold:
        return tick, TickMonitor.MISSING
    else:
        tick["Timestamp"] = tick["Timestamp"] - 3   # postpone 3S
        tick["Time"] = tick["Timestamp"].apply(lambda x: dt.datetime.fromtimestamp(x).strftime("%Y%m%d %H%M%S%f").split(" ")[1][:-3])

        tick_time = tick["Timestamp"].tolist()
        tick_amount = tick["Amount"].tolist()

        wrong_counter_postpone = 0
        for i in range(1, len(tick) - 1):
            if wrong_counter_postpone > postpone_times_threshold:
                break
            amount_diff = trans_amount.loc[tick_time[i-1]: tick_time[i]].sum() - tick_amount[i]
            if np.abs(amount_diff) > amount_diff_threshold:
                wrong_counter_postpone += 1
        if wrong_counter_postpone == 0:
            return tick, TickMonitor.POSTPONE_NORMAL
        elif wrong_counter_postpone <= postpone_times_threshold:
            return tick, TickMonitor.POSTPONE_MISSING
        else:
            return tick, TickMonitor.UNKOWN

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

def fill_none_tick_with_help_df_old(fill_df, help_df):
    # Code, Date, MinPrice, MaxPrice, PreviousClose字段一天中保持不变，直接复制
    # fill_df: 传入一个空DataFrame，列名给定
    fill_df.loc[0, :] = copy.deepcopy(help_df.values)
    fill_nan_columns = ["OpenPrice", "HighPrice", "LowPrice", "LastPrice", "AvgBidPrice", "AvgOfferPrice"]
    fill_zero_columns = ["Volume", "Amount", "TotalVolume", "TotalAmount", "NumTrades", "BidQty", "OfferQty"]
    fill_none_columns = ["BidPrice", "AskPrice", "BidVolume", "AskVolume", "BidNum", "AskNum", "Transactions"]
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

def daily_align_tick_tran_order_data(code, trading_day, tick, transaction, order):
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
    tick_array = tick.values
    sub_align_stock_idx = [tick.columns.get_loc(k) for k in SUB_ALIGN_STOCK_COLUMNS]
    bid_price_idx = [tick.columns.get_loc(k) for k in BID_PRICE_COLUMNS]
    ask_price_idx = [tick.columns.get_loc(k) for k in ASK_PRICE_COLUMNS]
    bid_volume_idx = [tick.columns.get_loc(k) for k in BID_VOLUME_COLUMNS]
    ask_volume_idx = [tick.columns.get_loc(k) for k in ASK_VOLUME_COLUMNS]
    bid_num_idx = [tick.columns.get_loc(k) for k in BID_NUM_COLUMNS]
    ask_num_idx = [tick.columns.get_loc(k) for k in ASK_NUM_COLUMNS]

    mock_timestamp_idx = ALIGN_TICK_COLUMNS.index("Timestamp")
    mock_volume_idx = ALIGN_TICK_COLUMNS.index("Volume")
    mock_amount_idx = ALIGN_TICK_COLUMNS.index("Amount")
    mock_num_trades_idx = ALIGN_TICK_COLUMNS.index("NumTrades")
    mock_bid_qty_idx = ALIGN_STOCK_TICK_COLUMNS.index("BidQty")
    mock_offer_qty_idx = ALIGN_STOCK_TICK_COLUMNS.index("OfferQty")
    mock_is_mock_idx = ALIGN_TICK_COLUMNS.index("IsMock")
    mock_ts_index_idx = ALIGN_TICK_COLUMNS.index("TSIndex")
    mock_te_index_idx = ALIGN_TICK_COLUMNS.index("TEIndex")
    mock_os_index_idx = ALIGN_TICK_COLUMNS.index("OSIndex")
    mock_oe_index_idx = ALIGN_TICK_COLUMNS.index("OEIndex")

    # 为了加速运行，提取出逐笔交易数据时间戳列表、数值矩阵
    tran_start_idx, tran_end_idx = 0, 0
    order_start_idx, order_end_idx = 0, 0
    tran_index_list = transaction["Timestamp"].to_list()
    if code.endswith(".SZ"):
        order_index_list = order["Timestamp"].tolist()

    timestamp_tick_values_list = []
    fill_tick_timestamp_list = []
    for i in range(tick_array.shape[0]):
        if len(timestamp_tick_values_list) > 0:
            last_tick_timestamp = copy.deepcopy(timestamp_tick_values_list[-1][mock_timestamp_idx])
        else:
            last_tick_timestamp = generate_timestamp(trading_day, "000000")

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
        tran_start_idx = tran_end_idx
        while tran_end_idx < len(tran_index_list):
            if tran_index_list[tran_end_idx] < tick_timestamp:
                tran_end_idx += 1
            else:
                break

        if code.endswith(".SZ"):
            order_start_idx = order_end_idx
            while order_end_idx < len(order_index_list):
                if order_index_list[order_end_idx] < tick_timestamp:
                    order_end_idx += 1
                else:
                    break

        timestamp_tick_values = base_cols + [bid_price_col, ask_price_col, bid_volume_col, ask_volume_col, bid_num_col, ask_num_col,
                                             tran_start_idx, tran_end_idx, order_start_idx, order_end_idx] + [0]

        # 补齐缺失tick，并加入align_daily_stock_tick_df中
        # 如果缺失数据数据时间戳大于10min，则不补TICK：主要是考虑到实盘中补齐这些缺失TICK数据并计算因子时间太长
        # 补齐10分钟缺失数据、计算因子和出信号，大约耗时 1S
        if 6 <= (tick_timestamp - last_tick_timestamp) <= 600:
            last_tick_timestamp_loop = last_tick_timestamp
            count = 1
            while 6 <= (tick_timestamp - last_tick_timestamp_loop) <= 600:
                fill_tick_timestamp = last_tick_timestamp_loop + 3
                fill_tick_timestamp_list.append(fill_tick_timestamp)
                last_tick_timestamp_loop = fill_tick_timestamp
                count += 1
                # i == 0 时，tick_timestamp - last_tick_timestamp > 3000，不需要填充
                fill_tick_values = copy.deepcopy(timestamp_tick_values_list[-1])

                fill_tick_values[mock_ts_index_idx] = fill_tick_values[mock_te_index_idx]
                fill_tick_values[mock_os_index_idx] = fill_tick_values[mock_oe_index_idx]
                fill_tick_values[mock_timestamp_idx] = fill_tick_timestamp
                fill_tick_values[mock_volume_idx] = 0
                fill_tick_values[mock_amount_idx] = 0
                fill_tick_values[mock_num_trades_idx] = 0
                fill_tick_values[mock_bid_qty_idx] = 0
                fill_tick_values[mock_offer_qty_idx] = 0
                fill_tick_values[mock_is_mock_idx] = 1

                timestamp_tick_values_list.append(fill_tick_values)

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

def daily_align_tick_transaction(trading_day, tick, transaction):
    """
    对齐某个交易日的股票/可转债/ETF Tick和Transaction：
    (1) 第一个Tick：Transaction数据为第一个TICK 3S内的Transaction数据
    (2）后面每个Tick计算时向前补齐
    """
    ALIGN_TICK_COLUMNS = ALIGN_STOCK_TICK_COLUMNS
    morning_start_timestamp = generate_timestamp(trading_day, "093015")
    morning_end_timestamp = generate_timestamp(trading_day, "112959")
    afternoon_start_timestamp = generate_timestamp(trading_day, "130015")
    afternoon_end_timestamp = generate_timestamp(trading_day, "145659")

    # 为了优化效率加速，提取出Numpy矩阵，以及各个列名idx
    tick_array = tick.values
    sub_align_stock_idx = [tick.columns.get_loc(k) for k in SUB_ALIGN_STOCK_COLUMNS]
    bid_price_idx = [tick.columns.get_loc(k) for k in BID_PRICE_COLUMNS]
    ask_price_idx = [tick.columns.get_loc(k) for k in ASK_PRICE_COLUMNS]
    bid_volume_idx = [tick.columns.get_loc(k) for k in BID_VOLUME_COLUMNS]
    ask_volume_idx = [tick.columns.get_loc(k) for k in ASK_VOLUME_COLUMNS]
    bid_num_idx = [tick.columns.get_loc(k) for k in BID_NUM_COLUMNS]
    ask_num_idx = [tick.columns.get_loc(k) for k in ASK_NUM_COLUMNS]

    mock_timestamp_idx = ALIGN_TICK_COLUMNS.index("Timestamp")
    mock_volume_idx = ALIGN_TICK_COLUMNS.index("Volume")
    mock_amount_idx = ALIGN_TICK_COLUMNS.index("Amount")
    mock_num_trades_idx = ALIGN_TICK_COLUMNS.index("NumTrades")
    mock_bid_qty_idx = ALIGN_STOCK_TICK_COLUMNS.index("BidQty")
    mock_offer_qty_idx = ALIGN_STOCK_TICK_COLUMNS.index("OfferQty")
    mock_is_mock_idx = ALIGN_TICK_COLUMNS.index("IsMock")

    # 为了加速运行，提取出逐笔交易数据时间戳列表、数值矩阵
    transaction_index_list = transaction["Timestamp"].to_list()
    transaction_array = transaction.values.astype(np.float64)
    left_idx, right_idx = 0, 1

    timestamp_tick_values_list = []
    fill_tick_timestamp_list = []
    for i in range(tick_array.shape[0]):
        if len(timestamp_tick_values_list) > 0:
            last_tick_timestamp = copy.deepcopy(timestamp_tick_values_list[-1][1])
        else:
            last_tick_timestamp = generate_timestamp(trading_day, "000000")

        # 当前Tick信息
        base_cols = tick_array[i, sub_align_stock_idx].tolist()
        bid_price_col = tick_array[i, bid_price_idx].reshape(len(BID_PRICE_COLUMNS),).astype(np.float64)
        ask_price_col = tick_array[i, ask_price_idx].reshape(len(ASK_PRICE_COLUMNS),).astype(np.float64)
        bid_volume_col = tick_array[i, bid_volume_idx].reshape(len(BID_VOLUME_COLUMNS),).astype(np.float64)
        ask_volume_col = tick_array[i, ask_volume_idx].reshape(len(ASK_VOLUME_COLUMNS),).astype(np.float64)
        bid_num_col = tick_array[i, bid_num_idx].reshape(len(BID_NUM_COLUMNS),).astype(np.int)
        ask_num_col = tick_array[i, ask_num_idx].reshape(len(ASK_NUM_COLUMNS),).astype(np.int)

        tick_timestamp = base_cols[1]

        # 抽取这个Tick之间的逐笔成交信息
        left_idx_updated = False
        right_bc_reached = True
        start_idx = right_idx - 1
        for idx in range(start_idx, len(transaction_index_list)):
            if transaction_index_list[idx] >= last_tick_timestamp and (not left_idx_updated):  # 左闭
                # 如果第一个找到的比上一个Tick时间戳大的idx，已经超出当前Tick的时间戳，则说明该Tick间没有交易
                if transaction_index_list[idx] >= tick_timestamp:
                    break
                left_idx = idx
                left_idx_updated = True
        if left_idx_updated:
            for idx in range(left_idx, len(transaction_index_list)):
                right_idx = idx
                # 右开
                if transaction_index_list[right_idx] >= tick_timestamp:
                    right_bc_reached = False
                    break

        if left_idx_updated:  # index 已更新，则取更新后的时间段
            if right_bc_reached:
                transactions_col = transaction_array[left_idx:None, :]
            else:
                transactions_col = transaction_array[left_idx:right_idx, :]
        else:  # index 未更新，则说明这段时间没有数值
            transactions_col = None  # np.ones([0, 7]).astype(np.float64)

        timestamp_tick_values = base_cols + [bid_price_col, ask_price_col, bid_volume_col, ask_volume_col,
                                             bid_num_col, ask_num_col, transactions_col] + [0]

        # 补齐缺失tick，并加入align_daily_stock_tick_df中
        # 如果缺失数据数据时间戳大于10min，则不补TICK：主要是考虑到实盘中补齐这些缺失TICK数据并计算因子时间太长
        # 补齐10分钟缺失数据、计算因子和出信号，大约耗时 1S
        if 6 <= (tick_timestamp - last_tick_timestamp) <= 600:
            last_tick_timestamp_loop = last_tick_timestamp
            count = 1
            while 6 <= (tick_timestamp - last_tick_timestamp_loop) <= 600:
                fill_tick_timestamp = last_tick_timestamp_loop + 3
                fill_tick_timestamp_list.append(fill_tick_timestamp)
                last_tick_timestamp_loop = fill_tick_timestamp
                count += 1
                # i == 0 时，tick_timestamp - last_tick_timestamp > 3000，不需要填充
                fill_tick_values = copy.deepcopy(timestamp_tick_values_list[-1])

                fill_tick_values[mock_timestamp_idx] = fill_tick_timestamp
                fill_tick_values[mock_volume_idx] = 0
                fill_tick_values[mock_amount_idx] = 0
                fill_tick_values[mock_num_trades_idx] = 0
                fill_tick_values[mock_bid_qty_idx] = 0
                fill_tick_values[mock_offer_qty_idx] = 0
                fill_tick_values[mock_is_mock_idx] = 1

                timestamp_tick_values_list.append(fill_tick_values)

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
        align_am_first_tick = fill_none_tick_with_help_df_old(align_am_first_tick, help_df)
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

def daily_align_index_tick_data(trading_day, tick):
    """
    trading_day: 交易日
    daily_index_tick_df: 一天指数TICK行情，返回清洗后TICK行情
    清洗逻辑：截取TICK数据
    """
    tick_array = tick.values

    mock_timestamp_idx = ALIGN_INDEX_TICK_COLUMNS.index("Timestamp")
    mock_volume_idx = ALIGN_INDEX_TICK_COLUMNS.index("Volume")
    mock_amount_idx = ALIGN_INDEX_TICK_COLUMNS.index("Amount")
    mock_is_mock_idx = ALIGN_INDEX_TICK_COLUMNS.index("IsMock")

    timestamp_tick_values_list = []
    fill_tick_timestamp_list = []

    for i in range(tick_array.shape[0]):
        if len(timestamp_tick_values_list) > 0:
            last_tick_timestamp = copy.deepcopy(timestamp_tick_values_list[-1][1])
        else:
            last_tick_timestamp = generate_timestamp(trading_day, "000000")

        base_cols = tick_array[i, :].tolist()
        tick_timestamp = base_cols[1]
        timestamp_tick_values = base_cols + [0]

        # 补齐缺失tick，并加入align_daily_index_tick_df中, 大盘指数行情5S一个TICK
        if 10 <= (tick_timestamp - last_tick_timestamp) <= 600:
            last_tick_timestamp_loop = last_tick_timestamp
            count = 1
            while 10 <= (tick_timestamp - last_tick_timestamp_loop) <= 600:
                fill_tick_timestamp = last_tick_timestamp_loop + 5
                fill_tick_timestamp_list.append(fill_tick_timestamp)
                last_tick_timestamp_loop = fill_tick_timestamp
                count += 1
                # i == 0 时，tick_timestamp - last_tick_timestamp > 3000，不需要填充
                fill_tick_values = copy.deepcopy(timestamp_tick_values_list[-1])

                fill_tick_values[mock_timestamp_idx] = fill_tick_timestamp
                fill_tick_values[mock_volume_idx] = 0
                fill_tick_values[mock_amount_idx] = 0
                fill_tick_values[mock_is_mock_idx] = 1

                timestamp_tick_values_list.append(fill_tick_values)

        # 把当前Tick数据加入到align_daily_index_tick_df中
        timestamp_tick_values_list.append(timestamp_tick_values)

    # 汇总已有数据
    align_tick = pd.DataFrame(timestamp_tick_values_list, columns=ALIGN_INDEX_TICK_COLUMNS)

    # 加入093012 TICK数据
    first_tick_timestamp = generate_timestamp(trading_day, "093012")
    first_tick = align_tick[align_tick["Timestamp"] <= first_tick_timestamp]
    help_df = align_tick[align_tick["Timestamp"] > first_tick_timestamp].head(1)

    # 检查是否存在093012 TICK数据
    align_am_first_tick = pd.DataFrame(columns=ALIGN_INDEX_TICK_COLUMNS)
    if first_tick.empty:
        # Code, Date, MinPrice, MaxPrice, PreviousClose 字段一天中保持不变，直接复制
        align_am_first_tick.loc[0, :] = copy.deepcopy(help_df.values)
        fill_nan_columns = ["OpenPrice", "HighPrice", "LowPrice", "LastPrice"]
        align_am_first_tick.loc[0, fill_nan_columns] = [np.nan for _ in range(len(fill_nan_columns))]
        fill_zero_columns = ["Volume", "Amount", "TotalVolume", "TotalAmount"]
        align_am_first_tick.loc[0, fill_zero_columns] = [np.nan for _ in range(len(fill_zero_columns))]
        align_am_first_tick.loc[0, "IsMock"] = 1
    else:
        align_am_first_tick.loc[0, :] = first_tick.tail(1).values
    align_am_first_tick.loc[0, "Timestamp"] = first_tick_timestamp

    # 获取一天中关键Timestamp
    morning_start_timestamp, morning_end_timestamp, afternoon_start_timestamp, afternoon_end_timestamp = generate_daily_key_timestamp(trading_day)

    # 处理上午数据，开始和结束均从第一个非补齐TICK开始
    am_tick_timestamp_list = align_tick[(align_tick["Timestamp"] >= morning_start_timestamp) &
                                        (align_tick["Timestamp"] <= morning_end_timestamp)]["Timestamp"].values.tolist()
    am_start_timestamp, am_end_timestamp = get_start_end_not_fill_tick(am_tick_timestamp_list, fill_tick_timestamp_list)
    if am_start_timestamp is None or am_end_timestamp is None:
        align_am_tick = pd.DataFrame(columns=ALIGN_INDEX_TICK_COLUMNS)
    else:
        am_start_timestamp = max(am_start_timestamp, morning_start_timestamp)
        am_end_timestamp = min(am_end_timestamp, morning_end_timestamp)
        align_am_tick = align_tick[(align_tick["Timestamp"] >= am_start_timestamp) & (align_tick["Timestamp"] <= am_end_timestamp)]

    # 处理下午时刻数据，开始和结束均从第一个非补齐TICK开始
    pm_tick_timestamp_list = align_tick[(align_tick["Timestamp"] >= afternoon_start_timestamp) &
                        (align_tick["Timestamp"] <= afternoon_end_timestamp)]["Timestamp"].values.tolist()
    pm_start_timestamp, pm_end_timestamp = get_start_end_not_fill_tick(pm_tick_timestamp_list, fill_tick_timestamp_list)
    if pm_start_timestamp is None or pm_end_timestamp is None:
        align_pm_tick = pd.DataFrame(columns=ALIGN_INDEX_TICK_COLUMNS)
    else:
        pm_start_timestamp = max(pm_start_timestamp, afternoon_start_timestamp)
        pm_end_timestamp = min(pm_end_timestamp, afternoon_end_timestamp)
        align_pm_tick = align_tick[(align_tick["Timestamp"] >= pm_start_timestamp) & (align_tick["Timestamp"] <= pm_end_timestamp)]

    # 合并上下午数据
    align_tick = pd.concat([align_am_first_tick, align_am_tick, align_pm_tick], axis=0)

    align_tick["Time"] = align_tick["Timestamp"].apply(lambda x: dt.datetime.fromtimestamp(x).strftime("%Y%m%d %H%M%S%f").split(" ")[1][:-3])
    align_tick = align_tick.reset_index(drop=True)

    return align_tick

def daily_align_future_tick_data(trading_day, tick):
    """
    trading_day: 交易日
    daily_tick: 一天指数TICK行情，返回清洗后TICK行情
    清洗逻辑：截取TICK数据
    """
    # 为了优化效率加速，提取出Numpy矩阵，以及各个列名idx
    tick_array = tick.values
    sub_align_idx = [tick.columns.get_loc(k) for k in SUB_ALIGN_FUTURE_COLUMNS]
    bid_price_idx = [tick.columns.get_loc(k) for k in FUTURE_BID_PRICE_COLUMNS]
    ask_price_idx = [tick.columns.get_loc(k) for k in FUTURE_ASK_PRICE_COLUMNS]
    bid_volume_idx = [tick.columns.get_loc(k) for k in FUTURE_BID_VOLUME_COLUMNS]
    ask_volume_idx = [tick.columns.get_loc(k) for k in FUTURE_ASK_VOLUME_COLUMNS]

    mock_timestamp_idx = ALIGN_FUTURE_TICK_COLUMNS.index("Timestamp")
    mock_volume_idx = ALIGN_FUTURE_TICK_COLUMNS.index("Volume")
    mock_amount_idx = ALIGN_FUTURE_TICK_COLUMNS.index("Amount")
    mock_is_mock_idx = ALIGN_FUTURE_TICK_COLUMNS.index("IsMock")

    timestamp_tick_values_list = []
    fill_tick_timestamp_list = []

    for i in range(tick_array.shape[0]):
        if len(timestamp_tick_values_list) > 0:
            last_tick_timestamp = copy.deepcopy(timestamp_tick_values_list[-1][1])
        else:
            last_tick_timestamp = generate_timestamp(trading_day, "000000")

        # 当前Tick信息
        base_cols = tick_array[i, sub_align_idx].tolist()
        bid_price_col = tick_array[i, bid_price_idx].reshape(len(FUTURE_BID_PRICE_COLUMNS),).astype(np.float64)
        ask_price_col = tick_array[i, ask_price_idx].reshape(len(FUTURE_ASK_PRICE_COLUMNS),).astype(np.float64)
        bid_volume_col = tick_array[i, bid_volume_idx].reshape(len(FUTURE_BID_VOLUME_COLUMNS),).astype(np.float64)
        ask_volume_col = tick_array[i, ask_volume_idx].reshape(len(FUTURE_ASK_VOLUME_COLUMNS),).astype(np.float64)

        tick_timestamp = base_cols[1]
        timestamp_tick_values = base_cols + [bid_price_col, ask_price_col, bid_volume_col, ask_volume_col] + [0]

        # 补齐缺失tick，并加入align_daily_future_tick_df中, 期货行情数据0.5S一个TICK
        if 1 <= (tick_timestamp - last_tick_timestamp) <= 60:
            last_tick_timestamp_loop = last_tick_timestamp
            count = 1
            while 1 <= (tick_timestamp - last_tick_timestamp_loop) <= 60:
                fill_tick_timestamp = last_tick_timestamp_loop + 0.5
                fill_tick_timestamp_list.append(fill_tick_timestamp)
                last_tick_timestamp_loop = fill_tick_timestamp
                count += 1
                # i == 0 时，tick_timestamp - last_tick_timestamp > 3000，不需要填充
                fill_tick_values = copy.deepcopy(timestamp_tick_values_list[-1])

                fill_tick_values[mock_timestamp_idx] = fill_tick_timestamp
                fill_tick_values[mock_volume_idx] = 0
                fill_tick_values[mock_amount_idx] = 0
                fill_tick_values[mock_is_mock_idx] = 1

                timestamp_tick_values_list.append(fill_tick_values)

        # 把当前Tick数据加入到align_daily_index_tick_df中
        timestamp_tick_values_list.append(timestamp_tick_values)

    # 汇总已有数据
    align_tick = pd.DataFrame(timestamp_tick_values_list, columns=ALIGN_FUTURE_TICK_COLUMNS)

    # 加入093012 TICK数据
    first_tick_timestamp = generate_timestamp(trading_day, "093012")
    first_tick = align_tick[align_tick["Timestamp"] <= first_tick_timestamp]
    help_df = align_tick[align_tick["Timestamp"] > first_tick_timestamp].head(1)

    # 检查是否存在093012 TICK数据
    align_am_first_tick = pd.DataFrame(columns=ALIGN_FUTURE_TICK_COLUMNS)
    if first_tick.empty:
        ### Code, Date, MinPrice, MaxPrice, PreviousClose, PreSettlePrice 字段一天中保持不变，直接复制
        align_am_first_tick.loc[0, :] = copy.deepcopy(help_df.values)
        fill_nan_columns = ["OpenPrice", "HighPrice", "LowPrice", "LastPrice"]
        align_am_first_tick.loc[0, fill_nan_columns] = [np.nan for _ in range(len(fill_nan_columns))]
        fill_zero_columns = ["Volume", "Amount", "TotalVolume", "TotalAmount", "OpenInterest"]
        align_am_first_tick.loc[0, fill_zero_columns] = [np.nan for _ in range(len(fill_zero_columns))]
        fill_none_columns = ["BidPrice", "AskPrice", "BidVolume", "AskVolume"]
        align_am_first_tick.loc[0, fill_none_columns] = [None for _ in range(len(fill_none_columns))]
        align_am_first_tick.loc[0, "IsMock"] = 1
    else:
        align_am_first_tick.loc[0, ALIGN_FUTURE_TICK_COLUMNS] = first_tick[ALIGN_FUTURE_TICK_COLUMNS].tail(1).values
    align_am_first_tick.loc[0, "Timestamp"] = first_tick_timestamp

    # 获取一天中关键Timestamp
    morning_start_timestamp = generate_timestamp(trading_day, "093015")
    morning_end_timestamp = generate_timestamp(trading_day, "112959")
    afternoon_start_timestamp = generate_timestamp(trading_day, "130015")
    afternoon_end_timestamp = generate_timestamp(trading_day, "145659")

    # 处理上午数据，开始和结束均从第一个非补齐TICK开始
    am_tick_timestamp_list = align_tick[(align_tick["Timestamp"] >= morning_start_timestamp) &
                                        (align_tick["Timestamp"] <= morning_end_timestamp)]["Timestamp"].values.tolist()
    am_start_timestamp, am_end_timestamp = get_start_end_not_fill_tick(am_tick_timestamp_list, fill_tick_timestamp_list)
    if am_start_timestamp is None or am_end_timestamp is None:
        align_am_tick = pd.DataFrame(columns=ALIGN_FUTURE_TICK_COLUMNS)
    else:
        am_start_timestamp = max(am_start_timestamp, morning_start_timestamp)
        am_end_timestamp = min(am_end_timestamp, morning_end_timestamp)
        align_am_tick = align_tick[(align_tick["Timestamp"] >= am_start_timestamp) & (align_tick["Timestamp"] <= am_end_timestamp)]

    # 处理下午时刻数据，开始和结束均从第一个非补齐TICK开始
    pm_tick_timestamp_list = align_tick[(align_tick["Timestamp"] >= afternoon_start_timestamp) &
                                        (align_tick["Timestamp"] <= afternoon_end_timestamp)]["Timestamp"].values.tolist()
    pm_start_timestamp, pm_end_timestamp = get_start_end_not_fill_tick(pm_tick_timestamp_list, fill_tick_timestamp_list)
    if pm_start_timestamp is None or pm_end_timestamp is None:
        align_pm_tick = pd.DataFrame(columns=ALIGN_FUTURE_TICK_COLUMNS)
    else:
        pm_start_timestamp = max(pm_start_timestamp, afternoon_start_timestamp)
        pm_end_timestamp = min(pm_end_timestamp, afternoon_end_timestamp)
        align_pm_tick = align_tick[(align_tick["Timestamp"] >= pm_start_timestamp) & (align_tick["Timestamp"] <= pm_end_timestamp)]

    # 合并上下午数据
    align_tick = pd.concat([align_am_first_tick, align_am_tick, align_pm_tick], axis=0)

    align_tick["Time"] = align_tick["Timestamp"].apply(lambda x: dt.datetime.fromtimestamp(x).strftime("%Y%m%d %H%M%S%f").split(" ")[1][:-3])
    align_tick = align_tick.reset_index(drop=True)

    return align_tick

def minute_data_transform(df, operation):
    """
    :param item: 变量名
    :param df: index为时间的DataFrame
    :param operation: ["", ""], 可取："", "drop", "merge"
    """
    df_index = list(df.index)
    if len(df_index) <= 1:
        return df

    cols = [col for col in df.columns if col in ["Volume", "Amount", "NumTrades"]]

    each_day_index_list = []
    is_open_call_list = []
    is_close_call_list = []
    trade_date_list = sorted(list(set(df["Date"].tolist())))

    invalid_index_list = []
    for date in trade_date_list:
        sub_df = df[df["Date"] == date]
        start_timestamp = dt.datetime.strptime("{} 09:25:00".format(date), "%Y%m%d %H:%M:%S").timestamp()
        end_timestamp = dt.datetime.strptime("{} 15:00:00".format(date), "%Y%m%d %H:%M:%S").timestamp()
        invalid_sub_df = sub_df[(sub_df["Timestamp"] < start_timestamp) | (sub_df["Timestamp"] > end_timestamp)]
        if not invalid_sub_df.empty:
            invalid_index_list.extend(invalid_sub_df.index.tolist())
    if len(invalid_index_list) > 0:
        for drop_index in invalid_index_list:
            df.drop(drop_index, axis=0, inplace=True)

    for date in trade_date_list:
        sub_df = df[df["Date"] == date]
        is_open_call = False
        is_close_call = False
        one_day_index = []
        for index in sub_df.index:
            one_day_index.append(index)
            if index.hour == 9 and index.minute == 25:
                is_open_call = True
            if index.hour == 15 and index.minute == 00:
                is_close_call = True

        each_day_index_list.append(one_day_index)
        is_open_call_list.append(is_open_call)
        is_close_call_list.append(is_close_call)

    for each_day_index, is_open_call, is_close_call in zip(each_day_index_list, is_open_call_list, is_close_call_list):

        open_process_num = 0   # 集合竞价drop或merge后分钟线减少的根数

        if is_close_call:
            if operation[0].startswith("drop"):
                drop_num = operation[0][len("drop"):]
                drop_num = 1 if drop_num == "" else int(drop_num)
                if len(each_day_index)  > drop_num:   # 保证有足够的分钟线可以drop
                    drop_index_list = [each_day_index[i] for i in range(drop_num)]
                    for drop_index in drop_index_list:
                        df.drop(drop_index, axis=0, inplace=True)

                open_process_num = max(open_process_num, drop_num)

            elif operation[0].startswith("merge"):
                merge_num = operation[0][len("merge"):]
                merge_num = 1 if merge_num == "" else int(merge_num)
                if len(each_day_index) > merge_num:   # 保证有足够的分钟线可以merge
                    merge_index_list = [each_day_index[i] for i in range(merge_num)]
                    result_index = each_day_index[merge_num]
                    for merge_index in merge_index_list:
                        df.loc[result_index, cols] = df.loc[merge_index, cols].values + df.loc[result_index, cols].values
                        df.loc[result_index,["OpenPrice"]] = df.loc[merge_index_list[0],["OpenPrice"]].values
                        df.loc[result_index,["LowPrice"]] = np.minimum(df.loc[merge_index,["LowPrice"]].values,
                                                                       df.loc[result_index,["LowPrice"]].values)
                        df.drop(merge_index, axis=0, inplace=True)

                open_process_num = max(open_process_num, merge_num)

        if is_close_call:
            if operation[1].startswith("drop"):
                drop_num = operation[1][len("drop"):]
                drop_num = 1 if drop_num == "" else int(drop_num)
                if len(each_day_index) > drop_num + open_process_num:   # 早盘处理后保证尾盘有足够的分钟线可以drop
                    drop_index_list = [each_day_index[-(i + 1)] for i in range(drop_num)]
                    for drop_index in drop_index_list:
                        df.drop(drop_index, axis=0, inplace=True)
            elif operation[1].startswith("merge"):
                merge_num = operation[1][len("merge"):]
                merge_num = 1 if merge_num == "" else int(merge_num)
                if len(each_day_index) > merge_num + open_process_num:    # 早盘处理后保证尾盘有足够的分钟线可以merge
                    merge_index_list = [each_day_index[-(i + 1)] for i in range(merge_num)]
                    result_index = each_day_index[-(merge_num + 1)]
                    for merge_index in merge_index_list:
                        df.loc[result_index, cols] = df.loc[merge_index, cols].values + df.loc[result_index, cols].values
                        df.loc[result_index,["ClosePrice"]] = df.loc[merge_index,["ClosePrice"]].values
                        df.loc[result_index,["LowPrice"]] = np.minimum(df.loc[merge_index,["LowPrice"]].values,
                                                                       df.loc[result_index,["LowPrice"]].values)
                        df.drop(merge_index, axis=0, inplace=True)

    return df

