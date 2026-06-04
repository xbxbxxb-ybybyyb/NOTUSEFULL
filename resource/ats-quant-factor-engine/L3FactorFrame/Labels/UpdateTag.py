import os
import pandas as pd
import polars as pl
from xquant.factordata import FactorData
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
from L3FactorFrame.MarketDataManager import get_l3_trade_order_data
from artifacts.flying_functions import *
from artifacts.utils import save_and_append_parquet
from datetime import datetime
import copy

pl.Config.set_tbl_width_chars(10000)
pl.Config.set_streaming_chunk_size(10000)
pl.Config.set_fmt_table_cell_list_len(10000)
pl.Config.set_tbl_rows(100)


def calculate_ret_tag(tick_df_fill, smooth_window="5s"):
    def calc_tag_inner(tick_df_fill1, period):
        period_shift = 6 - int(smooth_window[:-1]) + 1
        labelb_morning = tick_df_fill1.filter(((pl.col("DateTime").dt.strftime("%H%M%S") >= "093000") & (
                    pl.col("DateTime").dt.strftime("%H%M%S") <= "113000000"))).group_by_dynamic(index_column='DateTime',
                                                                                                every='1s', offset='0s',
                                                                                                period=str(
                                                                                                    period + period_shift) + 's',
                                                                                                closed="both",
                                                                                                label="left").agg(
            [
                (pl.col("AskP0_mean_smooth" + smooth_window).last() / pl.col(
                    "BidP0_mean_smooth" + smooth_window).first() * 1000 - 1000).alias(
                    "smooth_short_ret_{}s".format(period)),  # 未来1分钟的收益率
                (pl.col("AskP0_mean_smooth" + smooth_window).last() / pl.col("BidP0").first() * 1000 - 1000).alias(
                    "dol_short_ret_{}s".format(period)),  # 未来1分钟的收益率
                (pl.col("BidP0_mean_smooth" + smooth_window).last() / pl.col(
                    "AskP0_mean_smooth" + smooth_window).first() * 1000 - 1000).alias(
                    "smooth_long_ret_{}s".format(period)),  # 未来1分钟的收益率
                (pl.col("BidP0_mean_smooth" + smooth_window).last() / pl.col("AskP0").first() * 1000 - 1000).alias(
                    "dol_long_ret_{}s".format(period)),  # 其实dolphindb里面的标签是0-36秒，端到端的收益率，没有尾部平滑
                pl.col("DateTime").first().alias("DateTime1"),
                (pl.col("AskP0").last() / pl.col("AskP0").first() * 1000 - 1000).alias(
                    "ask2ask_ret_{}s".format(period)),
                (pl.col("BidP0").last() / pl.col("BidP0").first() * 1000 - 1000).alias(
                    "bid2bid_ret_{}s".format(period)),
                (pl.col("AskP0").last() / pl.col("BidP0").first() * 1000 - 1000).alias("short_ret_{}s".format(period)),
                (pl.col("BidP0").last() / pl.col("AskP0").first() * 1000 - 1000).alias("long_ret_{}s".format(period)),
                ######vwap标签，无需平滑######
                ((pl.col("BidVwap01").last() / pl.col("AskVwap01").first()) * 1000 - 1000).alias(
                    "vwap01_long_ret_{}s".format(period)),
                ((pl.col("AskVwap01").last() / pl.col("BidVwap01").first()) * 1000 - 1000).alias(
                    "vwap01_short_ret_{}s".format(period)),
                ((pl.col("BidVwap012").last() / pl.col("AskVwap012").first()) * 1000 - 1000).alias(
                    "vwap012_long_ret_{}s".format(period)),
                ((pl.col("AskVwap012").last() / pl.col("BidVwap012").first()) * 1000 - 1000).alias(
                    "vwap012_short_ret_{}s".format(period)),
            ]).with_columns(pl.col("DateTime1").alias("DateTime")).drop(["DateTime1"])

        labelb_afternoon = tick_df_fill1.filter(((pl.col("DateTime").dt.strftime("%H%M%S") >= "130000") & (
                    pl.col("DateTime").dt.strftime("%H%M%S") <= "150000000"))).group_by_dynamic(index_column='DateTime',
                                                                                                every='1s', offset='0s',
                                                                                                period=str(
                                                                                                    period + period_shift) + 's',
                                                                                                closed="both",
                                                                                                label="left").agg(
            [
                (pl.col("AskP0_mean_smooth" + smooth_window).last() / pl.col(
                    "BidP0_mean_smooth" + smooth_window).first() * 1000 - 1000).alias(
                    "smooth_short_ret_{}s".format(period)),  # 未来1分钟的收益率
                (pl.col("AskP0_mean_smooth" + smooth_window).last() / pl.col("BidP0").first() * 1000 - 1000).alias(
                    "dol_short_ret_{}s".format(period)),  # 未来1分钟的收益率
                (pl.col("BidP0_mean_smooth" + smooth_window).last() / pl.col(
                    "AskP0_mean_smooth" + smooth_window).first() * 1000 - 1000).alias(
                    "smooth_long_ret_{}s".format(period)),  # 未来1分钟的收益率
                (pl.col("BidP0_mean_smooth" + smooth_window).last() / pl.col("AskP0").first() * 1000 - 1000).alias(
                    "dol_long_ret_{}s".format(period)),  # 其实dolphindb里面的标签是0-36秒，端到端的收益率，没有尾部平滑
                pl.col("DateTime").first().alias("DateTime1"),
                (pl.col("AskP0").last() / pl.col("AskP0").first() * 1000 - 1000).alias(
                    "ask2ask_ret_{}s".format(period)),
                (pl.col("BidP0").last() / pl.col("BidP0").first() * 1000 - 1000).alias(
                    "bid2bid_ret_{}s".format(period)),
                (pl.col("AskP0").last() / pl.col("BidP0").first() * 1000 - 1000).alias("short_ret_{}s".format(period)),
                (pl.col("BidP0").last() / pl.col("AskP0").first() * 1000 - 1000).alias("long_ret_{}s".format(period)),
                ######vwap标签，无需平滑######
                ((pl.col("BidVwap01").last() / pl.col("AskVwap01").first()) * 1000 - 1000).alias(
                    "vwap01_long_ret_{}s".format(period)),
                ((pl.col("AskVwap01").last() / pl.col("BidVwap01").first()) * 1000 - 1000).alias(
                    "vwap01_short_ret_{}s".format(period)),
                ((pl.col("BidVwap012").last() / pl.col("AskVwap012").first()) * 1000 - 1000).alias(
                    "vwap012_long_ret_{}s".format(period)),
                ((pl.col("AskVwap012").last() / pl.col("BidVwap012").first()) * 1000 - 1000).alias(
                    "vwap012_short_ret_{}s".format(period)),
            ]).with_columns(pl.col("DateTime1").alias("DateTime")).drop(["DateTime1"])
        labelb = pl.concat([labelb_morning, labelb_afternoon])
        return labelb

    # 收益率标签计算, 事件戳打在开始日期上，
    tick_df_fill1 = tick_df_fill.with_columns(
        midprice=pl.when((pl.col("AskP0") > 0) & (pl.col("BidP0") > 0)).then(
            (pl.col("AskP0") + pl.col("BidP0")) / 2).otherwise(
            pl.when(pl.col("AskP0") > 0).then(pl.col("AskP0")).otherwise(pl.col("BidP0"))
        )
    ).with_columns([
        pl.when(pl.col("AskP0") > 0).then(pl.col("AskP0")).otherwise(pl.col("midprice")).alias("AskP0"),
        pl.when(pl.col("BidP0") > 0).then(pl.col("BidP0")).otherwise(pl.col("midprice")).alias("BidP0")
    ]).group_by_dynamic(index_column='DateTime', every='1s', period=smooth_window, offset='0s', closed="right",
                        label="left").agg(
        [
            pl.col("AskP0").mean().alias("AskP0_mean_smooth" + smooth_window),  # 未来n秒的价格均值
            pl.col("BidP0").mean().alias("BidP0_mean_smooth" + smooth_window),
            pl.col("AskP0").first().alias("AskP0"),
            pl.col("BidP0").first().alias("BidP0"),
            pl.col("AskV0").first().alias("AskV0"),
            pl.col("BidV0").first().alias("BidV0"),
            pl.col("AskPrice").first().list[1].alias("AskP1"),
            pl.col("BidPrice").first().list[1].alias("BidP1"),
            pl.col("AskVolume").first().list[1].alias("AskV1"),
            pl.col("BidVolume").first().list[1].alias("BidV1"),
            pl.col("AskPrice").first().list[2].alias("AskP2"),
            pl.col("BidPrice").first().list[2].alias("BidP2"),
            pl.col("AskVolume").first().list[2].alias("AskV2"),
            pl.col("BidVolume").first().list[2].alias("BidV2"),
            pl.col("DateTime").first().alias("DateTime1")
        ],  # 未来10s的价格平均值,offset 0秒，窗口不往前偏移
    ).with_columns(DateTime=pl.col("DateTime1"),
                   AskVwap01=(pl.col("AskP0") * pl.col("AskV0") + pl.col("AskP1") * pl.col("AskV1")) / (
                               pl.col("AskV0") + pl.col("AskV1")),
                   BidVwap01=(pl.col("BidP0") * pl.col("BidV0") + pl.col("BidP1") * pl.col("BidV1")) / (
                               pl.col("BidV0") + pl.col("BidV1")),
                   AskVwap012=(pl.col("AskP0") * pl.col("AskV0") * 0.22 + pl.col("AskP1") * pl.col(
                       "AskV1") * 0.18 + pl.col("AskP2") * pl.col("AskV2") * 0.14) / (
                                          pl.col("AskV0") * 0.22 + pl.col("AskV1") * 0.18 + pl.col("AskV2") * 0.14),
                   BidVwap012=(pl.col("BidP0") * pl.col("BidV0") * 0.22 + pl.col("BidP1") * pl.col(
                       "BidV1") * 0.18 + pl.col("BidP2") * pl.col("BidV2") * 0.14) / (
                                          pl.col("BidV0") * 0.22 + pl.col("BidV1") * 0.18 + pl.col("BidV2") * 0.14)
                   )

    # 计算1min端到端收益率
    labelb_30 = calc_tag_inner(tick_df_fill1, 30)
    labelb_60 = calc_tag_inner(tick_df_fill1, 60)
    labelb_120 = calc_tag_inner(tick_df_fill1, 120)
    labelb_180 = calc_tag_inner(tick_df_fill1, 180)
    labelb = labelb_30.join(labelb_60, on="DateTime").join(labelb_120, on="DateTime").join(labelb_180, on="DateTime")
    #     return labelb_30, labelb_60, labelb_120, labelb_180
    return labelb


def df_fill_null(df):
    # 补齐缺失成交秒内的数据，用前值填充
    df_fill = df.select([
        pl.col("DateTime").min().alias("startTime"), pl.col("DateTime").max().alias("endTime")
    ]).select([
        pl.datetime_range(pl.col("startTime"), pl.col("endTime"), interval='1s').alias("DateTime")
    ]).join(df, how="left", on=["DateTime"], coalesce = True)  # .fill_null(strategy = "zero")#合并左边相同列到右边
    df_fill = df_fill.with_columns([
        pl.all().exclude([]).fill_null(strategy="forward"),
    ]
    )
    return df_fill


if __name__=="__main__":
    fa = FactorData()
    flying_base_dir = "/dfs/group/800657/library/l3_event/event_data"
    symbols = pd.read_csv("/dfs/group/800657/exp_results/zz500_dataset/kc_amt_swing.csv", header=None)[0].tolist()
    symbols1 = pd.read_csv("/dfs/group/800657/exp_results/zz500_dataset/zz500_select74.csv", header=None)[0].tolist()
    SYMBOL_LIST = list(sorted(set(symbols + symbols1)))
    # SYMBOL_LIST = ["688256.SH"]

    start_date = "20220101"
    end_date = "20240626"
    DATES = fa.tradingday(start_date, end_date)
    DATES1 = [pd.to_datetime(date).strftime("%Y-%m-%d") for date in DATES]

    base_save_dir = "/dfs/group/800657/library/tag_data"
    tasks = []


    def inner_func(symbol_name, date):
        print(symbol_name, date)
        s_tick_df, s_order_df, s_trade_df, s_cancel_df = get_l3_trade_order_data(symbol_name, date,
                                                                                 merge_one_order=True)
        if len(s_tick_df)==0:
            return None
        tick_df = s_tick_df.with_columns(pl.col("DateTime").set_sorted()). \
            group_by_dynamic(index_column='DateTime', every='1s', offset='0s', closed="right", label="right").agg(
            [pl.all().exclude(["DateTime", "MDTime"]).last()]
        )
        # 补齐缺失成交秒内的数据，用前值填充
        tick_df_fill = df_fill_null(tick_df)
        tick_df_fill = tick_df_fill.filter(((pl.col("DateTime").dt.strftime("%H%M%S") >= "093000") & (
                pl.col("DateTime").dt.strftime("%H%M%S") <= "113000000")) | (
                                               ((pl.col("DateTime").dt.strftime("%H%M%S") >= "130000") & (
                                                       pl.col("DateTime").dt.strftime("%H%M%S") <= "145700000"))
                                           ))

        labelb_5 = calculate_ret_tag(tick_df_fill, smooth_window="5s")
        labelb_10 = calculate_ret_tag(tick_df_fill, smooth_window="10s")
        labelb = labelb_5.join(labelb_10, on="DateTime").to_pandas()
        os.makedirs(os.path.join(base_save_dir, "{}".format(symbol_name)), exist_ok=True)
        save_parquet_path = os.path.join(base_save_dir, "{}/{}-{}.pqt".format(symbol_name, symbol_name, date))
        save_and_append_parquet(symbol_name, labelb, save_parquet_path, overwrite_col="DateTime")
        return None


    remote_func = ray.remote(inner_func)
    for symbol_name in SYMBOL_LIST:
        for date in DATES:
            tasks.append(remote_func.remote(symbol_name, date))
        ray.get(tasks)


