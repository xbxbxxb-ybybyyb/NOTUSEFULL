import os
import datetime as dt
import pandas as pd
from xquant.factordata import FactorData
from xquant.xqutils.xqfile import HDFSFile
from BT_NEW.GetHighVol import get_high_vol_speed
from BT_NEW.BTDataTool import combine_trade_and_capacity

def get_kcb_code(base_date, n=60):
    """获取科创板股票样本，选择原则：必须在base_date前n日以前上市"""
    if not isinstance(base_date, str):
        base_date = str(base_date)
    fa = FactorData()
    market_stock_list = fa.hset("MARKET", "20210127", "ALLA_HIS")['stock'].to_list()
    kcb_stock_list = list(filter(lambda x: x.startswith('68'), market_stock_list))
    factor_df = fa.get_factor_value("Basic_factor", kcb_stock_list, [base_date], ['listing_date'])['listing_date']
    key_date = fa.tradingday(base_date, -(n+1))[0]
    kcb_code = list(factor_df[factor_df <= int(key_date)].index)
    return kcb_code

def get_index_weights(index="HS300", date="20201231", size=5*10**8):
    fa = FactorData()
    stock_weight = fa.hset("INDEX", date, index)
    stock_weight = stock_weight[["stock", "weight"]]  ## note the sum of weights equals 100
    stock_list = stock_weight["stock"].tolist()

    close = fa.get_factor_value("Basic_factor", stock_list, [date], ["close"]).droplevel(0)
    close.index.name = None
    close["stock"] = close.index.tolist()

    weights = pd.merge(stock_weight, close, on="stock")
    weights["weight"] = weights["weight"] / weights["close"] / 100 * size
    weights = weights[["stock", "weight"]]

    return weights

def combine_bt_data():

    trade_portfolios = ["hs300_Track", "zz500_Track"]
    today_str = "20201001"
    start_date = "20200506"
    end_date = "20200930"
    hs300 = False
    zz500 = False
    is_copy_to_share = True

    if hs300:
        trade_portfolios.append("hs300")

    if zz500:
        trade_portfolios.append("zz500")

    hf = HDFSFile()

    for portfolio in trade_portfolios:
        print("Combining {}'s Trade and Capacity".format(portfolio))
        if portfolio in ["hs300", "zz500"]:
            local_path = "/data/user/666888/AlgoGenzong2/portfolios/"
            file_name = local_path + "{}.xlsx".format(portfolio)
            portfolio_df = pd.read_excel(file_name)
            codes = list([code for code in portfolio_df.iloc[:, 0]])
            volumes = list([volume for volume in portfolio_df.iloc[:, 1]])

        elif portfolio in ["hs300_Track", "zz500_Track"]:
            base_date = "20201231"
            size = 5 * 10 ** 8
            index = portfolio.split("_")[0].upper()
            weights = get_index_weights(index, base_date, size)
            codes = weights["stock"].tolist()
            volumes = [int(x) for x in weights["weight"].tolist()]

        elif portfolio in ["cyb", "kcb"]:
            local_path = "/data/user/015629/StockPool/"
            file_name = "{}_20201009.xlsx".format(portfolio)
            df = pd.read_excel(local_path + file_name)
            codes = list([code for code in df.iloc[:, 0]])
            # volumes = list([volume for volume in df.iloc[:, 1]])
            base_date = "20210101"
            codes = get_kcb_code(base_date)
            volumes = [10000000 for _ in range(len(codes))]

        elif portfolio == "bigModel":
            small_models = pd.read_excel("/data/user/015629/StockPool/easy_full_small_model.xlsx")["stock"].tolist()
            close = FactorData().get_factor_value("Basic_factor", small_models, ["20200630"], ["close"]).droplevel(0)
            volumes = (300 * 10000 / close).astype(int)
            codes = volumes.index.tolist()
            volumes = volumes.iloc[:, 0].tolist()

        elif portfolio == "EasyTrack":
            local_path = "/data/user/015629/CreateDailyEasyParams/DailyLiveParams/"
            today_path = local_path + "Easy_{}/".format(today_str)
            if not os.path.exists(today_path):
                raise Exception(" Today Easy Live Portfolio Not Exists ")
            all_files = os.listdir(today_path)
            today_portfolio_files = [file for file in all_files if file.startswith("easy_") and file.endswith("_{}.xlsx".format(today_str))]
            if len(today_portfolio_files) == 0:
                raise Exception (" Today Easy Live Portfolio Not Exists ")
            concat_portfolio = pd.DataFrame()
            for file in today_portfolio_files:
                portfolio_df = pd.read_excel(today_path + file)
                concat_portfolio = pd.concat([concat_portfolio, portfolio_df], axis=0)
            concat_portfolio = concat_portfolio.groupby("证券代码")["证券额度"].sum()
            codes = concat_portfolio.index.tolist()
            volumes = concat_portfolio.tolist()
        else:
            local_path = "/data/user/015629/CreateDailyEasyParams/DailyLiveParams/"
            file_name = local_path + "Easy_{}/easy_{}_{}.xlsx".format(today_str, portfolio, today_str)
            portfolio_df = pd.read_excel(file_name)
            codes = list([code for code in portfolio_df.iloc[:, 0]])
            volumes = list([volume for volume in portfolio_df.iloc[:, 3]])

        ###  生成股票活跃度指标, 其中参数可以根据需要设置start_date, end_date, lookback
        print(" Generating High Vol Data, {} Codes ".format(len(codes)))
        high_vol_dict = get_high_vol_speed("ZeusDataLib", codes, start_date, end_date, lookback=20, process_num=20)
        combine_trade_and_capacity(codes, volumes, start_date, end_date, portfolio, high_vol_dict,  process_num=20)

    if is_copy_to_share:

        for portfolio in trade_portfolios:
            print(dt.datetime.now(), "Uploading {}'s Trade and Capacity to HDFS...".format(portfolio))
            hf.upload(
                '{}{}-{}-{}'.format("cv/Stock/ds-", start_date, end_date, portfolio),
                '{}{}-{}-{}'.format("/data/user/015629/BT_Trade_OrderCapacity/Stock/", start_date, end_date, portfolio)
            )


if __name__ == '__main__':
    combine_bt_data()