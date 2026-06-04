import datetime as dt
import pandas as pd
from xquant.factordata import FactorData
from xquant.xqutils.xqfile import HDFSFile
from BT_NEW.GetHighVol import get_high_vol_speed
from BT_NEW.BTDataTool import combine_trade_and_capacity
from CONFIG import USER_ID
fa = FactorData()


def get_kcb_code(base_date, n=60):
    """获取科创板股票样本，选择原则：必须在base_date前n日以前上市"""
    if not isinstance(base_date, str):
        base_date = str(base_date)
    market_stock_list = fa.hset("MARKET", "20210127", "ALLA_HIS")['stock'].to_list()
    kcb_stock_list = list(filter(lambda x: x.startswith('68'), market_stock_list))
    factor_df = fa.get_factor_value("Basic_factor", kcb_stock_list, [base_date], ['listing_date'])['listing_date']
    key_date = fa.tradingday(base_date, -(n+1))[0]
    kcb_code = list(factor_df[factor_df <= int(key_date)].index)
    return kcb_code

def get_cyb_code(base_date, n=60):
    """获取创业板股票样本，选择原则：必须在base_date前n日以前上市"""
    if not isinstance(base_date, str):
        base_date = str(base_date)
    market_stock_list = fa.hset("MARKET", base_date, "ALLA_HIS")['stock'].to_list()
    cyb_stock_list = list(filter(lambda x: x.startswith('3'), market_stock_list))
    factor_df = fa.get_factor_value("Basic_factor", cyb_stock_list, [base_date], ['listing_date'])['listing_date']
    key_date = fa.tradingday(base_date, -(n + 1))[0]
    cyb_code = list(factor_df[factor_df <= int(key_date)].index)
    return cyb_code

def get_index_weights(index="HS300", date="20201231", size=5*10**8):
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

def combine_bt_data(freq):
    trade_portfolios = ["Stock1S-{}".format(freq)]
    start_date = "20210401"
    end_date = "20210731"
    is_copy_to_share = True

    hf = HDFSFile()

    for portfolio in trade_portfolios:
        print("Combining {}'s Trade and Capacity".format(portfolio))
        if portfolio in ["hs300_Track", "zz500_Track"]:
            base_date = "20201231"
            size = 5 * 10 ** 8
            index = portfolio.split("_")[0].upper()
            weights = get_index_weights(index, base_date, size)
            codes = weights["stock"].tolist()
            volumes = [int(x) for x in weights["weight"].tolist()]

        elif portfolio in ["Stock1S", "Stock1S-036", "Stock1S-147", "Stock1S-258", "Stock1S-1"]:
            codes = pd.read_csv("/data/user/013050/chensf/StockPool/stock_1s_stock_list.csv")["stock"].tolist()
            # base_date = "20210301"
            # close = FactorData().get_factor_value("Basic_factor", codes, [base_date], ["close"]).droplevel(0).dropna()
            # volumes = (300 * 10000 / close).astype(int)
            daily = fa.get_factor_value("Basic_factor", codes, fa.tradingday("20210401", "20210731"), ["volume"])["volume"].unstack() * 100
            volumes = daily.mean() * 0.01
            codes = volumes.index.tolist()
            volumes = volumes.tolist()

        print(" Generating High Vol Data, {} Codes ".format(len(codes)))
        high_vol_dict = get_high_vol_speed(codes, start_date, end_date, process_num=20)
        combine_trade_and_capacity(codes, volumes, start_date, end_date, portfolio, high_vol_dict, process_num=20)

    if is_copy_to_share:

        for portfolio in trade_portfolios:
            print(dt.datetime.now(), "Uploading {}'s Trade and Capacity to HDFS...".format(portfolio))
            hf.upload(
                '{}{}-{}-{}'.format("cv/Stock/ds-", start_date, end_date, portfolio),
                '{}{}-{}-{}'.format("/data/user/{}/BT_Trade_OrderCapacity/Stock/".format(USER_ID), start_date, end_date, portfolio)
            )

if __name__ == '__main__':
    for freq in ["036", "147", "258", "1"]:
        combine_bt_data(freq)