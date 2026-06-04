#!/usr/bin/env python
# coding: utf-8

# In[1]:


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
import warnings
import time
import string
import random

warnings.filterwarnings('ignore')


# In[11]:


import numpy as np
import pandas as pd
import polars as pl
import datetime as dt
import os
import copy
from xquant.xqutils.perf_profile import profile

debug = False

def get_l2p_data(symbol, date, use_pandas=False, base_dir="./"):
    file_path = os.path.join(base_dir, f"{symbol}_{date}.parquet")
    if not os.path.exists(file_path):
        os.system("cd {} && python3 trade_test.py {} {}".format(base_dir, symbol, date))
    if use_pandas:
        l2p_df = pd.read_parquet(file_path)
        l2p_df = l2p_df[
            (l2p_df["mdtime"] >= int(date + '093000000')) & (l2p_df["mdtime"] <= int(date + '113000000')) | (
                    l2p_df["mdtime"] >= int(date + '130000000')) & (l2p_df["mdtime"] <= int(date + '145700000'))]
        l2p_df["MDTime"] = l2p_df["mdtime"].astype(str).apply(lambda x: int(x[8:]))
        l2p_df['AskP0'] = l2p_df["asks_price"].apply(lambda x: x[0])
        l2p_df['BidP0'] = l2p_df["bids_price"].apply(lambda x: x[0])
        l2p_df['AskV0'] = l2p_df["asks_qty"].apply(lambda x: x[0])
        l2p_df['BidV0'] = l2p_df["bids_qty"].apply(lambda x: x[0])
        l2p_df['LastAskP0'] = l2p_df["AskP0"].shift(1)
        l2p_df['LastBidP0'] = l2p_df["BidP0"].shift(1)
        l2p_df['LastAskV0'] = l2p_df["AskV0"].shift(1)
        l2p_df['LastBidV0'] = l2p_df["BidV0"].shift(1)
        l2p_df["LevelOneChg"] = (l2p_df['LastAskP0'] != l2p_df["AskP0"]) |                                               (l2p_df['LastBidP0'] != l2p_df["BidP0"]) |                                               (l2p_df['LastAskV0'] != l2p_df["AskV0"]) |                                               (l2p_df['LastBidV0'] != l2p_df["BidV0"])
    else:
        l2p_df = pl.read_parquet(file_path)
        l2p_df = l2p_df.filter(
            (l2p_df["mdtime"] >= int(date + '093000000')) & (l2p_df["mdtime"] <= int(date + '113000000')) |
            (l2p_df["mdtime"] >= int(date + '130000000')) & (l2p_df["mdtime"] <= int(date + '145700000')))
        l2p_df = l2p_df.with_columns(MDTime=pl.col("mdtime").map_elements(lambda x: int(str(x)[8:])),
                                     AskP0=pl.col('asks_price').list.first(),
                                     BidP0=pl.col('bids_price').list.first(),
                                     AskV0=pl.col('asks_qty').list.first(),
                                     BidV0=pl.col('bids_qty').map_elements(lambda x: x[0]))

        l2p_df = l2p_df.with_columns( ((pl.col('AskP0') != pl.col("AskP0").shift(1)) |
                        (pl.col('BidP0') != pl.col("BidP0").shift(1)) |
                        (pl.col('AskV0') != pl.col("AskV0").shift(1)) |
                        (pl.col('BidV0') != pl.col("BidV0").shift(1))).alias("LevelOneChg") )
    return l2p_df


# @profile
def get_l2p_trade_order_date(symbol, date, merge_one_order = False, use_pandas=True, base_dir="./"):
    l2p_df = get_l2p_data(symbol, date, use_pandas, base_dir)
    if use_pandas:
        tick_df = l2p_df[['mdtime', 'last_price', 'asks_price', 'bids_price', 'asks_qty',
                          'bids_qty', 'asks_count', 'bids_count', 'high_price', 'low_price',
                          'prev_close_price', 'ttl_volume', 'ttl_turn_over', 'ttl_trade_num',
                          'avg_ask_price', 'avg_bid_price', 'recvtime', 'msg_order_type', 'msg_trade_type',
                          'last_seq_num',  "AskP0", "BidP0", "AskV0", "BidV0", "LevelOneChg"
                          ]]
        order_df = l2p_df[["mdtime", 'msg_order_type', 'msg_bsflag', 'msg_price',
                           'msg_qty', 'msg_amt', 'msg_buy_no', 'msg_sell_no', "last_seq_num", "recvtime"]]
        trade_df = l2p_df[["mdtime", 'msg_trade_type', 'msg_bsflag', 'msg_price',
                           'msg_qty', 'msg_amt', 'msg_buy_no', 'msg_sell_no', "last_seq_num", "recvtime"]]
        order_df = order_df.rename(columns={"msg_order_type": "OrderType",
                                            "msg_bsflag": "BSFlag", "msg_price": "Price",
                                            "msg_qty": "Volume", "last_seq_num": "DataIndex",
                                            "mdtime": "Timestamp", "msg_amt": "Amount"})
        trade_df = trade_df.rename(columns={"msg_trade_type": "TradeType",
                                            "msg_bsflag": "BSFlag", "msg_price": "Price",
                                            "msg_qty": "Volume", "last_seq_num": "DataIndex",
                                            "mdtime": "Timestamp", "msg_amt": "Amount"})
        tick_df = tick_df.rename(columns={
            'asks_price': 'AskPrice', 'bids_price': 'BidPrice',
            'asks_qty': 'AskVolume', 'bids_qty': 'BidVolume',
            "last_seq_num": "DataIndex",
            'msg_order_type': 'OrderType',
            'msg_trade_type': 'TradeType',
            "mdtime": "Timestamp"
        })

        if symbol.endswith("SH"):
            order_df = order_df[order_df["OrderType"] != -1]
            trade_df = trade_df[trade_df["TradeType"] != -1]
            cancel_df = order_df[order_df["OrderType"] == 10]
            order_df = order_df[order_df["OrderType"] != 10]
        else:
            order_df = order_df[order_df["OrderType"] != -1]
            trade_df = trade_df[trade_df["TradeType"] != -1]
            cancel_df = trade_df[trade_df["TradeType"] == 1]
            trade_df = trade_df[trade_df["TradeType"] != 1]

        if merge_one_order:
            order_df, trade_df, tick_df = merge_one_order_trade(symbol, order_df, trade_df, tick_df, use_pandas)
    else:
        tick_df = l2p_df.select([
            "mdtime", "last_price", "asks_price", "bids_price", "asks_qty", "bids_qty", "asks_count", "bids_count",
            "high_price", "low_price", "prev_close_price", "ttl_volume", "ttl_turn_over", "ttl_trade_num",
            "avg_ask_price", "avg_bid_price", "recvtime", "msg_order_type", "msg_trade_type", "last_seq_num",
            "AskP0", "BidP0", "AskV0", "BidV0", "LevelOneChg"
        ])
        order_df = l2p_df.select([
            "mdtime", "msg_order_type", "msg_bsflag", "msg_price", "msg_qty", "msg_amt", "msg_buy_no",
            "msg_sell_no",
            "last_seq_num", "recvtime"
        ]).rename({"msg_order_type": "OrderType",
                   "msg_bsflag": "BSFlag", "msg_price": "Price",
                   "msg_qty": "Volume", "last_seq_num": "DataIndex",
                   "mdtime": "Timestamp", "msg_amt": "Amount"})
        trade_df = l2p_df.select([
            "mdtime", "msg_trade_type", "msg_bsflag", "msg_price", "msg_qty", "msg_amt", "msg_buy_no",
            "msg_sell_no",
            "last_seq_num", "recvtime"
        ]).rename({"msg_trade_type": "TradeType",
                   "msg_bsflag": "BSFlag", "msg_price": "Price",
                   "msg_qty": "Volume", "last_seq_num": "DataIndex",
                   "mdtime": "Timestamp", "msg_amt": "Amount"})
        tick_df = tick_df.rename({
            'asks_price': 'AskPrice', 'bids_price': 'BidPrice',
            'asks_qty': 'AskVolume', 'bids_qty': 'BidVolume',
            "last_seq_num": "DataIndex",
            'msg_order_type': 'OrderType',
            'msg_trade_type': 'TradeType',
            "mdtime": "Timestamp"
        })
        if symbol.endswith("SH"):
            order_df = order_df.filter(pl.col("OrderType") != -1)
            trade_df = trade_df.filter(pl.col("TradeType") != -1)
            cancel_df = order_df.filter(pl.col("OrderType") == 10)
            order_df = order_df.filter(pl.col("OrderType") != 10)
        else:
            order_df = order_df.filter(pl.col("OrderType") != -1)
            trade_df = trade_df.filter(pl.col("TradeType") != -1)
            cancel_df = trade_df.filter(pl.col("TradeType") == 1)
            trade_df = trade_df.filter(pl.col("TradeType") != 1)

        if merge_one_order:
            order_df, trade_df, tick_df = merge_one_order_trade(symbol, order_df, trade_df, tick_df, use_pandas)
        # print(new_tick_df.shape)
        # print(tick_df.shape)
    return tick_df, order_df, trade_df, cancel_df


# In[3]:


def l2p_data_prepare(l2p_data, time_mode='S'):
    l2p_data = l2p_data[['mdtime','asks_price','asks_qty','bids_price','bids_qty','high_price','low_price','prev_close_price','last_price', "ttl_volume"]]
    l2p_data = l2p_data.to_pandas()
    columns_map = {'asks_price':'M_SellPrice','asks_qty':'M_SellOrderQty','bids_price':'M_BuyPrice','bids_qty':'M_BuyOrderQty'}
    l2p_data.rename(columns=columns_map,inplace=True)
    
    l2p_data = l2p_data.drop_duplicates(subset=['mdtime'],keep='last')
    l2p_data = l2p_data.reset_index()
    
    if time_mode == 'S':
        l2p_data['M_MDTime'] = l2p_data['mdtime'].apply(lambda x: str(x)[8:14])
        
        l2p_data = l2p_data.groupby('M_MDTime').last()
        l2p_data.index = pd.to_datetime(l2p_data.index, format='%H%M%S')

        # 确保数据按时间顺序排序
        l2p_data.sort_index(inplace=True)

        # 以秒为单位进行重采样，并进行前向填充
        l2p_data = l2p_data.resample('1S').ffill()

        # 如果需要，可以再将索引转换回原始格式
        l2p_data.index = l2p_data.index.strftime('%H%M%S')
        l2p_data['M_MDTime'] = l2p_data.index
    elif time_mode == 'ms':
        l2p_data['M_MDTime'] = l2p_data['mdtime'].apply(lambda x: str(x)[8:])
        
    l2p_data.index = l2p_data['M_MDTime']
    
    l2p_data['Sell1'] = l2p_data['M_SellPrice'].apply(lambda x: x[0])
    l2p_data['Buy1'] = l2p_data['M_BuyPrice'].apply(lambda x: x[0])
    l2p_data["Volume"] = l2p_data["ttl_volume"]-l2p_data["ttl_volume"].shift(1)
    
    return l2p_data


# In[4]:


def order_data_prepare(l2p_data):
    order_b = l2p_data[['M_MDTime','M_BuyPrice','M_BuyOrderQty']]
    order_s = l2p_data[['M_MDTime','M_SellPrice','M_SellOrderQty']]

    order_b_qty = order_b[['M_MDTime','M_BuyOrderQty']].explode('M_BuyOrderQty')
    order_b_px = order_b[['M_MDTime','M_BuyPrice']].explode('M_BuyPrice')
    order_b_px['M_BuyOrderQty'] = order_b_qty['M_BuyOrderQty']

    order_s_qty = order_s[['M_MDTime','M_SellOrderQty']].explode('M_SellOrderQty')
    order_s_px = order_s[['M_MDTime','M_SellPrice']].explode('M_SellPrice')
    order_s_px['M_SellOrderQty'] = order_s_qty['M_SellOrderQty']

    order_data_b = order_b_px.reset_index(drop=True)
    order_data_s = order_s_px.reset_index(drop=True)

    order_data_b = order_data_b.fillna(value=0)
    order_data_b = order_data_b.rename(columns = {'M_BuyPrice':'price','M_BuyOrderQty':'bid_size'})
    order_data_b['ask_size'] = 0
    order_data_b['identifier'] = order_data_b['M_MDTime']

    order_data_s = order_data_s.fillna(value=0)
    order_data_s = order_data_s.rename(columns = {'M_SellPrice':'price','M_SellOrderQty':'ask_size'})
    order_data_s['bid_size'] = 0
    order_data_s['identifier'] = order_data_s['M_MDTime']

    df = pd.concat([order_data_b,order_data_s])
    df.index = df['M_MDTime']
    
    return df


# In[5]:


def heatmap_size_prepare(df):
    # 假设df是您的DataFrame，其中index是时间，'price'是您想要排序的列
    df = df.sort_values(by='price', ascending=True, kind='mergesort')  # 使用稳定的排序算法保持原始顺序不变
    # 创建新的列并为每组时间内的行分配顺序，范围是-5到5
    df['order'] = df.groupby(level=0).cumcount().apply(lambda x: (x - 10) if x < 10 else (x - 9))
    
    # df['sum'] = np.log10(df['bid_size']+1)-np.log10(df['ask_size']+1)
    df['sum'] = df['bid_size'] - df['ask_size']
    min_set = (df['bid_size'] + df['ask_size']).mean()
    df['sum'] = df['sum'].apply(lambda x: max((x/(x+min_set)-0.2),0.05) if x > 0 else min((x/(-x+min_set)+0.2),-0.05))

    return df


# In[6]:


def plot(df,l2p_data):

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[170, 30],
                        vertical_spacing=0.0,)

#     fig.add_trace(go.Scatter(x=self.df2['identifier'], y=self.df2['price'], text=self.df2['text'],
#                             name='VolumeProfile', textposition='middle right',
#                             textfont=dict(size=10, color='rgb(0, 0, 255, 0.0)'), hoverinfo='none',
#                             mode='text', showlegend=True,
#                             marker=dict(
#                             sizemode='area',
#                             sizeref=0.1,  # Adjust the size scaling factor as needed
#                             )), row=1, col=1)

    fig.add_trace(
        go.Heatmap(
            x=df['identifier'],
            y=df['price'],
            z=df['sum'],
#             z=df['order'],
#             text=df['text'],
            colorscale='rdylgn_r',
#             colorscale = grey_scale,
#             ygap=8,
#             xgap=8,
            showscale=False,
            showlegend=True,
            name='BidAsk',
            ),
        row=1,
        col=1)


    fig.add_trace(go.Scatter(name='Buy1',
                             x=l2p_data['M_MDTime'],
                             y=l2p_data['Buy1'],line_width=1,
                             line_color="orange"), row=1, col=1)
    
    fig.add_trace(go.Scatter(name='Sell1',
                             x=l2p_data['M_MDTime'],
                             y=l2p_data['Sell1'],line_width=1,
                             line_color="skyblue"), row=1, col=1)
    
    fig.add_trace(go.Bar(name='Volume',
                     x=l2p_data['M_MDTime'], y=l2p_data['Volume'], marker=dict(color="black"),#rgb(0, 139, 0)
                     # text = df["probs"]
                     ), secondary_y=False, row=2, col=1)


    fig.update_layout(title='Buy&Sell 20',
#                     yaxis=dict(title='Price', showgrid=False, range=[
#                                 ymax, ymin], tickformat='.3f'),
#                     yaxis2=dict(fixedrange=True, showgrid=False),
#                     xaxis2=dict(title='Time', showgrid=False),
#                     xaxis=dict(showgrid=False, range=[xmin, xmax]),
#                         height=1000,
                    paper_bgcolor='#FFFFFF', plot_bgcolor='#FFFFFF',
                    dragmode='pan', 
                    autosize=True
#                         margin=dict(l=10, r=0, t=40, b=20),
                     )

    fig.update_xaxes(
        showspikes=True,
        spikecolor="white",
        spikesnap="cursor",
        spikemode="across",
        spikethickness=0.25,
        tickmode='array',
#         tickvals=tickvals,
#         ticktext=ticktext
    )
    fig.update_yaxes(
        showspikes=True,
        spikecolor="white",
        spikesnap="cursor",
        spikemode="across",
        spikethickness=0.25)
    fig.update_layout(spikedistance=1000, hoverdistance=100)

    config = {
        'modeBarButtonsToRemove': ['zoomIn', 'zoomOut', 'zoom', 'autoScale'],
        'scrollZoom': True,
        'displaylogo': False,
        'modeBarButtonsToAdd': ['drawline',
                                'drawopenpath',
                                'drawclosedpath',
                                'drawcircle',
                                'drawrect',
                                'eraseshape'
                                ]
    }



    return fig


# In[7]:


def Stock_HeatMap(SYMBOL="000977.SZ", trade_date = "20231215", start_time = "093000", end_time = "094000", time_mode = 'S',base_dir="./"):
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    l2p_data = get_l2p_data(SYMBOL, trade_date, base_dir=base_dir)
    tick_df, order_df, trade_df, cancel_df = get_l2p_trade_order_date(SYMBOL, trade_date, base_dir=base_dir)
    l2p_data = l2p_data_prepare(l2p_data, time_mode=time_mode)
    df = order_data_prepare(l2p_data)
    df = heatmap_size_prepare(df)
    df_tmp = df[(df['identifier']>=start_time) & (df['identifier']<=end_time)]
    l2p_data_tmp = l2p_data[(l2p_data['M_MDTime']>=start_time) & (l2p_data['M_MDTime']<=end_time)]
    df_tmp = df_tmp.sort_index()
    l2p_data_tmp = l2p_data_tmp.sort_index()

    fig = plot(df_tmp,l2p_data_tmp)
    
    return fig


# In[12]:


# import plotly.io as pio

# SYMBOL="000977.SZ"
# trade_date = "20231215"
# start_time = "093000"
# end_time = "094000"
# time_mode = 'S'

# fig = Stock_HeatMap(SYMBOL=SYMBOL, trade_date = trade_date, start_time = start_time, end_time = end_time, time_mode = time_mode, base_dir="./")
# pio.write_image(fig, 'demo.png', format='png',width=1920, height=1080,scale=1)

