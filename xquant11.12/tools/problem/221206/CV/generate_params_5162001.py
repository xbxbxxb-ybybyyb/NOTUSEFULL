import os
import json
import shutil
import math
import pandas as pd
import DataAPI.DataToolkit as dtk
import DataAPI.GetTradingDay
from typing import List
from copy import deepcopy

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


def generate_target_qty_interval(symbol, quantity, today, period):
    timetable_raw = key_minutes()
    qty_pct_dict = target_qty_pct(symbol, today, today, period)

    qty_pct = qty_pct_dict[today]
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

    result = [{"Time": v1, "TargetQty": str(v2)} for v1, v2 in zip(timetable, qty_interval_list)]

    return result


def main():
    portfolio = "5162001"
    next_trading_day = "20191206"
    today = "20191205"
    period = 20

    start_date_customized = "20190916"
    end_date_customized = "20191129"

    start_date = "20190701"
    end_date = "20190831"

    portfolio_path = "/data/user/666888/Apollo/portfolios/{}/morning/".format(next_trading_day)
    output_path = "/data/user/666888/Apollo/parameters/Apollo_{}/{}/".format(next_trading_day, portfolio)
    param_path_universal = "/data/user/666888/Apollo/cv_results/results/{}-{}_universal/".format(start_date, end_date)
    param_path_customized = "/data/user/666888/Apollo/cv_results/results/{}-{}_{}/{}/".format(
        start_date_customized, end_date_customized, next_trading_day, portfolio
    )

    json_param = {
        "因子计算上午开始时间": "09:30:15",
        "因子计算上午结束时间": "11:30:00",
        "因子计算下午开始时间": "13:00:15",
        "因子计算下午结束时间": "14:56:59",
        "允许开仓起始时间": "09:30:00",
        "允许开仓结束时间": "14:57:00",
        "有效tick上午开始时间": "09:30:00",
        "有效tick上午结束时间": "11:29:59",
        "有效tick下午开始时间": "13:00:00",
        "有效tick下午结束时间": "14:56:59",
        "策略开始时间": "09:30:00",
        "策略结束时间": "14:56:59",
        "信号有效上午开始时间": "09:31:15",
        "信号有效上午结束时间": "11:29:59",
        "信号有效下午开始时间": "13:01:15",
        "信号有效下午结束时间": "14:56:59",
        "闭市区间上午开始时间": "11:29:00",
        "闭市区间上午结束时间": "11:30:00",
        "闭市区间下午开始时间": "14:56:00",
        "闭市区间下午结束时间": "14:57:00",
        "区间结束时间长度": "30",
        "区间结束激进下单时间长度": "15",
        "priceMulti": "0.0002",
        "priceLimitMulti": "0.002",
        "marketClosePriceMulti": "0.012",
        "最大需更新Tick数量": "3",
        "是否强制加载历史数据": "true",
        "模型目录": "resources/StrategyModel/apple",
        "是否使用通用模型": "true",
        "FrozenConfig": "0x0a, 0x07, 0x0a, 0x03, 0x43, 0x50, 0x55, 0x10, 0x06",
        "单笔最大委托金额": "1800000",
        "单笔最大报单量": "1000000",
        "涨跌停最大委托金额": "1800000",
        "下单价格最大偏离度": "0.012",
        "最大可接受系统延迟秒数": "20",
        "提前闭市区间下午开始时间": "14:30:00",
        "priceCutOff": "25",
        "ChaosNum": "20",
        "上午截止时间1": "11:25:00",
        "上午截止时间2": "11:28:00",
        "上午截止时间3": "11:29:00",
        "下午截止时间": "14:52:00",
        "下单模块名": "EZNew",
        "是否使用RemoveSelfOrder": "true"
    }

    if not os.path.exists(output_path):
        os.makedirs(output_path)
    else:
        shutil.rmtree(output_path)
        os.makedirs(output_path)

    portfolio_orders = pd.read_excel(portfolio_path + "Apollo_" + portfolio + "_" + next_trading_day + ".xlsx")
    portfolio_codes = portfolio_orders.iloc[:, 0].tolist()
    portfolio_quantities = (portfolio_orders.iloc[:, 3] - portfolio_orders.iloc[:, 4]).tolist()

    try:
        portfolio_customized_triggers = pd.read_excel(param_path_customized + "/TotalSummary.xlsx", index_col=0)
    except:
        portfolio_customized_triggers = None
    portfolio_universal_triggers_buy = pd.read_excel(param_path_universal + "/buy/TotalSummary.xlsx", index_col=0)
    portfolio_universal_triggers_sell = pd.read_excel(param_path_universal + "/sell/TotalSummary.xlsx", index_col=0)

    no_trigger_stocks = []

    for code, quantity in zip(portfolio_codes, portfolio_quantities):
        try:
            lt = portfolio_customized_triggers.loc[code, "longAggressiveRatio"]
            lc = portfolio_customized_triggers.loc[code, "longPassiveRatio"]
            st = portfolio_customized_triggers.loc[code, "shortAggressiveRatio"]
            sc = portfolio_customized_triggers.loc[code, "shortPassiveRatio"]
        except (KeyError, AttributeError):
            print("No customized triggers for {}, try to use universal triggers instead".format(code))
            try:
                if quantity > 0:
                    lt = portfolio_universal_triggers_buy.loc[code, "longAggressiveRatio"]
                    lc = portfolio_universal_triggers_buy.loc[code, "longPassiveRatio"]
                    st = portfolio_universal_triggers_buy.loc[code, "shortAggressiveRatio"]
                    sc = portfolio_universal_triggers_buy.loc[code, "shortPassiveRatio"]
                elif quantity < 0:
                    lt = portfolio_universal_triggers_sell.loc[code, "longAggressiveRatio"]
                    lc = portfolio_universal_triggers_sell.loc[code, "longPassiveRatio"]
                    st = portfolio_universal_triggers_sell.loc[code, "shortAggressiveRatio"]
                    sc = portfolio_universal_triggers_sell.loc[code, "shortPassiveRatio"]
                else:
                    print("Zero quantity for {}".format(code))
                    continue
            except KeyError:
                print("No universal triggers for {} either".format(code))
                no_trigger_stocks.append(code)
                continue

        json_param_tmp = deepcopy(json_param)
        json_param_tmp["历史数据日期"] = today[:4] + "-" + today[4:6] + "-" + today[6:]
        json_param_tmp["longAggressiveRatio"] = str(lt)
        json_param_tmp["longPassiveRatio"] = str(lc)
        json_param_tmp["shortAggressiveRatio"] = str(st)
        json_param_tmp["shortPassiveRatio"] = str(sc)
        json_param_tmp["目标持仓"] = generate_target_qty_interval(code, quantity, int(next_trading_day), period)

        with open(output_path + code + ".json", "w", encoding="utf-8") as f:
            json.dump(json_param_tmp, f, ensure_ascii=False)

    if no_trigger_stocks:
        no_trigger_stocks_path = "/data/user/666888/Apollo/no_trigger_stocks/{}/".format(next_trading_day)
        if not os.path.exists(no_trigger_stocks_path):
            os.makedirs(no_trigger_stocks_path)
        pd.Series(no_trigger_stocks).to_csv(no_trigger_stocks_path + portfolio + ".csv", index=False)


if __name__ == "__main__":
    main()
