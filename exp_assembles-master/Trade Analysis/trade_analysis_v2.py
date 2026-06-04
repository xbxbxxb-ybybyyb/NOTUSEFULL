#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# handout: begin-exclude

# #  Dolphindb实盘因子分析

import handout # handout: exclude
import sys
from analysis_function import *
from datetime import datetime
from datetime import timedelta
import os
import json
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider


### 基本信息配置
sys.path.insert(0, "/data/user/016869/online_scripts/shen/")
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


### 加载因子
user_id = '016869'
target_securities = [SYMBOL]
fd = FactorProvider(user_id)
factor_type = 'real_factor'
source_type = 'public'
# 先读取公共库中已存在的因子列表
fac = fd.load_info_from_dfs(factor_type, source_type=source_type)
# 加载因子库中因子数据
factor_df = fd.load_public_data_from_dfs(symbol=target_securities, factor_list=list(fac),
                                         start_time=tradingdate_1, end_time=tradingdate_1,
                                         factor_type=factor_type)
print("factor_df.shape:{}, factor_df_dropna.shape: {}.".format(factor_df.shape,
                                                               factor_df.dropna(axis=0, how="all").shape))



### 信号绩效分析
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


# 画出信号
# compute_acc_single(df, d_1=0.0012, d_2=0.003, r_1=0.0012, r_2=0.003)
for strategy in set(source_signal_df["STRATEGY_NAME"]):
    sub_df = source_signal_df[source_signal_df["STRATEGY_NAME"] == strategy]
    print("strategyModelName:", strategy)
    plot_signal(sub_df)



### 生成信号文件
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


### 成交绩效分析



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
if sql_use_real:
    schema = "security"
else:
    schema = "history_security"


sql_trade_all = """select * FROM {}.exchangeorder WHERE EntrustType=0 
            AND substring_index(AlgoOrderId,'-',1) ='STARAccumulativeSubStrategy'
           and SecurityId in('{}')
            and tradedate = '{}'""".format(schema, SYMBOL.split(".")[0], current_date)
print(sql_trade_all)



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

### 计算线上成交绩效
start_date = current_date_before
end_date = current_date
online_trade_result_df = compute_trade_result(SYMBOL, start_date, end_date, df_order, sh_order_status_map)
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

clipper_input_name = clipper_sess.get_inputs()[0].name
clipper_label_name = clipper_sess.get_outputs()[0].name
scaler_input_name = scaler_sess.get_inputs()[0].name
scaler_label_name = scaler_sess.get_outputs()[0].name
model_input_name = model_sess.get_inputs()[0].name
model_label_name = model_sess.get_outputs()[0].name
factor_name_list = pd.read_csv(os.path.join(model_path, "factors.csv"), header=None)[0].values.tolist()
print(model_input_name, model_label_name)

with open(os.path.join(model_path, "configs.json"), "r") as f:
    configs = json.load(f)

with open(os.path.join(model_path, "tables_1.json"), "r") as f:
    probs_table1 = json.load(f)
    key = list(map(float, probs_table1.keys()))
    value = list(probs_table1.values())
    probs_table1 = dict(zip(key, value))

with open(os.path.join(model_path, "tables_2.json"), "r") as f:
    probs_table2 = json.load(f)
    key = list(map(float, probs_table2.keys()))
    value = list(probs_table2.values())
    probs_table2 = dict(zip(key, value))

factor_df_online = pd.DataFrame()
factor_df_offline = pd.DataFrame()
try:
    user_id = factor_lib_user_id
    target_securities = [SYMBOL]
    fd = FactorProvider(user_id)
    factor_type = 'real_factor'
    source_type = 'public'
    # 先读取公共库中已存在的因子列表
    fac = fd.load_info_from_dfs(factor_type, source_type=source_type)
    # 读取模型需要的因子
    fac = [r for r in factor_name_list if r.startswith("Factor")]
    # 加载因子库中因子数据
    factor_df_online = fd.load_public_data_from_dfs(symbol=target_securities, factor_list=fac,
                                                    start_time=end_date, end_time=end_date, factor_type=factor_type)
    factor_df_online.dropna(inplace=True, axis=0, how="all")
    print(factor_df_online)
    factor_df_online.set_index("timestamp", drop=True, inplace=True)
    assert len(factor_df_online) > 0, "读取实时因子失败!"
    factor_df = factor_df_online
    print("use online, factor_df shape:", factor_df.shape)
except:
    print("读取实时因子失败, 将读取历史因子代替！")
    fd = FactorProvider(factor_lib_user_id)
    factor_df_offline = fd.load_public_data_from_dfs(
        symbol=SYMBOL,
        factor_list=[v for v in factor_name_list if v.startswith("Factor")],
        start_time=end_date,
        end_time=end_date,
        factor_type="factor"
    )
    factor_df_offline.dropna(inplace=True, axis=0, how="all")
    factor_df_offline.set_index("timestamp", drop=True, inplace=True)
    assert len(factor_df_offline) > 0, "读取历史因子失败!"
    factor_df = factor_df_offline
    print("use offline, factor_df shape:", factor_df.shape)

    
### 加载行情数据
mdp = MarketData()

raw_df_tick = mdp.get_data_by_date("STOCK", SYMBOL, end_date, sort_by_receive_time=True)
raw_df_tick.to_parquet("/tmp/ma_df_tick.parquet")
#os.system("curl ftp://168.8.2.68/013150/ -T {} -u 'ftphzh:ftphzh2602'".format("/tmp/ma_df_tick.parquet"))
assert len(raw_df_tick) > 0, "Tick行情数据为空！"

raw_df_tick['DateTime'] = raw_df_tick.apply(lambda x: pd.to_datetime(x['MDDate'] + " " + x['MDTime'][:-3]), axis=1)
raw_df_tick["TARGET_VALUE"] = (raw_df_tick["Sell1Price"] + raw_df_tick["Buy1Price"]) / 2.0
raw_df_tick.set_index(['DateTime'], drop=True, inplace=True)

raw_df = mdp.get_data_by_date("EnhancedTick", SYMBOL, end_date, sort_by_receive_time=True)
raw_df.to_parquet("/tmp/ma_df.parquet")
#os.system("curl ftp://168.8.2.68/013150/ -T {} -u 'ftphzh:ftphzh2602'".format("/tmp/ma_df.parquet"))
# print("Market Done!")
# assert len(raw_df) > 0, "行情数据为空！"

if len(raw_df) == 0:
    raw_df = raw_df_tick
    raw_df.to_parquet("/tmp/ma_df.parquet")

raw_df['DateTime'] = raw_df.apply(lambda x: pd.to_datetime(x['MDDate'] + " " + x['MDTime'][:-3]), axis=1)
raw_df["TARGET_VALUE"] = (raw_df["Sell1Price"] + raw_df["Buy1Price"]) / 2.0
raw_df.set_index(['DateTime'], drop=True, inplace=True)

print("marketdata_df shape:", raw_df.shape)
print("marketdata_df_tick shape:", raw_df_tick.shape)


# In[ ]:


import copy


# 下载和解析日志信号文件

### 生成信号
def generate_signals(factor_df):
    print("model configs:", configs)
    indx = []
    rest = []
    tart = []
    sub_factor_name_list = copy.copy(factor_name_list)
    sub_factor_name_list.remove("ReferenceMidPrice")
    for i in range(configs["trainingStep"], len(factor_df)):
        tmpdf = factor_df[sub_factor_name_list].iloc[i - configs["trainingStep"]:i]  # .reshape(-1,120)
        #     print(tmpdf.index[-1])
        if tmpdf.index[-1] not in set(raw_df_tick.index):
#             print(tmpdf.index[-1])
            continue
        tmp = tmpdf.values
        pred_clip = clipper_sess.run([clipper_label_name], {clipper_input_name: tmp.astype(np.float32)})[0]
        pred_scale = scaler_sess.run([scaler_label_name], {scaler_input_name: pred_clip})[0]
        pred_model =         model_sess.run([model_label_name], {model_input_name: pred_scale.reshape(-1, len(sub_factor_name_list))})[0]
        indx.append(tmpdf.index[-1])
        rest.append(pred_model[0][0])
        tart.append(raw_df_tick.loc[tmpdf.index[-1]][["TARGET_VALUE"]].values[-1])

    print("Succeed Predict")
    # todo: translate函数中获取probsThreshold
    yhat = pd.DataFrame(rest, index=indx, columns=["yhat"])
    print("yhat shape", yhat.shape)

    
    offline_df = generate_probs2(path="./", datasettype="test", yhat_df=yhat,
                                 table1=probs_table1, table2=probs_table2,
                                 probs=configs["probsThreshold"], threshold=configs["threshold"],
                                 amp=configs["maxMap"], period=configs["period"], target_value=tart, target_type=configs["referenceType"],
                                 n_jobs=0)

    return offline_df, yhat


# 线上信号
online_df_success = True
try:
    path = os.path.join(log_path,
                        "predictJson_{}.xlsx".format(end_date[:4] + "-" + end_date[4:6] + "-" + end_date[-2:]))
    if os.path.exists(path):
        # 从日志中加载信号
        online_df = load_online_signal(path, SYMBOL, StrategyModelName)
        print("线上预测信号(在线信号)：", online_df.shape)
        assert online_df.shape[0] > 0, "online_df为空"
    else:
        print("【Warning】: predictJson_文件不存在!将通过线上因子计算")
        # 从线上因子计算信号
        if not factor_df_online.empty:
            online_df, yhat = generate_signals(factor_df_online)
            online_df["PREDICT"] = yhat
            assert online_df.shape[0] > 0, "online_df为空"
            print("线上预测信号(线上因子计算)：", online_df.shape)
except:
    online_df_success = False
finally:
    if not factor_df_online.empty:
        offline_df, yhat = generate_signals(factor_df_online)
    else:
        offline_df, yhat = generate_signals(factor_df_offline)
    offline_df["PREDICT"] = yhat
    offline_df["yhat"] = yhat.loc[:, ["yhat"]]
    print("Succeed Generate Signal")

    if not online_df_success:
        online_df = offline_df
        print("线上预测信号（线下因子计算）：", online_df.shape)

print("线下信号的准确率：")
stats_dict = compute_acc_single(offline_df, d_1=-configs["udrange"][1], d_2=-configs["udrange"][0],
                                r_1=configs["udrange"][3], r_2=configs["udrange"][4])
stats_dict.reset_index(inplace=True) 
print("d1", -configs["udrange"][1], "d_2", -configs["udrange"][0],
      "r_1", configs["udrange"][3], "r_2", configs["udrange"][4])
print(stats_dict)
print("offline_df", offline_df.shape)
print("online_df", online_df.shape)

#022917
diff_df = pd.concat([offline_df, online_df, online_df]).drop_duplicates(subset = ['PERIOD_BEGIN', 'PERIOD_END'], keep = False)
print("diff_df", diff_df.shape)
print("9:33前信号的准确率：")

### 线上线下不一致的信号
stats_dict_diff = compute_acc_single(diff_df, d_1=-configs["udrange"][1], d_2=-configs["udrange"][0],
                                r_1=configs["udrange"][3], r_2=configs["udrange"][4])
stats_dict_diff.reset_index(inplace=True) 
# print("d1", -configs["udrange"][1], "d_2", -configs["udrange"][0],
#       "r_1", configs["udrange"][3], "r_2", configs["udrange"][4])
print(stats_dict_diff)

try:
    tmp = copy.deepcopy(online_df[["predicted".upper()]])
except:
    tmp = copy.deepcopy(online_df[["predicted".upper()]])

print("线上线下信号的相关性：")
tmp["yhat"] = yhat["yhat"]
print(tmp.corr())


# 校验实盘和盘后的one-hot编码的一致性

offline_df["flag"] = offline_df[["D_2", "D_1", "O_1", "R_1", "R_2"]].apply(return_flag, axis=1)
online_df["flag"] = online_df[["D_2", "D_1", "O_1", "R_1", "R_2"]].apply(return_flag, axis=1)
offline_df_flag = offline_df[offline_df.flag.isin([-2, -1, 0, 1, 2])][
    ["D_2", "D_1", "O_1", "R_1", "R_2", "flag", "PREDICTED"]]
online_df_flag = online_df[online_df.flag.isin([-2, -1, 0, 1, 2])][
    ["D_2", "D_1", "O_1", "R_1", "R_2", "flag", "PREDICTED"]]
print("online有效信号个数：", online_df[online_df.flag.isin([-2, -1, 1, 2])].shape[0])
print("offline有效信号个数：", offline_df[offline_df.flag.isin([-2, -1, 1, 2])].shape[0])

concat_df = pd.merge(online_df_flag, offline_df_flag, how="outer", left_index=True, right_index=True)
concat_df = concat_df[concat_df["flag_y"] != 0]
concat_df = concat_df[concat_df["flag_x"] != 0]
print("线上线下信号五分类一致性:", concat_df[["flag_x", "flag_y"]].corr())
# concat_df
print("线上(x)线下(y)信号五分类不一致明细：")
print(concat_df[concat_df["flag_x"] != concat_df["flag_y"]])

# 生成信号文件
file_name_offline = "{}.txt".format(end_date[:4] + "-" + end_date[4:6] + "-" + end_date[6:])
generate_signal_file(offline_df, signal_offline_path, file_name_offline)
print("线下信号文件已生成！{}".format(os.path.join(signal_offline_path, file_name_offline)))


# In[ ]:


import random


predict = -1.51107
res1_4 = reg_get_cls_prob(predict, probs_table1,configs['maxMap'], configs['minMap'], configs["threshold"])
print(res1_4)
res2_4 = reg_get_cls_prob(predict, probs_table2,configs['maxMap'], configs['minMap'], configs["threshold"])
print(res2_4)

df = pd.Series([res2_4[0], res1_4[0], res1_4[1], res1_4[2], res2_4[2]], index=["D2", "D1", "O1", "R1", "R2"])
print("offline", translate(df,configs["probsThreshold"]))
print("=============")
res = generate_signal(predict, probs_table1, probs_table2, configs['minMap'], configs['maxMap'], 1.0, configs["probsThreshold"])
print("online", res)


# In[ ]:


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

from xquant.strategy.ats_backtest.batch_runner import BatchRunner
from xquant.strategy.ats_backtest.backtest_request_builder import BackTestRequestBuilder
import json
from xquant.strategy.ats_backtest.analyze.analyze_tool import AnalyzeTool
import ray

try:
    ray.shutdown()
except:
    pass


class TaskDemo(BatchRunner):
    def create_backtest_meta(self):
        tasks = []
        return tasks


# In[ ]:


from xquant.marketdata import MarketData
ma = MarketData()
    
# 策略jar包存储路径，用户需提前上传
strategy_path = "/data/user/013150/trade_data/backtest"
# 策略日志存储路径，按照策略ID分别打包成不同zip包。创建失败的策略实例无日志zip包
log_path = "/data/user/013150/trade_data/backtest/log"

# 创建回测任务
#     lib_path ="/data/user/quanttest007/backtest-algo/Test/lib"    
t = TaskDemo(strategy_path=strategy_path, log_path=log_path,
             cpus_per_node=2, mem_per_node=4, workers=2, local_cluster=True)

# strategy_param = json.load(open("/data/user/013150/trade_data/backtest/params/param.json", "r"))
os_param = "/data/user/013150/trade_data/backtest/backup202310_v3/param/param+sell.json"
if os.path.exists(os_param):
    strategy_param = json.load(open("/data/user/013150/trade_data/backtest/backup202310_v3/param/param+sell.json", "r"))
else:
    print("param path error")
    strategy_param = json.load(open("/data/user/013150/trade_data/backtest/backup202310_v3/param/param+sell.json", "r"))
strategy_param["策略标的"] = SYMBOL

res_dict = t.run([
    {
        "Strategy": "STARArbitrageSubStrategy",
        "BackTestTimeFrame": "PERIOD_Tick",
        "MarketDataSortType": "RECEIVE_TIME",
        "ReportTimeFrame": "PERIOD_Tick",
        "MarketDataTunnel": "CUSTOMIZED",
        'SpecHistoryMDService': 'XQUANT',
        'SpecHisotryMDServiceParam': {'xquantStartDate': backtest_date, 'xquantEndDate': backtest_date},
        "StartDate": None,
        "EndDate": None,
        "Match": "CUSTOMIZED",
        "CustomizedXmlFile": "bean.xml",
        "StrategyType": "CONSUMER",
        "PublisherFile": publisher_file,
        "BenchMarks": [],
        "BaseCash": 5000000,
        "Commission": 0.0003,
        "StampDuty": 0.001,
        "Environment": "UAT",
        "IndicatorFile": "",
        "EventIndicatorFile": "",
        "Universe": [
            {
                "Symbol": SYMBOL,
                "Quantity": 200000,
                "BuySecAcc": "devjy998a",
                "SellSecAcc": "devjy998a",
                "BuyTradeAcc": "devjy998a",
                "SellTradeAcc": "devjy998a",
                "PortfolioNo": "1",
                "PortfolioType": "1"
            }
        ],
        "future_position": [],
        "StrategyParam": strategy_param
    }])

# 分析运行结果
analyze_tool = AnalyzeTool(log_path=log_path, res_dict=res_dict)
# 获取本次回测的所有task_id
task_ids = analyze_tool.get_all_task_ids()

task_id = 0
for t_id in task_ids:
    resp_df = analyze_tool.get_result_by_task_id(t_id)
    # print(resp_df)

    # 获取本次任务的执行流水
    trade_records_df = analyze_tool.get_trade_records_by_task_id(t_id)
    print(trade_records_df.shape)

    backtest_result_df = analyze_tool.get_last_trade_reports_by_task_id(t_id)
    task_id = t_id

    try:
        write = pd.ExcelWriter(os.path.join(order_path, "trade_records_{}.xlsx".format(backtest_date)))

        trade_records_df.to_excel(write, sheet_name='trade', index=False)  # 写入文件的Sheet1

        backtest_result_df.to_excel(write, sheet_name='profit', index=False)
        write.save()
        write.close()
    except:
        print("暂无相关行情数据!")
        
print("trade_records_df:", trade_records_df.shape)
        
#022917
### 回测委托为空，模拟字段名
if trade_records_df.empty:
    content = {"symbol": ["000000.SH"],
                'side': ["ASK"],
                'quantity': ["0"],
                'entrustQty': ["0"],
                'orderStatus': ["CANCELL"],
                'entrustPx': ["0"],
                'cumAmount': ["0"],
                'price': ["0"],
                'createDate': [pd.to_datetime("1970-01-01 00:00:00")],
                'filledDate':[pd.to_datetime("1970-01-01 00:00:00")],
                'tradeDate':[pd.to_datetime("1970-01-01")]
            }
    trade_records_df = pd.DataFrame(content)
    
print("trade_records_df:", trade_records_df.shape)
# trade_date_offline = pd.to_datetime("2023-07-31").strftime("%Y-%m-%d")
trade_records_df = trade_records_df[trade_records_df["tradeDate"]==trade_date_offline]


print("trade_records_df:", trade_records_df.shape)
print("回测结果：\n {}".format(backtest_result_df))


# In[ ]:


pd.set_option("display.max_colwidth", 100)
pd.set_option("display.max_columns", 30)
pd.set_option("display.max_rows", 100)


if not trade_records_df.empty:
    res1 = deal_amount(trade_records_df)
    res2 = dealqty_and_entrustqty(trade_records_df)
    res3 = targets_num_in_strategy(trade_records_df)
    res4 = strategy_num(trade_records_df)
    res5 = order_strategy_quantity_statistics(trade_records_df)
    print(res1)
    print(res2)
    print(res3)
    print(res4)
    print(res5)



def plot_signal_fig_offline(signal_file, trade_record_df, ma_df):
    with open(signal_file, "r") as f:
        signal_list = []
        lines = f.readlines()
        for line in lines[1:]:
            signal = json.loads(json.loads(line)[2])
            signal["PROBABILITY"] = str(signal["PROBABILITY"])
            signal["RANGE"] = str(signal["RANGE"])
            signal = pd.Series(signal)
            signal_list.append(signal)

    df_signal = pd.DataFrame(signal_list)
    df_signal["PROBABILITY"] = df_signal["PROBABILITY"].apply(lambda x: eval(x))
    df_signal["RANGE"] = df_signal["RANGE"].apply(lambda x: eval(x))

    # df_order = pd.read_excel(trade_records_file, sheet_name=date)
    # df_order = parse_offline_trade_records(df_order)
    trade_record_df = trade_record_df.rename(columns={'symbol': '交易标的',
                                        'createDate': '委托时间',
                                        'side': '买卖方向',
                                        'orderStatus': '委托状态',
                                        'entrustPx': '委托价格',
                                        'entrustQty': '委托数量',
                                        'price': '成交均价',
                                        'quantity': '成交数量',
                                        'cumAmount': '成交金额',
                                        'filledDate': '成交时间'
                                        })
    df_order = parse_trade_records(trade_record_df)
    print(111)
    print(222)
    df_ma = ma_df
    mkdata_df = df_ma[((df_ma["MDTime"]>="092500000") & (df_ma["MDTime"]<="113000000")) |                     (((df_ma["MDTime"]>="130000000") & (df_ma["MDTime"]<="150000000")))]
#     mkdata_df["Date"] = mkdata_df.apply(lambda x: pd.to_datetime(x["MDDate"] + " " + x["MDTime"][:-3]), axis=1)
    try:
        mkdata_df["Date"] = mkdata_df.apply(lambda x: pd.to_datetime(x["MDDate"] + " " + x["MDTime"][:-3]+"."+x["MDTime"][-3:],format = "%Y-%m-%d %H:%M:%S.%f"), axis=1)
    except:
        mkdata_df["Date"] = mkdata_df.apply(lambda x: pd.to_datetime(x["MDDate"] + " " + x["MDTime"][:-3]), axis=1)

    # visual_path_offline = os.path.join(visual_path, "offline") + "/{}.html".format(df_order["tradeDate"].iloc[0])
    visual_path_offline = "./demo_off.html"
    fig_signal1 = analyze1(mkdata_df, df_signal, df_order, visual_path_offline)
    fig_signal2 = analyze2(mkdata_df, df_signal, df_order, visual_path_offline)
    return fig_signal1, fig_signal2


### online

def plot_signal_fig_online(signal_file, trade_record_df, ma_df):
    with open(signal_file, "r") as f:
        signal_list = []
        lines = f.readlines()
        for line in lines[1:]:
            signal = json.loads(json.loads(line)[2])
            signal["PROBABILITY"] = str(signal["PROBABILITY"])
            signal["RANGE"] = str(signal["RANGE"])
            signal = pd.Series(signal)
            signal_list.append(signal)

    df_signal = pd.DataFrame(signal_list)
#     df_signal = signal_df
    df_signal["PROBABILITY"] = df_signal["PROBABILITY"].apply(lambda x: eval(x))

    trade_record_df = trade_record_df.rename(columns={'Symbol': '交易标的',
                                        'CreatedDate': '委托时间',
                                        'Side': '买卖方向',
                                        'OrdStatus': '委托状态',
                                        'Price': '委托价格',
                                        'Quantity': '委托数量',
                                        'AveragePrice': '成交均价',
                                        'CumQuantity': '成交数量',
                                        'CumAmount': '成交金额',
                                        'ModifiedDate': '成交时间'
                                        })


    df_order = parse_trade_records(trade_record_df)

    df_ma = ma_df
    mkdata_df = df_ma[((df_ma["MDTime"]>="092500000") & (df_ma["MDTime"]<="113000000")) |                     (((df_ma["MDTime"]>="130000000") & (df_ma["MDTime"]<="150000000")))]
#     mkdata_df["Date"] = mkdata_df.apply(lambda x: pd.to_datetime(x["MDDate"] + " " + x["MDTime"][:-3]), axis=1)
    try:
        mkdata_df["Date"] = mkdata_df.apply(lambda x: pd.to_datetime(x["MDDate"] + " " + x["MDTime"][:-3]+"."+x["MDTime"][-3:],format = "%Y-%m-%d %H:%M:%S.%f"), axis=1)
    except:
        mkdata_df["Date"] = mkdata_df.apply(lambda x: pd.to_datetime(x["MDDate"] + " " + x["MDTime"][:-3]), axis=1)
#     mkdata_df["index"] = mkdata_df["Date"].apply(lambda x: pd.to_datetime(x))
#     mkdata_df = mkdata_df.set_index("index")
#     visual_path_offline = os.path.join(visual_path, "offline") + "/{}.html".format(df_order["TradeDate"].iloc[0])
#     visual_path_offline = os.path.join(visual_path, "offline") + "/{}.html".format(df_order["tradeDate"].iloc[0])
    visual_path_online = "./demo_on.html"
    fig_signal1 = analyze1(mkdata_df, df_signal, df_order, visual_path_online)
    fig_signal2 = analyze2(mkdata_df, df_signal, df_order, visual_path_online)
#     save_path = save_path_online
    
#     fig_signal1 = analyze1(mkdata_df, df_signal, df_order, save_path)
#     fig_signal2 = analyze2(mkdata_df, df_signal, df_order, save_path)
    return fig_signal1, fig_signal2



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

doc.add_text(f"factor_df.shape: {factor_df.shape}")  # handout: exclude
doc.show()  # handout: exclude

factor_df_dropna = factor_df.dropna(axis=0, how="all")  # handout: exclude
doc.add_text(f"factor_df_dropna.shape: {factor_df_dropna.shape}")  # handout: exclude
doc.show()  # handout: exclude

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
 **3.信号线上线下一致性分析**
"""

"""
 3.1 线上线下信号个数: 
"""
doc.add_text(f"factor_df shape: {factor_df.shape}")  # handout: exclude
doc.show()  # handout: exclude
doc.add_text(f"online预测信号总数: online df shape: {online_df.shape}")  # handout: exclude
doc.add_text(f"offline预测信号总数: offline df shape: {offline_df.shape}")  # handout: exclude
doc.show()  # handout: exclude

online_df_flag_shape = online_df[online_df.flag.isin([-2, -1, 1, 2])].shape[0]  # handout: exclude
doc.add_text(f"online有效信号个数：{online_df_flag_shape}")  # handout: exclude
doc.show()  # handout: exclude

offline_df_flag_shape = offline_df[offline_df.flag.isin([-2, -1, 1, 2])].shape[0]  # handout: exclude
doc.add_text(f"offline有效信号个数：{offline_df_flag_shape}")  # handout: exclude
doc.show()  # handout: exclude


"""
 3.2 信号的准确率：
"""

doc.add_html(stats_dict.to_html())  # handout: exclude
doc.show()  # handout: exclude

"""
 3.3 线上线下信号的相关性： 
"""

doc.add_html(tmp.corr().to_html())  # handout: exclude
doc.show()  # handout: exclude


"""
 3.4 线上线下信号五分类一致性:
"""
concat_df_corr = concat_df[["flag_x", "flag_y"]].corr()  # handout: exclude
doc.add_html(concat_df_corr.to_html())  # handout: exclude
doc.show()  # handout: exclude

"""
 3.5 线上(x)线下(y)信号五分类不一致明细：
"""
concat_df_diff = concat_df[concat_df["flag_x"]!=concat_df["flag_y"]] # handout: exclude
doc.add_html(concat_df_diff.to_html())  # handout: exclude
doc.show()  # handout: exclude
                 
"""
 3.6 不一致信号的准确率(9:33以前）：
"""

doc.add_html(stats_dict_diff.to_html())  # handout: exclude
doc.show()  # handout: exclude


                 
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
 **5. 线下信号回测&策略回测**

"""

doc.add_text(f"publisher_file：{publisher_file}")  # handout: exclude
doc.show()  # handout: exclude

doc.add_text(f"trade_records_df shape: {trade_records_df.shape}")  # handout: exclude
doc.show()  # handout: exclude

"""
 5.1 策略回测结果：
"""
doc.add_html(backtest_result_df.to_html())  # handout: exclude
doc.show()  # handout: exclude

"""
 5.2 线下策略成交绩效: 
"""
"成交金额指标"
# handout: begin-exclude
df_order_source_offline = trade_records_df
# df_order_source_offline["tradeDate"] = df_order_source_offline["tradeDate"].apply(lambda x:datetime.strptime(str(x),'%Y%m%d'))
df_order_source_offline = df_order_source_offline[df_order_source_offline["tradeDate"] == trade_date_offline]
res1 = pd.DataFrame.from_dict(deal_amount(df_order_source_offline),orient='index').T
doc.add_html(res1.to_html())
doc.show()
# handout: end-exclude   
"成交股数和委托股数指标"
# handout: begin-exclude
res2 = pd.DataFrame.from_dict(dealqty_and_entrustqty(df_order_source_offline),orient='index').T
doc.add_html(res2.to_html())
doc.show()
# handout: end-exclude   
"策略涉及的标的数"
# handout: begin-exclude
res3 = pd.DataFrame.from_dict(targets_num_in_strategy(df_order_source_offline),orient='index').T
doc.add_html(res3.to_html())
doc.show()
# handout: end-exclude   
"策略实例条数"
# handout: begin-exclude
res4 = pd.DataFrame.from_dict(strategy_num(df_order_source_offline),orient='index').T
doc.add_html(res4.to_html())
doc.show()
# handout: end-exclude  
"订单策略的全成、部成和不成数量统计"
# handout: begin-exclude
res5 = pd.DataFrame.from_dict(order_strategy_quantity_statistics(df_order_source_offline),orient='index').T
doc.add_html(res5.to_html())
doc.show()
# handout: end-exclude  
    
"""
 **6. 线上成交绩效一致性分析**

"""

"""
 6.1 线上成交图：
"""
                 
# handout: begin-exclude
signal_file = publisher_file 
try:
    ma_df = pd.read_parquet("/tmp/ma_df.parquet")
#     ma_df = ma_df.drop_duplicates(subset = ["MDTime"], keep = 'last')
#     ma_df = ma.get_data_by_date("EnhancedTick", SYMBOL, trade_date_online)
#     df_online_tmp = df_order_source
#     df_online_tmp["TradeDate"] = df_online_tmp["TradeDate"].apply(lambda x:datetime.strptime(str(x),'%Y%m%d'))
#     df_online_tmp = df_online_tmp[df_online_tmp["TradeDate"] == trade_date_online]
    sh_order_status_map_2 = {"6": "CANCELLED", "8": "DONE", "5": "PARTIALLY_CANCELLED", "9": "REJECTED"}
    sh_side_2 = {"1": "BID", "2": "ASK"}
    df_order_source_online_tmp = df_order_source_online
    df_order_source_online_tmp = df_order_source_online_tmp.rename(columns={"Symbol": "交易标的",
                                                'CreatedDate': '委托时间',
                                                'Side': '买卖方向',
                                                'OrdStatus': '委托状态',
                                                'Price': '委托价格',
                                                'Quantity': '委托数量',
                                                'AveragePrice': '成交均价',
                                                'CumQuantity': '成交数量',
                                                'CumAmount': '成交金额',
                                                })
    df_order_source_online_tmp["委托状态"] = df_order_source_online_tmp["委托状态"].apply(lambda x: sh_order_status_map_2[x])
    df_order_source_online_tmp["买卖方向"] = df_order_source_online_tmp["买卖方向"].apply(lambda x: sh_side_2[x])
    
    fig_signal1, fig_signal2 = plot_signal_fig_online(signal_file, trade_record_df=df_order_source_online_tmp, ma_df = ma_df) 
    
    doc.add_html(fig_signal1.to_html(full_html=False, )) 
    doc.show()
except:
    import traceback 
    print(traceback.print_exc())
    print("绘图失败！")
# handout: end-exclude

"""
 6.2 线下成交图：
"""
                 
# handout: begin-exclude
signal_file = publisher_file 
try:
    ma_df = pd.read_parquet("/tmp/ma_df.parquet")#ma.get_data_by_date("Stock", SYMBOL, backtest_date.replace("-", ""))
#     ma_df = ma_df.drop_duplicates(subset = ["MDTime"], keep = 'last')
#     print(trade_records_df)
    fig_signal1, fig_signal2 = plot_signal_fig_offline(signal_file, trade_record_df=trade_records_df, ma_df = ma_df)
    
    doc.add_html(fig_signal1.to_html(full_html=False, )) 
    doc.show()
    doc.add_html(fig_signal2.to_html(full_html=False, )) 
    doc.show() 
except:
    import traceback 
    print(traceback.print_exc())
    print("绘图失败！")
# handout: end-exclude

"""
 6.3 线上成交明细：
"""
# handout: begin-exclude
#print("df_order_online_source shape:", df_order_source.shape)
#print("df_order_online_source:", df_order_source.columns)

trade_online = online_trade_analysis(df_order_source_online)

doc.add_html(trade_online.to_html())  
doc.show()  
# handout: end-exclude          
              
"""
 6.4 线下成交明细：
"""
# handout: begin-exclude            
#trade_online["tradeDate_on"] = trade_online["tradeDate_on"].apply(lambda x:datetime.strptime(str(x),'%Y%m%d'))

trade_online = trade_online[["side_on", "quantity_on", "entrustPx_on", "price_on", "createDate_on", "filledDate_on", "tradeDate_on"]]
trade_offline = offline_trade_analysis(trade_records_df)
                 
doc.add_html(trade_offline.to_html())  
doc.show()  
# handout: end-exclude   
                 
"""
 6.5 线上线下成交明细对比（线上每笔创建时间之前最近的线下委托）：
"""
# handout: begin-exclude  

if not trade_online.empty: 
    trade_on_off = on_off_trade_analysis(trade_online, trade_offline)
    
    doc.add_html(trade_on_off.to_html())  # handout: exclude
    doc.show()  # handout: exclude

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

