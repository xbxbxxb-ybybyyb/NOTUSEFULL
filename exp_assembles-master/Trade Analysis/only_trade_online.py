import sys
sys.path.append("/data/user/013150/online_scripts/shen/")
from datetime import datetime
from datetime import timedelta
import os
import pandas as pd
from collections import OrderedDict
from xquant.factordata import FactorData

pd.set_option("display.max.columns", None)


base_dir0 = "/data/user/016869/AutoMiningFrame/trade_data"


def get_trade_data(SYMBOL, StrategyModelName):
    base_dir = os.path.join(base_dir0, "COO", f"{SYMBOL}-{StrategyModelName}")
    trade_path_dir = os.path.join(base_dir, "mm_order/online/")
    df_order_source_list = []
    for trade_file in os.listdir(trade_path_dir):
        # trade_records_20230823.parquet
        trade_date = int(trade_file[14:22])
        trade_path = os.path.join(trade_path_dir, trade_file)
        sub_df_order_source = pd.read_parquet(trade_path)
        sub_df_order_source = sub_df_order_source[sub_df_order_source["TradeDate"]==trade_date]
        print(SYMBOL, trade_date, sub_df_order_source.shape)
        df_order_source_list.append(sub_df_order_source)

    if df_order_source_list:
        df_order_source = pd.concat(df_order_source_list).sort_values(by=["CreatedDate"])
    else:
        df_order_source = pd.DataFrame(columns = ['Id', 'TradeDate', 'OrganCode', 'UserId', 'InvestorAccount',
                                                 'ProductAccount', 'AssetAccount', 'TradingAccount', 'portfolioNo',
                                                 'orderid', 'ClOrdId', 'AffiliatedListId', 'AlgoOrderId', 'OrigOrderId',
                                                 'EngagedId', 'InvestType', 'TradingAction', 'TransactTime',
                                                 'SecurityExchange', 'SecurityAccount', 'SecurityId', 'Symbol',
                                                 'SecurityType', 'OptionType', 'OptionCode', 'OptionCombId',
                                                 'OptionCoveredFlag', 'OrderType', 'Side', 'PositionEffect', 'Currency',
                                                 'Quantity', 'Price', 'EntrustType', 'EntrustProp', 'OrderSource',
                                                 'OrderStation', 'StoreUnit', 'ReportUnit', 'ReportNo', 'OrigReportNo',
                                                 'JoinReportNo', 'PBU', 'SeatNo', 'ReportTime', 'ExchangeOrderId',
                                                 'ReportSide', 'CommTemplate', 'CumQuantity', 'AveragePrice',
                                                 'CumAmount', 'FreezedCash', 'CumNetMoney', 'CancelledQty',
                                                 'TimeInForce', 'MaxPriceLevels', 'MinQuantity', 'OrdStatus',
                                                 'ClOrdDesc', 'ExtFields', 'VolumeCondition', 'ContingentCondition',
                                                 'BranchNo', 'StopPrice', 'ErrorNo', 'ErrorMsg', 'PositionStr',
                                                 'ModifiedDate', 'CreatedDate', 'ExtUniqueOrderId', 'CloseDirection',
                                                 'ParentOrderId', 'OrderFlowType', 'ExtFieldsStr', 'SecurityIDSource',
                                                 'TargetStrategy', 'TargetStrategyParameters', 'ExecBroker', 'TraderID',
                                                 'LocateReqd', 'LocateBroker', 'SettlCurrency', 'CompactNo',
                                                 'PositionProperty', 'CreditTradingAccount', 'CreditSecurityAccount',
                                                 'Parties', 'SystemNodeId', 'OrderId', 'DBModifiedDate',
                                                 'DBCreatedDate'])
    # print("df_order_online_source:", df_order_source.columns)
    if 'OrderId' in df_order_source.columns:
        df_order_source['orderid']=df_order_source['OrderId']

    return  df_order_source


def analysis(df_order_source, SYMBOL):
    keep_columns = ["AssetAccount",
        "Side",
        "SecurityId",
        'CreatedDate',
        'ModifiedDate',
        "Price", #下单价格
        "Quantity", #下单数量
        "CancelledQty",
        "OrdStatus",
        "CumAmount",
        "CumQuantity",#成交数量
        "CumNetMoney",
        "orderid",
        "AveragePrice",# 成交均价
        "EntrustType",
        "TradeDate",
        "TransactTime"#？
    ]

    #部撤实际上是部分成交
    sh_order_status_map = {"已撤":6, "废单":9, "已成":8, "部撤部成":5, "部撤":7}
    sh_side = {"买":1, "卖":2}

    df_order = df_order_source[keep_columns]
    df_order.loc[:, "Side"] = df_order["Side"].astype(int)
    df_order.loc[:, "CumQuantity"] = df_order["CumQuantity"].astype(float)
    df_order.loc[:, "CumNetMoney"] = df_order["CumNetMoney"].astype(float)
    df_order.loc[:, "CumAmount"] = df_order["CumAmount"].astype(float)
    df_order.loc[:, "Price"] = df_order["Price"].astype(float)
    df_order.loc[:, "AveragePrice"] = df_order["AveragePrice"].astype(float)
    df_order.loc[:, "Quantity"] = df_order["Quantity"].astype(float)


    df_order = df_order.sort_values(by = ["CreatedDate"]).reset_index()
    # df_order.loc[:, ['Quantity', 'CumQuantity', "CumAmount", "CumNetMoney", "AveragePrice"]]

    # 例如参与率 报价差  敞口盈亏 回转盈亏
    # 我们一般分敞口盈亏和回转盈亏
    # 敞口就是形成敞口的成交价和当前最新价的差额
    # 回转就是已经成交的除掉敞口之外的卖金额减买金额除以卖金额
    # start_date = datetime.strptime(str(df_order_source["TradeDate"].iloc[0]), "%Y%m%d").strftime("%Y-%m-%d")
    # end_date = datetime.strptime(str(df_order_source["TradeDate"].iloc[-1]), "%Y%m%d").strftime("%Y-%m-%d")
    if df_order_source.empty:
        return pd.DataFrame(columns = ['交易标的', '交易日期', '买成交数量', '卖成交数量', '敞口', '买成交金额', '卖成交金额', '税前盈亏',
       '税后盈亏', '税后收益率', '年化收益率', '税前盈亏(去除敞口)', '税后盈亏(去除敞口)'])
    fa = FactorData()
    dates = fa.tradingday(str(df_order_source["TradeDate"].iloc[0]), str(df_order_source["TradeDate"].iloc[-1]))
    dates = [int(day) for day in dates]
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
        buy_df = df[df.Side==1]
        sell_df = df[df.Side==2]
        buy_position = buy_df.groupby("SecurityId").CumQuantity.sum().sort_index()
        sell_postion = sell_df.groupby("SecurityId").CumQuantity.sum().sort_index()
        df_price = df.groupby("SecurityId").Price.last().sort_index()
        df_position = buy_position-sell_postion

        rest_dict["敞口"] = rest_dict["买成交数量"]-rest_dict["卖成交数量"]
        rest_dict["买成交金额"] = round(df[df.Side==1].CumAmount.sum(),2)
        rest_dict["卖成交金额"] = round(df[df.Side==2].CumAmount.sum(),2)
        rest_dict["税前盈亏"] = round(df[df.Side==2].CumAmount.sum() - df[df.Side==1].CumAmount.sum(), 2)
        rest_dict["税后盈亏"] = round(df[df.Side==2].CumAmount.sum()*0.9995 - df[df.Side==1].CumAmount.sum(), 2)
        if rest_dict["敞口"]:
            print("df_price", df_price, "df_position:", df_position)
            last_price = df.iloc[-1]["Price"]
            # position_amount = rest_dict["敞口"]*last_price
            position_amount = (df_price*df_position).sum()

            rest_dict["税前盈亏(去除敞口)"] = rest_dict["税前盈亏"]+position_amount
            rest_dict["税后盈亏(去除敞口)"] = rest_dict["税后盈亏"]+position_amount
            trade_amount_open_posion = position_amount if rest_dict["敞口"]>0 else 0
            print("trade_amount_open_posion:", trade_amount_open_posion)
            trade_amount = df[df.Side==2].CumAmount.sum()+trade_amount_open_posion
            rest_dict["税后收益率"] = round(rest_dict["税后盈亏(去除敞口)"]/trade_amount,6) if trade_amount else 0
            rest_dict["年化收益率"] = rest_dict["税后收益率"]*252
        else:
            trade_amount = df[df.Side==2].CumAmount.sum()#+df[df.Side==1].CumAmount.sum()
            rest_dict["税后收益率"] = round((df[df.Side==2].CumAmount.sum()*0.9995 - df[df.Side==1].CumAmount.sum())/trade_amount,6) if trade_amount else 0
            rest_dict["年化收益率"] = rest_dict["税后收益率"]*252
            rest_dict["税前盈亏(去除敞口)"] = rest_dict["税前盈亏"]
            rest_dict["税后盈亏(去除敞口)"] = rest_dict["税后盈亏"]

        ret_df = pd.DataFrame.from_dict(rest_dict, orient="index").T
        ret_df_list.append(ret_df)
    if ret_df_list:
        online_trade_result_df = pd.concat(ret_df_list)
    else:
        online_trade_result_df = pd.DataFrame()
    
    online_trade_result_df = online_trade_result_df.reindex(columns = ['交易标的', '交易日期', '买成交数量', '卖成交数量', '敞口', '买成交金额', '卖成交金额', '税前盈亏',
       '税后盈亏', '税后收益率', '年化收益率', '税前盈亏(去除敞口)', '税后盈亏(去除敞口)'])
    print(online_trade_result_df.columns)
    online_trade_result_df.to_excel("online_trade_result_df_{}.xlsx".format(SYMBOL))
    return online_trade_result_df


if __name__=="__main__":
    now_date = datetime.now().strftime("%Y-%m-%d")
    symbol_list = [
                   # ("688599.SH", "688599.SH"),
                   ("688599.SH", "688599.SH_trade_v1.2"),
                   ("688012.SH", "688012.SH_trade_v1.2"),
                   ("688303.SH", "688303.SH_trade_v1.1"),
                   ("688385.SH", "688385.SH_trade_v1.1"),
                   ("688521.SH", "688521.SH_trade_v1.1"),
                   ("688536.SH", "688536.SH_trade_v1.1"),
                   ("688036.SH", "688036.SH_trade_v1.1"),
                   ("689009.SH", "689009.SH_trade_v1.1"), 
                   ("000977.SZ", "000977.SZ_trade_v1.1"),
                    ("688111.SH", "688111.SH_trade_v1.1"),
                    ("002594.SZ", "002594.SZ_trade_v1.1"),
                    ("688256.SH", "688256.SH_trade_v1.1"),
                    ("688017.SH", "688017.SH_trade_v1.1")
                   ]

    sub_order_df_list = []
    sub_trade_result_df_list = []
    for SYMBOL, StrategyModelName in symbol_list:
        sub_order_df = get_trade_data(SYMBOL, StrategyModelName)
        print("===================",StrategyModelName, sub_order_df.shape, "====================")
        sub_order_df_list.append(sub_order_df)
        sub_trade_result_df = analysis(sub_order_df, SYMBOL)
        sub_trade_result_df_list.append(sub_trade_result_df)


    order_df = pd.concat(sub_order_df_list).sort_values(by=["CreatedDate"])
    trade_result_df = analysis(order_df, "ALL").reset_index()
    print(trade_result_df)
    trade_result_df.to_excel(os.path.join(base_dir0, "COO", f"online_trade_result_df_{now_date}.xlsx"))


    stock_trade_result_df = pd.concat(sub_trade_result_df_list).reset_index()
    stock_trade_result_df.to_excel(os.path.join(base_dir0, "COO", f"online_stock_trade_result_df_{now_date}.xlsx"))
    print(stock_trade_result_df)




