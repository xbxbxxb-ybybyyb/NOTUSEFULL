import pandas as pd
import numpy as np
import os
import datetime as dt
from xquant.factordata import FactorData

def max_drawdown(capital_line):
    # return max draw down in decimal
    cline_e = pd.DataFrame(np.maximum.accumulate(capital_line) - capital_line)
    mdd_end = cline_e.idxmax().loc[0]
    # mdd_end = np.argmax(np.maximum.accumulate(capital_line) - capital_line)
    if mdd_end == 0:
        return None, None, np.nan, np.nan
    cline_s = pd.DataFrame(capital_line[:mdd_end])
    mdd_start = cline_s.idxmax().loc[0]
    # mdd_start = np.argmax(capital_line[:mdd_end])
    mdd = capital_line[mdd_start] - capital_line[mdd_end]
    mdd_ratio = (capital_line[mdd_start]-capital_line[mdd_end]) / capital_line[mdd_start]
    # print(capital_line[mdd_end], capital_line[mdd_start])
    return mdd_start, mdd_end, -mdd, mdd_ratio


def analysis_trade_summary(trade_records_df):
    """
    :param trade_records_df:  ATS线下成交数据格式
    :return:
    """
    sub_trade_records = trade_records_df[
        (trade_records_df["orderStatus"] != "CANCELLED") & (trade_records_df["orderStatus"] != "REJECTED")]
    if not sub_trade_records.empty:
        trade_summary = {}
        trade_summary["监控日期"] = sub_trade_records["tradeDate"].iloc[0]
        trade_summary["回测日期"] = sub_trade_records["tradeDate"].iloc[0]
        trade_summary["标的"] = sub_trade_records["symbol"].iloc[0]
        trade_summary["股票代码"] = sub_trade_records["symbol"].iloc[0]
        trade_summary["敞口数量"] = sub_trade_records[sub_trade_records["side"] == "BID"]["quantity"].sum() - \
                                sub_trade_records[sub_trade_records["side"] == "ASK"]["quantity"].sum()
        trade_summary["买成交金额"] = sub_trade_records[sub_trade_records["side"] == "BID"]["cumAmount"].sum()
        trade_summary["卖成交金额"] = sub_trade_records[sub_trade_records["side"] == "ASK"]["cumAmount"].sum()
        trade_summary["买成交数量"] = sub_trade_records[sub_trade_records["side"] == "BID"]["quantity"].sum()
        trade_summary["卖成交数量"] = sub_trade_records[sub_trade_records["side"] == "ASK"]["quantity"].sum()
        trade_summary["下单次数"] = trade_records_df.iloc[:, 1].count()
        trade_summary["成交次数"] = sub_trade_records.iloc[:, 1].count()
        trade_summary["撤单次数"] = trade_records_df[trade_records_df["orderStatus"] == "CANCELLED"].iloc[:, 1].count()

        if trade_summary["敞口数量"]:
            last_price = trade_records_df.iloc[-1]["price"]
            long_orders = trade_records_df[trade_records_df["side"] == "BID"].sort_values(by=["createDate"])
            short_orders = trade_records_df[trade_records_df["side"] == "ASK"].sort_values(by=["createDate"])
            if trade_summary["敞口数量"] > 0:
                accu_buy_sum = 0
                accu_sell_sum = short_orders["quantity"].sum()
                for i in range(len(long_orders)):
                    if accu_buy_sum + long_orders.iloc[i]["quantity"] <= accu_sell_sum:
                        accu_buy_sum += long_orders.iloc[i]["quantity"]
                    else:
                        break
                # 前i笔买单的数量小于等于卖单，所以用第i+1笔买单的，部分成交量配平卖成交量
                add_buy_amount = long_orders.iloc[i]["price"] * (accu_sell_sum - long_orders.iloc[:i]["quantity"].sum())
                buy_i_amount = long_orders.iloc[:i]["cumAmount"].sum()
                #                 print("buy_i_amount",buy_i_amount)
                trade_summary["买成交金额(去除敞口)"] = buy_i_amount + add_buy_amount
                trade_summary["卖成交金额(去除敞口)"] = trade_summary["卖成交金额"]

                trade_summary["回转盈亏"] = trade_summary["卖成交金额"] - (buy_i_amount + add_buy_amount)
                trade_summary["税后回转盈亏"] = trade_summary["回转盈亏"] - trade_summary["卖成交金额"] * 0.0005
                # 敞口盈亏按最后一笔成交的价格计算
                trade_summary["敞口盈亏"] = last_price * trade_summary["敞口数量"] - long_orders.iloc[i:][
                    "cumAmount"].sum() + add_buy_amount
                trade_summary["税后收益率"] = round(trade_summary["税后回转盈亏"] / trade_summary["卖成交金额"], 6) if trade_summary[
                    "卖成交金额"] else 0
                trade_summary["年化收益率"] = trade_summary["税后收益率"] * 252
            else:
                accu_buy_sum = long_orders["quantity"].sum()
                accu_sell_sum = 0
                for i in range(len(short_orders)):
                    if accu_sell_sum + short_orders.iloc[i]["quantity"] <= accu_buy_sum:
                        accu_sell_sum += short_orders.iloc[i]["quantity"]
                    else:
                        break
                # 前i比卖单的数量小于等于买单，所以用第i+1笔卖单，部分成交量配平卖成交量
                add_sell_amount = short_orders.iloc[i]["price"] * (
                            accu_buy_sum - short_orders.iloc[:i]["quantity"].sum())
                sell_i_amount = short_orders.iloc[:i]["cumAmount"].sum()
                trade_summary["买成交金额(去除敞口)"] = trade_summary["买成交金额"]
                trade_summary["卖成交金额(去除敞口)"] = sell_i_amount + add_sell_amount

                trade_summary["回转盈亏"] = (sell_i_amount + add_sell_amount) - (trade_summary["买成交金额"])
                trade_summary["税后回转盈亏"] = trade_summary["回转盈亏"] - trade_summary["卖成交金额(去除敞口)"] * 0.0005
                # 敞口盈亏按最后一笔成交的价格计算
                trade_summary["敞口盈亏"] = short_orders.iloc[i:]["cumAmount"].sum() - add_sell_amount - last_price * abs(
                    trade_summary["敞口数量"])
                trade_summary["税后收益率"] = round(trade_summary["税后回转盈亏"] / trade_summary["卖成交金额(去除敞口)"], 6) if (
                            sell_i_amount + add_sell_amount) else 0
                trade_summary["年化收益率"] = trade_summary["税后收益率"] * 252

            # trade_summary["税前盈亏(去除敞口)"] = trade_summary["税前盈亏"]+trade_summary["敞口数量"]*last_price
            # trade_summary["税后盈亏(去除敞口)"] = trade_summary["税后盈亏"]+trade_summary["敞口数量"]*last_price
            # trade_amount_open_posion = trade_summary["敞口数量"]*last_price if trade_summary["敞口数量"]>0 else 0
            # trade_amount = trade_summary["卖成交金额"] +trade_amount_open_posion
            # trade_summary["税后收益率"] = round(trade_summary["税后盈亏(去除敞口)"]/trade_amount,6) if trade_amount else 0
            # trade_summary["年化收益率"] = trade_summary["税后收益率"]*252
        else:
            trade_summary["买成交金额(去除敞口)"] = trade_summary["买成交金额"]
            trade_summary["卖成交金额(去除敞口)"] = trade_summary["卖成交金额"]

            trade_summary["回转盈亏"] = trade_summary["卖成交金额"] - trade_summary["买成交金额"]
            trade_summary["税后回转盈亏"] = trade_summary["卖成交金额"] * 0.9995 - trade_summary["买成交金额"]
            trade_summary["敞口盈亏"] = 0
            trade_amount = trade_summary["卖成交金额"]  # +trade_records_df[trade_records_df.Side==1].CumAmount.sum()
            trade_summary["税后收益率"] = round(trade_summary["税后回转盈亏"] / trade_amount, 6) if trade_amount else 0
            trade_summary["年化收益率"] = trade_summary["税后收益率"] * 252
        return pd.DataFrame(trade_summary, index=[0])
    else:
        return pd.DataFrame(
            columns=['标的', '监控日期', '敞口数量',
                     '买成交金额', '卖成交金额','买成交数量', '卖成交数量', '下单次数', '成交次数', '撤单次数',
                     '买成交金额(去除敞口)', '卖成交金额(去除敞口)', '回转盈亏','税后回转盈亏',	'敞口盈亏',	'税后收益率', '年化收益率'])



def analysis_total_trade_summray(daily_trade_summary, daily_market_df = pd.DataFrame()):
    result_list = []
    backtest_result = daily_trade_summary
    if "股票代码" in backtest_result.columns:
        backtest_result["标的"] = backtest_result["股票代码"]
    symbol = backtest_result["标的"].iloc[0]
    if not symbol.endswith("SH") and not symbol.endswith("SZ"):
        raise Exception("股票代码必须以SZ或SH结尾！")
    backtest_result["Date"] = backtest_result["监控日期"].apply(lambda x: pd.to_datetime(x).strftime("%Y%m%d"))
    backtest_result = backtest_result.set_index("Date")
    try:
        backtest_result.drop(columns="Unnamed: 0")
    except:
        pass

    start_date, end_date = backtest_result["监控日期"].min(), backtest_result["监控日期"].max()
    start_date, end_date = pd.to_datetime(start_date).strftime("%Y%m%d"), pd.to_datetime(end_date).strftime(
        "%Y%m%d")

    if not daily_market_df.empty:
        market_df = daily_market_df[(daily_market_df["MDTime"] >= "093000000") & (daily_market_df["MDTime"] <= "150000000")]
        initial_price = daily_market_df["PreClosePx"].iloc[0]
        if not "max_price" in backtest_result.columns:
            max_price = market_df.loc[:, ["MDDate", "LastPx"]].groupby("MDDate").max()
            min_price = market_df.loc[:, ["MDDate", "LastPx"]].groupby("MDDate").min()
            tol_volume = market_df.loc[:, ["MDDate", "TotalVolumeTrade"]].groupby("MDDate").last()

            amp_price = max_price - min_price
            std_price = market_df.loc[:, ["MDDate", "LastPx"]].groupby("MDDate").std()

            analysis_df = pd.concat([tol_volume, std_price, max_price, min_price, amp_price], axis=1)
            analysis_df.columns = ["tol_volume", "std_price", "max_price", "min_price", "amp_price"]

            backtest_result = pd.merge(backtest_result, analysis_df, left_index=True, right_index=True)
        else:
            print("行情数据分析已添加。")
    else:
        fa = FactorData()
        days = fa.tradingday(start_date, end_date)
        factor_df = fa.get_factor_value("Basic_factor", [symbol], days, ["pre_close", "close"])
        initial_price = factor_df["pre_close"].iloc[0]


    if not "税后回转盈亏" in backtest_result.columns:
        backtest_result["卖成交数量"] = backtest_result["卖成交金额"] / backtest_result["逐笔成交价"]
        backtest_result["税后回转盈亏"] = backtest_result["回转盈亏"] - backtest_result["卖成交金额"] * 0.0005
        sum_amount = backtest_result["卖成交金额"]
        backtest_result["税后回转盈亏收益率"] = backtest_result["税后回转盈亏"] / sum_amount
        backtest_result["税后回转盈亏收益率"] = backtest_result["税后回转盈亏收益率"].replace(np.nan, 0)
        # print(backtest_result["税后回转盈亏收益率"])
        backtest_result["税后回转盈亏收益率(年化)"] = backtest_result["税后回转盈亏收益率"] * 252
    else:
        pass
        # print("绩效分析已添加。")


    # 胜率、盈亏比、行情波动率
    win_time = (backtest_result["回转盈亏"] > 0).sum()
    lose_time = (backtest_result["回转盈亏"] < 0).sum()
    win_amount = (backtest_result[backtest_result["回转盈亏"] > 0])["回转盈亏"].sum()
    lose_amount = (backtest_result[backtest_result["回转盈亏"] < 0])["回转盈亏"].sum()

    win_time_after = (backtest_result["税后回转盈亏"] > 0).sum()
    lose_time_after = (backtest_result["税后回转盈亏"] < 0).sum()
    win_amount_after = (backtest_result[backtest_result["税后回转盈亏"] > 0])["税后回转盈亏"].sum()
    lose_amount_after = (backtest_result[backtest_result["税后回转盈亏"] < 0])["税后回转盈亏"].sum()

    win_rate = round(win_time / (win_time + lose_time), 2)
    win_amount_ratio = -round(win_amount / lose_amount, 2)

    win_rate_after = round(win_time_after / (win_time_after + lose_time_after), 2)
    win_amount_ratio_after = -round(win_amount_after / lose_amount_after, 2)

    winmoney = round(backtest_result["回转盈亏"].mean(), 1)
    winmoney_after = round(backtest_result["税后回转盈亏"].mean(), 1)
    amount_avg = round(backtest_result["卖成交金额"].mean(), 1)
    volume_avg = round(backtest_result["卖成交数量"].mean(), 1)
    tradetime_avg = round(backtest_result["下单次数"].mean(), 1)
    position_avg = round(backtest_result["敞口数量"].mean(), 1)

    _, _, mdd, mdd_ratio = max_drawdown(backtest_result["税后回转盈亏"].cumsum().values)

    profit_10, profit_90 = backtest_result["税后回转盈亏"].sort_values().quantile([0.1, 0.9])
    profit_10_avg = backtest_result[backtest_result["税后回转盈亏"] <= profit_10]["税后回转盈亏"].mean()
    profit_90_avg = backtest_result[backtest_result["税后回转盈亏"] >= profit_90]["税后回转盈亏"].mean()

    profit_5, profit_95 = backtest_result["税后回转盈亏"].sort_values().quantile([0.05, 0.95])
    profit_5_avg = backtest_result[backtest_result["税后回转盈亏"] <= profit_5]["税后回转盈亏"].mean()
    profit_95_avg = backtest_result[backtest_result["税后回转盈亏"] >= profit_95]["税后回转盈亏"].mean()

    # 20231124 add by fqs Get max amount as Dicang
    max_sell_volume = np.max(backtest_result["卖成交数量"])
    name = backtest_result["标的"].iloc[0]
    useage_ratio = volume_avg/ max_sell_volume
    re_by_useage = 252*winmoney_after/(initial_price * max_sell_volume)
    re_by_volume = 252*winmoney_after/amount_avg 

    analysis_dict = {
                     "名称": name,
                     "回测开始时间":start_date,
                     "回测结束时间":end_date,
                     "日均成交额": amount_avg,
                     "日均成交量": volume_avg,
                     # "日胜率_税前": win_rate,
                     # "日盈亏比_税前": win_amount_ratio,
                     "日均收益_税前": winmoney,
                     "日均收益_税后": winmoney_after,
                     "最大回撤": mdd,
                     "最大底仓年化收益率": re_by_useage,
                     "年化收益率":re_by_volume,
                    "底仓初始价格": initial_price,
                    "最大底仓": max_sell_volume * initial_price,
                    "底仓使用率": useage_ratio,
                    "日胜率_税后": win_rate_after,
                    "日盈亏比_税后": win_amount_ratio_after,
                    "日均下单次数": tradetime_avg,
                    "日均敞口数量": position_avg,
                    "top5%日均收益_税后": profit_95_avg,
                    "top10%日均收益_税后": profit_90_avg,
                    "bottom5%日均收益_税后": profit_5_avg,
                    "bottom10%日均收益_税后": profit_10_avg,
                    "标的": name,
    }

    result_list.append(analysis_dict)
    result_df = pd.DataFrame(result_list)
    return  result_df
