import numpy as np
import pandas as pd
import datetime as dt
import copy
from HFDataLoader.Config import SUB_ALIGN_STOCK_COLUMNS, BID_PRICE_COLUMNS, ASK_PRICE_COLUMNS, BID_VOLUME_COLUMNS, ASK_VOLUME_COLUMNS
from HFDataLoader.Config import ALIGN_STOCK_COLUMNS, ALIGN_INDEX_COLUMNS, ALIGN_CBOND_COLUMNS, ALIGN_FUND_COLUMNS
from HFDataLoader.Config import SUB_ALIGN_FUTURE_COLUMNS, FUTURE_BID_PRICE_COLUMNS, FUTURE_ASK_PRICE_COLUMNS, FUTURE_BID_VOLUME_COLUMNS, FUTURE_ASK_VOLUME_COLUMNS
from HFDataLoader.Config import ALIGN_FUTURE_COLUMNS
from HFDataLoader.Config import TickMonitor

def tickdata_OHL_filter(stock_tick_df):
    # 本函数将连续竞价期间OpenPrice, HighPrice和LowPrice为0的条目删掉
    stock_filter_df = stock_tick_df[((True ^ stock_tick_df['OpenPx'].isin([0])) & (True ^ stock_tick_df['HighPx'].isin([0])) &
                                    (True ^ stock_tick_df['LowPx'].isin([0])))].copy()
    return stock_filter_df

def tickdata_circuit_filter(cbond_tick_df):
    # 本函数将可转债盘中熔断时间段内TICK行情删掉，判断条件为: 十档买卖盘口价格均为0
    PRICE_COLUMNS = ["Buy1Price", "Buy2Price", "Buy3Price", "Buy4Price", "Buy5Price", "Buy6Price", "Buy7Price",
                     "Buy8Price", "Buy9Price", "Buy10Price",
                     "Sell1Price", "Sell2Price", "Sell3Price", "Sell4Price", "Sell5Price", "Sell6Price", "Sell7Price",
                     "Sell8Price", "Sell9Price", "Sell10Price"]
    cbond_filter_df = cbond_tick_df[~(cbond_tick_df[PRICE_COLUMNS].sum(axis=1)==0)].reset_index(drop=True).copy()
    return cbond_filter_df

def daily_clean_GEMSecurities(trading_day, stock_tick_df, stock_transaction_df):
    tick_df = copy.deepcopy(stock_tick_df)
    trans_df = copy.deepcopy(stock_transaction_df)

    if tick_df.empty or trans_df.empty:
        return tick_df, TickMonitor.EMPTY

    tick_amount = tick_df["Amount"].tolist()
    tick_time = tick_df['Timestamp'].tolist()
    trans_df_amount = trans_df["Price"] * trans_df["Volume"]
    trans_df_amount.index = trans_df['Timestamp']

    amount_diff_threshold = 10        # amount difference less than 10 yuan
    postpone_times_threshold = 20     # abnormal appears 20 times, then postpone

    wrong_counter = 0
    for i in range(2, len(tick_df) - 2):
        if wrong_counter > postpone_times_threshold:
            break
        x = trans_df_amount.loc[tick_time[i] - 4: tick_time[i] + 1].sum() - tick_amount[i]
        if x <= - amount_diff_threshold:
            wrong_counter += 1
    if wrong_counter == 0:
        return tick_df, TickMonitor.NORMAL
    elif wrong_counter <= postpone_times_threshold:
        return tick_df, TickMonitor.MISSING
    else:
        tick_df["Timestamp"] = tick_df["Timestamp"] - 3   # postpone 3S
        tick_df["Time"] = tick_df["Timestamp"].apply(lambda x: dt.datetime.fromtimestamp(x).strftime("%Y%m%d %H%M%S%f").split(" ")[1][:-3])

        tick_time = tick_df["Timestamp"].tolist()
        tick_amount = tick_df["Amount"].tolist()

        wrong_counter_postpone = 0
        for i in range(2, len(tick_df) - 2):
            if wrong_counter_postpone > postpone_times_threshold:
                break
            x = trans_df_amount.loc[tick_time[i] - 4: tick_time[i] + 1].sum() - tick_amount[i]
            if x <= - amount_diff_threshold:
                wrong_counter += 1
        if wrong_counter_postpone == 0:
            return tick_df, TickMonitor.POSTPONE_NORMAL
        elif wrong_counter_postpone <= postpone_times_threshold:
            return tick_df, TickMonitor.POSTPONE_MISSING
        else:
            return tick_df, TickMonitor.UNKOWN

def generate_timestamp(trading_day, time):
    """ time: "093015", trading_day: "20190101" """
    return dt.datetime.strptime("{0} {1}".format(trading_day, time), "%Y%m%d %H%M%S").timestamp()

def generate_daily_key_timestamp(trading_day):
    '''指定交易日日期，生成当天的深交所格式的每隔3秒一个的时间戳'''
    morning_start_timestamp = generate_timestamp(trading_day, "093015")
    morning_end_timestamp = generate_timestamp(trading_day, "112959")
    afternoon_start_timestamp = generate_timestamp(trading_day, "130015")
    afternoon_end_timestamp = generate_timestamp(trading_day, "145659")
    return morning_start_timestamp, morning_end_timestamp, afternoon_start_timestamp, afternoon_end_timestamp

def fill_nonetick_with_help_df(fill_df, help_df):
    ### Code, Date, MinPrice, MaxPrice, PreviousClose字段一天中保持不变，直接复制
    ### fill_df: 传入一个空DataFrame，列名给定
    fill_df.loc[0,:] = copy.deepcopy(help_df.values)
    fill_zero_columns = ["OpenPrice", "HighPrice", "LowPrice", "LastPrice", "Volume", "Amount", "TotalVolume", "TotalAmount"]
    fill_df.loc[0, fill_zero_columns] = [np.nan for _ in range(len(fill_zero_columns))]
    fill_df.loc[0, "BidPrice"] = None
    fill_df.loc[0, "AskPrice"] = None
    fill_df.loc[0, "BidVolume"] = None
    fill_df.loc[0, "AskVolume"] = None
    fill_df.loc[0, "Transactions"] = None
    fill_df.loc[0, "IsMock"] = 1
    return fill_df

def get_startend_nofill_tick(tick_timestamp_list, fill_tick_timestamp_list):
    start_nofill_tick_timestamp = None
    end_nofill_tick_timestamp = None
    if len(tick_timestamp_list):
        for tick_timestamp in tick_timestamp_list:
            if tick_timestamp not in fill_tick_timestamp_list:
                start_nofill_tick_timestamp = tick_timestamp
                break
        for tick_timestamp in tick_timestamp_list[::-1]:
            if tick_timestamp not in fill_tick_timestamp_list:
                end_nofill_tick_timestamp = tick_timestamp
                break
    return start_nofill_tick_timestamp, end_nofill_tick_timestamp

def daily_tick_transaction_align(trading_day, daily_tick_df, daily_transaction_df, code_type):
    '''
    对齐某个交易日的股票/可转债/ETF Tick和Transaction：
    (1) 第一个Tick：Transaction数据为第一个TICK 3S内的Transaction数据
    (2）后面每个Tick计算时向前补齐
    :param trading_day:   交易日日期
    :param daily_tick_df:   1天的Tick数据
    :param daily_transaction_df:   1天的Transaction数据
    :return:
    '''
    # 获取一天中关键Timestamp
    morning_start_timestamp = generate_timestamp(trading_day, "093015")
    morning_end_timestamp = generate_timestamp(trading_day, "112959")
    afternoon_start_timestamp = generate_timestamp(trading_day, "130015")

    if code_type == "STOCK":
        ALIGN_COLUMNS = ALIGN_STOCK_COLUMNS
        afternoon_end_timestamp = generate_timestamp(trading_day, "145659")
    elif code_type == "CBOND":
        ALIGN_COLUMNS = ALIGN_CBOND_COLUMNS
        afternoon_end_timestamp = generate_timestamp(trading_day, "145659")
    elif code_type == "ETF":
        ALIGN_COLUMNS = ALIGN_FUND_COLUMNS
        afternoon_end_timestamp = generate_timestamp(trading_day, "145959")  # 存在尾盘集合竞价，need change to 145659
    elif code_type == "LOF":
        ALIGN_COLUMNS = ALIGN_FUND_COLUMNS
        afternoon_end_timestamp = generate_timestamp(trading_day, "145959")
    else:
        raise Exception("Not Supported Code Yet: {}".foramt(code_type))

    # 为了优化效率加速，提取出Numpy矩阵，以及各个列名idx
    daily_tick_array = daily_tick_df.values
    sub_align_stock_idx = [daily_tick_df.columns.get_loc(k) for k in SUB_ALIGN_STOCK_COLUMNS]
    bid_price_idx = [daily_tick_df.columns.get_loc(k) for k in BID_PRICE_COLUMNS]
    ask_price_idx = [daily_tick_df.columns.get_loc(k) for k in ASK_PRICE_COLUMNS]
    bid_volume_idx = [daily_tick_df.columns.get_loc(k) for k in BID_VOLUME_COLUMNS]
    ask_volume_idx = [daily_tick_df.columns.get_loc(k) for k in ASK_VOLUME_COLUMNS]

    # 为了加速运行，提取出逐笔交易数据时间戳列表、数值矩阵
    transactions_index_list = daily_transaction_df["Timestamp"].to_list()
    transactions_value_array = daily_transaction_df.values.astype(np.float64)
    left_idx, right_idx = 0, 1

    # 对每一个Tick逐个运算
    timestamp_tick_values_list = []
    fill_tick_timestamp_list = []
    for i in range(daily_tick_array.shape[0]):
        # 上一个Tick时间戳
        if len(timestamp_tick_values_list) > 0:  # i > 0
            last_tick_timestamp = copy.deepcopy(timestamp_tick_values_list[-1][1])
        else: # i==0
            last_tick_timestamp = generate_timestamp(trading_day, "000000")

        # 当前Tick信息
        base_cols = daily_tick_array[i, sub_align_stock_idx].tolist()
        bid_price_col = daily_tick_array[i, bid_price_idx].reshape(len(BID_PRICE_COLUMNS),).astype(np.float64)
        ask_price_col = daily_tick_array[i, ask_price_idx].reshape(len(ASK_PRICE_COLUMNS),).astype(np.float64)
        bid_volume_col = daily_tick_array[i, bid_volume_idx].reshape(len(BID_VOLUME_COLUMNS),).astype(np.float64)
        ask_volume_col = daily_tick_array[i, ask_volume_idx].reshape(len(ASK_VOLUME_COLUMNS),).astype(np.float64)

        tick_timestamp = base_cols[1]

        # 抽取这个Tick之间的逐笔成交信息
        flag_left = True
        start_idx = right_idx - 1
        for j in range(start_idx, len(transactions_index_list)):
            if transactions_index_list[j] >= last_tick_timestamp and flag_left:  # 左闭
                if transactions_index_list[j] >= tick_timestamp:  # 如果第一个找到的比上一个Tick时间戳大的idx，已经超出当前Tick的时间戳
                    break
                left_idx = j
                flag_left = False
                continue
            if transactions_index_list[j] >= tick_timestamp:  # 右开
                right_idx = j
                break
        if not flag_left:  # index已更新，则取更新后的时间段
            if left_idx==right_idx==len(transactions_index_list)-1:
                transactions_col = transactions_value_array[left_idx:None, :]
            else:
                transactions_col = transactions_value_array[left_idx:right_idx, :]
        else:  # index未更新，则说明这段时间没有数值
            transactions_col = None  # np.ones([0, 7]).astype(np.float64)

        timestamp_tick_values = base_cols + [bid_price_col, ask_price_col, bid_volume_col, ask_volume_col, transactions_col] + [0]

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
                # i==0时，tick_timestamp - last_tick_timestamp > 3000，不需要填充
                fill_daily_tick_values = copy.deepcopy(timestamp_tick_values_list[-1])
                fill_daily_tick_values[10] = 0     ### volume
                fill_daily_tick_values[11] = 0     ### amount
                fill_daily_tick_values[-2] = None  ### transactions
                fill_daily_tick_values[-1] = 1     ### 标记为补充TICK
                fill_daily_tick_values[1] = fill_tick_timestamp
                timestamp_tick_values_list.append(fill_daily_tick_values)

        # 把当前Tick数据加入到align_daily_stock_tick_df中
        timestamp_tick_values_list.append(timestamp_tick_values)

    # 汇总已有数据
    align_daily_tick_df = pd.DataFrame(timestamp_tick_values_list, columns=ALIGN_COLUMNS)

    # 加入093012 TICK数据
    first_tick_timestamp = generate_timestamp(trading_day, "093012")
    first_tick_df = align_daily_tick_df[align_daily_tick_df["Timestamp"] <= first_tick_timestamp]
    help_df = align_daily_tick_df[align_daily_tick_df["Timestamp"] > first_tick_timestamp].head(1)

    # 检查是否存在093012 TICK数据
    align_am_first_tick_df = pd.DataFrame(columns=ALIGN_COLUMNS)
    if first_tick_df.empty:
        align_am_first_tick_df = fill_nonetick_with_help_df(align_am_first_tick_df, help_df)
    else:
        align_am_first_tick_df.loc[0, ALIGN_COLUMNS] = first_tick_df[ALIGN_COLUMNS].tail(1).values
    align_am_first_tick_df.loc[0, "Timestamp"] = first_tick_timestamp

    # 处理上午数据，开始和结束均从第一个非补齐TICK开始
    am_tick_timestamp_list = align_daily_tick_df[(align_daily_tick_df["Timestamp"]>=morning_start_timestamp) &
                                (align_daily_tick_df["Timestamp"]<=morning_end_timestamp)]["Timestamp"].values.tolist()
    am_start_timestamp, am_end_timestamp = get_startend_nofill_tick(am_tick_timestamp_list, fill_tick_timestamp_list)
    if am_start_timestamp is None or am_end_timestamp is None:
        align_am_tick_df = pd.DataFrame(columns=ALIGN_COLUMNS)
    else:
        am_start_timestamp = max(am_start_timestamp, morning_start_timestamp)
        am_end_timestamp = min(am_end_timestamp, morning_end_timestamp)
        align_am_tick_df = align_daily_tick_df[(align_daily_tick_df["Timestamp"] >= am_start_timestamp) &
                                                            (align_daily_tick_df["Timestamp"] <= am_end_timestamp)]

    # 处理下午时刻数据，开始和结束均从第一个非补齐TICK开始
    pm_tick_timestamp_list = align_daily_tick_df[(align_daily_tick_df["Timestamp"] >=afternoon_start_timestamp) &
                            (align_daily_tick_df["Timestamp"] <=afternoon_end_timestamp)]["Timestamp"].values.tolist()
    pm_start_timestamp, pm_end_timestamp = get_startend_nofill_tick(pm_tick_timestamp_list, fill_tick_timestamp_list)
    if pm_start_timestamp is None or pm_end_timestamp is None:
        align_pm_tick_df = pd.DataFrame(columns=ALIGN_COLUMNS)
    else:
        pm_start_timestamp = max(pm_start_timestamp, afternoon_start_timestamp)
        pm_end_timestamp = min(pm_end_timestamp, afternoon_end_timestamp)
        align_pm_tick_df = align_daily_tick_df[(align_daily_tick_df["Timestamp"] >= pm_start_timestamp) &
                                                            (align_daily_tick_df["Timestamp"] <= pm_end_timestamp)]

    # 合并上下午数据
    align_daily_tick_df = pd.concat([align_am_first_tick_df, align_am_tick_df, align_pm_tick_df], axis=0)
    align_daily_tick_df["Time"] = align_daily_tick_df["Timestamp"].apply(lambda x: dt.datetime.fromtimestamp(x).strftime("%Y%m%d %H%M%S%f").split(" ")[1][:-3])
    align_daily_tick_df = align_daily_tick_df.reset_index(drop=True)
    return align_daily_tick_df

def daily_index_align(trading_day, daily_index_tick_df):
    """
    trading_day: 交易日
    daily_index_tick_df: 一天指数TICK行情，返回清洗后TICK行情
    清洗逻辑：截取TICK数据
    """
    daily_index_tick_df_array = daily_index_tick_df.values

    timestamp_tick_values_list = []
    fill_tick_timestamp_list = []

    for i in range(daily_index_tick_df_array.shape[0]):
        # 上一个Tick时间戳
        if len(timestamp_tick_values_list) > 0:  # i > 0
            last_tick_timestamp = copy.deepcopy(timestamp_tick_values_list[-1][1])
        else: # i==0
            last_tick_timestamp = generate_timestamp(trading_day, "000000")

        base_cols = daily_index_tick_df_array[i, :].tolist()
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
                # i==0时，tick_timestamp - last_tick_timestamp > 3000，不需要填充
                fill_daily_stock_tick_values = copy.deepcopy(timestamp_tick_values_list[-1])
                fill_daily_stock_tick_values[8] = 0     ### volume
                fill_daily_stock_tick_values[9] = 0     ### amount
                fill_daily_stock_tick_values[-1] = 1    ### 为填充TICK
                fill_daily_stock_tick_values[1] = fill_tick_timestamp
                timestamp_tick_values_list.append(fill_daily_stock_tick_values)

        # 把当前Tick数据加入到align_daily_index_tick_df中
        timestamp_tick_values_list.append(timestamp_tick_values)

    # 汇总已有数据
    align_daily_index_tick_df = pd.DataFrame(timestamp_tick_values_list, columns=ALIGN_INDEX_COLUMNS)

    # 加入093012 TICK数据
    first_tick_timestamp = generate_timestamp(trading_day, "093012")
    first_index_tick_df = align_daily_index_tick_df[align_daily_index_tick_df["Timestamp"] <= first_tick_timestamp]
    help_df = align_daily_index_tick_df[align_daily_index_tick_df["Timestamp"] > first_tick_timestamp].head(1)

    # 检查是否存在093012 TICK数据
    align_am_first_tick_df = pd.DataFrame(columns=ALIGN_INDEX_COLUMNS)
    if first_index_tick_df.empty:
        ### Code, Date, MinPrice, MaxPrice, PreviousClose 字段一天中保持不变，直接复制
        align_am_first_tick_df.loc[0, :] = copy.deepcopy(help_df.values)
        fill_zero_columns = ["OpenPrice", "HighPrice", "LowPrice", "LastPrice", "Volume", "Amount", "TotalVolume", "TotalAmount"]
        align_am_first_tick_df.loc[0, fill_zero_columns] = [np.nan for _ in range(len(fill_zero_columns))]
        align_am_first_tick_df.loc[0, "IsMock"] = 1
    else:
        align_am_first_tick_df.loc[0, :] = first_index_tick_df.tail(1).values
    align_am_first_tick_df.loc[0, "Timestamp"] = first_tick_timestamp

    # 获取一天中关键Timestamp
    morning_start_timestamp, morning_end_timestamp, afternoon_start_timestamp, afternoon_end_timestamp = generate_daily_key_timestamp(trading_day)

    # 处理上午数据，开始和结束均从第一个非补齐TICK开始
    am_tick_timestamp_list = align_daily_index_tick_df[(align_daily_index_tick_df["Timestamp"]>=morning_start_timestamp) &
                           (align_daily_index_tick_df["Timestamp"]<=morning_end_timestamp)]["Timestamp"].values.tolist()
    am_start_timestamp, am_end_timestamp = get_startend_nofill_tick(am_tick_timestamp_list, fill_tick_timestamp_list)
    if am_start_timestamp is None or am_end_timestamp is None:
        align_am_index_tick_df = pd.DataFrame(columns=ALIGN_INDEX_COLUMNS)
    else:
        am_start_timestamp = max(am_start_timestamp, morning_start_timestamp)
        am_end_timestamp = min(am_end_timestamp, morning_end_timestamp)
        align_am_index_tick_df = align_daily_index_tick_df[(align_daily_index_tick_df["Timestamp"] >= am_start_timestamp) &
                                                            (align_daily_index_tick_df["Timestamp"] <= am_end_timestamp)]

    # 处理下午时刻数据，开始和结束均从第一个非补齐TICK开始
    pm_tick_timestamp_list = align_daily_index_tick_df[(align_daily_index_tick_df["Timestamp"] >=afternoon_start_timestamp) &
                        (align_daily_index_tick_df["Timestamp"] <=afternoon_end_timestamp)]["Timestamp"].values.tolist()
    pm_start_timestamp, pm_end_timestamp = get_startend_nofill_tick(pm_tick_timestamp_list, fill_tick_timestamp_list)
    if pm_start_timestamp is None or pm_end_timestamp is None:
        align_pm_index_tick_df = pd.DataFrame(columns=ALIGN_INDEX_COLUMNS)
    else:
        pm_start_timestamp = max(pm_start_timestamp, afternoon_start_timestamp)
        pm_end_timestamp = min(pm_end_timestamp, afternoon_end_timestamp)
        align_pm_index_tick_df = align_daily_index_tick_df[(align_daily_index_tick_df["Timestamp"] >= pm_start_timestamp) &
                                                            (align_daily_index_tick_df["Timestamp"] <= pm_end_timestamp)]

    # 合并上下午数据
    align_daily_index_tick_df = pd.concat([align_am_first_tick_df, align_am_index_tick_df, align_pm_index_tick_df], axis=0)
    align_daily_index_tick_df["Time"] = align_daily_index_tick_df["Timestamp"].apply(lambda x: dt.datetime.fromtimestamp(x).strftime("%Y%m%d %H%M%S%f").split(" ")[1][:-3])
    align_daily_index_tick_df = align_daily_index_tick_df.reset_index(drop=True)
    return align_daily_index_tick_df

def daily_future_align(trading_day, daily_future_tick_df):
    """
    trading_day: 交易日
    daily_index_tick_df: 一天指数TICK行情，返回清洗后TICK行情
    清洗逻辑：截取TICK数据
    """
    # 为了优化效率加速，提取出Numpy矩阵，以及各个列名idx
    daily_future_tick_df_array = daily_future_tick_df.values
    sub_align_future_idx = [daily_future_tick_df.columns.get_loc(k) for k in SUB_ALIGN_FUTURE_COLUMNS]
    bid_price_idx = [daily_future_tick_df.columns.get_loc(k) for k in FUTURE_BID_PRICE_COLUMNS]
    ask_price_idx = [daily_future_tick_df.columns.get_loc(k) for k in FUTURE_ASK_PRICE_COLUMNS]
    bid_volume_idx = [daily_future_tick_df.columns.get_loc(k) for k in FUTURE_BID_VOLUME_COLUMNS]
    ask_volume_idx = [daily_future_tick_df.columns.get_loc(k) for k in FUTURE_ASK_VOLUME_COLUMNS]

    timestamp_tick_values_list = []
    fill_tick_timestamp_list = []

    for i in range(daily_future_tick_df_array.shape[0]):
        # 上一个Tick时间戳
        if len(timestamp_tick_values_list) > 0:  # i > 0
            last_tick_timestamp = copy.deepcopy(timestamp_tick_values_list[-1][1])
        else: # i==0
            last_tick_timestamp = generate_timestamp(trading_day, "000000")

        # 当前Tick信息
        base_cols = daily_future_tick_df_array[i, sub_align_future_idx].tolist()
        bid_price_col = daily_future_tick_df_array[i, bid_price_idx].reshape(len(FUTURE_BID_PRICE_COLUMNS),).astype(np.float64)
        ask_price_col = daily_future_tick_df_array[i, ask_price_idx].reshape(len(FUTURE_ASK_PRICE_COLUMNS),).astype(np.float64)
        bid_volume_col = daily_future_tick_df_array[i, bid_volume_idx].reshape(len(FUTURE_BID_VOLUME_COLUMNS),).astype(np.float64)
        ask_volume_col = daily_future_tick_df_array[i, ask_volume_idx].reshape(len(FUTURE_ASK_VOLUME_COLUMNS),).astype(np.float64)

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
                # i==0时，tick_timestamp - last_tick_timestamp > 3000，不需要填充
                fill_daily_stock_tick_values = copy.deepcopy(timestamp_tick_values_list[-1])
                fill_daily_stock_tick_values[10] = 0     ### volume
                fill_daily_stock_tick_values[11] = 0     ### amount
                fill_daily_stock_tick_values[-1] = 1    ### 为填充TICK
                fill_daily_stock_tick_values[1] = fill_tick_timestamp
                timestamp_tick_values_list.append(fill_daily_stock_tick_values)

        # 把当前Tick数据加入到align_daily_index_tick_df中
        timestamp_tick_values_list.append(timestamp_tick_values)

    # 汇总已有数据
    align_daily_future_tick_df = pd.DataFrame(timestamp_tick_values_list, columns=ALIGN_FUTURE_COLUMNS)

    # 加入093012 TICK数据
    first_tick_timestamp = generate_timestamp(trading_day, "093012")
    first_future_tick_df = align_daily_future_tick_df[align_daily_future_tick_df["Timestamp"] <= first_tick_timestamp]
    help_df = align_daily_future_tick_df[align_daily_future_tick_df["Timestamp"] > first_tick_timestamp].head(1)

    # 检查是否存在093012 TICK数据
    align_am_first_tick_df = pd.DataFrame(columns=ALIGN_FUTURE_COLUMNS)
    if first_future_tick_df.empty:
        ### Code, Date, MinPrice, MaxPrice, PreviousClose, PreSettlePrice 字段一天中保持不变，直接复制
        align_am_first_tick_df.loc[0, :] = copy.deepcopy(help_df.values)
        fill_zero_columns = ["OpenPrice", "HighPrice", "LowPrice", "LastPrice", "Volume", "Amount", "TotalVolume", "TotalAmount", "OpenInterest"]
        align_am_first_tick_df.loc[0, fill_zero_columns] = [np.nan for _ in range(len(fill_zero_columns))]
        align_am_first_tick_df.loc[0, "BidPrice"] = None
        align_am_first_tick_df.loc[0, "AskPrice"] = None
        align_am_first_tick_df.loc[0, "BidVolume"] = None
        align_am_first_tick_df.loc[0, "AskVolume"] = None
        align_am_first_tick_df.loc[0, "IsMock"] = 1
    else:
        align_am_first_tick_df.loc[0, ALIGN_FUTURE_COLUMNS] = first_future_tick_df[ALIGN_FUTURE_COLUMNS].tail(1).values
    align_am_first_tick_df.loc[0, "Timestamp"] = first_tick_timestamp

    # 获取一天中关键Timestamp
    morning_start_timestamp = generate_timestamp(trading_day, "093015")
    morning_end_timestamp = generate_timestamp(trading_day, "112959")
    afternoon_start_timestamp = generate_timestamp(trading_day, "130015")
    afternoon_end_timestamp = generate_timestamp(trading_day, "145659")

    # 处理上午数据，开始和结束均从第一个非补齐TICK开始
    am_tick_timestamp_list = align_daily_future_tick_df[(align_daily_future_tick_df["Timestamp"]>=morning_start_timestamp) &
                           (align_daily_future_tick_df["Timestamp"]<=morning_end_timestamp)]["Timestamp"].values.tolist()
    am_start_timestamp, am_end_timestamp = get_startend_nofill_tick(am_tick_timestamp_list, fill_tick_timestamp_list)
    if am_start_timestamp is None or am_end_timestamp is None:
        align_am_future_tick_df = pd.DataFrame(columns=ALIGN_FUTURE_COLUMNS)
    else:
        am_start_timestamp = max(am_start_timestamp, morning_start_timestamp)
        am_end_timestamp = min(am_end_timestamp, morning_end_timestamp)
        align_am_future_tick_df = align_daily_future_tick_df[(align_daily_future_tick_df["Timestamp"] >= am_start_timestamp) &
                                                            (align_daily_future_tick_df["Timestamp"] <= am_end_timestamp)]

    # 处理下午时刻数据，开始和结束均从第一个非补齐TICK开始
    pm_tick_timestamp_list = align_daily_future_tick_df[(align_daily_future_tick_df["Timestamp"] >=afternoon_start_timestamp) &
                        (align_daily_future_tick_df["Timestamp"] <=afternoon_end_timestamp)]["Timestamp"].values.tolist()
    pm_start_timestamp, pm_end_timestamp = get_startend_nofill_tick(pm_tick_timestamp_list, fill_tick_timestamp_list)
    if pm_start_timestamp is None or pm_end_timestamp is None:
        align_pm_future_tick_df = pd.DataFrame(columns=ALIGN_FUTURE_COLUMNS)
    else:
        pm_start_timestamp = max(pm_start_timestamp, afternoon_start_timestamp)
        pm_end_timestamp = min(pm_end_timestamp, afternoon_end_timestamp)
        align_pm_future_tick_df = align_daily_future_tick_df[(align_daily_future_tick_df["Timestamp"] >= pm_start_timestamp) &
                                                            (align_daily_future_tick_df["Timestamp"] <= pm_end_timestamp)]

    # 合并上下午数据
    align_daily_future_tick_df = pd.concat([align_am_first_tick_df, align_am_future_tick_df, align_pm_future_tick_df], axis=0)
    align_daily_future_tick_df["Time"] = align_daily_future_tick_df["Timestamp"].apply(lambda x: dt.datetime.fromtimestamp(x).strftime("%Y%m%d %H%M%S%f").split(" ")[1][:-3])
    align_daily_future_tick_df = align_daily_future_tick_df.reset_index(drop=True)
    return align_daily_future_tick_df

def minute_data_transform(df, operation):
    """
    :param item: 变量名
    :param df: index为时间的DataFrame
    :param operation: ["",""], 可取："","drop","merge"
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
        sub_df = df[df["Date"]==date]
        start_timestamp = dt.datetime.strptime("{} 09:25:00".format(date), "%Y%m%d %H:%M:%S").timestamp()
        end_timestamp = dt.datetime.strptime("{} 15:00:00".format(date), "%Y%m%d %H:%M:%S").timestamp()
        invalid_sub_df = sub_df[(sub_df["Timestamp"] < start_timestamp) | (sub_df["Timestamp"] > end_timestamp)]
        if not invalid_sub_df.empty:
            invalid_index_list.extend(invalid_sub_df.index.tolist())
    if len(invalid_index_list) > 0:
        for drop_index in invalid_index_list:
            df.drop(drop_index, axis=0, inplace=True)

    for date in trade_date_list:
        sub_df = df[df["Date"]==date]
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

        open_process_num = 0   ### 集合竞价drop或merge后分钟线减少的根数

        if is_close_call:
            if operation[0].startswith("drop"):
                drop_num = operation[0][len("drop"):]
                drop_num = 1 if drop_num == "" else int(drop_num)
                if len(each_day_index)  > drop_num:   ### 保证有足够的分钟线可以drop
                    drop_index_list = [each_day_index[i] for i in range(drop_num)]
                    for drop_index in drop_index_list:
                        df.drop(drop_index, axis=0, inplace=True)

                open_process_num = max(open_process_num, drop_num)

            elif operation[0].startswith("merge"):
                merge_num = operation[0][len("merge"):]
                merge_num = 1 if merge_num == "" else int(merge_num)
                if len(each_day_index) > merge_num:   ### 保证有足够的分钟线可以merge
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
                if len(each_day_index) > drop_num + open_process_num:   ### 早盘处理后保证尾盘有足够的分钟线可以drop
                    drop_index_list = [each_day_index[-(i + 1)] for i in range(drop_num)]
                    for drop_index in drop_index_list:
                        df.drop(drop_index, axis=0, inplace=True)
            elif operation[1].startswith("merge"):
                merge_num = operation[1][len("merge"):]
                merge_num = 1 if merge_num == "" else int(merge_num)
                if len(each_day_index) > merge_num + open_process_num:    ### 早盘处理后保证尾盘有足够的分钟线可以merge
                    merge_index_list = [each_day_index[-(i + 1)] for i in range(merge_num)]
                    result_index = each_day_index[-(merge_num + 1)]
                    for merge_index in merge_index_list:
                        df.loc[result_index, cols] = df.loc[merge_index, cols].values + df.loc[result_index, cols].values
                        df.loc[result_index,["ClosePrice"]] = df.loc[merge_index,["ClosePrice"]].values
                        df.loc[result_index,["LowPrice"]] = np.minimum(df.loc[merge_index,["LowPrice"]].values,
                                                                       df.loc[result_index,["LowPrice"]].values)
                        df.drop(merge_index, axis=0, inplace=True)

    return df

