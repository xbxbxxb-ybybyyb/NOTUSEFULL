import sys
import os
sys.path.append("/tmp/pycharm_project_92/")
from backtest.xbrain_backtest_utils import *
import ray
from artifacts.parse_format import parse_online_trade_records
from artifacts.backtest_save_and_evaluate import backtest_trade_evaluation, backtest_plot_trade_only
from xquant.marketdata import MarketData
import time

# def parse_online_trade_records(trade_records):
#     # 返回和ATS一致的数据结构
#     trade_records_df = df_order_source.rename(columns={
#         "SecurityId": "symbol",
#         "Side": "side",
#         "Quantity": "entrustQty",
#         "CumQuantity": "quantity",
#         'Price': 'entrustPx',
#         'AveragePrice': 'price',
#         'OrdStatus': 'orderStatus',
#         'CreatedDate': 'createDate',
#         'TransactTime': 'filledDate'
#     })
#     #     sh_order_status_map0 = {"已撤":6, "废单":9, "已成":8, "部撤部成":5, "部撤":7} 2已报, 1待报, 2已报，3已报待撤
#     order_status_map = {'1': 'CANCELLED', '2': "CANCELLED","3":"CANCELLED", '6':"CANCELLED", '8': "DONE", '5': "PARTIALLY_CANCELLED",
#                         '7': "PARTIALLY_CANCELLED", '9': "REJECTED"}
#     side_map = {"买": "BID", "卖": "ASK"}
#
#     print("df_order shape:", trade_records_df.shape)
#     print("df_order:", trade_records_df.columns)
#     trade_records_df["cumAmount"] = trade_records_df["price"] * trade_records_df["quantity"]
#     trade_records_df["cumAmount"] = trade_records_df["cumAmount"].apply(lambda x: abs(x))
#     trade_records_df["orderStatus"] = trade_records_df["orderStatus"].apply(lambda x: order_status_map[x])
#     trade_records_df["side"] = trade_records_df["side"].apply(lambda x: side_map[x])
#     trade_records_df["tradeDate"] = trade_records_df["createDate"].apply(
#         lambda x: pd.to_datetime(x).strftime("%Y-%m-%d"))
#     return trade_records_df


# def parse_trade_summary(trade_records_df):
#     sub_trade_records = trade_records_df[
#         (trade_records_df["orderStatus"] != "CANCELLED") & (trade_records_df["orderStatus"] != "REJECTED")]
#     if not sub_trade_records.empty:
#         trade_summary = {}
#         trade_summary["日期"] = sub_trade_records["tradeDate"].iloc[0]
#         trade_summary["标的"] = sub_trade_records["symbol"].iloc[0]
#         trade_summary["敞口数量"] = sub_trade_records[sub_trade_records["side"] == "BID"]["quantity"].sum() - \
#                                 sub_trade_records[sub_trade_records["side"] == "ASK"]["quantity"].sum()
#         trade_summary["买成交金额"] = sub_trade_records[sub_trade_records["side"] == "BID"]["cumAmount"].sum()
#         trade_summary["卖成交金额"] = sub_trade_records[sub_trade_records["side"] == "ASK"]["cumAmount"].sum()
#         trade_summary["买成交数量"] = sub_trade_records[sub_trade_records["side"] == "BID"]["quantity"].sum()
#         trade_summary["卖成交数量"] = sub_trade_records[sub_trade_records["side"] == "ASK"]["quantity"].sum()
#         trade_summary["下单次数"] = trade_records_df.iloc[:, 1].count()
#         trade_summary["成交次数"] = sub_trade_records.iloc[:, 1].count()
#         trade_summary["撤单次数"] = trade_records_df[trade_records_df["orderStatus"] == "CANCELLED"].iloc[:, 1].count()
#
#         if trade_summary["敞口数量"]:
#             last_price = trade_records_df.iloc[-1]["price"]
#             long_orders = trade_records_df[trade_records_df["side"] == "BID"].sort_values(by=["createDate"])
#             short_orders = trade_records_df[trade_records_df["side"] == "ASK"].sort_values(by=["createDate"])
#             if trade_summary["敞口数量"] > 0:
#                 accu_buy_sum = 0
#                 accu_sell_sum = short_orders["quantity"].sum()
#                 for i in range(len(long_orders)):
#                     #                     print(i, accu_buy_sum, accu_sell_sum)
#                     if accu_buy_sum + long_orders.iloc[i]["quantity"] <= accu_sell_sum:
#                         accu_buy_sum += long_orders.iloc[i]["quantity"]
#                     else:
#                         break
#                 # 前i比买单的数量小于等于卖单，所以用第i+1笔买单的，部分成交量配平卖成交量
#                 add_buy_amount = long_orders.iloc[i]["price"] * (accu_sell_sum - long_orders.iloc[:i]["quantity"].sum())
#                 buy_i_amount = long_orders.iloc[:i]["cumAmount"].sum()
#                 #                 print("buy_i_amount",buy_i_amount)
#                 trade_summary["买成交金额(去除敞口)"] = buy_i_amount + add_buy_amount
#                 trade_summary["卖成交金额(去除敞口)"] = trade_summary["卖成交金额"]
#
#                 trade_summary["回转盈亏"] = trade_summary["卖成交金额"] - (buy_i_amount + add_buy_amount)
#                 trade_summary["税后回转盈亏"] = trade_summary["回转盈亏"] - trade_summary["卖成交金额"] * 0.0005
#                 trade_summary["敞口盈亏"] = last_price * trade_summary["敞口数量"] - long_orders.iloc[i:][
#                     "cumAmount"].sum() + add_buy_amount
#                 trade_summary["税后收益率"] = round(trade_summary["税后回转盈亏"] / trade_summary["卖成交金额"], 6) if trade_summary[
#                     "卖成交金额"] else 0
#                 trade_summary["年化收益率"] = trade_summary["税后收益率"] * 252
#             else:
#                 accu_buy_sum = long_orders["quantity"].sum()
#                 accu_sell_sum = 0
#                 for i in range(len(short_orders)):
#                     if accu_sell_sum + short_orders.iloc[i]["quantity"] <= accu_buy_sum:
#                         accu_sell_sum += short_orders.iloc[i]["quantity"]
#                     else:
#                         break
#                 # 前i比卖单的数量小于等于买单，所以用第i+1笔卖单，部分成交量配平卖成交量
#                 add_sell_amount = short_orders.iloc[i]["price"] * (
#                             accu_buy_sum - short_orders.iloc[:i]["quantity"].sum())
#                 sell_i_amount = short_orders.iloc[:i]["cumAmount"].sum()
#
#                 trade_summary["买成交金额(去除敞口)"] = trade_summary["买成交金额"]
#                 trade_summary["卖成交金额(去除敞口)"] = sell_i_amount + add_sell_amount
#
#                 trade_summary["回转盈亏"] = (sell_i_amount + add_sell_amount) - (trade_summary["买成交金额"])
#                 trade_summary["税后回转盈亏"] = trade_summary["回转盈亏"] - trade_summary["卖成交金额(去除敞口)"] * 0.0005
#                 trade_summary["敞口盈亏"] = long_orders.iloc[i:]["cumAmount"].sum() - add_sell_amount - last_price * abs(
#                     trade_summary["敞口数量"])
#                 trade_summary["税后收益率"] = round(trade_summary["税后回转盈亏"] / trade_summary["卖成交金额(去除敞口)"], 6) if (
#                             sell_i_amount + add_sell_amount) else 0
#                 trade_summary["年化收益率"] = trade_summary["税后收益率"] * 252
#
#             # trade_summary["税前盈亏(去除敞口)"] = trade_summary["税前盈亏"]+trade_summary["敞口数量"]*last_price
#             # trade_summary["税后盈亏(去除敞口)"] = trade_summary["税后盈亏"]+trade_summary["敞口数量"]*last_price
#             # trade_amount_open_posion = trade_summary["敞口数量"]*last_price if trade_summary["敞口数量"]>0 else 0
#             # trade_amount = trade_summary["卖成交金额"] +trade_amount_open_posion
#             # trade_summary["税后收益率"] = round(trade_summary["税后盈亏(去除敞口)"]/trade_amount,6) if trade_amount else 0
#             # trade_summary["年化收益率"] = trade_summary["税后收益率"]*252
#         else:
#             trade_summary["买成交金额(去除敞口)"] = trade_summary["买成交金额"]
#             trade_summary["卖成交金额(去除敞口)"] = trade_summary["卖成交金额"]
#
#             trade_summary["回转盈亏"] = trade_summary["卖成交金额"] - trade_summary["买成交金额"]
#             trade_summary["税后回转盈亏"] = trade_summary["卖成交金额"] * 0.9995 - trade_summary["买成交金额"]
#             trade_summary["敞口盈亏"] = 0
#             trade_amount = trade_summary["卖成交金额"]  # +trade_records_df[trade_records_df.Side==1].CumAmount.sum()
#             trade_summary["税后收益率"] = round(trade_summary["税后回转盈亏"] / trade_amount, 6) if trade_amount else 0
#             trade_summary["年化收益率"] = trade_summary["税后收益率"] * 252
#         return pd.DataFrame(trade_summary, index=[0])
#     else:
#         return pd.DataFrame(
#             columns=['AvailableCash', 'StrategyProfitRate', 'AnnualProfitRate', 'MaxDrawDown', 'MaxDrawDownFrom',
#                      'MaxDrawDownTo', 'SharpeRatio', 'RewardRiskRatio', 'WinRate', '股票代码', '敞口数量',
#                      '买成交金额', '卖成交金额', '下单次数', '成交次数', '撤单次数', '税前盈亏', '税后盈亏', '税后收益率', '年化收益率', '回转盈亏'])

def load_trade_records(start_date, end_date):
    from xquant.marketdata import MarketData
    import pymysql1
    import pandas as pd
    import pymysql
    pd.set_option("display.max.colwidth", None)
    from sqlalchemy import create_engine, Column, Integer, String
    import sys
    sys.path.append("/data/user/013150/online_scripts/shen/")

    stock = "688012.SH"
    date = "20231019"

    ma = MarketData()
    tick_df = ma.get_data_by_date("STOCK", stock, date)
    trade_df = ma.get_data_by_date("TRANSACTION", stock, date)
    order_df = ma.get_data_by_date("ORDER", stock, date)

    # TODO: 区分不同的策略来统计
    # 数据库链接信息
    db = pymysql1.connect(host='168.11.33.144',
                          port=3307,
                          user='xtraderops',
                          password='wXE1QGmIc3+gDYVOnwrzw37SZN0FBLx9OqBpEGJMVic=',
                          database='ats_quant',
                          )
    keep_columns = ["AssetAccount",
                    "Side",
                    "SecurityId",
                    'CreatedDate',
                    'ModifiedDate',
                    "Price",  # 下单价格
                    "Quantity",  # 下单数量
                    "CancelledQty",
                    "OrdStatus",
                    "CumAmount",
                    "CumQuantity",  # 成交数量
                    "CumNetMoney",
                    "orderid",
                    "AveragePrice",  # 成交均价
                    "EntrustType",
                    "TradeDate",
                    "TransactTime"  # ？
                    ]
    # 部撤实际上是部分成交
    sh_order_status_map0 = {"已撤": 6, "废单": 9, "已成": 8, "部撤部成": 5, "部撤": 7}
    sh_side0 = {"买": 1, "卖": 2}
    sh_order_status_map = {value: key for key, value in sh_order_status_map0.items()}
    sh_side = {value: key for key, value in sh_side0.items()}

    schema = "history_security"
    # schema = "history_security2023"
    sql_trade_all = """select AssetAccount, Side, SecurityId, CreatedDate, ModifiedDate, Price, Quantity, CancelledQty, OrdStatus, CumAmount, 
            CumQuantity, CumNetMoney, orderid, AveragePrice,
           EntrustType, TradeDate, TransactTime FROM history_security.exchangeorder 
        WHERE TradeDate  between '{}' and '{}'
        and substring_index(AlgoOrderId,'-',1) ='Sappe'
        and EntrustType=0 
        and  OrdStatus!=9
    """.format(start_date, end_date)
    print(sql_trade_all)
    ## 读取实盘成交数据
    df_order_source = pd.read_sql(sql_trade_all, con=db)[keep_columns]
    df_order_source["Side"] = df_order_source["Side"].astype(int)
    df_order_source["CumQuantity"] = df_order_source["CumQuantity"].astype(float)
    df_order_source["CumNetMoney"] = df_order_source["CumNetMoney"].astype(float)
    df_order_source["CumAmount"] = df_order_source["CumAmount"].astype(float)
    df_order_source["Price"] = df_order_source["Price"].astype(float)
    df_order_source["AveragePrice"] = df_order_source["AveragePrice"].astype(float)
    df_order_source["Quantity"] = df_order_source["Quantity"].astype(float)
    return df_order_source


if __name__=="__main__":
    t1 = time.time()
    df_order_source = load_trade_records(start_date="20240620", end_date="20240620")
    print("load_trade_records time:", time.time()-t1)
    # df_order_source = pd.read_parquet("/home/appadmin/sappe2024.parquet")

    # df_order_source["Side"] = df_order_source["Side"].astype(int)
    df_order_source["CumQuantity"] = df_order_source["CumQuantity"].astype(float)
    df_order_source["CumNetMoney"] = df_order_source["CumNetMoney"].astype(float)
    df_order_source["CumAmount"] = df_order_source["CumAmount"].astype(float)
    df_order_source["Price"] = df_order_source["Price"].astype(float)
    df_order_source["AveragePrice"] = df_order_source["AveragePrice"].astype(float)
    df_order_source["Quantity"] = df_order_source["Quantity"].astype(float)
    print(df_order_source.shape)

    trade_records = parse_online_trade_records(df_order_source)
    dates = list(set(trade_records["TradeDate"].tolist()))
    symbols = list(set(trade_records["symbol"].tolist()))
    dates = sorted(dates)
    print(dates)

    @ray.remote
    def parallel_date(date, symbols, trade_records, plot_save_dir = "/data/user/013150/2024_plot"):
        from artifacts import parse_format, backtest_save_and_evaluate
        result_list = []
        for symbol in symbols:
            sub_trade_records = trade_records[
                (trade_records["TradeDate"] == date) & (trade_records['symbol'] == symbol)]
            if symbol.startswith("6"):
                symbol_c = str(symbol) + ".SH"
            else:
                symbol_c = str(symbol) + ".SZ"
            sub_trade_records["symbol"] = symbol_c
            ma = MarketData()
            ma_df_day = ma.get_data_by_date("Stock", symbol_c, date)
            plot_path = os.path.join(plot_save_dir, f"{symbol}-{date}.html")
            backtest_plot_trade_only(sub_trade_records, ma_df_day, plot = False, plot_save_dir = plot_path, volume_unit = 2000)
            trade_summary_day = backtest_save_and_evaluate.backtest_trade_evaluation(sub_trade_records)
            result_list.append(trade_summary_day)
        result_df = pd.concat(result_list).reset_index(drop= True)
        return result_df


    @ray.remote
    def parallel_trade(trade_records, symbol, date_list, plot_save_dir = "/data/user/013150/2024_plot"):
        from artifacts import parse_format, backtest_save_and_evaluate
        trade_summary_list = []
        ma = MarketData()
        if symbol.startswith("6"):
            symbol_c = str(symbol)+".SH"
        else:
            symbol_c = str(symbol)+".SZ"
        print(symbol_c)
        ma_df = ma.get_data_by_time_frame("Stock", symbol_c, str(min(date_list))+" 093000000", str(max(date_list))+" 150000000")
        for date in date_list:
            sub_trade_records = trade_records[
                (trade_records["symbol"] == symbol) & (trade_records["TradeDate"] == date)]
            sub_trade_records["symbol"] = symbol_c
            trade_summary_day = backtest_save_and_evaluate.backtest_trade_evaluation(sub_trade_records)
            ma_df_day = ma_df[ma_df["MDDate"]==str(date)]
            if symbol_c.endswith("SH"):
                backtest_plot_trade_only(sub_trade_records, ma_df_day, plot=False, plot_save_dir=os.path.join(plot_save_dir, f"{symbol}-{date}.html"), volume_unit=2000)
            trade_summary_list.append(trade_summary_day)
        return pd.concat(trade_summary_list, axis=0).reset_index()

    if False:
        ray.init(num_cpus=10)
        # 按标的并行
        symbols = [symbol for symbol in symbols if symbol.startswith("688")]
        print(symbols)
        print(dates)
        tasks = [parallel_trade.remote(trade_records[(trade_records["symbol"] == symbol)], symbol, dates) for symbol in
                 symbols]
        final_trade_summary_list = ray.get(tasks)
        final_trade_summary = pd.concat(final_trade_summary_list, axis=0).reset_index()
        print(final_trade_summary)
        final_trade_summary.to_csv("/home/appadmin/C1++.csv", encoding = "gbk")
        os.system("curl ftp://168.8.2.68/013150/ -T /home/appadmin/C1++.csv -u 'ftphzh:ftphzh2602'")
    if True:
        # symbols = ["688012", "688041", "688981", "688111"]
        symbols = ["688012","688041","688047","688256","688271","688498","688506", "688017","688981"]
        # 按天并行
        tasks =[parallel_date.remote(date, symbols, trade_records) for date in dates]
        result_list_big = ray.get(tasks)
        result_df_big = pd.concat(result_list_big)
        print(result_df_big)
        result_df_big.to_csv("/home/appadmin/C++.csv", encoding = "gbk")
        os.system("curl ftp://168.8.2.68/013150/ -T /home/appadmin/C++.csv -u 'ftphzh:ftphzh2602'")
