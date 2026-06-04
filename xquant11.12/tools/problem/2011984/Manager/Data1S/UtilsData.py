import os
from xquant.compute.sparkmr import remote_print
from DataAPI.TradingDay import trading_day


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
    trade_dates = trading_day(start_date, end_date)
    if len(trade_dates) == 0:
        return []
    else:
        trade_dates = sorted(list(map(lambda date_int: str(date_int), trade_dates)))
    return trade_dates
