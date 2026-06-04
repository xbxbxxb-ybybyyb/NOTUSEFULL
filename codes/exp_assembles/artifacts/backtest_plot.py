import sys
sys.path.insert(0, "../")

from datetime import datetime
import os
import json
from collections import defaultdict
import pandas as pd
import numpy as np
import plotly
from plotly.subplots import make_subplots
import plotly.graph_objects as go
pyplt = plotly.offline.plot

# def calc_ret(df):
#     rest_dict = {}
#     rest_dict["交易标的"] = SYMBOL
#     rest_dict["交易日期"] = df["tradeDate"].iloc[0]
#     rest_dict["税前盈亏"] = round(
#         df[df.买卖方向 == "卖"].成交金额.apply(_convert_float).sum() - df[df.买卖方向 == "买"].成交金额.apply(_convert_float).sum(), 2)
#     rest_dict["税后盈亏"] = round(
#         df[df.买卖方向 == "卖"].成交金额.apply(_convert_float).sum() * 0.999 - df[df.买卖方向 == "买"].成交金额.apply(
#             _convert_float).sum(), 2)
#     rest_dict["税后收益率"] = round((df[df.买卖方向 == "卖"].成交金额.apply(_convert_float).sum() * 0.999 - df[
#         df.买卖方向 == "买"].成交金额.apply(_convert_float).sum()) / (df[df.买卖方向 == "卖"].成交金额.apply(_convert_float).sum() + df[
#         df.买卖方向 == "买"].成交金额.apply(_convert_float).sum()), 6)
#     rest_dict["买成交金额"] = round(df[df.买卖方向 == "买"].成交金额.apply(_convert_float).sum(), 2)
#     rest_dict["卖成交金额"] = round(df[df.买卖方向 == "卖"].成交金额.apply(_convert_float).sum(), 2)
#     rest_dict["卖成交数量"] = df[df.买卖方向 == "卖"].成交数量.sum()
#     rest_dict["买成交数量"] = df[df.买卖方向 == "买"].成交数量.sum()

#     ret_df = pd.DataFrame.from_dict(rest_dict, orient="index")
#     print(ret_df)
#     return ret_df


def analyze_port(df_order):
    cash = 0.0
    amount_buy = 0.0  # 成交量
    amount_sell = 0.0
    position = defaultdict(int)
    df_order["成交金额"] = df_order["成交金额"].apply(lambda x: x.replace(" ", "") if type(x) == str else x).astype(float)

    for tidx, trade in df_order.iterrows():
        #         if trade["委托状态"] == "已撤" or trade["委托状态"] == "部撤" or trade["委托状态"] == "废单":
        if trade["委托状态"] == "废单":
            pass
        if trade["买卖方向"] == "买":
            cash = cash - trade["成交金额"]
            amount_buy += trade["成交金额"]
            position[trade["证券代码"]] += trade["成交数量"]
        else:
            cash = cash + trade["成交金额"]
            amount_sell += trade["成交金额"]
            position[trade["证券代码"]] -= trade["成交数量"]
    print("盈亏：", cash, "买入总成交量", amount_buy, "卖出总成交量", amount_sell, "最后持仓：", position)


def plot_trade(df_order, dates, prices, lastpxs, time_dict, start_time):
    # 遍历交易点数据
    trade_points_buy_time = []
    trade_points_buy_time_exe = []
    trade_points_buy_v = []
    trade_points_buy_size = []
    trade_points_buy_size_str = []
    trade_points_buy_type = []

    trade_points_sell_time = []
    trade_points_sell_time_exe = []
    trade_points_sell_v = []
    trade_points_sell_size = []
    trade_points_sell_size_str = []
    trade_points_sell_type = []

    positions = [0]
    positions_time = []

    cash = [0.0]
    cash_time = []

    for tidx, trade in df_order.iterrows():
        #         if trade["委托状态"] == "已撤" or trade["委托状态"] == "部撤" or trade["委托状态"] == "废单":
        if trade["委托状态"] == "废单":
            continue
        trade_time = (pd.to_datetime(trade['委托时间']) - start_time).total_seconds()
        trade_direction = trade['买卖方向']
        trade_qty = trade['成交数量']
        trade_qty_str = str(trade['成交数量']) + "/" + str(trade["委托数量"])
        # 在交易点位置添加标记
        nearest_index = np.where(dates >= trade_time)[0]
        if len(nearest_index) > 0:
            nearest_index = nearest_index[0]
        if trade_direction == "买":
            if trade_time not in dates:
                dates = np.insert(dates, nearest_index, trade_time)
                prices = np.insert(prices, nearest_index, prices[nearest_index])
                lastpxs = np.insert(lastpxs, nearest_index, lastpxs[nearest_index])
                time_dict[trade_time] = pd.to_datetime(trade['委托时间']).strftime("%H:%M:%S")

            trade_points_buy_time.append(time_dict[trade_time])
            trade_points_buy_time_exe.append(pd.to_datetime(trade['filledDate']))
            trade_points_buy_v.append(trade['委托价格'])
            trade_points_buy_size_str.append(trade_qty_str)
            trade_points_buy_size.append(trade_qty)
            trade_points_buy_type.append(trade['委托状态'])
            cash.append(cash[-1] - trade["成交金额"])
            positions.append(positions[-1] + abs(trade_qty))
            positions_time.append(time_dict[trade_time])
            cash_time.append(time_dict[trade_time])
        else:
            if trade_time not in dates:
                dates = np.insert(dates, nearest_index, trade_time)
                prices = np.insert(prices, nearest_index, prices[nearest_index])
                lastpxs = np.insert(lastpxs, nearest_index, lastpxs[nearest_index])
                time_dict[trade_time] = pd.to_datetime(trade['委托时间']).strftime("%H:%M:%S")

            trade_points_sell_time.append(time_dict[trade_time])
            trade_points_sell_time_exe.append(pd.to_datetime(trade['filledDate']))
            trade_points_sell_v.append(trade['委托价格'])
            trade_points_sell_size_str.append(trade_qty_str)
            trade_points_sell_size.append(trade_qty)
            trade_points_sell_type.append(trade['委托状态'])
            cash.append(cash[-1] + trade["成交金额"])
            positions.append(positions[-1] - abs(trade_qty))
            positions_time.append(time_dict[trade_time])
            cash_time.append(time_dict[trade_time])

    return dates, prices, lastpxs, {"trade_points_buy_time": trade_points_buy_time,
                                    "trade_points_buy_time_exe": trade_points_buy_time_exe,
                                    "trade_points_buy_v": trade_points_buy_v,
                                    "trade_points_buy_size": trade_points_buy_size,
                                    "trade_points_buy_size_str": trade_points_buy_size_str,
                                    "trade_points_buy_type": trade_points_buy_type,
                                    "trade_points_sell_time": trade_points_sell_time,
                                    "trade_points_sell_time_exe": trade_points_sell_time_exe,
                                    "trade_points_sell_v": trade_points_sell_v,
                                    "trade_points_sell_size": trade_points_sell_size,
                                    "trade_points_sell_size_str": trade_points_sell_size_str,
                                    "trade_points_sell_type": trade_points_sell_type,
                                    "cash": cash[1:],
                                    "positions": positions[1:],
                                    "positions_time": positions_time,
                                    "cash_time": cash_time}


def analyze1(mkdata_df, df_signal_source, df_order, save_pic_path="./demo.html", plot = False):
    # 提取日期和价格列
    backtest_date = mkdata_df["MDDate"].iloc[0]
    mkdata_df["index"] = mkdata_df["Date"]
    if not df_signal_source.empty:
        df_signal_source["index"] = df_signal_source["PERIOD_BEGIN"].apply(lambda x: pd.to_datetime(x))
        mkdata_df = mkdata_df.set_index("index")
        df_signal_source = df_signal_source.set_index("index")
        df_signal = pd.merge(mkdata_df, df_signal_source, how="left", left_index=True, right_index=True)
        df_signal.rename(columns={"Date_x": "Date"}, inplace=True)
    else:
        #无信号数据
        df_signal = mkdata_df
    start_time = df_signal['Date'].iloc[0]
    dates = df_signal['Date'].apply(lambda x: (x - start_time).total_seconds()).values
    try:
        time_dict = {(i - start_time).total_seconds(): i.strftime("%H:%M:%S.%f") for i in df_signal['Date']}
        #     prices = df_signal["TARGET_VALUE"].values
        prices = (np.around(df_signal['Buy1Price'].replace(0, np.nan).values, 2) +
                  np.around(df_signal['Sell1Price'].replace(0, np.nan).values, 2)) / 2.0
        prices = np.around(prices, 2)
    except:
        time_dict = {(i - start_time).total_seconds(): i.strftime("%H:%M:%S") for i in df_signal['Date']}
        prices = df_signal["TARGET_VALUE"].values

    lastpxs = df_signal["LastPx"].replace(0, np.nan).values

    first_price = lastpxs[0]
    percent_function = lambda x: (x - first_price) / first_price
    percent = percent_function(lastpxs)

    volumes = df_signal["TotalVolumeTrade"] - df_signal["TotalVolumeTrade"].shift(1)

    dates, prices, lastpxs, result1 = plot_trade(df_order[df_order["委托状态"] == "已撤"], dates, prices, lastpxs, time_dict,
                                                 start_time)
    dates, prices, lastpxs, result2 = plot_trade(df_order[df_order["委托状态"] != "已撤"], dates, prices, lastpxs, time_dict,
                                                 start_time)
    position_dict = dict(zip(result2["positions_time"], result2["positions"]))
    cash_dict = dict(zip(result2["cash_time"], result2["cash"]))
    #     positions = [position_dict[time_dict[i]] if time_dict[i] in position_dict.keys() else 0 for i in dates ]

    positions = [0]
    cash = [0.0]
    for i in dates:
        if time_dict[i] in position_dict.keys():
            positions.append(position_dict[time_dict[i]])
            #         if time_dict[i] in cash_dict.keys():
            cash.append(cash_dict[time_dict[i]])
        else:
            positions.append(positions[-1])
            cash.append(cash[-1])

    cash = cash[1:] + positions[1:] * lastpxs

    bid_asks = (df_signal["Sell1Price"] - df_signal["Buy1Price"]).values

    try:
        BS10 = zip(np.around(df_signal['Sell1Price'], 2),
                   np.around(df_signal['Buy1Price'], 2))
    except:
        print("Tick")

    ###############
    fig = make_subplots(specs=[[{'secondary_y': True}], [{'secondary_y': True}]],
                        row_heights=[150, 50],
                        rows=2, cols=1)

    fig.add_trace(go.Bar(name='Position',
                         x=[time_dict[i] for i in dates], y=positions[1:], marker=dict(color="black", opacity=1),
                         # text = df["probs"]
                         ), secondary_y=False, row=2, col=1)

    fig.add_trace(go.Scatter(name='cash',
                             x=[time_dict[i] for i in dates], y=cash, line_color="skyblue",
                             # text = df["probs"]
                             ), secondary_y=True, row=2, col=1)

    fig.add_trace(go.Scatter(name='LastPx',
                             x=[time_dict[i] for i in dates], y=lastpxs, line_color="orange",
                             text=np.around(percent, 4)
                             ), secondary_y=False, row=1, col=1)

    try:
        fig.add_trace(go.Scatter(name='Mid',
                                 x=[time_dict[i] for i in dates], y=prices, line_color="skyblue",
                                 text=list(BS10)
                                 ), secondary_y=False, row=1, col=1)
    except:
        fig.add_trace(go.Scatter(name='Mid',
                                 x=[time_dict[i] for i in dates], y=prices, line_color="skyblue",
                                 # text = df["probs"]
                                 ), secondary_y=False, row=1, col=1)

    fig.add_trace(go.Scatter(name='TradeBuy_Canceled',
                             x=result1["trade_points_buy_time"], y=result1["trade_points_buy_v"], mode='markers',
                             line_color="pink",
                             marker=dict(size=7, opacity=1),
                             text=list(zip(result1["trade_points_buy_time_exe"], result1["trade_points_buy_size_str"])),
                             ), secondary_y=False, row=1, col=1)

    fig.add_trace(go.Scatter(name='TradeSell_Canceled',
                             x=result1["trade_points_sell_time"], y=result1["trade_points_sell_v"], mode='markers',
                             line_color="lightgreen",
                             marker=dict(size=7, opacity=1),
                             text=list(
                                 zip(result1["trade_points_sell_time_exe"], result1["trade_points_sell_size_str"])),
                             ), secondary_y=False, row=1, col=1)

    fig.add_trace(go.Scatter(name='TradeBuy_Executed',
                             x=result2["trade_points_buy_time"], y=result2["trade_points_buy_v"], mode='markers',
                             line_color="red",
                             marker=dict(size=7, opacity=1),
                             text=list(zip(result2["trade_points_buy_time_exe"], result2["trade_points_buy_size_str"])),
                             ), secondary_y=False, row=1, col=1)

    fig.add_trace(go.Scatter(name='TradeSell_Executed',
                             x=result2["trade_points_sell_time"], y=result2["trade_points_sell_v"], mode='markers',
                             line_color="green",
                             marker=dict(size=7, opacity=1),
                             text=list(
                                 zip(result2["trade_points_sell_time_exe"], result2["trade_points_sell_size_str"])),
                             ), secondary_y=False, row=1, col=1)

    signal_points_buy_time = []
    signal_points_buy_v = []
    signal_points_buy_size = []
    signal_points_buy_pred = []

    signal_points_sell_time = []
    signal_points_sell_v = []
    signal_points_sell_size = []
    signal_points_sell_pred = []

    if not df_signal_source.empty:
        for sidx, signal in df_signal.iterrows():
            if pd.isna(signal["PERIOD_BEGIN"]):
                continue
            signal_time = (pd.to_datetime(signal["PERIOD_BEGIN"]) - start_time).total_seconds()
            signal_type = np.array(signal["PROBABILITY"]).argmax()
            nearest_index = np.where(dates >= signal_time)[0]
            if len(nearest_index) > 0:
                nearest_index = nearest_index[0]
            if signal_type in [3, 4]:
                signal_v = signal_type - 2
                signal_points_buy_time.append(time_dict[signal_time])
                signal_points_buy_v.append(prices[nearest_index])
                signal_points_buy_size.append(signal_v * 10)
                signal_points_buy_pred.append(signal["PREDICTED"])
            elif signal_type in [2]:
                signal_v = 0
                continue
            else:
                signal_v = 2 - signal_type
                signal_points_sell_time.append(time_dict[signal_time])
                signal_points_sell_v.append(prices[nearest_index])
                signal_points_sell_size.append(signal_v * 10)
                signal_points_sell_pred.append([signal["PREDICTED"],  signal["Sell1Price"], signal["Buy1Price"]])
        # 存html
        #     signalbuy_size = []
        #     signal_points_buy_v_min = min(signal_points_buy_v)
        #     for i in signal_points_buy_v:
        #         signalbuy_size.append((i - signal_points_buy_v_min) * 100)

        fig.add_trace(go.Scatter(name='SignalBuy',
                                 x=signal_points_buy_time, y=signal_points_buy_v,
                                 # marker = dict(opacity=1,symbol="triangle-up", sizemode="area",size=np.array(signalbuy_size),sizeref=0.9),
                                 marker=dict(size=10, opacity=1, symbol="triangle-up"),
                                 mode='markers', line_color="tomato",
                                 text=signal_points_buy_pred,
                                 ), secondary_y=False, row=1, col=1)
        fig.add_trace(go.Scatter(name='SignalSell',
                                 x=signal_points_sell_time, y=signal_points_sell_v,
                                 marker=dict(size=10, opacity=1, symbol='triangle-down'),
                                 mode='markers', line_color="limegreen",
                                 text=signal_points_sell_pred,
                                 ), secondary_y=False, row=1, col=1)
    fig.update_layout(width=1600, height=1200, title_text='MarketData with Signals & Trades',
                      xaxis_title="Date_" + backtest_date, yaxis_title="Price",
                      legend=dict(y=0.5, traceorder='reversed', font_size=16))
    #     fig.update_xaxes(range = [min([time_dict[i] for i in dates]), max([time_dict[i] for i in dates])], row = 1, col = 1)

#    只有notebook能显示
    if plot:
        fig.show()

    #     analyze_port(df_order)
    #     calc_ret(df_order)
    with open(save_pic_path, "w") as f:
        f.write(fig.to_html(full_html=False, ))
    return fig



def analyze2(mkdata_df, df_signal_source, df_order, save_pic_path="./demo.html", plot = False):
    backtest_date = mkdata_df["MDDate"].iloc[0]
    # 提取日期和价格列
    mkdata_df["index"] = mkdata_df["Date"]
    df_signal_source["index"] = df_signal_source["PERIOD_BEGIN"].apply(lambda x: pd.to_datetime(x))
    mkdata_df = mkdata_df.set_index("index")
    df_signal_source = df_signal_source.set_index("index")
    df_signal = pd.merge(mkdata_df, df_signal_source, how="left", left_index=True, right_index=True)
    df_signal.rename(columns={"Date_x": "Date"}, inplace=True)
    start_time = df_signal['Date'].iloc[0]
    dates = df_signal['Date'].apply(lambda x: (x - start_time).total_seconds()).values
    try:
        time_dict = {(i - start_time).total_seconds(): i.strftime("%H:%M:%S.%f") for i in df_signal['Date']}
        #     prices = df_signal["TARGET_VALUE"].values
        prices = (df_signal['Buy1Price'].replace(0, np.nan).values + df_signal['Buy1Price'].replace(0,
                                                                                                    np.nan).values) / 2.0
    except:
        time_dict = {(i - start_time).total_seconds(): i.strftime("%H:%M:%S") for i in df_signal['Date']}
        prices = df_signal["TARGET_VALUE"].values

    lastpxs = df_signal["LastPx"].replace(0, np.nan).values
    volumes = df_signal["TotalVolumeTrade"] - df_signal["TotalVolumeTrade"].shift(1)

    dates, prices, lastpxs, result1 = plot_trade(df_order[df_order["委托状态"] == "已撤"], dates, prices, lastpxs, time_dict,
                                                 start_time)
    dates, prices, lastpxs, result2 = plot_trade(df_order[df_order["委托状态"] != "已撤"], dates, prices, lastpxs, time_dict,
                                                 start_time)
    position_dict = dict(zip(result2["positions_time"], result2["positions"]))
    positions = [position_dict[time_dict[i]] if time_dict[i] in position_dict.keys() else 0 for i in dates]
    bid_asks = (df_signal["Sell1Price"] - df_signal["Buy1Price"]).values

    ###############
    fig = make_subplots(specs=[[{'secondary_y': True}], [{'secondary_y': False}], ],
                        row_heights=[50, 50],
                        rows=2, cols=1)

    fig.add_trace(go.Bar(name='Volume',
                         x=[time_dict[i] for i in dates], y=volumes, marker=dict(color="blue", opacity=1),
                         # text = df["probs"]
                         ), secondary_y=False, row=1, col=1)

    fig.add_trace(go.Bar(name='Ask1P-Bid1P',
                         x=[time_dict[i] for i in dates], y=bid_asks, marker=dict(color="purple", opacity=1),
                         # text = df["probs"]
                         ), secondary_y=False, row=2, col=1)

    fig.update_layout(width=1600, height=1000, title_text='MarketData with Trades & BidAsks',
                      xaxis_title="Time", yaxis_title="Volume",
                      legend=dict(y=0.5, traceorder='reversed', font_size=16))
    #     fig.update_xaxes(range = [min([time_dict[i] for i in dates]), max([time_dict[i] for i in dates])], row = 1, col = 1)

    if plot:
        fig.show()

    #     analyze_port(df_order)
    #     calc_ret(df_order)
    with open(save_pic_path, "a") as f:
        f.write(fig.to_html(full_html=False, ))
    return fig



def plot_signal_fig(df_signal, plot = False):
    #设置开始结束时间
    df_signal["index"] = df_signal["PERIOD_BEGIN"].apply(lambda x: pd.to_datetime(x))
    df_signal["Date"] = df_signal["index"]
    df_signal = df_signal.set_index("index")
    start_time = df_signal.index[0]
    backtest_date = start_time.strftime("%Y%m%d")
    dates = df_signal['Date'].apply(lambda x: (x - start_time).total_seconds()).values
    time_dict = {(i - start_time).total_seconds(): i.strftime("%H:%M:%S") for i in df_signal['Date']}
    prices = df_signal["TARGET_VALUE"].values
    if not "PREDICTED" in df_signal.columns:
        df_signal["PREDICTED"] = df_signal["PREDICT"]

    #画点
    signal_points_buy_time = []
    signal_points_buy_v = []
    signal_points_buy_size = []
    signal_points_buy_pred = []

    signal_points_sell_time = []
    signal_points_sell_v = []
    signal_points_sell_size = []
    signal_points_sell_pred = []

    for sidx, signal in df_signal.iterrows():
        if pd.isna(signal["PERIOD_BEGIN"]):
            continue
        signal_time = (pd.to_datetime(signal["PERIOD_BEGIN"]) - start_time).total_seconds()
        signal_type = np.array(signal["PROBABILITY"]).argmax()
        nearest_index = np.where(dates >= signal_time)[0]
        if len(nearest_index) > 0:
            nearest_index = nearest_index[0]
        if signal_type in [3, 4]:
            signal_v = signal_type - 2
            signal_points_buy_time.append(time_dict[signal_time])
            signal_points_buy_v.append(prices[nearest_index])
            signal_points_buy_size.append(signal_v * 10)
            signal_points_buy_pred.append(signal["PREDICTED"])
        elif signal_type in [2]:
            signal_v = 0
            continue
        else:
            signal_v = 2 - signal_type
            signal_points_sell_time.append(time_dict[signal_time])
            signal_points_sell_v.append(prices[nearest_index])
            signal_points_sell_size.append(signal_v * 10)
            signal_points_sell_pred.append(signal["PREDICTED"])
    # 存html
    #     signalbuy_size = []
    #     signal_points_buy_v_min = min(signal_points_buy_v)
    #     for i in signal_points_buy_v:
    #         signalbuy_size.append((i - signal_points_buy_v_min) * 100)

    fig = make_subplots(specs=[[{'secondary_y': True}]],
                        row_heights=[150],
                        rows=1, cols=1)

    fig.add_trace(go.Scatter(name='Mid',
                             x=[time_dict[i] for i in dates], y=prices, line_color="skyblue",
                             # text = df["probs"]
                             ), secondary_y=False, row=1, col=1)

    fig.add_trace(go.Scatter(name='SignalBuy',
                             x=signal_points_buy_time, y=signal_points_buy_v,
                             # marker = dict(opacity=1,symbol="triangle-up", sizemode="area",size=np.array(signalbuy_size),sizeref=0.9),
                             marker=dict(size=10, opacity=1, symbol="triangle-up"),
                             mode='markers', line_color="tomato",
                             text=signal_points_buy_pred,
                             ), secondary_y=False, row=1, col=1)
    fig.add_trace(go.Scatter(name='SignalSell',
                             x=signal_points_sell_time, y=signal_points_sell_v,
                             marker=dict(size=10, opacity=1, symbol='triangle-down'),
                             mode='markers', line_color="limegreen",
                             text=signal_points_sell_pred,
                             ), secondary_y=False, row=1, col=1)
    fig.update_layout(width=1600, height=1200, title_text='MarketData with Signals & Trades',
                      xaxis_title="Date_" + backtest_date, yaxis_title="Price",
                      legend=dict(y=0.5, traceorder='reversed', font_size=16))
    #     fig.update_xaxes(range = [min([time_dict[i] for i in dates]), max([time_dict[i] for i in dates])], row = 1, col = 1)

    #    只有notebook能显示
    if plot:
        fig.show()
    return fig

