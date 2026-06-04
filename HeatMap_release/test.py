import sys
from Stock_HeatMap_v1 import Stock_HeatMap
import plotly.io as pio
import os
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
import plotly.figure_factory as ff
import plotly.io as pio
from plotly.graph_objs import *
from plotly.subplots import make_subplots
# 需安装trade_mocker_rust(见http://168.7.17.87:8084/xquant/sdk-help/xquant-newapi/strategy/Xtrademocker/)和polars==0.20.5
# 暂不支持notebook运行，只能通过terminal运行
###SYMBOL: 标的名
###trade_date: 日期
###start_time,end_time: 画图的起止时间
###time_mode: 时间模式，'S'和'ms'两种，即秒级数据和逐笔数据
###num_mode: 调节买卖档位，最高可显示50档

# fig = Stock_HeatMap(SYMBOL="000977.SZ", trade_date = "20231215", start_time = "093000", end_time = "094000", time_mode = 'S', num_mode=20, base_dir="./")

import pandas as pd

# 设置起始时间与结束时间
start_time = pd.Timestamp('09:30:00')
end_time = pd.Timestamp('15:00:00')

# 生成时间序列，频率为10分钟
time_stamps = pd.date_range(start=start_time, end=end_time, freq='10T')

# 将生成的时间序列转换为字符串格式，如果需要的话
time_stamps_str = time_stamps.strftime('%H%M%S')
from artifacts import parse_format
import numpy as np
import ray


#print(time_stamps)
print(time_stamps_str)
symbol = "688047.SH"
date = "20240514"
os.system("python3 trade_test.py {} {}".format(symbol, date))
date1 = date[:4]+"-"+date[4:6]+"-"+date[6:]
#strategy_name = "unite_semi_test"
strategy_name = "l3_kc50_flying4"

signal_df = pd.read_excel("/dfs/user/013150/tmp/event/predictJson66_{}.xlsx".format(date1), sheet_name = symbol)
signal_df = signal_df[signal_df["STRATEGY_NAME"]==strategy_name]
signal_df["MDTime"] = signal_df["PERIOD_BEGIN"].apply(lambda x:pd.to_datetime(x).strftime("%H%M%S"))
signal_df["cls"] = signal_df["PROBABILITY"].apply(lambda x:np.argmax(eval(x)))
print(signal_df)



@ray.remote
def func_inner(iidx, i):
    if time_stamps_str[i]>="113000" and time_stamps_str[i] < "130000":
        return
    if time_stamps_str[i]>='150000':
        return
    fig = Stock_HeatMap(SYMBOL=symbol, trade_date = date, start_time = time_stamps_str[i], end_time = time_stamps_str[i+1], time_mode = 'S',num_mode=20, base_dir="./")
    if not os.path.exists(f'./{symbol}/'):
        os.makedirs(f'./{symbol}')
    sub_signal_df = signal_df[(signal_df["MDTime"]>=time_stamps_str[i]) & ((signal_df["MDTime"]<=time_stamps_str[i+1]))] 
    sell_group = sub_signal_df[(sub_signal_df["cls"]==0) | (sub_signal_df["cls"]==1)]
    buy_group = sub_signal_df[(sub_signal_df["cls"]==3) | (sub_signal_df["cls"]==4)]
    fig.add_trace(go.Scatter(name='BuyActivePriceVolume',
                                 x=buy_group['MDTime'], y=buy_group["TARGET_VALUE"],
                                 marker=dict(size=9, opacity=1, symbol="triangle-up"),
                                 mode='markers', line_color="red",
                                 ), secondary_y=False, row=1, col=1)

    fig.add_trace(go.Scatter(name='SellActivePriceVolume',
                                 x=sell_group['MDTime'], y=sell_group["TARGET_VALUE"],
                                 marker=dict(size=9, opacity=1, symbol="triangle-down"),
                                 mode='markers', line_color="green",
                                 ), secondary_y=False, row=1, col=1)



    pio.write_image(fig, f'./{symbol}/{symbol}_{date}_{time_stamps_str[i]}.png', format='png',width=1920, height=1080,scale=1)

tasks = []
for iidx,i in enumerate(range(len(time_stamps_str)-1)):
    tasks.append(func_inner.remote(iidx, i))

ray.get(tasks)


