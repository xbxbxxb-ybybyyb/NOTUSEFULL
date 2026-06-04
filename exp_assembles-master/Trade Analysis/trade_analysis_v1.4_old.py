
# coding: utf-8

# In[ ]:


# handout: begin-exclude

# #  Dolphindb实盘因子分析

import handout # handout: exclude

# # Dolphindb实盘因子分析

import sys

sys.path.insert(0, "/data/user/016869/online_scripts/shen/")

from datetime import datetime
from datetime import timedelta
import os
import json
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider

base_dir0 = "/data/user/016869/AutoMiningFrame/trade_data"

try:
    SYMBOL = sys.argv[1]
    StrategyModelName = sys.argv[2]
    run_date = sys.argv[3]
except:
    SYMBOL="688599.SH"
    StrategyModelName = "688599.SH_trade_v1.2"
    # SYMBOL="688599.SH"
    # StrategyModelName = "688599.SH_trade"

try:
    run_date = sys.argv[3]
    currentdate = datetime.strptime(run_date, "%Y%m%d")
    currentdate_delta = 0
except:
    currentdate_delta = 0            ### date
    currentdate = (datetime.now() + timedelta(days=currentdate_delta))
    run_date = datetime.strftime(currentdate, "%Y%m%d")
    # currentdate = datetime.strptime("202307110", "%Y%m%d")
    
if run_date==datetime.now().strftime("%Y%m%d"):
    sql_use_real = True
    print(sql_use_real)
else:
    sql_use_real = False


trade_date_online = currentdate.strftime("%Y%m%d")   ##022917
trade_date_offline = currentdate.strftime("%Y-%m-%d")   ##022917

StrategyName = "OnnxTest"
base_dir = os.path.join(base_dir0, "COO", f"{SYMBOL}-{StrategyModelName}")
model_path = os.path.join(base_dir, StrategyModelName)
signal_path = os.path.join(base_dir, "mm_ai_signal")
order_path = os.path.join(base_dir, "mm_order")
visual_path = os.path.join(base_dir, "mm_visual")
log_path = os.path.join(base_dir0, "mm_log")

tradingdate_1 = currentdate.strftime("%Y%m%d")

if not os.path.exists(model_path):
    os.makedirs(model_path)
if not os.path.exists(signal_path):
    os.makedirs(signal_path)
    os.makedirs(os.path.join(signal_path, "online"))
    os.makedirs(os.path.join(signal_path, "offline"))
if not os.path.exists(order_path):
    os.makedirs(order_path)
    os.makedirs(os.path.join(order_path, "online"))
    os.makedirs(os.path.join(order_path, "offline"))
if not os.path.exists(visual_path):
    os.makedirs(visual_path)
    os.makedirs(os.path.join(visual_path, "online"))
    os.makedirs(os.path.join(visual_path, "offline"))
print(tradingdate_1)
print("model_path:", model_path)
print("signal_path:", signal_path)


# In[ ]:


user_id = '016869'
target_securities = [SYMBOL]
fd = FactorProvider(user_id)
factor_type = 'real_factor'
source_type = 'public'


# # 信号绩效分析


tradingdate = currentdate.strftime("%Y-%m-%d")
signal_path_online = os.path.join(signal_path, "online")

with open(os.path.join(model_path, "configs.json"), "r") as f:
    configs = json.load(f)
    print(configs)

import json
import os
import warnings

warnings.filterwarnings('ignore')
from src.utils.utils import *
from online_check.utils import *
from datetime import datetime

# 下载和解析日志信号文件
# assert os.system("sh onnx_version.sh")==0
path = os.path.join(log_path, "predictJson_{}.xlsx".format(tradingdate))
if datetime.now().hour >= 15 and not os.path.exists(path) and datetime.now().strftime("%Y%m%d") == run_date:
    # 交易时间禁止访问！！！
    assert os.system(f"python3 /data/user/016869/online_scripts/shen/predictJson_collect.py prod {tradingdate}") == 0
    print(path)
    assert os.system("curl ftp://168.8.2.68/013150/ -T {} -u 'ftphzh:ftphzh2602'".format(path)) == 0


# In[ ]:


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


source_signal_df = load_online_signal(path, SYMBOL, StrategyModelName)
print("online source signal df shape:", source_signal_df.shape)

online_signal_df = source_signal_df[
    (source_signal_df.SYMBOL == SYMBOL) & (source_signal_df.STRATEGY_NAME == StrategyModelName)]
print(f"online signal df of SYMBOL {SYMBOL} and StrategyModelName {StrategyModelName}: ", online_signal_df.shape)

# 计算信号的个数和准确率
print("线上信号的准确率：")
# compute_acc_single(df, d_1=0.0012, d_2=0.003, r_1=0.0012, r_2=0.003)
for strategy in set(source_signal_df["STRATEGY_NAME"]):
    sub_df = source_signal_df[source_signal_df["STRATEGY_NAME"] == strategy]
    result = compute_acc_single(source_signal_df, d_1=-configs["udrange"][1], d_2=-configs["udrange"][0],
                                r_1=configs["udrange"][3], r_2=configs["udrange"][4])
    print("StrategyModelName:", strategy, "d1", -configs["udrange"][1], "d_2", -configs["udrange"][0],
          "r_1", configs["udrange"][3], "r_2", configs["udrange"][4])
    print(result)
# compute_acc_single(df, d_1=0.0015, d_2=0.002, r_1=0.0015, r_2=0.002)


# In[ ]:


# 画出信号
# compute_acc_single(df, d_1=0.0012, d_2=0.003, r_1=0.0012, r_2=0.003)
for strategy in set(source_signal_df["STRATEGY_NAME"]):
    sub_df = source_signal_df[source_signal_df["STRATEGY_NAME"] == strategy]
    print("strategyModelName:", strategy)
    plot_signal(sub_df)


# 生成信号文件

def generate_signal_file(signal_df, signa_path, file_name):
    result_list = []
    for ridx, row in signal_df.iterrows():
        preidict_result = [str(row["PERIOD_BEGIN"]), "mm_ai_signal"]
        preidict_json = r""""PROBABILITY": {0}, 
        "RANGE": {1}, 
        "PERIOD_BEGIN": "{2}", 
        "PERIOD_END": "{3}", 
        "TRGET_TYPE": "{4}", 
        "TARGET_VALUE": {5}, 
        "STRATEGY_NAME": "{6}", 
        "SYMBOL": "{7}",
        "PREDICTED":{8}
        """.format([row.D_2, row.D_1, row.O_1, row.R_1, row.R_2],
                   configs["udrange"],
                   str(row.PERIOD_BEGIN),
                   str(row.PERIOD_END),
                   row.TARGET_TYPE,
                   row.TARGET_VALUE,
                   StrategyName,
                   SYMBOL,
                   row.PREDICTED)
        preidict_json = "{" + preidict_json.replace("\n", "").replace("  ", " ") + "}"

        preidict_result.append(preidict_json)
        result = json.dumps(preidict_result)

        result_list.append(result)
    if not os.path.exists(signa_path):
        os.makedirs(signa_path)

    signal_save_path = os.path.join(signa_path, file_name)
    with open(signal_save_path, "w") as f:
        f.writelines("{" + r'"StrategyName": "{}"'.format(StrategyName) + "}\n")
        for line in result_list:
            f.writelines(line + "\n")
    f.close()


file_name_online = "{}.txt".format(tradingdate)
generate_signal_file(online_signal_df, signal_path_online, file_name_online)
print("线上信号文件已生成！{}".format(os.path.join(signal_path_online, file_name_online)))


# In[ ]:


# # 成交绩效分析



from datetime import datetime
from datetime import timedelta
import os
import pandas as pd
from collections import OrderedDict
import pymysql1
import pandas as pd
import pymysql
from sqlalchemy import create_engine,Column,Integer,String


current_date = currentdate.strftime("%Y%m%d")
# current_date_before = "20230521"
# current_date_before = datetime.now() + timedelta(days=-7)
current_date_before = currentdate + timedelta(days=-1)
current_date_before = current_date_before.strftime("%Y%m%d")


#TODO: 区分不同的策略来统计
#数据库链接信息
db = pymysql1.connect(host='168.11.33.144',
                     port = 3307,
                     user='xtraderops',
                     password='wXE1QGmIc3+gDYVOnwrzw37SZN0FBLx9OqBpEGJMVic=',
                     database='ats_quant',
                     )
# db = pymysql1.connect(host='168.9.65.8',
#                      port = 3308,
#                      user='xtraderops_new',
#                      password='wXE1QGmIc3+gDYVOnwrzw37SZN0FBLx9OqBpEGJMVic=',
#                      database='ats_quant',
#                      )
if sql_use_real:
    schema = "security"
else:
    schema = "history_security"

# sql_trade_all = """select * FROM {}.exchangeorder WHERE EntrustType=0 
#             AND substring_index(AlgoOrderId,'-',1) ='STARArbitrageSubStrategy'
#            and SecurityId in('{}')
#             and tradedate between '{}' and '{}'""".format(schema, SYMBOL.split(".")[0], current_date_before, current_date)
sql_trade_all = """select * FROM {}.exchangeorder WHERE EntrustType=0 
            AND substring_index(AlgoOrderId,'-',1) ='STARArbitrageSubStrategy'
           and SecurityId in('{}')
            and tradedate = '{}'""".format(schema, SYMBOL.split(".")[0], current_date)
print(sql_trade_all)

def deal_amount_online(df):
    """成交金额指标"""
    df = df[df["TradeDate"]==trade_date_online]
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
    df = df[df["TradeDate"]==trade_date_online]
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
    df = df[df["TradeDate"]==trade_date_online]
    df1 = df[df["OrdStatus"] == "8"]
    df2 = df[df["OrdStatus"] == "5"]
    countStock = len(set(list(df1["Symbol"]) + list(df2["Symbol"])))
    res_dic = {"策略涉及的标的数":countStock}
    return res_dic


def strategy_num_online(df):
    "策略实例条数"
    df = df[df["TradeDate"]==trade_date_online]
    df1 = df[df["OrdStatus"] == "8"]
    df2 = df[df["OrdStatus"] == "5"]
    strategy_num = len(df1) + len(df2)
    res_dic = {"策略实例条数":strategy_num}
    return res_dic



def order_strategy_quantity_statistics_online(df):
    "订单策略的全成、部成和不成数量统计"
    df = df[df["TradeDate"] == trade_date_online]
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





trade_path = os.path.join(base_dir, "mm_order/online/trade_records_{}.parquet".format(current_date))
df_order_source = pd.read_sql(sql_trade_all, con = db)
if not df_order_source.empty:
    df_order_source.to_parquet(trade_path)
    os.system("curl ftp://168.8.2.68/013150/ -T {} -u 'ftphzh:ftphzh2602'".format(trade_path))
if df_order_source.empty:
    print("Online Empty!")
if df_order_source.empty and os.path.exists(trade_path):
    df_order_source = pd.read_parquet(trade_path)
print("df_order_online_source shape:", df_order_source.shape)
print("df_order_online_source:", df_order_source.columns)


if 'OrderId' in df_order_source.columns:
    df_order_source['orderid']=df_order_source['OrderId']

print("===================")


keep_columns = ["AssetAccount",
    "Side",
    "SecurityId",
    'CreatedDate',
    'ModifiedDate',
    "Price",
    "Quantity", #下单数量
    "CancelledQty",
    "OrdStatus",
    "CumAmount",
    "CumQuantity",#成交数量
    "CumNetMoney",
    "orderid",
    "AveragePrice",
    "EntrustType",
    "TradeDate",
    "TransactTime"
]

#部撤实际上是部分成交
sh_order_status_map = {"已撤":6, "废单":9, "已成":8, "部撤部成":5, "部撤":7}
sh_side = {"买":1, "卖":2}

df_order = df_order_source[keep_columns]
print("df_order shape:", df_order.shape)
print("df_order:", df_order.columns)
df_order["Side"] = df_order["Side"].astype(int)
df_order["CumQuantity"] = df_order["CumQuantity"].astype(float)
df_order["CumNetMoney"] = df_order["CumNetMoney"].astype(float)
df_order["CumAmount"] = df_order["CumAmount"].astype(float)
df_order["Price"] = df_order["Price"].astype(float)
df_order["AveragePrice"] = df_order["AveragePrice"].astype(float)
df_order["Quantity"] = df_order["Quantity"].astype(float)


df_order = df_order.sort_values(by = ["CreatedDate"]).reset_index()
# df_order.loc[:, ['Quantity', 'CumQuantity', "CumAmount", "CumNetMoney", "AveragePrice"]]

# 例如参与率 报价差  敞口盈亏 回转盈亏
# 我们一般分敞口盈亏和回转盈亏
# 敞口就是形成敞口的成交价和当前最新价的差额
# 回转就是已经成交的除掉敞口之外的卖金额减买金额除以卖金额
start_date = current_date_before
end_date = current_date

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
        rest_dict["税后收益率"] = round((df[df.Side==2].CumAmount.sum()*0.9995 - df[df.Side==1].CumAmount.sum())/trade_amount,6) if trade_amount else 0
        rest_dict["年化收益率"] = rest_dict["税后收益率"]*252

    ret_df = pd.DataFrame.from_dict(rest_dict, orient="index").T
    ret_df_list.append(ret_df)
if ret_df_list:
    online_trade_result_df = pd.concat(ret_df_list)
else:
    online_trade_result_df = pd.DataFrame()
    
print(online_trade_result_df)


# In[ ]:


# # 信号线上线下一致性分析



from datetime import datetime
from datetime import timedelta
from xquant.marketdata import MarketData

signal_offline_path = os.path.join(signal_path, "offline")
start_date = (datetime.now() + timedelta(days=-20)).strftime("%Y%m%d")

end_date = currentdate.strftime("%Y%m%d")
factor_lib_user_id = '016884'

print(end_date)

from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
import onnxruntime as rt
from tqdm import tqdm
import pandas as pd
import os
from src.utils.utils import *
from online_check.utils import *
from xquant.marketdata import MarketData
import json
import copy

clipper_sess = rt.InferenceSession(os.path.join(model_path, "clipper.onnx"))
scaler_sess = rt.InferenceSession(os.path.join(model_path, "scaler.onnx"))
model_sess = rt.InferenceSession(os.path.join(model_path, "model.onnx"))
#


# 线上信号
# online_df_success = True
try:
    path = os.path.join(log_path,
                         "predictJson_{}.xlsx".format(end_date[:4] + "-" + end_date[4:6] + "-" + end_date[-2:]))
    if os.path.exists(path):
#         # 从日志中加载信号
        online_df = load_online_signal(path, SYMBOL, StrategyModelName)
        print("线上预测信号(在线信号)：", online_df.shape)
        assert online_df.shape[0] > 0, "online_df为空"
    else:
        print("【Warning】: predictJson_文件不存在!将通过线上因子计算")
#         # 从线上因子计算信号
#         if not factor_df_online.empty:
#             online_df, yhat = generate_signals(factor_df_online)
#             online_df["PREDICT"] = yhat
#             assert online_df.shape[0] > 0, "online_df为空"
#             print("线上预测信号(线上因子计算)：", online_df.shape)
except:
    online_df_success = False

# 校验实盘和盘后的one-hot编码的一致性
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





# # 信号回测&策略回测


from datetime import datetime
from datetime import timedelta
import os
import json
import os
import subprocess
import pandas as pd
import numpy as np

# 注意：当天7点后可以回测
backtest_date = currentdate.strftime("%Y-%m-%d")
signal_path_online = os.path.join(signal_path, "online")
order_path_offline = os.path.join(order_path, "offline")

publisher_file = os.path.join(signal_path_online, "{}.txt".format(backtest_date))
print("publisher_file:", publisher_file)

# os.system('hadoop fs -ls /htdata/mdc/MDCProvider/XSHG_Stock_Snapshot_Level2_Month/month={}|grep {}'.format(backtest_date.replace("-","")[:6], SYMBOL))
# os.system("hadoop fs -ls /htdata/mdc/MDCProvider/XSHG_Stock_Transaction_Auction_Month/month={}|grep {}".format(backtest_date.replace("-","")[:6],SYMBOL))
# os.system("hadoop fs -ls /htdata/mdc/MDCProvider/XSHG_Stock_Order_Auction_Month/month={}|grep {}".format(backtest_date.replace("-","")[:6],SYMBOL))


with open(os.path.join(model_path, "configs.json"), "r") as f:
    configs = json.load(f)
    print(configs)




##################################################
# handout: end-exclude


# In[ ]:



"""
 **Operational Analysis Results**
"""

import handout  # handout: exclude
import matplotlib.pyplot as plt  # handout: exclude
import numpy as np  # handout: exclude
import pandas as pd  # handout: exclude


html_path = os.path.join(base_dir0,"COO/daily_report", f"{SYMBOL}-{StrategyModelName}-{tradingdate_1}") # handout: exclude
#html_path = "./trade_online_offline"   # handout: exclude
doc = handout.Handout(html_path)  # handout: exclude

"""
 **1. Dolphindb实盘因子分析**
"""

"""
 **2. 信号绩效分析**
"""

doc.add_text(f"configs: {configs}")  # handout: exclude
doc.show()  # handout: exclude

doc.add_text(f"online source signal df shape: {source_signal_df.shape}")  # handout: exclude
doc.show()  # handout: exclude

doc.add_text(f"online signal df of SYMBOL {SYMBOL} and StrategyModelName {StrategyModelName}:\n") # handout: exclude
doc.show() # handout: exclude
doc.add_text(f"{online_signal_df.shape}")  # handout: exclude
doc.show()  # handout: exclude

"""
2.1 线上信号的准确率：
"""

for strategy in set(source_signal_df["STRATEGY_NAME"]): # handout: exclude
    sub_df = source_signal_df[source_signal_df["STRATEGY_NAME"] == strategy] # handout: exclude
    result = compute_acc_single(source_signal_df, d_1=-configs["udrange"][1], d_2=-configs["udrange"][0], r_1=configs["udrange"][3], r_2=configs["udrange"][4]) # handout: exclude
    result.reset_index(inplace=True) # handout: exclude
    doc.add_text(f"StrategyModelName: {strategy}, d1: {-configs['udrange'][1]}, d_2: {-configs['udrange'][0]}, r_1: {configs['udrange'][3]}, r_2: {configs['udrange'][4]}\n") # handout: exclude
    doc.add_html(result.to_html()) # handout: exclude
doc.show() # handout: exclude

"""
 **4. 线上成交绩效分析**
"""
# handout: begin-exclude
doc.add_text("成交绩效指标")
doc.add_html(online_trade_result_df.to_html())
doc.show()
# handout: end-exclude   
"成交金额指标"
# handout: begin-exclude
df_order_source_online = df_order_source
df_order_source_online["TradeDate"] = df_order_source_online["TradeDate"].apply(lambda x:datetime.strptime(str(x),'%Y%m%d'))
df_order_source_online = df_order_source_online[df_order_source_online["TradeDate"] == trade_date_online]
res11 = pd.DataFrame.from_dict(deal_amount_online(df_order_source_online),orient='index').T
doc.add_html(res11.to_html())
doc.show()
# handout: end-exclude   
"成交股数和委托股数指标"
# handout: begin-exclude
res22 = pd.DataFrame.from_dict(dealqty_and_entrustqty_online(df_order_source_online),orient='index').T
doc.add_html(res22.to_html())
doc.show()
# handout: end-exclude   
"策略涉及的标的数"
# handout: begin-exclude
res33 = pd.DataFrame.from_dict(targets_num_in_strategy_online(df_order_source_online),orient='index').T
doc.add_html(res33.to_html())
doc.show()
# handout: end-exclude   
"策略实例条数"
# handout: begin-exclude
res44 = pd.DataFrame.from_dict(strategy_num_online(df_order_source_online),orient='index').T
doc.add_html(res44.to_html())
doc.show()
# handout: end-exclude  
"订单策略的全成、部成和不成数量统计"
# handout: begin-exclude
res55 = pd.DataFrame.from_dict(order_strategy_quantity_statistics_online(df_order_source_online),orient='index').T
doc.add_html(res55.to_html())
doc.show()
# handout: end-exclude  


"""
 6.3 线上成交明细：
"""
# handout: begin-exclude

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

    doc.add_html(trade_online.to_html())  
    doc.show()  
# handout: end-exclude          
              

# In[ ]:


# handout: begin-exclude
import os
import zipfile
 
def zipDir(dirpath, outFullName):
    """
    压缩指定文件夹
    :param dirpath: 目标文件夹路径
    :param outFullName: 压缩文件保存路径+xxxx.zip
    :return: 无
    """
    zip = zipfile.ZipFile(outFullName, "w", zipfile.ZIP_DEFLATED)
    for path, dirnames, filenames in os.walk(dirpath):
        # 去掉目标跟路径，只对目标文件夹下边的文件及文件夹进行压缩
        fpath = path.replace(dirpath, '')
 
        for filename in filenames:
            zip.write(os.path.join(path, filename), os.path.join(fpath, filename))
    zip.close()
    
html_path_zip = html_path+".zip"
print(html_path_zip)

html_index_path = os.path.join(html_path, f"{SYMBOL}-{StrategyModelName}-{tradingdate_1}.html")
os.system("mv {}/index.html {}".format(html_path, html_index_path))
zipDir(html_path, html_path_zip)
os.system("curl ftp://168.8.2.68/013150/ai_signals/ -T {} -u 'ftphzh:ftphzh2602'".format(html_index_path))
# handout: end-exclude

