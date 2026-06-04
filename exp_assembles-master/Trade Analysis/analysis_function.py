#!/usr/bin/env python
# coding: utf-8

# In[1]:


import sys
from datetime import datetime
from datetime import timedelta
import random
import pandas as pd
import numpy as np
from collections import OrderedDict

### 加载线上信号
def load_online_signal(path, SYMBOL, StrategyModelName):
    df = pd.read_excel(path, sheet_name=SYMBOL)
    df = df[(df.SYMBOL == SYMBOL) & (df.STRATEGY_NAME == StrategyModelName)]
    df.index = df.PERIOD_BEGIN
    df.index = pd.to_datetime(df.index)
    df["PERIOD_BEGIN"] = df["PERIOD_BEGIN"].apply(pd.to_datetime)
    df["PERIOD_END"] = df["PERIOD_END"].apply(pd.to_datetime)
    tmp_df = df["PROBABILITY"].apply(eval).apply(pd.Series, index=['D_2', 'D_1', 'O_1', "R_1", "R_2"])
    df = pd.merge(df, tmp_df, left_index=True, right_index=True)
    return df


# In[5]:


### 计算线上成交绩效
def compute_trade_result(SYMBOL, start_date, end_date, df_order, sh_order_status_map):
    dates = [int(str(d).split(" ")[0].replace("-", "")) for d in  pd.date_range(start_date, end_date)]
    ret_df_list = []
    for date in dates:
        df = df_order[df_order["TradeDate"]==date]
        #过滤废单和撤单
        df = df[(df.OrdStatus!=sh_order_status_map["已撤"])&(df.OrdStatus!=sh_order_status_map["废单"])]
        if df.empty:
            print(f"Warning: {date}没有交易记录！")
            continue

        rest_dict = OrderedDict()
        rest_dict["交易标的"] = SYMBOL
        rest_dict["交易日期"] = date
        #security
        rest_dict["买成交数量"] = df[df.Side==1].CumQuantity.sum()
        rest_dict["卖成交数量"] = df[df.Side==2].CumQuantity.sum()
        rest_dict["敞口"] = rest_dict["买成交数量"]-rest_dict["卖成交数量"]
        rest_dict["买成交金额"] = round(df[df.Side==1].CumAmount.sum(),2)
        rest_dict["卖成交金额"] = round(df[df.Side==2].CumAmount.sum(),2)
        rest_dict["税前盈亏"] = round(df[df.Side==2].CumAmount.sum() - df[df.Side==1].CumAmount.sum(), 2)
#     rest_dict["税后盈亏"] = round(df[df.Side==2].CumAmount.sum()*0.999 - df[df.Side==1].CumAmount.sum(), 2)
        rest_dict["税后盈亏"] = round(df[df.Side==2].CumAmount.sum()*0.9995 - df[df.Side==1].CumAmount.sum(), 2)
        if rest_dict["敞口"]:
            last_price = df.iloc[-1]["Price"]
            rest_dict["税前盈亏(去除敞口)"] = rest_dict["税前盈亏"]+rest_dict["敞口"]*last_price
            rest_dict["税后盈亏(去除敞口)"] = rest_dict["税后盈亏"]+rest_dict["敞口"]*last_price
            trade_amount_open_posion = rest_dict["敞口"]*last_price if rest_dict["敞口"]>0 else 0
            print("trade_amount_open_posion:", trade_amount_open_posion)
            trade_amount = df[df.Side==2].CumAmount.sum()+trade_amount_open_posion
            rest_dict["税后收益率"] = round(rest_dict["税后盈亏(去除敞口)"]/trade_amount,6) if trade_amount else 0
            rest_dict["年化收益率"] = rest_dict["税后收益率"]*252
        else:
            trade_amount = df[df.Side==2].CumAmount.sum()#+df[df.Side==1].CumAmount.sum()
#         rest_dict["税后收益率"] = round((df[df.Side==2].CumAmount.sum()*0.999 - df[df.Side==1].CumAmount.sum())/trade_amount,6) if trade_amount else 0
            rest_dict["税后收益率"] = round((df[df.Side==2].CumAmount.sum()*0.9995 - df[df.Side==1].CumAmount.sum())/trade_amount,6) if trade_amount else 0
            rest_dict["年化收益率"] = rest_dict["税后收益率"]*252

        ret_df = pd.DataFrame.from_dict(rest_dict, orient="index").T
        ret_df_list.append(ret_df)
    if ret_df_list:
        online_trade_result_df = pd.concat(ret_df_list)
    else:
        online_trade_result_df = pd.DataFrame()
        
    return online_trade_result_df
    


# In[ ]:



### 线上成交绩效
def deal_amount_online(df):
    """成交金额指标"""
#     df = df[df["TradeDate"]==trade_date_online]
    DealAmount_ALL = sum(df["CumAmount"])
    BuydealAmount = sum(df[df["Side"]=="1"]["CumAmount"])
    SelldealAmount = sum(df[df["Side"]=="2"]["CumAmount"])
#     TotalAmount_ALL = sum(df["Quantity"]*df["Price"])
#     BuyTotalAmount = sum(df[df["Side"]=="1"]["Quantity"]*df[df["Side"]=="1"]["Price"])
#     SellTotalAmount = sum(df[df["Side"]=="2"]["Quantity"]*df[df["Side"]=="2"]["Price"])
#     res_dic = {"累计成交金额总和":DealAmount_ALL,"累计买单成交金额总和":BuydealAmount,"累计卖单成交金额总和":SelldealAmount,"成交金额总和":TotalAmount_ALL,"买单成交金额总和":BuyTotalAmount,"卖单成交金额总和":SellTotalAmount}
    res_dic = {"成交金额总和":DealAmount_ALL,"买单成交金额总和":BuydealAmount,"卖单成交金额总和":SelldealAmount}
    return res_dic


def dealqty_and_entrustqty_online(df):
    """成交股数和委托股数指标"""
#     df = df[df["TradeDate"]==trade_date_online]
    df = df[df["OrdStatus"]!="9"]
#     df["CumQuantity"] = np.cumsum(df["Quantity"])
#     DealQuantity_ALL = sum(df["CumQuantity"])
#     BuydealQuantity = sum(df[df["Side"]=="1"]["CumQuantity"])
#     SelldealQuantity = sum(df[df["Side"]=="2"]["CumQuantity"])
    Quantity_ALL = sum(df["Quantity"])
    BuyQuantity = sum(df[df["Side"]=="1"]["Quantity"])
    SellQuantity = sum(df[df["Side"]=="2"]["Quantity"])
    cum_Quantity_ALL = sum(df["CumQuantity"])
    cum_BuyQuantity = sum(df[df["Side"]=="1"]["CumQuantity"])
    cum_SellQuantity = sum(df[df["Side"]=="2"]["CumQuantity"])
#     res_dic = {"累计成交股数总和":DealQuantity_ALL, "累计买单成交股数总和":BuydealQuantity, "累计卖单成交股数总和":SelldealQuantity, "成交股数总和":Quantity_ALL, "买单成交股数总和":BuyQuantity, "卖单成交股数总和":SellQuantity}
    res_dic = {"委托股数总和":Quantity_ALL, "买单委托股数总和":BuyQuantity, "卖单委托股数总和":SellQuantity,"成交股数总和":cum_Quantity_ALL, "买单成交股数总和":cum_BuyQuantity, "卖单成交股数总和":cum_SellQuantity}
    return res_dic


def targets_num_in_strategy_online(df):
    "策略涉及的标的数"
#     df = df[df["TradeDate"]==trade_date_online]
    df1 = df[df["OrdStatus"] == "8"]
    df2 = df[df["OrdStatus"] == "5"]
    countStock = len(set(list(df1["Symbol"]) + list(df2["Symbol"])))
    res_dic = {"策略涉及的标的数":countStock}
    return res_dic


def strategy_num_online(df):
    "策略实例条数"
#     df = df[df["TradeDate"]==trade_date_online]
    df1 = df[df["OrdStatus"] == "8"]
    df2 = df[df["OrdStatus"] == "5"]
    strategy_num = len(df1) + len(df2)
    res_dic = {"策略实例条数":strategy_num}
    return res_dic



def order_strategy_quantity_statistics_online(df):
    "订单策略的全成、部成和不成数量统计"
#     df = df[df["TradeDate"] == trade_date_online]
    allOrder = len(df)
    df1 = df[df["OrdStatus"]=="8"]
    allDeal = len(df1)
    df2 = df[df["OrdStatus"]=="5"]
    partDeal = len(df2)
    df3 = df[df["OrdStatus"]!="8"]
    df3 = df3[df3["OrdStatus"] != "5"]
    noDeal = len(df3)
    red_dic = {"订单总数":allOrder,"成交订单数":allDeal,"部成订单数":partDeal,"不成订单数":noDeal}
    return red_dic


# In[ ]:



###线下成交绩效
def deal_amount(df):
    """成交金额指标"""
#     DealAmount_ALL = sum(df["cumAmount"])
#     BuydealAmount = sum(df[df["side"]=="BID"]["cumAmount"])
#     SelldealAmount = sum(df[df["side"]=="ASK"]["cumAmount"])
    TotalAmount_ALL = sum(df["quantity"]*df["price"])
    BuyTotalAmount = sum(df[df["side"]=="BID"]["quantity"]*df[df["side"]=="BID"]["price"])
    SellTotalAmount = sum(df[df["side"]=="ASK"]["quantity"]*df[df["side"]=="ASK"]["price"])
    res_dic = {"成交金额总和":TotalAmount_ALL,"买单成交金额总和":BuyTotalAmount,"卖单成交金额总和":SellTotalAmount}
    return res_dic


def dealqty_and_entrustqty(df):
    """成交股数和委托股数指标"""
    df = df[df["orderStatus"]!="REJECTED"]
#     df["CumQuantity"] = np.cumsum(df["quantity"])
#     DealQuantity_ALL = sum(df["CumQuantity"])
#     BuydealQuantity = sum(df[df["side"]=="BID"]["CumQuantity"])
#     SelldealQuantity = sum(df[df["side"]=="ASK"]["CumQuantity"])
    Quantity_ALL = sum(df["quantity"])
    BuyQuantity = sum(df[df["side"]=="BID"]["quantity"])
    SellQuantity = sum(df[df["side"]=="ASK"]["quantity"])
    res_dic = {"成交股数总和":Quantity_ALL, "买单成交股数总和":BuyQuantity, "卖单成交股数总和":SellQuantity}
    return res_dic


def targets_num_in_strategy(df):
    "策略涉及的标的数"
    df1 = df[df["orderStatus"] == "DONE"]
    df2 = df[df["orderStatus"] == "PARTIALLY_CANCELLED"]
    countStock = len(set(list(df1["symbol"]) + list(df2["symbol"])))
    res_dic = {"策略涉及的标的数":countStock}
    return res_dic


def strategy_num(df):
    "策略实例条数"
    df1 = df[df["orderStatus"] == "DONE"]
    df2 = df[df["orderStatus"] == "PARTIALLY_CANCELLED"]
    strategy_num = len(df1) + len(df2)
    res_dic = {"策略实例条数":strategy_num}
    return res_dic



def order_strategy_quantity_statistics(df):
    "订单策略的全成、部成和不成数量统计"
    allOrder = len(df)
    df1 = df[df["orderStatus"]=="DONE"]
    allDeal = len(df1)
    df2 = df[df["orderStatus"]=="PARTIALLY_CANCELLED"]
    partDeal = len(df2)
    df3 = df[df["orderStatus"]!="DONE"]
    df3 = df3[df3["orderStatus"] != "PARTIALLY_CANCELLED"]
    noDeal = len(df3)
    red_dic = {"订单总数":allOrder,"成交订单数":allDeal,"部成订单数":partDeal,"不成订单数":noDeal}
    return red_dic


# In[ ]:





# In[ ]:



### 校验实盘和盘后的one-hot编码的一致性
def return_flag(df):
    if np.argmax(df) in ["R_1", 0]:
        return 1
    if np.argmax(df) in ["R_2", 1]:
        return 2
    if np.argmax(df) in ["D_1", 3]:
        return -1
    if np.argmax(df) in ["D_2", 4]:
        return -2
    return 0


# In[ ]:



### 生成信号
def normalize_probs(probs):
    total_sum = sum(probs)
    for i in range(len(probs)):
        probs[i] /= total_sum

def translate(df, th):
    # [D2, D1, 01, R1, R2]
    # less than 0.001
    if (df["O1"] > df["D1"] and df["O1"] > df["R1"]) or (df["R1"] < th and df["D1"] < th):
        tmp = np.random.random_sample(4)
        tmp = np.insert(tmp, 2, 1.5)
        tmp = tmp / sum(tmp)
        return tmp.tolist()
    if df["R1"] >= th and df["R2"] >= th:
        tmp = np.random.random_sample(4)
        tmp = np.insert(tmp, 4, 1.5)
        tmp = tmp / sum(tmp)
        return tmp.tolist()
    if df["R1"] >= th and df["R2"] < th:
        tmp = np.random.random_sample(4)
        tmp = np.insert(tmp, 3, 1.5)
        tmp = tmp / sum(tmp)
        return tmp.tolist()
    if df["D1"] >= th and df["D2"] >= th:
        tmp = np.random.random_sample(4)
        tmp = np.insert(tmp, 0, 1.5)
        tmp = tmp / sum(tmp)
        return tmp.tolist()
    if df["D1"] >= th and df["D2"] < th:
        tmp = np.random.random_sample(4)
        tmp = np.insert(tmp, 1, 1.5)
        tmp = tmp / sum(tmp)
        return tmp.tolist()

def reg_get_cls_prob(y, predict_dict, maxamp, minamp, threshold):
    if abs(y) < threshold:
        other = random.uniform(0.48, 0.5)
        up = random.uniform(0.15, 0.25)
        down = 1 - other - up
        ans = [down, other, up]
    elif (abs(y) >= threshold) and (abs(y) <= maxamp):
        if y >= 0:
            left = round(int(y // 0.1) * 0.1, 2)
            right = round(int(y // 0.1 + 1) * 0.1, 2)
            up = ((y - left) / (right - left)) * (predict_dict[right] - predict_dict[left]) + predict_dict[left]
            down = random.uniform(0, (1 - up) / 2)
            other = 1 - up - down
            ans = [down, other, up]
            print("==up", up, "down", down)
        else:
            right = round(int(y * 10) * 0.1, 2)
            left = round(int(y * 10 - 1) * 0.1, 2)
            down = ((-y + right) / (right - left)) * (predict_dict[right] - predict_dict[left]) + predict_dict[left]
            up = random.uniform(0, (1 - down) / 2)
            other = 1 - up - down
            # ans = [down, other, up]
            ans = [down, other, up]
            print("==up", up, "down", down)
    elif y > maxamp:
        up = predict_dict[maxamp]
        down = random.uniform(0, (1 - up) / 2)
        other = 1 - up - down
        ans = [down, other, up]
    elif y <= minamp:
        up = predict_dict[minamp]
        down = random.uniform(0, (1 - up) / 2)
        other = 1 - up - down
        ans = [up, other, down]
    ans = [round(v, 4) for v in ans]
    return ans

def compare_probs(res1, res2, probs):
    probs_list = [random.random() for _ in range(5)]

    if (res1[1] > res1[0] and res1[1] > res1[2]) or (res1[0] < probs and res1[2] < probs):
        probs_list[2] = 1.5
    elif res1[0] >= probs:
        if res2[0] >= probs:
            probs_list[4] = 1.5
        else:
            probs_list[3] = 1.5
    elif res1[2] >= probs:
        if res2[2] >= probs:
            probs_list[0] = 1.5
        else:
            probs_list[1] = 1.5

    normalize_probs(probs_list)
    return probs_list

def generate_signal(predict_value, m1, m2, min_map, max_map, threshold, probs):
    res1 = translate_predict(predict_value, m1, min_map, max_map, threshold)
    res2 = translate_predict(predict_value, m2, min_map, max_map, threshold)
    print("==", res1)
    print("==", res2)
    res = compare_probs(res1, res2, probs)
    return res


def translate_predict(predict_value, m_table, min_map, max_map, threshold):
    rand = random.Random()
    r, o, d = 0.0, 0.0, 0.0
    if abs(predict_value) < threshold:
        o = (rand.randint(0, 4) + 45.0) / 100.0
        r = (rand.randint(0, 9) + 20.0) / 100.0
        d = 1 - o - r
        print(1)
    else:
        if abs(predict_value) < max_map:
            if predict_value > 0:
                print(2)
                low = int(predict_value * 10.0) / 10.0
                high = int(predict_value * 10.0 + 1.0) / 10.0
                y = predict_value
                #                 low = round(int(y // 0.1) * 0.1, 2)
                #                 high = round(int(y // 0.1 + 1) * 0.1, 2)
                r = (predict_value - low) / (high - low) * (m_table[high] - m_table[low]) + m_table[low]
                o = (1 - r) / 2
                d = 1 - r - o
            else:
                print(3)
                low = int(predict_value * 10.0 - 1.0) / 10.0
                high = int(predict_value * 10.0) / 10.0
                y = predict_value
                #                 low = round(int(y // 0.1) * 0.1, 2)
                #                 high = round(int(y // 0.1 - 1) * 0.1, 2)
                d = (-predict_value + high) / (high - low) * (m_table[high] - m_table[low]) + m_table[low]
                o = (1 - d) / 2
                r = 1 - d - o
        elif predict_value >= max_map:
            print(4, predict_value, max_map)
            r = m_table[max_map]
            o = (1 - r) / 2
            d = 1 - r - o
        elif predict_value <= min_map:
            print(5, min_map)
            d = m_table[min_map]
            o = (1 - d) / 2
            r = 1 - d - o
    res = [r, o, d]
    return res


# In[ ]:





# In[4]:



### 信号图


from collections import defaultdict
import pandas as pd
import numpy as np
from _plotly_future_ import v4_subplots
#from plotly.figure_factory import create_2d_density
from plotly.subplots import make_subplots
# import plotly.graph_objects as go
from plotly import graph_objs as go
from plotly import tools
import plotly
from plotly.tools import FigureFactory as ff
pyplt = plotly.offline.plot


def _convert_float(x):
    return x
    # x = x.replace(" ","")
    # return float(x)

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
def parse_trade_records(df_order):
    sh_order_status_map = {"CANCELLED": "已撤", "DONE": "已成", "PARTIALLY_CANCELLED": "部撤", "REJECTED": "废单"}
    sh_side = {"BID": "买", "ASK": "卖"}

    df_order["委托状态"] = df_order["委托状态"].apply(lambda x: sh_order_status_map[x])
    df_order["买卖方向"] = df_order["买卖方向"].apply(lambda x: sh_side[x])
    df_order["证券代码"] = df_order["交易标的"]
    df_order['成交比例'] = df_order['成交数量'] / df_order['委托数量']
    df_order['未完成数量'] = df_order['委托数量'] - df_order['成交数量']
    df_order['委托金额'] = df_order['委托价格'] * df_order['委托数量']
    df_order['价格类型'] = '限价'
    return df_order


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

    for tidx, trade in df_order.iterrows():
    #         if trade["委托状态"] == "已撤" or trade["委托状态"] == "部撤" or trade["委托状态"] == "废单":
        if trade["委托状态"] == "废单":
            continue
        trade_time = (pd.to_datetime(trade['委托时间']) - start_time).total_seconds()
        trade_direction = trade['买卖方向']
#         print(trade_direction)
        trade_qty = trade['成交数量']
        trade_qty_str = str(trade['成交数量'])+"/"+str(trade["委托数量"])
        # 在交易点位置添加标记
        nearest_index = np.where(dates>=trade_time)[0]
        if len(nearest_index)>0:
            nearest_index = nearest_index[0]
        if trade_direction == "买":
            if trade_time not in dates:
                dates = np.insert(dates, nearest_index, trade_time)
                prices = np.insert(prices, nearest_index, prices[nearest_index])
#                 print(prices)
#                 print(lastpxs)
#                 print(nearest_index)
                lastpxs = np.insert(lastpxs, nearest_index, lastpxs[nearest_index])
                time_dict[trade_time] = pd.to_datetime(trade['委托时间']).strftime("%H:%M:%S")

            trade_points_buy_time.append(time_dict[trade_time])
            trade_points_buy_time_exe.append(pd.to_datetime(trade['成交时间']))
            trade_points_buy_v.append(trade['委托价格'])
            trade_points_buy_size_str.append(trade_qty_str)
            trade_points_buy_size.append(trade_qty)
            trade_points_buy_type.append(trade['委托状态'])
            positions.append(positions[-1]+trade_qty)
            positions_time.append(time_dict[trade_time])
        else:
            if trade_time not in dates:
                dates = np.insert(dates, nearest_index, trade_time)
                prices = np.insert(prices, nearest_index, prices[nearest_index])
                lastpxs = np.insert(lastpxs, nearest_index, lastpxs[nearest_index])
                time_dict[trade_time] = pd.to_datetime(trade['委托时间']).strftime("%H:%M:%S")

            trade_points_sell_time.append(time_dict[trade_time])
            trade_points_sell_time_exe.append(pd.to_datetime(trade['成交时间']))
            trade_points_sell_v.append(trade['委托价格'])
            trade_points_sell_size_str.append(trade_qty_str)
            trade_points_sell_size.append(trade_qty)
            trade_points_sell_type.append(trade['委托状态'])
            positions.append(positions[-1]-trade_qty)
            positions_time.append(time_dict[trade_time])

    return     dates, prices, lastpxs, {"trade_points_buy_time":trade_points_buy_time,
                                        "trade_points_buy_time_exe": trade_points_buy_time_exe,
                "trade_points_buy_v":trade_points_buy_v,
                "trade_points_buy_size":trade_points_buy_size,
                "trade_points_buy_size_str":trade_points_buy_size_str,
                "trade_points_buy_type":trade_points_buy_type,
                "trade_points_sell_time":trade_points_sell_time,
                "trade_points_sell_time_exe": trade_points_sell_time_exe,
                "trade_points_sell_v":trade_points_sell_v,
                "trade_points_sell_size":trade_points_sell_size,
                "trade_points_sell_size_str": trade_points_sell_size_str,
                "trade_points_sell_type":trade_points_sell_type,
                "positions":positions[1:],
                "positions_time":positions_time}

def analyze1(mkdata_df, df_signal_source, df_order, save_pic_path="./demo.html"):
    # 提取日期和价格列
    mkdata_df["index"] = mkdata_df["Date"]
#     df_signal_source["index"] = df_signal_source["PERIOD_BEGIN"].apply(lambda x: pd.to_datetime(x))
    try:
        df_signal_source["PERIOD_BEGIN"] = df_signal_source["PERIOD_BEGIN"].apply(lambda x:datetime.strptime(str(x),'%Y-%m-%d %H:%M:%S'))
        df_signal_source["index"] = df_signal_source["PERIOD_BEGIN"]
        mkdata_df = mkdata_df.set_index("index")
        mkdata_df = mkdata_df.resample('500ms').mean()
        mkdata_df = mkdata_df.dropna()
    
        mkdata_df['Date'] = mkdata_df.index
    except:
        df_signal_source["index"] = df_signal_source["PERIOD_BEGIN"].apply(lambda x: pd.to_datetime(x))
        mkdata_df = mkdata_df.set_index("index")
    
    df_signal_source = df_signal_source.set_index("index")
    df_signal = pd.merge(mkdata_df, df_signal_source, how = "left", left_index = True, right_index = True)
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
    percent_function = lambda x: (x-first_price)/first_price
    percent = percent_function(lastpxs)
    
    volumes = df_signal["TotalVolumeTrade"]-df_signal["TotalVolumeTrade"].shift(1)
    

    dates, prices, lastpxs, result1 = plot_trade(df_order[df_order["委托状态"]=="已撤"], dates, prices, lastpxs, time_dict, start_time)
    dates, prices, lastpxs, result2 = plot_trade(df_order[df_order["委托状态"]!="已撤"], dates, prices, lastpxs, time_dict, start_time)
    position_dict = dict(zip(result2["positions_time"], result2["positions"]))
#     positions = [position_dict[time_dict[i]] if time_dict[i] in position_dict.keys() else 0 for i in dates ]
    
    positions = [0]
    for i in dates:
        if time_dict[i] in position_dict.keys():
            positions.append(position_dict[time_dict[i]])
        else:
            positions.append(positions[-1])
    
    bid_asks = (df_signal["Sell1Price"]-df_signal["Buy1Price"]).values
    
    try:
        BS10 = zip(np.around(df_signal['Sell5Price'],2),np.around(df_signal['Sell4Price'],2),np.around(df_signal['Sell3Price'],2),
                   np.around(df_signal['Sell2Price'],2),np.around(df_signal['Sell1Price'],2),
                   np.around(df_signal['Buy1Price'],2),np.around(df_signal['Buy2Price'],2),np.around(df_signal['Buy3Price'],2),
                   np.around(df_signal['Buy4Price'],2),np.around(df_signal['Buy5Price'],2))
    except:
        print("Tick")
               
    ###############
    fig = make_subplots(specs=[[{'secondary_y': True}],[{'secondary_y': False}]], 
                        row_heights = [150, 50],
                        rows = 2, cols = 1)
                                
    fig.add_trace(go.Bar(name='Position',
                             x=[time_dict[i] for i in dates], y=positions, marker = dict(color = "black", opacity = 1),
                             # text = df["probs"]
                             ), secondary_y=False, row = 2, col = 1)

    fig.add_trace(go.Scatter(name='LastPx',
                             x=[time_dict[i] for i in dates], y=lastpxs, line_color="orange",
                             text = np.around(percent,4)
                             ), secondary_y=False, row = 1, col = 1)

    try:
        fig.add_trace(go.Scatter(name='Mid',
                             	x=[time_dict[i] for i in dates], y=prices, line_color="skyblue",
                             	text = list(BS10)
                             	), secondary_y=False, row = 1, col = 1)
    except:
        fig.add_trace(go.Scatter(name='Mid',
                             x=[time_dict[i] for i in dates], y=prices, line_color="skyblue",
                             # text = df["probs"]
                             ), secondary_y=False, row = 1, col = 1)

    fig.add_trace(go.Scatter(name='TradeBuy_Canceled',
                             x=result1["trade_points_buy_time"], y=result1["trade_points_buy_v"], mode='markers', line_color="pink",
                             marker=dict(size=7, opacity=1),
                                     text = list(zip(result1["trade_points_buy_time_exe"], result1["trade_points_buy_size_str"])),
                             ), secondary_y=False, row = 1, col = 1)

    fig.add_trace(go.Scatter(name='TradeSell_Canceled',
                             x=result1["trade_points_sell_time"], y=result1["trade_points_sell_v"], mode='markers', line_color="lightgreen",
                             marker=dict(size=7, opacity=1),
                             text = list(zip(result1["trade_points_sell_time_exe"], result1["trade_points_sell_size_str"])),
                             ), secondary_y=False, row = 1, col = 1)

    fig.add_trace(go.Scatter(name='TradeBuy_Executed',
                             x=result2["trade_points_buy_time"], y=result2["trade_points_buy_v"], mode='markers', line_color="red",
                             marker=dict(size=7, opacity=1),
                             text = list(zip(result2["trade_points_buy_time_exe"],result2["trade_points_buy_size_str"])),
                             ), secondary_y=False, row = 1, col = 1)

    fig.add_trace(go.Scatter(name='TradeSell_Executed',
                             x=result2["trade_points_sell_time"], y=result2["trade_points_sell_v"], mode='markers', line_color="green",
                             marker=dict(size=7, opacity=1),
                            text = list(zip(result2["trade_points_sell_time_exe"],result2["trade_points_sell_size_str"])),
                             ), secondary_y=False, row = 1, col = 1)

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
        nearest_index = np.where(dates>=signal_time)[0]
        if len(nearest_index)>0:
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
            signal_points_sell_pred.append([signal["PREDICTED"],signal["Sell1Price"], signal["Buy1Price"]])
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
                             text = signal_points_buy_pred,
                             ), secondary_y=False, row = 1, col = 1)
    fig.add_trace(go.Scatter(name='SignalSell',
                             x=signal_points_sell_time, y=signal_points_sell_v,
                             marker=dict(size=10, opacity=1, symbol='triangle-down'),
                             mode='markers', line_color="limegreen",
                             text = signal_points_sell_pred,
                             ), secondary_y=False, row = 1, col = 1)
    fig.update_layout(width=1600, height=1200, title_text='MarketData with Signals & Trades',
                      xaxis_title="Time", yaxis_title="Price",
                      legend=dict(y=0.5, traceorder='reversed', font_size=16))
    fig.update_xaxes(range = [min([time_dict[i] for i in dates]), max([time_dict[i] for i in dates])], row = 1, col = 1)

    # 只有notebook能显示
#     fig.show()

#     analyze_port(df_order)
#     calc_ret(df_order)
    with open(save_pic_path, "w") as f:
        f.write(fig.to_html(full_html=False, ))
    return fig


def analyze2(mkdata_df, df_signal_source, df_order, save_pic_path="./demo.html"):
    # 提取日期和价格列
    mkdata_df["index"] = mkdata_df["Date"]
#     df_signal_source["index"] = df_signal_source["PERIOD_BEGIN"].apply(lambda x: pd.to_datetime(x))	
    try:
        df_signal_source["PERIOD_BEGIN"] = df_signal_source["PERIOD_BEGIN"].apply(lambda x:datetime.strptime(str(x),'%Y-%m-%d %H:%M:%S'))
        df_signal_source["index"] = df_signal_source["PERIOD_BEGIN"]
        mkdata_df = mkdata_df.set_index("index")
        mkdata_df = mkdata_df.resample('500ms').mean()
        mkdata_df = mkdata_df.dropna()
        mkdata_df['Date'] = mkdata_df.index
    except:
        df_signal_source["index"] = df_signal_source["PERIOD_BEGIN"].apply(lambda x: pd.to_datetime(x))
        mkdata_df = mkdata_df.set_index("index")
    
    df_signal_source = df_signal_source.set_index("index")
    df_signal = pd.merge(mkdata_df, df_signal_source, how = "left", left_index = True, right_index = True)
    start_time = df_signal['Date'].iloc[0]
    dates = df_signal['Date'].apply(lambda x: (x - start_time).total_seconds()).values
    try:
        time_dict = {(i - start_time).total_seconds(): i.strftime("%H:%M:%S.%f") for i in df_signal['Date']}
#     prices = df_signal["TARGET_VALUE"].values
        prices = (df_signal['Buy1Price'].replace(0, np.nan).values + df_signal['Buy1Price'].replace(0, np.nan).values) / 2.0
    except:
        time_dict = {(i - start_time).total_seconds(): i.strftime("%H:%M:%S") for i in df_signal['Date']}
        prices = df_signal["TARGET_VALUE"].values

    lastpxs = df_signal["LastPx"].replace(0, np.nan).values
    volumes = df_signal["TotalVolumeTrade"]-df_signal["TotalVolumeTrade"].shift(1)

    dates, prices, lastpxs, result1 = plot_trade(df_order[df_order["委托状态"]=="已撤"], dates, prices, lastpxs, time_dict, start_time)
    dates, prices, lastpxs, result2 = plot_trade(df_order[df_order["委托状态"]!="已撤"], dates, prices, lastpxs, time_dict, start_time)
    position_dict = dict(zip(result2["positions_time"], result2["positions"]))
    positions = [position_dict[time_dict[i]] if time_dict[i] in position_dict.keys() else 0 for i in dates ]
    bid_asks = (df_signal["Sell1Price"]-df_signal["Buy1Price"]).values

    ###############
    fig = make_subplots(specs=[[{'secondary_y': True}],[{'secondary_y': False}],], 
                        row_heights = [50, 50],
                        rows = 2, cols = 1)
                                
    fig.add_trace(go.Bar(name='Volume',
                             x=[time_dict[i] for i in dates], y=volumes, marker = dict(color = "blue", opacity = 1),
                             # text = df["probs"]
                             ), secondary_y=False, row = 1, col = 1)
    
    fig.add_trace(go.Bar(name='Ask1P-Bid1P',
                             x=[time_dict[i] for i in dates], y=bid_asks, marker = dict(color = "purple", opacity = 1),
                             # text = df["probs"]
                             ), secondary_y=False, row = 2, col = 1)
        
   
    fig.update_layout(width=1600, height=1000, title_text='MarketData with Trades & BidAsks',
                      xaxis_title="Time", yaxis_title="Volume",
                      legend=dict(y=0.5, traceorder='reversed', font_size=16))
    fig.update_xaxes(range = [min([time_dict[i] for i in dates]), max([time_dict[i] for i in dates])], row = 1, col = 1)

    # 只有notebook能显示
#     fig.show()

#     analyze_port(df_order)
#     calc_ret(df_order)
    with open(save_pic_path, "a") as f:
        f.write(fig.to_html(full_html=False, ))
    return fig
# plot_signal_fig(publisher_file, trade_records_df)
# plot_signal_fig(publisher_file, trade_records_df)


# In[ ]:


###线上成交明细
def online_trade_analysis(df_order_source_online):
    trade_online = df_order_source_online[["Symbol", "Side", "CumQuantity", "Quantity", "OrdStatus", "Price", "CumAmount", "AveragePrice","CreatedDate", "ModifiedDate", "TradeDate"]]
    trade_online = trade_online.rename(columns={"Symbol": "symbol_on",
                                                'Side': 'side_on',
                                                'CumQuantity': 'quantity_on',
                                                'Quantity': 'entrustQty_on',
                                                'OrdStatus': 'orderStatus_on',
                                                'Price': 'entrustPx_on',
                                                'CumAmount': 'cumAmount_on',
                                                'AveragePrice': 'price_on',
                                                'CreatedDate': 'createDate_on',
                                                'ModifiedDate':'filledDate_on',
                                                'TradeDate':'tradeDate_on'
                                            })

    trade_online = trade_online.reset_index(drop = True)
    if not trade_online.empty:                  
        symbol = trade_online["symbol_on"][0]
        #symbol = SYMBOL
        # print(trade_online)
        symbol_map = {symbol: symbol+".SH"}
        trade_online["symbol_on"] = trade_online["symbol_on"].apply(lambda x: symbol_map[x])
        side_map = {"1":"BID", "2":"ASK"}
        trade_online["side_on"] = trade_online["side_on"].apply(lambda x: side_map[x])
        ord_map = {"8":"DONE", "5":"PARTIALLY_CANCELLED", "6":"CANCELLED", "7":"PARTIALLY_CANCELLED", "9": "REJECTED"}
        trade_online["orderStatus_on"] = trade_online["orderStatus_on"].apply(lambda x: ord_map[x])
    return trade_online

###线下成交明细
def offline_trade_analysis(trade_records_df):
    trade_offline = trade_records_df
    trade_offline = trade_offline[["symbol", "side", "quantity", "entrustQty", "orderStatus", "entrustPx", "cumAmount", "price","createDate", "filledDate", "tradeDate"]]
    trade_offline = trade_offline.rename(columns={"symbol": "symbol_off",
                                            'side': 'side_off',
                                            'quantity': 'quantity_off',
                                            'entrustQty': 'entrustQty_off',
                                            'orderStatus': 'orderStatus_off',
                                            'entrustPx': 'entrustPx_off',
                                            'cumAmount': 'cumAmount_off',
                                            'price': 'price_off',
                                            'createDate': 'createDate_off',
                                            'filledDate':'filledDate_off',
                                            'tradeDate':'tradeDate_off'
                                        })
    return trade_offline

###线上线下成交明细对比
def on_off_trade_analysis(trade_online, trade_offline):
    trade_offline = trade_offline[["side_off", "quantity_off", "entrustPx_off", "price_off", "createDate_off", "filledDate_off", "tradeDate_off"]]
    # trade_offline = trade_offline.sort_values(by=['createDate_off'],ascending=[True])
    trade_online["createDate_on"] = trade_online["createDate_on"].apply(lambda x: pd.to_datetime(x))
    trade_offline["createDate_off"] = trade_offline["createDate_off"].apply(lambda x: pd.to_datetime(x))
    trade_res = pd.merge_asof(trade_online, trade_offline, left_on='createDate_on', right_on='createDate_off', left_by = 'side_on', right_by = 'side_off', direction='backward')
    trade_res = trade_res.drop(columns=['tradeDate_on', 'side_off'])
    trade_res = trade_res.rename(columns={  'tradeDate_off': 'tradeDate',
                                            'side_on': 'side', 
                                            })
    trade_res.loc[trade_res.duplicated(['createDate_off', 'filledDate_off']), ["quantity_off", "entrustPx_off", "price_off", "createDate_off", "filledDate_off"]]=np.nan

    return trade_res

