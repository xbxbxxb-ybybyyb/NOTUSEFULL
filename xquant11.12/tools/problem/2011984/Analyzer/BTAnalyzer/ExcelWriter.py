"""update at 2022.1.12"""

import copy
import datetime
import numpy as np
import pandas as pd
from DataAPI.DataTools import get_stock_daily_result
from xquant.xqutils.xqfile import HDFSFile


def trading_evaluate(trading_order, init_qty, code, st_date, cost_rate, show):
    threshold = 0.001  # 盈利阈值
    trigger_times = trading_order["order"].__len__()  # 触发次数
    win_times = 0  # 获利次数
    win_rate = 0  # 胜率
    times_per_day = 0  # 日均开仓次数
    long_times = 0  # 开多仓次数
    short_times = 0  # 开空仓次数
    average_return_rate = 0  # 平均收益率
    average_return_rate_profit = 0  # 平均获利收益率
    average_return_rate_loss = 0  # 平均亏损收益率
    profit_loss_ratio = 0  # 盈亏比
    max_loss = 0  # 最大亏损
    average_position_time = 0  # 平均持仓时间
    after_cost_profit = 0  # 算上手续费的总盈亏
    ave_daily_cum_amount = 0  # 日均成交额
    max_daily_cum_amount = 0  # 最大日成交额
    annual_return_mv = 0  # 年化市值收益率
    average_trading_return_rate = 0  # 交易收益率
    day_winning_rate = 0  # 日胜率
    cum_open_amount = 0

    pre_close = get_stock_daily_result([code], [st_date], ['pre_close'])['pre_close'].values[0]
    if isinstance(init_qty, dict):
        init_amt = pre_close * max(init_qty.values())
    else:
        init_amt = pre_close * init_qty

    if trigger_times != 0:
        win_rate = win_times / trigger_times
        cum_open_amount = trading_order["cumOpenAmount"]
        pre_cost_profit = trading_order["preCostProfit"]
        after_cost_profit = pre_cost_profit - cost_rate * cum_open_amount
        after_cost_profit = round(after_cost_profit, 2)
        day_counts = trading_order["dayCounts"]
        if day_counts != 0:
            ave_daily_cum_amount = cum_open_amount / day_counts
            for item in trading_order["dailyOpenAmount"].values():
                if item > max_daily_cum_amount:
                    max_daily_cum_amount = item
            annual_return_mv = after_cost_profit / init_amt / day_counts * 250
            after_cost_daily_profit = trading_order["afterCostDailyProfit"]
            day_winning_times = 0
            for daily_profit in after_cost_daily_profit.values():
                if daily_profit > 0:
                    day_winning_times += 1
            day_winning_rate = day_winning_times / len(after_cost_daily_profit.values())

        if day_counts != 0:
            times_per_day = trigger_times / day_counts
    if trigger_times > 0:
        for order in trading_order["order"]:
            if show:
                print(order)
            # 计算持仓时间(min)
            start_time = datetime.datetime.strptime(order["startTime"], "%m/%d/%y-%H:%M:%S")
            end_time = datetime.datetime.strptime(order["endTime"], "%m/%d/%y-%H:%M:%S")
            if start_time.hour <= 11 and end_time.hour >= 13:
                average_position_time += (end_time - start_time).seconds / 60 - 90
            else:
                average_position_time += (end_time - start_time).seconds / 60
            # 计算开多和开空次数
            if order["direction"] == 'long ':
                long_times += 1
            else:
                short_times += 1
            # 计算收益率相关值
            if np.isinf(order['returnRate']):
                continue
            average_return_rate += order["returnRate"]
            if order["returnRate"] > threshold:
                win_times += 1
                average_return_rate_profit += order["returnRate"] - threshold
            else:
                average_return_rate_loss += order["returnRate"] - threshold
                if order["returnRate"] < max_loss:
                    max_loss = order["returnRate"]
        average_position_time /= trigger_times
        win_rate = win_times / trigger_times
        average_return_rate /= trigger_times
        if win_times > 0:
            average_return_rate_profit /= win_times
        if trigger_times > win_times:
            average_return_rate_loss /= (trigger_times - win_times)
            if abs(average_return_rate_loss) > 0:
                profit_loss_ratio = average_return_rate_profit / abs(average_return_rate_loss)
    trading_order.update({"triggerTimes": trigger_times})
    trading_order.update({"timesPerDay": times_per_day})
    trading_order.update({"winTimes": win_times})
    trading_order.update({"winRate": win_rate})
    trading_order.update({"longTimes": long_times})
    trading_order.update({"shortTimes": short_times})
    trading_order.update({"averageReturnRate": average_return_rate})
    trading_order.update({"averageReturnRateProfit": average_return_rate_profit})
    trading_order.update({"averageReturnRateLoss": average_return_rate_loss})
    trading_order.update({"profitLossRatio": profit_loss_ratio})
    trading_order.update({"maxLoss": max_loss})
    trading_order.update({"averagePositionTime": average_position_time})

    if cum_open_amount != 0:
        average_trading_return_rate = after_cost_profit / cum_open_amount
    trading_order.update({"dayWinningRate": day_winning_rate})
    trading_order.update({"averageTradingReturnRate": average_trading_return_rate})
    trading_order.update({"afterCostProfit": after_cost_profit})
    trading_order.update({"initQty": init_qty})
    trading_order.update({'initAmount': init_amt})
    trading_order.update({"aveDailyCumAmount": ave_daily_cum_amount})
    trading_order.update({"maxDailyCumAmount": max_daily_cum_amount})
    trading_order.update({"annualReturnMV": annual_return_mv})
    return trading_order


def output_spread_sheet(detailed_orders, result, dir_path, dfs):
    detailed_orders_df = output_detailed_orders(detailed_orders)
    result_orders_df = output_result_orders(result)
    date_df = output_date(result_orders_df, result)
    summary_df = output_summary(result)
    py = HDFSFile(dfs=dfs)
    if py.exists(dir_path):
        py.delete(dir_path)

    with py.open(dir_path, 'wb') as f:
        writer = pd.ExcelWriter(f)
        detailed_orders_df.to_excel(writer, sheet_name='detailedOrders', index=False)
        result_orders_df.to_excel(writer, sheet_name='orders', index=False)
        date_df.to_excel(writer, sheet_name='dailyInfo', index=False)
        summary_df.to_excel(writer, sheet_name='summary', index=False)
        writer.save()
        writer.close()


def output_detailed_orders(detailed_orders):
    col_names = ['tradeNo', 'code', 'orderTime', 'direction', 'price', 'quantity',
                 'avgPrice', 'cumQty', 'status', 'orderAmount', 'cumAmount']
    res_list = []
    for i, sub_ in enumerate(detailed_orders):
        for sub2 in sub_:
            sub2.update({'tradeNo': i + 1})
        res_list.extend(sub_)
    if len(res_list) > 0:
        res_df = pd.DataFrame(res_list)[col_names]
    else:
        res_df = pd.DataFrame(columns=col_names)
    return res_df


def output_result_orders(result):
    col_names = ['code', 'date', 'startTime', 'endTime', 'holdTime', 'direction', 'startPrice',
                 'endPrice', 'orderAmount', 'cumAmount', 'returnRate', 'afterCostProfit']
    orders = result.get('order')
    res_list = []
    for i in range(len(orders)):
        start_time = datetime.datetime.strptime(orders[i].get('startTime'), '%m/%d/%y-%H:%M:%S')
        end_time = datetime.datetime.strptime(orders[i].get('endTime'), '%m/%d/%y-%H:%M:%S')
        date = str(start_time).split(" ")[0]
        orders_data_daily = [orders[i].get('code'), date, str(start_time).split(" ")[1], str(end_time).split(" ")[1],
                             str(end_time - start_time), orders[i].get('direction'), orders[i].get('startPrice'),
                             orders[i].get('endPrice'), orders[i].get('orderAmount'), orders[i].get('cumAmount'),
                             orders[i].get('returnRate') - 0.0001, orders[i].get('afterCostProfit')]
        res_list.append(orders_data_daily)
    order_df = pd.DataFrame(res_list, columns=col_names)
    return order_df


def output_date(orders_data, result):
    date_title_list = ['日期', '总市值', '总盈利', '交易次数', '获利次数', '胜率', '平均收益率', '利用率',
                       '交易总市值', '市值收益率', '获利收益率', '亏损收益率', '盈亏比',
                       '最大单笔亏损', '平均持仓时间', '撤单比']
    stock_size = result['initAmount']

    if orders_data.empty:
        return pd.DataFrame(columns=date_title_list)
    date_list = sorted(np.unique(orders_data["date"]))

    res_list = []
    for i in range(len(date_list)):
        date = date_list[i]
        daily_data = orders_data[orders_data["date"] == date]

        after_cost_profit = sum(daily_data["afterCostProfit"])
        trigger_times = daily_data.shape[0]
        win_times = sum(daily_data["afterCostProfit"] > 0)
        win_rate = win_times / trigger_times
        daily_open_amount = sum(daily_data["cumAmount"])

        after_cost_profit_earn = sum(daily_data[daily_data["afterCostProfit"] > 0]["afterCostProfit"])
        after_cost_profit_loss = sum(daily_data[daily_data["afterCostProfit"] < 0]["afterCostProfit"])
        daily_open_amount_earn = sum(daily_data[daily_data["afterCostProfit"] > 0]["cumAmount"])
        daily_open_amount_loss = sum(daily_data[daily_data["afterCostProfit"] < 0]["cumAmount"])
        earn_return_rate = after_cost_profit_earn / daily_open_amount_earn if daily_open_amount_earn != 0 else 0
        loss_return_rate = after_cost_profit_loss / daily_open_amount_loss if daily_open_amount_loss != 0 else 0
        earn_loss_rate = round(-after_cost_profit_earn / after_cost_profit_loss, 2) if after_cost_profit_loss != 0 else "nan"

        hold_time = list(daily_data["holdTime"])
        for m in range(len(hold_time)):
            hold_time[m] = t2m(hold_time[m])
        ave_hold_time = np.mean(hold_time)
        ave_hold_time = m2t(ave_hold_time)

        daily_info_data = [date, stock_size, after_cost_profit, trigger_times, win_times,
                           str(int(win_rate * 100)) + "%",
                           round(after_cost_profit / daily_open_amount * 1000, 2),
                           str(int(daily_open_amount / stock_size * 100)) + "%", daily_open_amount,
                           round(after_cost_profit / stock_size * 1000, 2),
                           round(earn_return_rate * 1000, 2), round(loss_return_rate * 1000, 2), earn_loss_rate,
                           round(min(0, min(daily_data["returnRate"])) * 1000, 2), ave_hold_time,
                           result['dailyCancelledRatio'][date]]
        res_list.append(daily_info_data)
    res_df = pd.DataFrame(res_list, columns=date_title_list)
    return res_df


def output_summary(result):
    date_title_list = ['date', 'preCostDailyProfit', 'afterCostDailyProfit', 'dailyOpenAmount', 'dailyCancelledRatio']
    temp_result = copy.deepcopy(result)
    temp_result.pop('order', None)
    for i in range(len(date_title_list)):
        temp_result.pop(date_title_list[i], None)
    res_df = pd.DataFrame([temp_result])
    return res_df


def t2m(t):
    h, m, s = t.strip().split(":")
    return int(h) * 60 + int(m) + int(s) / 60


def m2t(t):
    m = int(t)
    s = int((t - m) * 60)
    h = int(m / 60)
    m = m - h * 60
    ss = str(s)
    mm = str(m)
    if len(ss) == 1:
        ss = "0" + ss
    if len(mm) == 1:
        mm = "0" + mm
    return str(h) + ":" + mm + ":" + ss
