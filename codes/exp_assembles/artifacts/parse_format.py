import pandas as pd
import json
import datetime as dt
from xquant.xqutils.perf_profile import profile
pd.set_option("display.max.columns", 20)

def parse_online_trade_records(trade_records):
    """
    将线上成交数据，转化为ATS线下回测结构
    :param trade_records:
    :return:
    """
    # 返回和ATS一致的数据结构
    trade_records_df = trade_records.rename(columns={
        "SecurityId": "symbol",
        "Side": "side",
        "Quantity": "entrustQty",
        "CumQuantity": "quantity",
        'Price': 'entrustPx',
        'AveragePrice': 'price',
        'OrdStatus': 'orderStatus',
        'CreatedDate': 'createDate',
        'TransactTime': 'filledDate'
    })

    # df_order_source["Side"] = df_order_source["Side"].astype(int)
    # df_order_source["CumQuantity"] = df_order_source["CumQuantity"].astype(float)
    # df_order_source["CumNetMoney"] = df_order_source["CumNetMoney"].astype(float)
    # df_order_source["CumAmount"] = df_order_source["CumAmount"].astype(float)
    # df_order_source["Price"] = df_order_source["Price"].astype(float)
    # df_order_source["AveragePrice"] = df_order_source["AveragePrice"].astype(float)
    # df_order_source["Quantity"] = df_order_source["Quantity"].astype(float)

    #     sh_order_status_map0 = {"已撤":6, "废单":9, "已成":8, "部撤部成":5, "部撤":7} 2已报, 1待报, 2已报，3已报待撤
    order_status_map = {'1': 'CANCELLED', '2': "CANCELLED","3":"CANCELLED", '6':"CANCELLED", '8': "DONE", '5': "PARTIALLY_CANCELLED",
                        '7': "PARTIALLY_CANCELLED", '9': "REJECTED"}
    side_map = {1: "BID", 2: "ASK"}

    print("df_order shape:", trade_records_df.shape)
    # print("df_order:", trade_records_df.columns)
    trade_records_df["cumAmount"] = trade_records_df["price"] * trade_records_df["quantity"]
    trade_records_df["cumAmount"] = trade_records_df["cumAmount"].apply(lambda x: abs(x))
    trade_records_df["orderStatus"] = trade_records_df["orderStatus"].apply(lambda x: order_status_map[int(x)])
    trade_records_df["side"] = trade_records_df["side"].apply(lambda x: side_map[x])
    trade_records_df["tradeDate"] = trade_records_df["createDate"].apply(
        lambda x: pd.to_datetime(x).strftime("%Y-%m-%d"))

    return trade_records_df

def parse_xbrain_trade_records(trade_records):
    # 将xbrain的和ATS一致的数据结构
    trade_records_df = trade_records.rename(columns={
        "Code": "symbol",
        "Direction": "side",
        "CreatedSize": "entrustQty",
        "ExecutedSize": "quantity",
        'CreatedPrice': 'entrustPx',
        'ExecutedPrice': 'price',
        'Comm': 'commissionCost',
        'Status': 'orderStatus',
        'CreateDatetime': 'createDate',
        'LastTradeTime': 'filledDate'
    })

    order_status_map = {"CANCELED": "CANCELLED", "COMPLETED": "DONE", "PARTIAL": "PARTIALLY_CANCELLED"}
    side_map = {"LONG": "BID", "SHORT": "ASK"}

    trade_records_df["entrustQty"] = trade_records_df["entrustQty"].apply(lambda x:abs(x))
    trade_records_df["quantity"] = trade_records_df["quantity"].apply(lambda x:abs(x))
    trade_records_df["cumAmount"] = trade_records_df["price"]*trade_records_df["quantity"]
    trade_records_df["cumAmount"] = trade_records_df["cumAmount"].apply(lambda x: abs(x))
    trade_records_df["orderStatus"] = trade_records_df["orderStatus"].apply(lambda x: order_status_map[x])
    trade_records_df["side"] = trade_records_df["side"].apply(lambda x: side_map[x])
    trade_records_df["tradeDate"] = trade_records_df["createDate"].apply(
        lambda x: pd.to_datetime(x).strftime("%Y-%m-%d"))

    return trade_records_df

def parse_ats_trade_records(df_order):
    """
    将ATS线下回测格式转换为标准格式
    :param df_order:
    :return:
    """
    sh_order_status_map = {"CANCELLED": "已撤", "DONE": "已成", "PARTIALLY_CANCELLED": "部撤"}
    sh_side = {"BID": "买", "ASK": "卖"}

    # 不确定price是成交均价，还是成交最新价
    df_order = df_order.rename(columns={"symbol": "交易标的",
                                        'createDate': '委托时间',
                                        'side': '买卖方向',
                                        'orderStatus': '委托状态',
                                        'entrustPx': '委托价格',
                                        'entrustQty': '委托数量',
                                        'price': '成交均价',
                                        'quantity': '成交数量',
                                        'cumAmount': '成交金额',
                                        })

    df_order["委托状态"] = df_order["委托状态"].apply(lambda x: sh_order_status_map[x])
    df_order["买卖方向"] = df_order["买卖方向"].apply(lambda x: sh_side[x])
    df_order["证券代码"] = df_order["交易标的"]
    df_order['成交比例'] = df_order['成交数量'] / df_order['委托数量']
    df_order['未完成数量'] = df_order['委托数量'] - df_order['成交数量']
    df_order['委托金额'] = df_order['委托价格'] * df_order['委托数量']
    df_order['价格类型'] = '限价'
    return df_order

def parse_signal_txt(signal_file):
    """
    解析ATS回测的信号文件
    :param signal_file:
    :return:
    """
    with open(signal_file, "r") as f:
        signal_list = []
        lines = f.readlines()
        for line in lines[1:]:
            signal = json.loads(json.loads(line)[2])
            signal_list.append(signal)

    df_signal = pd.DataFrame(signal_list)
    df_signal["PROBABILITY"] = df_signal["PROBABILITY"].apply(lambda x:eval(str(x)))
    df_signal["DATETIME"] = df_signal["PERIOD_BEGIN"].apply(lambda x: dt.datetime.strptime(x, "%Y-%m-%d %H:%M:%S"))
    df_signal["PERIOD_BEGIN"] = df_signal["PERIOD_BEGIN"].apply(lambda x: pd.to_datetime(x))
    df_signal["PERIOD_END"] = df_signal["PERIOD_END"].apply(lambda x: pd.to_datetime(x))
    df_signal["RANGE"] = df_signal["RANGE"].apply(lambda x: eval(str(x)))
    df_signal['D_2'] = df_signal["PROBABILITY"].apply(lambda x:x[0])
    df_signal['D_1'] = df_signal["PROBABILITY"].apply(lambda x: x[1])
    df_signal['O_1'] = df_signal["PROBABILITY"].apply(lambda x: x[2])
    df_signal['R_1'] = df_signal["PROBABILITY"].apply(lambda x: x[3])
    df_signal['R_2'] = df_signal["PROBABILITY"].apply(lambda x: x[4])
    if "PREDICTED" not in df_signal.columns:
        df_signal["PREDICTED"] = df_signal["PREDICT"]
    # print("df_signal:", df_signal.shape)
    return df_signal
