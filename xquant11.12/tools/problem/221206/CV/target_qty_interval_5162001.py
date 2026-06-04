import json
import math
import datetime as dt
import pandas as pd
import DataAPI.DataToolkit as dtk
import DataAPI.GetTradingDay
from typing import List
from xquant.pyfile import Pyfile

last_interval_time1 = "14:55:30"
last_interval_time2 = "14:56:00"


def key_minutes():
    minutes = ["09:31:15", "09:40:00", "09:50:00", "10:00:00", "10:10:00", "10:20:00", "10:30:00", "10:40:00",
               "10:50:00", "11:00:00", "11:10:00", "11:20:00", "13:00:00", "13:01:15", "13:10:00", "13:20:00",
               "13:30:00", "13:40:00", "13:50:00", "14:00:00", "14:10:00", "14:20:00", "14:30:00", "14:40:00",
               "14:50:00", "15:00:00"]
    return minutes


def trading_dates(s_date: int, e_date: int) -> List[int]:
    trading_days = DataAPI.GetTradingDay.trading_day_list
    dates = [x for x in trading_days if s_date <= x <= e_date]
    return dates


def non_suspend_start_date(symbol, s_date, period) -> int:
    trading_days = DataAPI.GetTradingDay.trading_day_list
    index = 0
    while trading_days[index] < s_date:
        index += 1
    start = index - period + 1
    end = index - 1
    count = -1
    while count != period:
        start -= 1
        amts = dtk.get_panel_daily_pv_df([symbol], trading_days[start], trading_days[end], "amt")
        count = amts.astype(bool)[symbol].sum()
    return trading_days[start]


def is_suspended(df: pd.DataFrame, date: int) -> bool:
    return df.loc[date]["amt"].sum() == 0


def real_lb_period(df: pd.DataFrame, date: int, period: int) -> List[int]:
    dates = df.index.get_level_values("dt").unique()
    real = []
    index = 0
    while dates[index] < date:
        index += 1
    while len(real) != period:
        index -= 1
        d = dates[index]
        if not is_suspended(df, d):
            real.append(d)
    real.sort()
    return real


def daily_volume_list(df: pd.DataFrame):
    volumes = []
    minutes = key_minutes()
    minutes = list(map(lambda x: int(x[:2] + x[3:5]), minutes))
    pre = None
    for minute in minutes:
        s_index = df.index.get_loc(pre) if pre is not None else 0
        e_index = df.index.get_loc(minute)
        volume = df.iloc[s_index: e_index]["volume"].sum()
        volumes.append(volume)
        pre = minute
    assert len(volumes) == len(minutes)
    return volumes


def target_qty_pct(symbol, s_date, e_date, period=3):
    output = {}  # key = date, value = [target pct of qty each (10 min) interval]
    trading_d = trading_dates(s_date, e_date)
    if not trading_d:
        raise Exception("No trading days in the period: {}-{}".format(str(s_date), str(e_date)))
    real_s_date = non_suspend_start_date(symbol, trading_d[0], period)
    data = dtk.get_single_stock_minute_data2(symbol, real_s_date, trading_d[-1])
    for date in trading_d:
        real_t_dates = real_lb_period(data, date, period)
        df_list = []
        for t_date in real_t_dates:
            daily_df = data.loc[t_date]
            volumes = daily_volume_list(daily_df)
            df_list.append(volumes)
        df_summary = pd.DataFrame(df_list)
        df_summary = df_summary.transpose()
        df_summary = df_summary.sum(axis=1)
        df_summary["pct"] = df_summary.iloc[:] / df_summary.sum()
        pct_list = df_summary["pct"].cumsum().tolist()
        pct_list[0] = min(math.ceil(pct_list[0] * 100) / 100, pct_list[1])
        pct_list[-1] = 1
        output.update({date: pct_list})
    return output


def generate_target_qty_on_pct(target_qty, pct):
    target_qty_list = []
    for i in range(len(pct)):
        if i == 0:
            value = target_qty * pct[i]
            value = int(value / 100) * 100
        else:
            value = target_qty * pct[i] - sum(target_qty_list)
            value = int(value / 100) * 100
        target_qty_list.append(value)
    assert sum(target_qty_list) == int(target_qty / 100) * 100
    return target_qty_list


def generate_target_qty_interval(cv_info_dir, output_dir, json_filename, s_date, e_date, period):
    py = Pyfile()
    with py.open(cv_info_dir + json_filename) as f:
        quantity_dict = json.load(f)["quantity"]

    symbols = list(quantity_dict.keys())
    symbols.sort()
    symbols = symbols[:]

    total_num = len(symbols)
    curr_num = 1
    for symbol in symbols:
        time1 = dt.datetime.now()

        result = {}
        if 300000 <= int(symbol[0:6]) <= 399999:
            result["Holo"] = "true"
        else:
            result["Holo"] = "false"

        quantity = abs(quantity_dict[symbol])
        timetable_raw = key_minutes()
        qty_pct_dict = target_qty_pct(symbol, s_date, e_date, period)

        qty_interval_dict = {}
        timetable_dict = {}
        for date in qty_pct_dict.keys():
            qty_pct = qty_pct_dict[date]
            qty_table = generate_target_qty_on_pct(quantity, qty_pct)

            qty_interval_list = []
            timetable = []
            for i in range(len(qty_table)):
                if qty_table[i] != 0:
                    timetable.append(timetable_raw[i])
                    qty_interval_list.append(sum(qty_table[:i + 1]))

            if "09:31:15" not in timetable:
                timetable.insert(0, "09:31:15")
                qty_interval_list.insert(0, 0)

            if "15:00:00" not in timetable:
                timetable.append("15:00:00")
                qty_interval_list.append(int(quantity / 100) * 100)

            timetable.insert(-1, last_interval_time1)
            qty_interval_list.insert(-1, qty_interval_list[-1])
            timetable.insert(-1, last_interval_time2)
            qty_interval_list.insert(-1, qty_interval_list[-1])

            timetable_dict[date] = timetable
            qty_interval_dict[date] = qty_interval_list

        result["TimeTable"] = timetable_dict
        result["TargetQtyInterval"] = qty_interval_dict

        with py.open(output_dir + "/" + symbol + ".json", "wb") as f:
            json.dump(result, f)

        time2 = dt.datetime.now()
        print("{} time cost: {}s, {}/{}".format(symbol, (time2 - time1).total_seconds(), curr_num, total_num))

        curr_num += 1


def main():
    portfolio = "5162001"
    next_trading_day = "20191206"
    s_date = 20190916
    e_date = 20191129
    period = 20

    cv_info_dir = "Apollo/cv_info/{}-{}_{}/{}/".format(s_date, e_date, next_trading_day, portfolio)
    output_dir = "Apollo/cv_params/{}-{}_{}/{}/".format(s_date, e_date, next_trading_day, portfolio)
    json_filename = "{}_quantity.json".format(portfolio)

    generate_target_qty_interval(cv_info_dir, output_dir, json_filename, s_date, e_date, period)


if __name__ == "__main__":
    main()
