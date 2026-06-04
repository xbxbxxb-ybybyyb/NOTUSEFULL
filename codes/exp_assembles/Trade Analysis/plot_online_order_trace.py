
from collections import deque
##################### 逐笔 有效 订单 追踪 #########################
def check_position(inv_long, inv_short):
    res = 0
    if len(inv_long) >= 0:
        for i in inv_long:
            res += i["Q"]
    if len(inv_short) >= 0:
        for i in inv_short:
            res -= i["Q"]       
    return res

def FIFO_trace(trade_online):
    # 定义多单存货栈， 空单存货栈, 采取FIFO方式计价
    inv_long  = deque([])
    inv_short = deque([])
    position = []
    record = []
    info = []
    benfits = []
    for no, row in trade_online.iterrows():
        tmp_record = []
        gl = 0
        if row.orderStatus_on in ["DONE", "PARTIALLY_CANCELLED"]:
        ############### 有 效 单 ####################
            if row.side_on == "BID": # 遇到买单
                if len(inv_short) > 0: # 先检查是否为空单平仓
                    flow_q = row.quantity_on # 本次操作的量
                    while flow_q>0 and len(inv_short) > 0: # 循环消费空单
                        # 收益为 本期量价 减去 FIFO量价
                        if inv_short[0]["Q"] == flow_q:      
                            # print("情况1 第一笔空单正好满足本次平仓")
                            tmp_record.append(inv_short[0])
                            gl += flow_q * (inv_short[0]["P"] - row.entrustPx_on) 
                            flow_q = 0
                            inv_short.popleft()
                            
                        elif inv_short[0]["Q"] > flow_q: 
                            #print("情况2 消费第一笔空单的部分")
                            gl += flow_q * (inv_short[0]["P"]  - row.entrustPx_on) 
                            inv_short[0]["Q"] -=  flow_q  
                            tmp_record.append({"Q":flow_q, "P":inv_short[0]["P"], "T":inv_short[0]["T"]})
                            flow_q = 0
                        else: 
                            #print("情况3 第一笔空单不够消费")
                            tmp_record.append(inv_short[0])
                            gl += inv_short[0]["Q"] * (inv_short[0]["P"] - row.entrustPx_on) 
                            flow_q -= inv_short[0]["Q"]
                            inv_short.popleft()
                            if len(inv_short)==0: # 如果最后一个空单消费完了仍然不够cover CF， 则反向开多仓
                                inv_long.append({"Q":flow_q, "P":row.entrustPx_on, "T":row.MDTime})
                     
                                
                else: # 如若不是，必为多单开仓
                    #print("多单开仓")
                    inv_long.append({"Q":row.quantity_on, "P":row.entrustPx_on, "T":row.MDTime})
                    
            elif row.side_on == "ASK": # 卖方
                if len(inv_long) > 0: # 先检查是否为多单平仓
                    flow_q = row.quantity_on # 本次操作的量
                    while flow_q>0 and len(inv_long) > 0: # 循环消费多单
                        # 收益为 FIFO量价 减去 本期量价 
                        if inv_long[0]["Q"] == flow_q:      
                            #print("情况1 第一笔多单正好满足本次平仓")
                            tmp_record.append(inv_long[0])
                            gl += flow_q * (row.entrustPx_on - inv_long[0]["P"])  
                            flow_q = 0
                            inv_long.popleft()
                            
                        elif inv_long[0]["Q"] > flow_q: 
                            #print("情况2 消费第一笔多单的部分")
                            gl += flow_q * (row.entrustPx_on - inv_long[0]["P"])  
                            inv_long[0]["Q"] -= flow_q  
                            #print(inv_long[0]["Q"])
                            tmp_record.append({"Q":flow_q, "P":inv_long[0]["P"], "T":inv_long[0]["T"] })
                            flow_q = 0
                            
                        else: 
                            #print("情况3 第一笔多单不够消费")
                            tmp_record.append(inv_long[0])
                            gl += inv_long[0]["Q"] * (row.entrustPx_on - inv_long[0]["P"]) 
                            flow_q -= inv_long[0]["Q"]
                            inv_long.popleft()
                            if len(inv_long)==0: # 如果最后一个多单消费完了仍然不够cover CF， 则反向开空仓
                                inv_short.append({"Q":flow_q, "P":row.entrustPx_on, "T":row.MDTime})                    
                else: # 如若不是，必为空单开仓
                    #print("空单开仓")
                    inv_short.append({"Q":row.quantity_on, "P":row.entrustPx_on, "T":row.MDTime})
                       
#             print("时间{},方向{},状态{},价格{},量{}".format(row.MDTime, row.side_on, row.orderStatus_on, row.entrustPx_on, row.quantity_on)) 
#             print("LONG", inv_long)
#             print("SHORT", inv_short)
#             print("本期消费",tmp_record)
#             print("G/L: ", gl)
#             print()
        benfits.append(gl)
        record.append(tmp_record)
        pos = check_position(inv_long, inv_short)
        position.append(pos)
    
#     print("Finish")
    return record, position, benfits


from plotly.subplots import make_subplots
import plotly.graph_objects as go

def plot_daily_analysis(data):
    """画图"""

    fig = make_subplots(rows=3, cols=1,shared_xaxes=True, 
                            vertical_spacing=0.02, 
                            row_heights=[0.8, 0.2, 0.15],
                            subplot_titles = ["Daily points", "Position", "Gain/Loss"]
                               )
    
    # 绘制买一价
    fig.add_trace(go.Scatter(x=data["MDTime"], y=data["Buy1Price"], name="Buy1Price", showlegend=True,
                             fill = None, line_color = "skyblue"), 
                    row=1, col=1
    )    
    
    # 绘制卖一价
    fig.add_trace(go.Scatter(x=data["MDTime"], y=data["Sell1Price"], name="Sell1Price", showlegend=True,
                             fill = "tonexty", line_color = "skyblue", fillcolor="rgba(0,179,0,0.4)"), 
                    row=1, col=1
    )    

    # Bid 未成
    fig.add_trace(go.Scatter(x=data["MDTime"], y=data["Buy_Canceled"], name="Buy_Canceled", showlegend=True,
                             mode='markers', line_color="pink", marker=dict(size=7, opacity=1)), 
                    row=1, col=1
    )    
    
    # Ask 未成
    fig.add_trace(go.Scatter(x=data["MDTime"], y=data["Sell_Canceled"], name="Sell_Canceled", showlegend=True,
                             mode='markers', line_color="lightgreen", marker=dict(size=7, opacity=1)), 
                    row=1, col=1
    )    
    # Bid成交
    fig.add_trace(go.Scatter(x=data["MDTime"], y=data["Buy_Executed"], name="Buy_Executed", showlegend=True,
                             mode='markers', line_color="red", marker=dict(size=7, opacity=1),
                             text = data["info"] ), 
                    row=1, col=1
    )    
    
    # Ask 成交
    fig.add_trace(go.Scatter(x=data["MDTime"], y=data["Sell_Executed"], name="Sell_Executed", showlegend=True,
                             mode='markers', line_color="green", marker=dict(size=7, opacity=1),
                             text = data["info"]), 
                    row=1, col=1
    )    
    
    ######################### part 2 #############################
    # 绘制持仓头寸
    fig.add_trace(go.Scatter(x=data['MDTime'], y=data['position'], showlegend=False, name="Position",
                             fill = "tozeroy", fillcolor="rgba(135,206,250,0.4)", line_color = "rgba(135,206,250,1)"),
                  row=2, col=1)

    # 绘制收益金额
    fig.add_trace(go.Scatter(x=data['MDTime'], y=data['Cumbenfits'], showlegend=False, name="Cumbenfits",
                             fill = "tozeroy", fillcolor="rgba(250,179,135,0.4)", line_color = "rgba(250,179,135,1)"),
                  row=3, col=1)

    fig.update(layout_xaxis_rangeslider_visible=False)
    fig.update_xaxes(tickvals=list(all_df["MDTime"][::100]))
    fig.update_layout(width = 1000, height = 800,
                legend = dict(orientation = "h", yanchor = "top"))
    #fig.show()
    return fig


# plot_daily_analysis(all_df)


def make_plot_col(row, types):
    if types == "Buy_Executed":
        if row.side_on == "BID" and row.orderStatus_on != "CANCELLED":
            return row.entrustPx_on
        else:
            return np.nan
    if types == "Sell_Executed":
        if row.side_on == "ASK" and row.orderStatus_on != "CANCELLED":
            return row.entrustPx_on
        else:
            return np.nan
    if types == "Buy_Canceled":
        if row.side_on == "BID" and row.orderStatus_on == "CANCELLED":
            return row.entrustPx_on
        else:
            return np.nan
    if types == "Sell_Canceled":
        if row.side_on == "ASK" and row.orderStatus_on == "CANCELLED":
            return row.entrustPx_on
        else:
            return np.nan
        
def points_info(row):
    info = ""
    if row.side_on == "BID" and row.orderStatus_on != "CANCELLED":
        info += "买入{}股: ".format(row.quantity_on)
        if len(row.record) == 0:
            info += "【多头开仓】"
        else:
            for i in row.record:
                tt = str(i["T"])[:-4] + ":" + str(i["T"])[-4:-2] + ":" + str(i["T"])[-2:] 
                info += "【平{}的空仓{}股, 收益为{}】".format(tt, str(i["Q"]), str(round(row.benfits)))
                
    if row.side_on == "ASK" and row.orderStatus_on != "CANCELLED":
        info += "卖出{}股: ".format(row.quantity_on)
        if len(row.record) == 0:
            info += "【空头开仓】"
        else:
            for i in row.record:
                tt = str(i["T"])[:-4] + ":" + str(i["T"])[-4:-2] + ":" + str(i["T"])[-2:] 
                info += "【平{}的多仓{}股, 收益为{}】".format(tt, str(i["Q"]), str(round(row.benfits)))
    return info

def plot_online_order_trace(trade_records_df, ma_df):
#     trade_records_df = pd.read_parquet("trade_records_20231017.parquet")
    trade_online = trade_records_df[["Symbol", "Side", "CumQuantity", "Quantity", "OrdStatus", "Price", "CumAmount", "AveragePrice","CreatedDate", "ModifiedDate", "TradeDate"]]
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
    symbol = trade_online["symbol_on"][0]
    symbol_map = {symbol:symbol+".SH"}
    trade_online["symbol_on"] = trade_online["symbol_on"].apply(lambda x: symbol_map[x])

    side_map = {"1":"BID", "2":"ASK"}
    trade_online["side_on"] = trade_online["side_on"].apply(lambda x: side_map[x])

    ord_map = {"8":"DONE", "5":"PARTIALLY_CANCELLED", "6":"CANCELLED"}
    trade_online["orderStatus_on"] = trade_online["orderStatus_on"].apply(lambda x: ord_map[x])

    trade_online["MDTime"] = trade_online["createDate_on"].apply(lambda x:int(str(x)[11:].replace(":","")))

    trade_online = trade_online[["side_on", "quantity_on", "orderStatus_on","cumAmount_on", "entrustPx_on", "price_on", 
                              "createDate_on", "filledDate_on", "MDTime"]]    

#     trade_online.iloc[20:30]
    record, position, benfits = FIFO_trace(trade_online)
    trade_online["record"] = record
    trade_online["position"] = position
    trade_online["benfits"] = benfits
    trade_online["Cumbenfits"] = trade_online["benfits"].cumsum()
    
#     ma_df = pd.read_parquet("ma_df_20231017.parquet")
    ma_df = ma_df[["MDDate", "MDTime", "SecurityID", "Symbol", "TotalValueTrade", "LastPx", "Buy1Price", "Sell1Price"]]
    ma_df["Volume"] = ma_df["TotalValueTrade"].diff().fillna(0)
    ma_df["MidPx"] = (ma_df["Buy1Price"] + ma_df["Sell1Price"]) /2
    ma_df["MDTime"] = ma_df["MDTime"].apply(lambda x:int(x[0:6])) 
    ma_df = ma_df[((ma_df["MDTime"]>93000)&(ma_df["MDTime"]<113000)) | ((ma_df["MDTime"]>130000)&(ma_df["MDTime"]<145500))]
    ma_df = ma_df.drop(columns=[ "TotalValueTrade"])
#     print(len(ma_df), len(trade_online))
    all_df = pd.merge(ma_df, trade_online, how="outer", left_on="MDTime", right_on="MDTime")
# print(len(all_df))
    all_df = all_df.sort_values("MDTime")

    for i in list(ma_df.columns)+["position","benfits"]:
        all_df[i] = all_df[i].fillna(method="ffill")
        all_df[i] = all_df[i].fillna(0)
    all_df["MDTime"] = all_df["MDTime"].apply(lambda x: "{}:{}:{}".format(str(x)[:-4],str(x)[-4:-2],str(x)[-2:]  ))
#     all_df.iloc[2000:2050]


        
        
    all_df["Buy_Executed"]  = all_df.apply(lambda row: make_plot_col(row,types="Buy_Executed"), axis=1 )
    all_df["Sell_Executed"] = all_df.apply(lambda row: make_plot_col(row,types="Sell_Executed"), axis=1 )
    all_df["Buy_Canceled"]  = all_df.apply(lambda row: make_plot_col(row,types="Buy_Canceled"), axis=1 )
    all_df["Sell_Canceled"] = all_df.apply(lambda row: make_plot_col(row,types="Sell_Canceled"), axis=1 )
    all_df["info"] = all_df.apply(lambda x: points_info(x),axis=1) 
    
    return all_df

# all_df.head()

# trade_online[trade_online["quantity_on"]>=1].iloc[22:35]

trade_records_df = pd.read_parquet("trade_records_20231017.parquet")
ma_df = pd.read_parquet("ma_df_20231017.parquet")
all_df = plot_online_order_trace(trade_records_df, ma_df)
plot_daily_analysis(all_df)
