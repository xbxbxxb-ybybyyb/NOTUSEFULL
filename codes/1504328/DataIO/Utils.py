#-*- coding:utf-8 -*-
# author: 015629
# datetime:2021/3/16 15:13
import os
import pandas as pd
from xquant.compute.sparkmr import remote_print
from DataIO.TradingDay import getTradingDay


def MyPrint(x_str):
    if "RPC_DRIVER_HOST" in os.environ and "RPC_DRIVER_PORT" in os.environ:
        return remote_print(x_str)
    else:
        return print(x_str)

def get_code_type(code):
    if is_cbond_code(code):
        return "CBOND"
    else:
        return "STOCK"

def is_cbond_code(code):
    if code.endswith(".SH"):
        if code.startswith("100") or code.startswith("110") or code.startswith("113") or code.startswith("118") or code.startswith("111"):
            return True
    elif code.endswith(".SZ"):
        if code.startswith("12") or code == "117103.SZ":
            return True
    return False

def get_trading_day(start_date, end_date):
    if not isinstance(start_date, int):
        start_date = int(start_date)
    if not isinstance(end_date, int):
        end_date = int(end_date)
    trade_dates = getTradingDay(start_date, end_date)
    if len(trade_dates) == 0:
        return []
    else:
        trade_dates = sorted(list(map(lambda date_int: str(date_int), trade_dates)))
    return trade_dates

def split_calc_date_into_group(calc_date_list, max_date_num_per_task=20):
    # 按照天数将需要计算的时间段进行分组，例如，每20个交易日分一组
    group = []
    size = len(calc_date_list)
    from_index = 0
    while from_index < size:
        group.append(calc_date_list[from_index: min(size, from_index + max_date_num_per_task)])
        from_index += max_date_num_per_task
    return group

def get_cbond_stock_map(code_list, code_type="CBOND"):
    from xquant.factordata import FactorData

    fa = FactorData()

    """ 注意存在同一个正股，同一个COMPCODE对应多个CBOND的情况，比如：113020.SH, 113032.SH, 对应 601233.SH
        返回键值为CBond，值为 STOCK的字典
    """
    if isinstance(code_list, str):
        code_list = [code_list]

    if code_type == "STOCK":
        stock_info = fa.get_factor_value("WIND_AShareDescription", factors=["S_INFO_WINDCODE", "S_INFO_COMPCODE"],
                                         S_INFO_WINDCODE=code_list)
        stock_info.columns = ["STOCK", "COMPCODE"]
        s_info_compcode = stock_info["COMPCODE"].tolist()

        cbond_info = fa.get_factor_value("WIND_CCBondIssuance", factors=["S_INFO_WINDCODE", "S_INFO_COMPCODE"],
                                         S_INFO_COMPCODE=s_info_compcode, IS_CONVERTIBLE_BONDS="1")
        if cbond_info.empty:
            cbond_info = pd.DataFrame(columns=["CBOND", "COMPCODE"])
        cbond_info.columns = ["CBOND", "COMPCODE"]

    elif code_type == "CBOND":
        cbond_info = fa.get_factor_value("WIND_CCBondIssuance", factors=["S_INFO_WINDCODE", "S_INFO_COMPCODE"],
                                         S_INFO_WINDCODE=code_list, IS_CONVERTIBLE_BONDS="1")
        cbond_info.columns = ["CBOND", "COMPCODE"]
        s_info_compcode = cbond_info["COMPCODE"].tolist()

        stock_info = fa.get_factor_value("WIND_AShareDescription", factors=["S_INFO_WINDCODE", "S_INFO_COMPCODE"],
                                         S_INFO_COMPCODE=s_info_compcode)
        if stock_info.empty:
            stock_info = pd.DataFrame(columns=["STOCK", "COMPCODE"])
        stock_info.columns = ["STOCK", "COMPCODE"]

    cbond_stock_info = pd.merge(stock_info, cbond_info, on="COMPCODE", how="outer")
    cbond_stock_map = cbond_stock_info[["CBOND", "STOCK"]].set_index("CBOND")["STOCK"].to_dict()
    ### 剔除CBond为NaN键值对
    cbond_stock_map = {cb: stock for cb, stock in cbond_stock_map.items() if isinstance(cb, str) and
                       (cb.endswith(".SH") or cb.endswith(".SZ"))}
    return cbond_stock_map

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