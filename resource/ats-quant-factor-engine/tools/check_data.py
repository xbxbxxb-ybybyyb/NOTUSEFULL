
import datetime as dt
import os
import numpy as np
import pandas as pd
import polars as pl


tick_df = pl.read_parquet("./688012.SH_tick.parquet")
# tick_df_dol = pl.read_parquet("./688012.SH.parquet")
tick_df_dol = pl.read_parquet("/root/codes/ats-quant-factor-engine/dataset/688012.SH.parquet")

tick_df_dol.columns = [col.replace("M_", "") for col in tick_df_dol.columns]
# TotalValueTrade, OpenPx,WeightedAvgOfferPx,TradingPhaseCode
#  'BuyQty', 'SellQty', 'BuyMoney', 'SellMoney',
tick_df_dol = tick_df_dol.rename({"BuyPrice":"bids_price",
                                "BuyOrderQty": "bids_qty",
                                "SellPrice":"asks_price",
                                "SellOrderQty": "asks_qty",
                              "PreClosePx": "prev_close_price",
                              "TotalVolumeTrade": "ttl_volume",
                              "LastPx": "last_price",
                              "HighPx": "high_price",
                              "LowPx": "low_price",
                              "WeightedAvgBidPx": "avg_bid_price",
                              "BuyNumOrders": "bids_count",
                              "SellNumOrders": "asks_count"
                            })

tick_df_dol = tick_df_dol.with_columns(
    # pl.col("DateTime").dt.strftime("%Y%m%d%H%M%S%3f").cast(pl.Int64),
    pl.col("DateTime").dt.cast_time_unit(time_unit="ms"),
    pl.col("MDDate").dt.strftime("%Y%m%d"),
).filter(pl.col("MDDate")=="20240614").with_columns(
                pl.col("asks_price").list[0].alias("ask0_p"),
                pl.col("asks_price").list[1].alias("ask1_p"),
                pl.col("asks_price").list[2].alias("ask2_p"),
                pl.col("asks_price").list[3].alias("ask3_p"),
                pl.col("asks_price").list[4].alias("ask4_p"),
                pl.col("bids_price").list[0].alias("bid0_p"),
                pl.col("bids_price").list[1].alias("bid1_p"),
                pl.col("bids_price").list[2].alias("bid2_p"),
                pl.col("bids_price").list[3].alias("bid3_p"),
                pl.col("bids_price").list[4].alias("bid4_p"),
                pl.col("asks_qty").list[0].alias("ask0_v"),
                pl.col("asks_qty").list[1].alias("ask1_v"),
                pl.col("asks_qty").list[2].alias("ask2_v"),
                pl.col("asks_qty").list[3].alias("ask3_v"),
                pl.col("asks_qty").list[4].alias("ask4_v"),
                pl.col("bids_qty").list[0].alias("bid0_v"),
                pl.col("bids_qty").list[1].alias("bid1_v"),
                pl.col("bids_qty").list[2].alias("bid2_v"),
                pl.col("bids_qty").list[3].alias("bid3_v"),
                pl.col("bids_qty").list[4].alias("bid4_v"),
                pl.col("bids_qty").list[5].alias("bid5_v"),
)
tick_df = tick_df.with_columns(
                pl.col("asks_price").list[0].alias("ask0_p"),
                pl.col("asks_price").list[1].alias("ask1_p"),
                pl.col("asks_price").list[2].alias("ask2_p"),
                pl.col("asks_price").list[3].alias("ask3_p"),
                pl.col("asks_price").list[4].alias("ask4_p"),
                pl.col("bids_price").list[0].alias("bid0_p"),
                pl.col("bids_price").list[1].alias("bid1_p"),
                pl.col("bids_price").list[2].alias("bid2_p"),
                pl.col("bids_price").list[3].alias("bid3_p"),
                pl.col("bids_price").list[4].alias("bid4_p"),
                pl.col("asks_qty").list[0].alias("ask0_v"),
                pl.col("asks_qty").list[1].alias("ask1_v"),
                pl.col("asks_qty").list[2].alias("ask2_v"),
                pl.col("asks_qty").list[3].alias("ask3_v"),
                pl.col("asks_qty").list[4].alias("ask4_v"),
                pl.col("bids_qty").list[0].alias("bid0_v"),
                pl.col("bids_qty").list[1].alias("bid1_v"),
                pl.col("bids_qty").list[2].alias("bid2_v"),
                pl.col("bids_qty").list[3].alias("bid3_v"),
                pl.col("bids_qty").list[4].alias("bid4_v"),
                pl.col("bids_qty").list[5].alias("bid5_v"),)

tick_df = tick_df.to_pandas()
tick_df_dol = tick_df_dol.to_pandas()
tick_df_cols = tick_df.columns.tolist()
tick_df_dol_cols = tick_df_dol.columns.tolist()

public_cols = list(set(tick_df_cols) & set(tick_df_dol_cols))

tick_df = tick_df[public_cols]
tick_df_dol = tick_df_dol[public_cols]

# print(tick_df)
# print(tick_df_dol)


def fun(x, y):
    if isinstance(x, list) or isinstance(y, list):
        if type(x) == type(y):
            x.sort()
            y.sort()
            if x == y:
                return True
            else:
                return False
        else:
            return False
    elif isinstance(x, np.ndarray) or isinstance(y, np.ndarray):
        if type(x) == type(y):
            x = list(x)
            y = list(y)
            if x == y:
                return True
            else:
                return False
        else:
            return False
    else:
        if x == y:
            return True
        else:
            return False

def check_data(df_x, df_y, index_cols, csv_root, sign=None):
    """
    :param df_x: DataFrame
    :param df_y: DataFrame
    :param index_cols: 索引列，list类型
    :param csv_root: 结果存储路径
    :param sign: 标识字段，string类型，如多个标的的数据存储区分目录
    :return:
    """
    if sign is not None:
        csv_root = os.path.join(csv_root, sign)
    if not os.path.exists(csv_root):
        os.makedirs(csv_root)
    df_x.set_index(index_cols, inplace=True)
    df_y.set_index(index_cols, inplace=True)

    data_targe = ["x_num", "y_num", "abnormal_num", "different_num", "same_num", "deviation_rate"]
    factors = list(df_x.columns)
    print(factors)
    df_p = pd.DataFrame(np.zeros((len(factors), len(data_targe))), columns=data_targe, index=factors)
    df_p.index.name = 'factor'

    for factor in factors:
        try:
            df_x_factor = pd.DataFrame(df_x.loc[:, factor])
            df_x_factor[pd.isnull(df_x_factor)] = np.nan
            df_y_factor = pd.DataFrame(df_y.loc[:, factor])
            df_y_factor[pd.isnull(df_y_factor)] = np.nan
        except Exception as e:
            print("factor：%s Error occurred:%s" % (factor, e))
            continue
        try:
            df_x_factor[factor] = df_x_factor[factor].astype(float)
            df_y_factor[factor] = df_y_factor[factor].astype(float)
        except:
            pass
        df_x_factor.fillna(999999999, inplace=True)
        df_y_factor.fillna(999999999, inplace=True)
        # TODO 用outer连接，
        try:
            df = pd.merge(df_x_factor, df_y_factor, how='outer', left_index=True, right_index=True,
                           suffixes=('_x', '_y'))
        except Exception as e:
            raise Exception("merge error:{0}".format(e))
        column_x = factor + '_x'
        column_y = factor + '_y'
        try:
            df = df.round(6)
        except:
            pass
            print("因子:{0}为str类型".format(factor))

        #  TODO 两个数据索引对不上的数据
        df_abnormal = df[(df[column_x].isnull()) | (df[column_y].isnull())]
        df = df.dropna(how="any")
        df['result'] = df.apply(lambda x: fun(x[column_x], x[column_y]), axis=1)
        if not df_abnormal.empty:
            abnormal_csv = os.path.join(csv_root, '%s_abnormal.csv' % (factor))
            df_abnormal.to_csv(abnormal_csv)
        df_diff = df[(df['result'] == False) & (~pd.isnull(df[column_y]))]
        if not df_diff.empty:
            diff_csv = os.path.join(csv_root, '%s_different.csv' % (factor))
            df_diff.to_csv(diff_csv)
        accuracy_rate = df['result'].sum() / len(df)
        deviation_rate = 1 - accuracy_rate
        dataset = [len(df_x_factor), len(df_y_factor), len(df_abnormal), len(df_diff),
                   df['result'].sum(), deviation_rate]
        df_p.loc[factor, :] = dataset
        print("factor:{0},Deviation_rate:{1}".format(factor, deviation_rate))
    result_csv = os.path.join(csv_root, 'ckeck_data_result.csv')
    df_p.to_csv(result_csv)
    print("*****校验结束*****")

if __name__ == '__main__':
    check_data(tick_df, tick_df_dol, index_cols=["DateTime"],
               csv_root="/tmp/pycharm_project_852/ats-quant-factor-engine/tmp/check_res",
               sign="688012.SH")

