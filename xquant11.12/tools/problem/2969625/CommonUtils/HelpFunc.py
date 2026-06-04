import pandas as pd
import datetime as dt
from xquant.factordata import FactorData
from Constants.INDEX_LIST import INDEX_LIST, SHENWAN_INDEX_LIST, THIRD_INDEX_LIST
from Constants.FUND_LIST import ETF_LIST, LOF_LIST, THIRD_ADD_STOCK_ETF_INDEX_LIST
from Constants.FUTURE_LIST import is_future_code, get_future_contract_type
from FactorDataTool.Config import CITICS_I_CODE, CITICS_II_CODE, SW_I_CODE, SW_II_CODE, SHENWAN_I_CODE, SHENWAN_II_CODE
from System.TradingDay import getTradingDay, getNDaysOff


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

def get_ndays_offset(start_date, offset=0):
    if not isinstance(start_date, int):
        start_date = int(start_date)
    start_date_offset = str(getNDaysOff(start_date, offset))
    return start_date_offset

def get_code_type(code):
    if code in INDEX_LIST + THIRD_ADD_STOCK_ETF_INDEX_LIST:
        return 'INDEX'
    elif is_cbond_code(code):
        return "CBOND"
    elif code in ETF_LIST:
        return "ETF"
    elif code in LOF_LIST:
        return "LOF"
    elif code in CITICS_I_CODE + CITICS_II_CODE + SW_I_CODE + SW_II_CODE + SHENWAN_I_CODE + SHENWAN_II_CODE:
        return "INDUSTRY"
    elif is_future_code(code):
        return "FUTURE"
    else:
        return "STOCK"
    # else:
    #     raise Exception("Not Supported Type Yet: {}".format(code))

def is_cbond_code(code):
    if code.endswith(".SH"):
        if code.startswith("100") or code.startswith("110") or code.startswith("113") or code.startswith("118") or code.startswith("111"):
            return True
    elif code.endswith(".SZ"):
        if code.startswith("12") or code == "117103.SZ":
            return True
    return False

def get_industry_type(industry_code):
    if industry_code in CITICS_I_CODE + CITICS_II_CODE:
        return "CITICS"
    elif industry_code in SW_I_CODE + SW_II_CODE:
        return "SW"
    elif industry_code in SHENWAN_I_CODE + SHENWAN_II_CODE:
        return "SHENWAN"
    else:
        raise Exception("NOT Supported Industry Code: {}".format(industry_code))

def get_index_type(index_code):
    assert index_code in INDEX_LIST + THIRD_ADD_STOCK_ETF_INDEX_LIST, "NOT Supported Index Code: {}".format(index_code)
    if index_code in SHENWAN_INDEX_LIST:
        return "SHENWAN"
    elif index_code in THIRD_INDEX_LIST + THIRD_ADD_STOCK_ETF_INDEX_LIST:
        return "THIRD"
    else:
        return "ZZ"

def split_calc_date_into_group(calc_date_list, max_date_num_per_task=20):
    # 按照天数将需要计算的时间段进行分组，例如，每20个交易日分一组
    group = []
    size = len(calc_date_list)
    from_index = 0
    while from_index < size:
        group.append(calc_date_list[from_index: min(size, from_index + max_date_num_per_task)])
        from_index += max_date_num_per_task
    return group

def generate_timestamp(date: str, time: str):
    """ time: "093015", trading_day: "20190101" """
    if len(time) == 6:
        time += "000000"
    elif len(time) == 9:
        time += "000"
    elif len(time) != 12:
        raise Exception(" Time Format Error: {} ".format(time))
    return dt.datetime.strptime("{0} {1}".format(date, time), "%Y%m%d %H%M%S%f").timestamp()

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


