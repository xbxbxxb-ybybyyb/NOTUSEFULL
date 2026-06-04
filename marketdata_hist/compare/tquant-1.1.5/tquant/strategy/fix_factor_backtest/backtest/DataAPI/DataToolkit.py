import pandas as pd
import numpy as np
import os
import datetime as dt
import fix_factor_backtest.backtest.DataAPI.GetTradingDay as GetTradingDay
from tquant.stock_data import StockData
from tquant.basic_data import BasicData
import time
bd = BasicData()
sd = StockData()

root_013542 = '/'.join(os.path.abspath(__file__).split('/')[:-4]) + "/data/Apollo/AlphaDataBase"

database_dir = root_013542
barra_dir = root_013542
complete_stock_list_path = root_013542 + "/CompleteStockList.csv"


def get_trading_day(start_date, end_date, freq='D') -> list:
    """
    :param start_date: 起始日期
    :param end_date: 结束日期
    :param freq: 查询频率。默认是日频（'D'）。
                  如查询月频（'M'），则仿照Wind的“插入日期”的规则，输出start_date和end_date之间每个月末的最后一个
                  交易日，如end_date不是当月的最后一个交易日，那么再加上end_date（含end_date）前的最后一个交易日；
                  如start_date和end_date同属一个月、且其中包含超过一个交易日，那么输出之间的最后一个交易日。
                  参考以下3个例子：其中20181108和20181109是周四周五、是交易日；20181110和20181111是周末、不是交易日。
                  例1: t_d0 = trading_day(20181110, 20181111, 'M')  --- t_d0 = []
                  例2: t_d1 = trading_day(20181108, 20181111, 'M')  --- t_d1 = [20181109]
                  例3: t_d2 = trading_day(20181001, 20181111, 'M')  --- t_d2 = [20181031, 20181109]
    :return: 输出list，已按升序排列；如start_date和end_date都是交易日，则都将被包含进来（前闭后闭）
    """
    answer_list = GetTradingDay.trading_day(start_date, end_date, freq)
    return answer_list


def get_n_days_off(key_date, n_days_off):
    """
    2019/3/14 -- 011673重写了本函数，为了修改当n_days_off < -200的时候的bug
    2019/3/22 -- 006566修复了bug -- 如n_days_off > 0, 应当包含key_date
    """
    # 给定key_date, 取其前后n_days_off天的数据，并返回list，list的长度等于n_days_off，日期数值类型为int；
    # 如key_date是交易日，那么key_date应当被包含进来
    # 例如输入20180503, 3, 返回[20180503, 2080504, 20180507]
    # 或输入20180503, -3, 返回[20180427, 20180502, 20180503]
    # 如key_date是非交易日，先按照n_days_off的正负符号位移到最近的交易日，如n_days_off<0，则往前取到最近的交易日，反之
    # 则往后取到最近的交易日；然后再按n_days_off天数来涵盖
    # 例如输入2080501, 3；往后最近的交易日是20180502，故返回[20180502, 20180503, 20180504]
    # 或输入20180501, -3，往前最近的交易日是20180427，故返回[20180425, 20180426, 20180427]

    trading_day_list = GetTradingDay.get_complete_trading_day_list()

    def find_date(number: int, list_data: list):
        if number not in list_data:
            if (number >= list_data[-1]) or (number <= list_data[0]):
                raise Exception('input date is out of boundary')
            for i in range(0, (len(list_data) - 1)):
                if (list_data[i] < number) and (number < list_data[i + 1]):
                    return i
            raise Exception('input date is out of boundary')
        else:
            return list_data.index(number)

    if n_days_off < 0:
        index_number = find_date(key_date, trading_day_list)
        start_index = index_number + n_days_off
        if start_index + 1 >= 0:
            selected_list = trading_day_list[start_index + 1:index_number + 1]
        else:
            selected_list = []
    elif n_days_off == 0:
        selected_list = []
    else:
        if key_date in trading_day_list:
            index_number = find_date(key_date, trading_day_list)
        else:
            index_number = find_date(key_date, trading_day_list) + 1
        end_index = index_number + n_days_off
        if end_index + 1 < len(trading_day_list):
            selected_list = trading_day_list[index_number:end_index]
        else:
            selected_list = []
    return selected_list


def convert_date_or_time_int_to_datetime(date_time_input):
    # 将int型的日期或日期时间，转化为datetime型的；如输入单一值、则返回单一值；如输入list，则返回list
    # 可支持输入8位数的日期、例如20180509，也可支持输入14位数的日期时间、例如20180509145559
    # 但若输入的是list, 则list中元素的格式必须一样，不能8位和14位混淆
    if isinstance(date_time_input, list):
        original_input_is_list = True
    else:
        original_input_is_list = False
        date_time_input = [date_time_input]
    if (isinstance(date_time_input[0], int) or isinstance(date_time_input[0], np.int64)) \
            and str(date_time_input[0]).__len__() == 8:
        date_list_str = [str(i_date) for i_date in date_time_input]
        answer_list = [dt.datetime(int(i_date[0:4]), int(i_date[4:6]), int(i_date[6:8])) for i_date in date_list_str]
    elif (isinstance(date_time_input[0], int) or isinstance(date_time_input[0], np.int64)) \
            and str(date_time_input[0]).__len__() == 14:
        date_time_list_str = [str(i_date_time) for i_date_time in date_time_input]
        answer_list = [
            dt.datetime(int(i_date_time[0:4]), int(i_date_time[4:6]), int(i_date_time[6:8]), int(i_date_time[8:10]),
                        int(i_date_time[10:12]), int(i_date_time[12:14])) for i_date_time in date_time_list_str]
    else:
        print("function convert_date_or_time_int_to_datetime: input type or format error")
        answer_list = []
    if not original_input_is_list:
        answer_list = answer_list[0]
    return answer_list


def get_complete_stock_list(end_date=None, drop_delisted_stocks=False) -> list:
    """
    :param end_date: 返回在此日期之前存在过的所有股票; 如为nan, 则以最新日期为标准
    :param drop_delisted_stocks: 是否要删去退市的股票, 对于每日更新数据应选True, 对于研究和回测应选False
    :return: 返回股票的list
    """
    # revised on 2019/7/11-12 fixed the bug of delisting dates
    # 输入end_date, 则; 如drop_delisted_stocks为True, 则删去所有退市的股票
    complete_stock_list = []
    if os.path.exists(complete_stock_list_path):
        df = pd.read_csv(complete_stock_list_path)
        df = df.fillna(0)
        if drop_delisted_stocks:
            df = df[df.Delisting_date < 1]
        if end_date is None:
            complete_stock_list = df['Stock_code'].tolist()
        else:
            # 上市日期早于end_date的股票都要列出来
            df = df[df.Listing_date <= end_date]
            complete_stock_list = df['Stock_code'].tolist()
    else:
        print("Error: cannot find the CompleteStockList file")
    return complete_stock_list


def get_panel_interval_pv_df(stock_list, start_date_int, end_date_int, pv_type='interval_twap_30_5', adj_type='NONE',
                             interval_time=None) \
        -> pd.DataFrame:
    # by 陈世峰; revised by 郑润泽, 2019/5/27 - 若要取复权的数据，需将adj_df展开为日内级的
    #SJL Data_interval_buy_twap_30_5.h5
    if pv_type in ['interval_twap_30_5', 'interval_buy_twap_30_5', 'interval_buy_twap_fill_rate_30_5',
                   'interval_sell_twap_30_5', 'interval_sell_twap_fill_rate_30_5', 'interval_pre_close_30_0',
                   'interval_buyable_volume_30_5', 'interval_sellable_volume_30_5', 'interval_twap_60_5',
                   'interval_sell_twap_60_5', 'interval_buy_twap_60_5', 'interval_sellable_volume_60_5',
                   'interval_buyable_60_5', 'interval_buy_twap_fill_rate_60_5', 'interval_sell_twap_fill_rate_60_5',
                   'interval_vwap_30_5', 'interval_buy_vwap_30_5', 'interval_sell_vwap_30_5']:
        pass
    else:
        raise TypeError
    available_index_list = ["000001.SH", "000016.SH", "000300.SH", "000905.SH", "000906.SH", "399001.SZ",
                            "399006.SZ"]
    for available_index in available_index_list:  # 如要取指数的数据，但涉及到复权因子或复权价格
        if available_index in stock_list and adj_type is not 'NONE':
            raise Exception('Adjustment price is not applicable to index data')
    query_date_list = get_trading_day(start_date_int, end_date_int)  # 获取起止日期list
    start_date_int = query_date_list[0]  # 确保start_date_int是交易日
    end_date_int = query_date_list[-1]  # 确保end_date_int是交易日，以利于后续计算BACKWARD2（前复权）时定位用
    data_file = "Data_" + pv_type + ".h5"
    data_full_path = os.path.join(database_dir, data_file)
    store = pd.HDFStore(data_full_path, mode='r')
    data_df = store.select("/factor")
    store.close()
    start_date_int_14 = start_date_int * 1e6
    end_date_int_14 = end_date_int * 1e6 + 150000
    data_df = data_df[(data_df.index >= start_date_int_14) & (data_df.index <= end_date_int_14)]
    data_df = data_df.reindex(columns=stock_list)

    if interval_time is not None:
        data_df = data_df[(data_df.index % 1e6) % interval_time == 0]

    if adj_type == "FORWARD":
        daily_adj_df = get_panel_daily_info(stock_list, start_date_int, end_date_int, 'adjfactor')
        data_df = pd.DataFrame([row * daily_adj_df.loc[int(index / 1e6)] for index, row in data_df.iterrows()],
                               index=data_df.index)
    elif adj_type == "BACKWARD2":
        daily_adj_df = get_panel_daily_info(stock_list, start_date_int, end_date_int, 'adjfactor')
        data_df = pd.DataFrame([row * daily_adj_df.loc[int(index / 1e6)] for index, row in data_df.iterrows()],
                               index=data_df.index)
        data_df = data_df / daily_adj_df.loc[end_date_int]
    # 因为Python原生的None在pandas/numpy中兼容性不好，影响读写以及在其他模块中的调用，这里转为np.nan
    data_df = data_df.add(0.0)
    data_df = data_df.reindex(columns=stock_list)  # 使输出的列名顺序等于输入的顺序
    return data_df


def get_panel_daily_pv_df(stock_list, start_date_int, end_date_int, pv_type='close', adj_type='NONE') -> pd.DataFrame:
    """
    获取日级别的价量（pv - price & volume）行情，形式是panel data，即[股票list * 日期list]
    :param stock_list:  股票代码列表，e.g., ['000001.SZ', '600000.SH', '601688.SH']
    :param start_date_int: 查询起始日，e.g., 20180801，如当天是交易日，则将被包括进来
    :param end_date_int: 查询终止日， e.g., 20180808，如当天是交易日，则将被包括进来
    :param pv_type: 查询类型
    :param adj_type: 复权类型，'NONE'-不复权，'FORWARD'-（从上市日）向后复权， 'BACKWARD2' - 从end_date_int日向前复权；
                      仅对各种价格有效，对volume, amt, suspension和pct_chg无意义，对指数无意义，
    :return: 返回类型为DataFrame, 行为日期，列为股票代码
    """
    #SJL twap暂时不支持，用vwap代替
    if pv_type in ['close', 'open', 'high', 'low', 'pre_close', 'volume', 'amt', 'pct_chg', 'turn', 'twap', 'vwap']:
        pass
    else:
        raise TypeError
    available_index_list = ["000001.SH", "000016.SH", "000300.SH", "000905.SH", "000906.SH", "399001.SZ",
                            "399006.SZ"]
    for available_index in available_index_list:  # 如要取指数的数据，但涉及到复权因子或复权价格
        if available_index in stock_list and adj_type is not 'NONE':
            raise Exception('Adjustment price is not applicable to index data')
    query_date_list = get_trading_day(start_date_int, end_date_int)  # 获取起止日期list
    start_date_int = query_date_list[0]  # 确保start_date_int是交易日
    end_date_int = query_date_list[-1]  # 确保end_date_int是交易日，以利于后续计算BACKWARD2（前复权）时定位用
    #SJL
    # data_file = "Data_" + pv_type + ".h5"
    # data_full_path = os.path.join(database_dir, data_file)
    # store = pd.HDFStore(data_full_path, mode='r')
    # data_df = store.select("/factor")
    # store.close()

    data_df = sd.get_factor_price_daily(stock_list,query_date_list,pv_type, fill_na=True).iloc[:, 0].unstack()
    data_df.index = [int(x) for x in data_df.index]
    data_df = data_df.loc[start_date_int: end_date_int]
    data_df = data_df.reindex(columns=stock_list)
    if adj_type == "FORWARD" and pv_type in ['open', 'high', 'low', 'close', 'pre_close', 'twap', 'buy_twap',
                                             'sell_twap', 'buy_vwap', 'sell_vwap', 'UpPrice', 'DownPrice']:
        adj_df = get_panel_daily_info(stock_list, start_date_int, end_date_int, 'adjfactor')
        data_df = data_df * adj_df
    elif adj_type == "BACKWARD2" and pv_type in ['open', 'high', 'low', 'close', 'pre_close', 'twap', 'buy_twap',
                                                 'sell_twap', 'buy_vwap', 'sell_vwap', 'UpPrice', 'DownPrice']:
        adj_df = get_panel_daily_info(stock_list, start_date_int, end_date_int, 'adjfactor')
        data_df = data_df * adj_df / adj_df.loc[end_date_int]
    # 因为Python原生的None在pandas/numpy中兼容性不好，影响读写以及在其他模块中的调用，这里转为np.nan
    data_df = data_df.add(0.0)
    if pv_type == 'volume':  # 因得到的VOLUME单位是“手”，这里转为“股”
        data_df = data_df.mul(100)
    elif pv_type == 'amt':  # 因得到的AMOUNT单位是“千元”，这里转为“元”
        data_df = data_df.mul(1000)
    data_df = data_df.reindex(columns=stock_list)  # 使输出的列名顺序等于输入的顺序
    return data_df


def get_panel_daily_info(stock_list, start_date_int, end_date_int, info_type, output_index_type='date_int') \
        -> pd.DataFrame:
    """
    updated 2019/2/24 by 011672 修正了stock_universe和industry两类数据的S盘及XQuant接口
    updated 2018/9/6 by 006688, 新增中信一级行业（info_type是industry3）
    updated 2018/11/20 by 006566，彻底更改数据来源，只有adjfactor是自己维护的，其他字段不再维护
    updated 2019/2/28 by 006566，适应新版XQuant的h5因子库; 另外，对应md范畴的14个字段，以及alpha_universe和
                                 risk_universe直接读取Data_文件
    updated 2019/9/3 by 006566, 新增alpha_universe_b - 在alpha_universe的基础上新增条件：剔除过去10日成交额最少的5%股票
    获取日级别的信息，形式是panel data，即[股票list * 日期list]；因为不是为取价量而设计的，所以这里没加入复权选项
    :param stock_list:  股票代码列表，e.g., ['000001.SZ', '600000.SH', '601688.SH']
    :param start_date_int: 查询起始日，e.g., 20180801，如当天是交易日，则将被包括进来
    :param end_date_int: 查询终止日， e.g., 20180808，如当天是交易日，则将被包括进来
    :param info_type: 查询的信息类型
    :param output_index_type: 返回的DataFrame的索引的类型，默认是'date_int'，可改为'timestamp'
    :return: 返回类型为DataFrame, 行为日期，列为股票代码；如查询不到，则返回空的DataFrame
    """
    query_date_list = get_trading_day(start_date_int, end_date_int)  # 获取起止日期list
    start_date_int = query_date_list[0]  # 确保start_date_int是交易日
    end_date_int = query_date_list[-1]  # 确保end_date_int是交易日
    all_key_set = return_panel_info_complete_key_set()
    if info_type in all_key_set:
        pass
    else:
        raise TypeError
    # 对应md范畴的14个字段，以及alpha_universe和risk_universe直接读取Data_文件
    #SJL
    if info_type in ['alpha_universe', 'industry3']:
        data_file = "Data_" + info_type + ".h5"
        data_full_path = os.path.join(database_dir, data_file)
        store = pd.HDFStore(data_full_path, mode='r')
        data_df = store.select("/factor")
        store.close()
        data_df = data_df.loc[start_date_int: end_date_int]
        data_df = data_df.reindex(columns=stock_list)
    elif info_type in ['mkt_cap_ard']:
        #SJL
        days = bd.get_trading_day(str(start_date_int), str(end_date_int))
        data_df = sd.get_factor_valuation_metrics(stock_list, days, ['mkt_cap_ard'], fill_na=True).iloc[:, 0].unstack()
        data_df.index = [int(x) for x in data_df.index]
        data_df = data_df.loc[start_date_int: end_date_int]
        data_df = data_df.reindex(columns=stock_list)
    elif info_type in ['adjfactor']:
        #SJL
        days = bd.get_trading_day(str(start_date_int), str(end_date_int))
        data_df = sd.get_factor_price_daily(stock_list, days, ['adjfactor'], fill_na=True).iloc[:, 0].unstack()
        data_df.index = [int(x) for x in data_df.index]
        data_df = data_df.loc[start_date_int: end_date_int]
        data_df = data_df.reindex(columns=stock_list)
    else:
        data_df = pd.DataFrame()
        data_path, key_list = key_related_search(info_type)
        if key_list == "optm_self_made":
            if info_type == "index_800":
                data_file0 = "Data_index_300.h5"
                data_file1 = "Data_index_500.h5"
                data_df0 = pd.read_hdf(os.path.join(database_dir, data_file0), 'factor')
                data_df1 = pd.read_hdf(os.path.join(database_dir, data_file1), 'factor')
                data_df = data_df0 + data_df1
                data_df = data_df.shift(-1)  # 在原始数据中t日的指数信息，key是t+1日的，因此指数要用下一天的数据
                data_df = data_df.fillna(0)
                data_df = data_df.loc[start_date_int: end_date_int]
                data_df = data_df.add(0.0)  # 将Bool值转成1/0，否则后续在*universe/universe时会出错
            elif info_type in ["alpha_uni_large", "alpha_uni_mid", "alpha_uni_small"]:
                # 在alpha_universe中，按市值大小三等分
                # 以下分别读取mkt_cap_ard和alpha_universe
                data_file = "Data_mkt_cap_ard.h5"
                data_full_path = os.path.join(database_dir, data_file)
                store = pd.HDFStore(data_full_path, mode='r')
                mkt_cap_ard = store.select("/factor")
                store.close()
                mkt_cap_ard = mkt_cap_ard.loc[start_date_int: end_date_int]

                data_file = "Data_alpha_universe.h5"
                data_full_path = os.path.join(database_dir, data_file)
                store = pd.HDFStore(data_full_path, mode='r')
                alpha_universe = store.select("/factor")
                store.close()
                alpha_universe = alpha_universe.reindex(index=mkt_cap_ard.index, columns=mkt_cap_ard.columns)

                # 将总市值按alpha_universe过滤，然后排序
                mkt_cap_ard = mkt_cap_ard * alpha_universe / alpha_universe
                mkt_cap_ard_rank = mkt_cap_ard.rank(axis=1)
                univ_stock_num = mkt_cap_ard_rank.max(axis=1)  # 每日alpha_universe中的股票数量

                # 三等分标记
                small_cap_df = mkt_cap_ard_rank.sub(univ_stock_num / 3, axis=0)
                large_cap_df = mkt_cap_ard_rank.sub(univ_stock_num * 2 / 3, axis=0)

                if info_type == "alpha_uni_small":  # 三等分小市值
                    data_df = small_cap_df < 0
                elif info_type == "alpha_uni_large":  # 三等分大市值
                    data_df = large_cap_df > 0
                else:  # 三等分中市值
                    data_df = (small_cap_df >= 0) & (large_cap_df <= 0)
                data_df = data_df.add(0.0)
                data_df = data_df.reindex(columns=stock_list)
            else:
                raise TypeError
        elif key_list == 'fdd_q':
            store = pd.HDFStore(data_path, mode='r')
            data_df_info = store.select("/" + info_type)
            ann_df = store.select("/stm_issuingdate")
            store.close()
            ann_df = unfold_df(ann_df)
            data_df_info = unfold_df(data_df_info)
            ann_df = convert_df_index_type(ann_df, 'timestamp2', 'date_int')
            data_df_info = convert_df_index_type(data_df_info, 'timestamp2', 'date_int')
            ann_df = ann_df.fillna(0)
            data_df_info = data_df_info.reindex(columns=ann_df.columns)
            ann_df = ann_df.reindex(data_df_info.index)  # 2019/7/2 修复bug: XQuant数据中发布日信息可能比数据信息多一行
            last_report_date = start_date_backfill(start_date_int)
            trading_day_1 = get_trading_day(last_report_date, end_date_int)
            data_df_raw = pd.DataFrame(index=trading_day_1, columns=stock_list)
            data_df = back_fill(data_df_raw, data_df_info, ann_df)
            data_df = data_df.loc[start_date_int:]
    if output_index_type == 'timestamp':
        data_df = convert_df_index_type(data_df, 'date_int', 'timestamp')
    elif output_index_type == 'datetime':
        data_df = convert_df_index_type(data_df, 'date_int', 'datetime')
    # 因为Python原生的None在pandas/numpy中兼容性不好，影响读写以及在其他模块中的调用，这里转为np.nan
    data_df = data_df.add(0.0)
    data_df = data_df.reindex(columns=stock_list)
    data_df[stock_list] = data_df[stock_list].astype('float')  # 将1/0转化为1.0/0.0，否则在*universe/universe时会出错
    data_df.index.name = 'index'  # 使输出的index的名字是'index'，其实没有实际意义
    return data_df


def get_complete_minute_list():
    complete_minute_list = [925, 930, 931, 932, 933, 934, 935, 936, 937, 938, 939, 940, 941, 942, 943, 944, 945, 946,
                            947, 948, 949, 950, 951, 952, 953, 954, 955, 956, 957, 958, 959, 1000, 1001, 1002, 1003,
                            1004, 1005, 1006, 1007, 1008, 1009, 1010, 1011, 1012, 1013, 1014, 1015, 1016, 1017, 1018,
                            1019, 1020, 1021, 1022, 1023, 1024, 1025, 1026, 1027, 1028, 1029, 1030, 1031, 1032, 1033,
                            1034, 1035, 1036, 1037, 1038, 1039, 1040, 1041, 1042, 1043, 1044, 1045, 1046, 1047, 1048,
                            1049, 1050, 1051, 1052, 1053, 1054, 1055, 1056, 1057, 1058, 1059, 1100, 1101, 1102, 1103,
                            1104, 1105, 1106, 1107, 1108, 1109, 1110, 1111, 1112, 1113, 1114, 1115, 1116, 1117, 1118,
                            1119, 1120, 1121, 1122, 1123, 1124, 1125, 1126, 1127, 1128, 1129, 1300, 1301, 1302, 1303,
                            1304, 1305, 1306, 1307, 1308, 1309, 1310, 1311, 1312, 1313, 1314, 1315, 1316, 1317, 1318,
                            1319, 1320, 1321, 1322, 1323, 1324, 1325, 1326, 1327, 1328, 1329, 1330, 1331, 1332, 1333,
                            1334, 1335, 1336, 1337, 1338, 1339, 1340, 1341, 1342, 1343, 1344, 1345, 1346, 1347, 1348,
                            1349, 1350, 1351, 1352, 1353, 1354, 1355, 1356, 1357, 1358, 1359, 1400, 1401, 1402, 1403,
                            1404, 1405, 1406, 1407, 1408, 1409, 1410, 1411, 1412, 1413, 1414, 1415, 1416, 1417, 1418,
                            1419, 1420, 1421, 1422, 1423, 1424, 1425, 1426, 1427, 1428, 1429, 1430, 1431, 1432, 1433,
                            1434, 1435, 1436, 1437, 1438, 1439, 1440, 1441, 1442, 1443, 1444, 1445, 1446, 1447, 1448,
                            1449, 1450, 1451, 1452, 1453, 1454, 1455, 1456, 1457, 1458, 1459, 1500]
    return complete_minute_list


def convert_df_index_type(df_input, index_type_input, index_type_output) -> pd.DataFrame:
    """
    转化dataframe的索引的数据类型, timestamp是数字型的timestamp, timestamp2是类似datetime型的
    """
    df = df_input.copy()
    index_name = df.index.name
    if index_type_input == 'date_int' and index_type_output == 'timestamp':
        index_list = list(df.index)
        index_list_datetime = convert_date_or_time_int_to_datetime(index_list)
        index_list_timestamp = [i.timestamp() for i in index_list_datetime]
        df['timestamp'] = index_list_timestamp
        df = df.set_index(['timestamp'])
    elif index_type_input == 'date_int' and index_type_output == 'datetime':
        index_list = list(df.index)
        index_list_datetime = convert_date_or_time_int_to_datetime(index_list)
        df['datetime'] = index_list_datetime
        df = df.set_index(['datetime'])
    elif index_type_input == 'date_time_int_multi_index' and index_type_output == 'timestamp':
        index_list = list(df.index)
        index_list = [x[0] * 1000000 + x[1] * 100 for x in index_list]
        index_list_datetime = convert_date_or_time_int_to_datetime(index_list)
        index_list_timestamp = [i.timestamp() for i in index_list_datetime]
        df['timestamp'] = index_list_timestamp
        df = df.set_index(['timestamp'])
    elif index_type_input == 'timestamp' and index_type_output == 'date_time_int_multi_index':
        index_list = list(df.index)
        index_date_time_list = [dt.datetime.fromtimestamp(i) for i in index_list]
        date_int_list = [int((i.year * 10000 + i.month * 100 + i.day)) for i in index_date_time_list]
        time_int_list = [int((i.hour * 100 + i.minute)) for i in index_date_time_list]
        df['date'] = date_int_list
        df['time'] = time_int_list
        df = df.set_index(['date', 'time'])
    elif index_type_input == 'timestamp' and index_type_output == 'date_int':
        index_list = list(df.index)
        index_date_time_list = [dt.datetime.fromtimestamp(i) for i in index_list]
        date_int_list = [int((i.year * 10000 + i.month * 100 + i.day)) for i in index_date_time_list]
        df['date'] = date_int_list
        df = df.set_index(['date'])
    elif index_type_input == 'timestamp' and index_type_output == 'date14_int':
        index_list = list(df.index)
        index_date_time_list = [dt.datetime.fromtimestamp(i) for i in index_list]
        date_int_list = [int(
            (i.year * 10000000000 + i.month * 100000000 + i.day * 1000000 + i.hour * 10000 + i.minute * 100 + i.second))
            for i in index_date_time_list]
        df['date'] = date_int_list
        df = df.set_index(['date'])
    elif index_type_input in ['timestamp2', 'datetime'] and index_type_output == 'date_int':
        index_list = list(df.index)
        date_int_list = [int((i.year * 10000 + i.month * 100 + i.day)) for i in index_list]
        df['date'] = date_int_list
        df = df.set_index(['date'])
    elif index_type_input == 'str' and index_type_output == 'date_int':
        df = df.reset_index()
        df['date'] = df[index_name].astype(int)
        df = df.set_index(['date'])
    if index_name in list(df.columns):  # 原有的index列可能残留，删除之
        df = df.drop(index_name, axis=1)
    return df


def key_related_search(key):
    # updated on 2019/2/28 更改了支持的字段名和表名
    # updated on 2019/5/15 - 17 逐步删光，仅保留fdd_q和optm_self_made
    fdd_q_list = ['eps_basic', 'roa2', 'roa', 'roic', 'grossprofitmargin', 'optoebt', 'profittogr', 'optogr',
                  'operateexpensetogr', 'ebitdatosales', 'operateincometoebt', 'investincometoebt',
                  'nonoperateprofittoebt', 'ocftocf', 'fcftocf', 'ocftosales', 'ocftoop', 'ocftoassets',
                  'ocftodividend', 'debttoassets', 'longdebttolongcaptial', 'longcapitaltoinvestment', 'assetstoequity',
                  'catoassets', 'currentdebttoequity', 'intdebttototalcap', 'currentdebttodebt', 'ncatoequity',
                  'current', 'quick', 'ocftointerest', 'ocftodebt', 'longdebttodebt', 'cashtostdebt', 'invturn',
                  'arturn', 'caturn', 'faturn', 'apturn', 'yoyeps_basic', 'yoyocfps', 'yoy_tr', 'yoyop', 'yoyprofit',
                  'yoynetprofit', 'yoyocf', 'yoyroe', 'yoy_equity', 'yoydebt', 'yoy_assets', 'yoy_cash',
                  'yoy_fixedassets', 'stm_issuingdate', 'tot_assets', 'tot_non_cur_liab', 'tot_liab', 'tot_equity',
                  'roe_basic', 'assetsturn1', 'fcff', 'fcfe', 'qfa_operateincome', 'qfa_roe', 'qfa_roa',
                  'qfa_grossprofitmargin', 'qfa_profittogr', 'qfa_operateincometoebt', 'qfa_ocftosales', 'qfa_ocftoor',
                  'qfa_yoygr', 'qfa_yoysales', 'qfa_yoyop', 'qfa_yoyprofit', 'roe_ttm2', 'roa2_ttm2',
                  'netprofittoassets', 'roic_ttm2', 'netprofitmargin_ttm2', 'grossprofitmargin_ttm2', 'profittogr_ttm2',
                  'optogr_ttm2', 'gctogr_ttm2', 'netprofittoor_ttm', 'operateincometoebt_ttm2', 'ebttoor_ttm',
                  'ocftoor_ttm2', 'gr_ttm2', 'gc_ttm2', 'grossmargin_ttm2', 'interestexpense_ttm', 'profit_ttm2',
                  'operatecashflow_ttm2', 'cashflow_ttm2', 'operatecaptialturn', 'ebittoassets2', 'qfa_yoyeps',
                  'qfa_grossmargin', 'qfa_yoyocf', 'qfa_yoycf', 'qfa_netprofitmargin']
    optm_self_made_list = ['index_800', 'alpha_uni_large', 'alpha_uni_mid', 'alpha_uni_small']

    if key in fdd_q_list:
        path = root_013542 + "/wdb_h5/WIND/FDD_CHINA_STOCK_QUARTERLY_WIND/FDD_CHINA_STOCK_QUARTERLY_WIND.h5"
        item = "fdd_q"
    elif key in optm_self_made_list:
        path = ''
        item = 'optm_self_made'
    else:
        raise TypeError
    return path, item


def return_panel_info_complete_key_set():
    # updated on 2019/2/28 更改了支持的字段名
    # updated on 2019/9/3 新增alpha_universe_b
    key_set = ('adjfactor', 'mkt_cap_ard', 'free_float_shares', 'total_shares', 'alpha_universe',
               'risk_universe', 'alpha_universe_b', 'limit_pctg',

               'eps_basic', 'roa2', 'roa', 'roic', 'grossprofitmargin', 'optoebt', 'profittogr', 'optogr',
               'operateexpensetogr', 'ebitdatosales', 'operateincometoebt', 'investincometoebt',
               'nonoperateprofittoebt', 'ocftocf', 'fcftocf', 'ocftosales', 'ocftoop', 'ocftoassets',
               'ocftodividend', 'debttoassets', 'longdebttolongcaptial', 'longcapitaltoinvestment', 'assetstoequity',
               'catoassets', 'currentdebttoequity', 'intdebttototalcap', 'currentdebttodebt', 'ncatoequity',
               'current', 'quick', 'ocftointerest', 'ocftodebt', 'longdebttodebt', 'cashtostdebt', 'invturn',
               'arturn', 'caturn', 'faturn', 'apturn', 'yoyeps_basic', 'yoyocfps', 'yoy_tr', 'yoyop', 'yoyprofit',
               'yoynetprofit', 'yoyocf', 'yoyroe', 'yoy_equity', 'yoydebt', 'yoy_assets', 'yoy_cash',
               'yoy_fixedassets', 'stm_issuingdate', 'tot_assets', 'tot_non_cur_liab', 'tot_liab', 'tot_equity',
               'roe_basic', 'assetsturn1', 'fcff', 'fcfe', 'qfa_operateincome', 'qfa_roe', 'qfa_roa',
               'qfa_grossprofitmargin', 'qfa_profittogr', 'qfa_operateincometoebt', 'qfa_ocftosales', 'qfa_ocftoor',
               'qfa_yoygr', 'qfa_yoysales', 'qfa_yoyop', 'qfa_yoyprofit', 'roe_ttm2', 'roa2_ttm2',
               'netprofittoassets', 'roic_ttm2', 'netprofitmargin_ttm2', 'grossprofitmargin_ttm2', 'profittogr_ttm2',
               'optogr_ttm2', 'gctogr_ttm2', 'netprofittoor_ttm', 'operateincometoebt_ttm2', 'ebttoor_ttm',
               'ocftoor_ttm2', 'gr_ttm2', 'gc_ttm2', 'grossmargin_ttm2', 'interestexpense_ttm', 'profit_ttm2',
               'operatecashflow_ttm2', 'cashflow_ttm2', 'operatecaptialturn', 'ebittoassets2', 'qfa_yoyeps',
               'qfa_grossmargin', 'qfa_yoyocf', 'qfa_yoycf', 'qfa_netprofitmargin',

               'pb_lf', 'pcf_ocf_ttm', 'pe_ttm', 'ps_ttm', 'dividendyield2',

               'alpha_universe', 'index_300', 'index_50', 'index_500', 'index_weight_hs300',
               'index_weight_sh50', 'index_weight_zz500', 'risk_universe',

               'industry3',

               'Beta', 'EarningsYield', 'Growth', 'Industry', 'Leverage', 'Liquidity', 'Momentum', 'NonLinearSize',
               'ResidualVolatility', 'Size', 'Value',

               'index_800', 'alpha_uni_large', 'alpha_uni_mid', 'alpha_uni_small')
    return key_set


def unfold_df(df_input):
    """将双重索引的dataframe展开(unstack)，并将列索引的第1层去掉，只留下股票代码"""
    df = df_input.copy()
    df = df.unstack()
    col_list = list(df.columns)
    col_list2 = [item[1] for item in col_list]
    df.columns = col_list2
    return df


def get_stock_listing_date(end_date=None, drop_delisted_stocks=False):
    # 获取股票上市股票及对应的上市日期
    if os.path.exists(complete_stock_list_path):
        df = pd.read_csv(complete_stock_list_path, index_col=0)
        df = df.fillna(0)
        if drop_delisted_stocks:
            df = df[df.Delisting_date < 1]
        if end_date is None:
            return df
        else:
            df = df[(df.Listing_date <= end_date) & (df.Delisting_date <= end_date)]
            return df


def back_fill(df_fill, df_qfa, df_ann, fill_na=True):
    # 将财务数据按交易日向后填充到complete_stock_list的空表内
    """
    :param df_fill: 全样本股票列表及交易日的空表
    :param df_qfa: 财务数据表
    :param df_ann: 实际披露日期
    :param fill_na: 是否将nan值填充为0。目前万得数据库中一个报表数据不存在或值为0都会被填充为nan
    :return: 将df_fill填充完成后的Dataframe
    """
    import math
    df_fill_new = df_fill.copy()
    trading_days = list(df_fill_new.index)
    start_date = trading_days[0]
    end_date = trading_days[-1]
    trading_days_np = np.array(trading_days)
    columns = df_fill_new.columns
    index = df_fill_new.index
    df_fill_np = df_fill_new.values  # 计算时涉及到循环，采用numpy计算提高速度
    stock_listing_date = get_stock_listing_date()
    for col_i, col in enumerate(columns):
        # 如果个股在报表内
        if col in df_ann and col in df_qfa:
            listing_date = stock_listing_date.at[col, 'Listing_date']
            s_ann = df_ann[col].values
            s_ann = np.array([int(x) for x in s_ann])
            s_qfa = df_qfa[col].values
            # 将报告期list和数据list置于规定的开始日期和结束日期之内
            s_ann_temp = s_ann[(s_ann <= end_date) & ((s_ann >= start_date) & (s_ann > listing_date))]
            s_qfa_temp = s_qfa[(s_ann <= end_date) & ((s_ann >= start_date) & (s_ann > listing_date))]
            for idate in range(len(s_ann_temp)):
                # 如果非nan且非inf，则填充到披露期那一天，如果披露期非交易日，则顺延到最近的一个交易日
                if not math.isnan(s_ann_temp[idate]) and not math.isnan(s_qfa_temp[idate]) and not math.isinf(
                        s_qfa_temp[idate]):
                    ann_date = int(s_ann_temp[idate])
                    # 因为要填充到下一个发布日，所以首先判断是不是最后一个发布日
                    if idate < len(s_ann_temp) - 1:
                        # 下一个发布日的int
                        ann_date_next = int(s_ann_temp[idate + 1])
                        # 如果下一个发布日之后还有交易日的话（避免出现下一个发布日与最后一个交易日重叠的情况）
                        if np.where(trading_days_np > ann_date_next)[0].tolist() != []:
                            # 当前发布日在交易日list中的位置
                            ann_date_id = np.where(trading_days_np > ann_date)[0][0]
                            # 下一个发布日在交易日list中的位置
                            ann_date_next_id = np.where(trading_days_np > ann_date_next)[0][0]
                            # 将此两个位置之间的交易日填充为新值
                            df_fill_np[ann_date_id:ann_date_next_id, col_i] = s_qfa_temp[idate]
                        # 如果下一个交易日之后没有交易日了，也要进行填充，不然在下一步也不会填充了。
                        else:
                            # 有时年报和下一年一季报在同一天发布
                            if ann_date != ann_date_next:
                                # 当前发布日在交易日list中的位置
                                ann_date_id = np.where(trading_days_np > ann_date)[0][0]
                                # 将当前交易日之后的交易日填充
                                df_fill_np[ann_date_id:, col_i] = s_qfa_temp[idate]
                    # 如果到了最后一个发布日
                    else:
                        # 如果当前发布日之后还有交易日的话（避免出现当前发布日与最后一个交易日重叠的情况）
                        if np.where(trading_days_np > ann_date)[0].tolist() != []:
                            # 当前发布日在交易日list中的位置
                            ann_date_id = np.where(trading_days_np > ann_date)[0][0]
                            # 将当前交易日之后的交易日填充
                            df_fill_np[ann_date_id:, col_i] = s_qfa_temp[idate]
                        else:
                            pass
    df_fill_new = pd.DataFrame(df_fill_np, index=index, columns=columns)
    df_fill_new.sort_index(inplace=True)
    if fill_na:
        df_fill_new = df_fill_new.fillna(0)
    return df_fill_new


def start_date_backfill(start_date_int, back_years=0):
    # by 011672 - 向前回溯2个季度
    # revised by 006566 on 2019/4/4 - 添加back_years
    start_month = int(str(start_date_int)[4:6])
    start_year = int(str(start_date_int)[0:4])
    if 1 <= start_month <= 3:
        last_report_date = int(str(start_year - back_years - 1) + '0630')
    elif 4 <= start_month <= 6:
        last_report_date = int(str(start_year - back_years - 1) + '0930')
    elif 7 <= start_month <= 9:
        last_report_date = int(str(start_year - back_years - 1) + '1231')
    elif 10 <= start_month <= 12:
        last_report_date = int(str(start_year - back_years) + '0331')
    else:
        raise Exception('Start date error')
    last_report_date = get_n_days_off(last_report_date, -1)[0]
    return last_report_date
