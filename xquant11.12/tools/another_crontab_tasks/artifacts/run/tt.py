import copy
import importlib
import os
from datetime import datetime

import pandas as pd
import polars as pl
from artifacts import flying_functions
from artifacts.flying_functions import *
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
from L3FactorFrame import MarketDataManager
from L3FactorFrame.MarketDataManager import *
from matplotlib import pyplot as plt
from xquant.factordata import FactorData

# importlib.reload(flying_functions)
# importlib.reload(MarketDataManager)

fa = FactorData()
fp = FactorProvider("016884")

debug = False
flying_base_dir = "/dfs/group/800657/library/l3_event/tmp_event_data1"
symbol = "688981.SH"
start_date, end_date = "20240614", "20240614"
dates = fa.tradingday(start_date, end_date)
date = dates[0]
date1 = pd.to_datetime(date).strftime("%Y-%m-%d")
long_pred_th, short_pred_th = 1.5, -1.4

# 加载标签数据
data_type = "tick_l2p"  # "enhanced_tick"
label_list = [
    "LabelFirstPeak_th12_60s",
    "LabelFirstPeak_th10_60s",
    "LabelFirstPeak_th05_60s",
]
label_name = "LabelFirstPeak_th10_60s"
symbol_list = [
    symbol
]  # [symbol for symbol in model_config["symbol_list"] if symbol.startswith("688")]
source_label_df = fp.load_public_data_from_dfs(
    symbol=symbol_list,
    factor_list=label_list,
    start_time=start_date,
    end_time=end_date,
    factor_type="label",
    data_type=data_type,
)
source_label_df.dropna(inplace=True, axis=0, how="all")
source_label_df["date"] = source_label_df["timestamp"].apply(
    lambda x: x.strftime("%Y%m%d")
)
source_label_df = pl.from_pandas(
    source_label_df.rename(columns={"timestamp": "DateTime"})
).with_columns(pl.col("DateTime").dt.cast_time_unit(time_unit="ms"))

# 加载因子数据
columns = [
    "P0Change",
    "OneBigTradeVol",
    "NetBidTrade",
    "NetBidOrder",
    "BreakNum",
    "BreakPricePct",
    "AskV0",
    "BidV0",
]
columns = ["Fac" + col for col in columns]
event_list = [
    "BreakingP0NumOrders",
    "OneBigOrder",
    "CumOrdersNetVolOverV0",
    "PriceSpread",
    "OneBigOrderExtend",
    "LevelOneChange",
]
event_list1 = [
    "BreakingP0NumOrders",
    "OneBigOrder",
    "CumOrdersNetVolOverV0",
    "PriceSpread",
    "LevelOneChange",
]


event_df = pl.read_parquet(
    os.path.join(flying_base_dir, "{}/{}-{}.pqt".format(symbol, symbol, date))
)
event_df = event_df.with_columns(
    (
        ((pl.col("DateTime").dt.timestamp(time_unit="ms") / 1000).cast(pl.Int64) + 1)
        * 1000
    ).alias("DateTimeSec")
).with_columns(pl.from_epoch("DateTimeSec", time_unit="ms"))
event_df = event_df.filter(
    (pl.col("DateTime") >= pd.to_datetime("{} 09:32:00".format(date)))
    & (pl.col("DateTime") <= pd.to_datetime("{} 14:50:00".format(date)))
)
# 删除事件数据
event_df = event_df.select(pl.all().exclude(event_list1))
# l3_df = pd.read_parquet('/dfs/group/800657/library/l3_data/{}/{}_{}.parquet'.format(symbol, symbol, date))
tick_df, order_df, trade_df, cancel_df = get_l3_trade_order_date(
    symbol, date, merge_one_order=True
)
tick_df = tick_df.with_columns(
    midprice=(pl.col("AskPrice").list[0] + pl.col("BidPrice").list[0]) / 2,
    volume=pl.col("ttl_volume") - pl.col("ttl_volume").shift(1),
)
# tick_df, order_df, trade_df, cancel_df = tick_df.to_pandas(), order_df.to_pandas(), trade_df.to_pandas(), cancel_df.to_pandas()
event_df = event_df.with_columns(
    pl.col("OneBigOrderExtend1").list[0].alias(columns[0]),
    pl.col("OneBigOrderExtend1").list[1].alias(columns[1]),
    pl.col("OneBigOrderExtend1").list[2].alias(columns[2]),
    pl.col("OneBigOrderExtend1").list[3].alias(columns[3]),
    pl.col("OneBigOrderExtend1").list[4].alias(columns[4]),
    pl.col("OneBigOrderExtend1").list[5].alias(columns[5]),
    pl.col("OneBigOrderExtend1").list[6].alias(columns[6]),
    pl.col("OneBigOrderExtend1").list[7].alias(columns[7]),
).drop("OneBigOrderExtend1")
edf_resample = resample_edf_1s(event_df, event_list=event_list)
# merge_df = edf_resample.join(source_label_df, on = "DateTime")
# columns


source_label_df.sort(label_name).select(["DateTime", label_name])
merge_df = event_df.join(
    source_label_df, left_on="DateTimeSec", right_on="DateTime", how="left"
)
sub_merge_df = (
    group_by_sort(merge_df, label_name).sort("DateTime")#.filter(pl.col("groups") == 9)
)
# 过滤先跌的时刻
# sub_merge_df = sub_merge_df.filter(pl.col("LabelFirstPeak_th05_60s") > 0)
# sub_merge_df = sub_merge_df.select(
#     [pl.col("DateTimeSec"), pl.all().exclude("DateTimeSec")]
# )
sub_merge_df = sub_merge_df.to_pandas()
sub_merge_df1 = sub_merge_df.set_index("DateTimeSec")
# sub_merge_df1["LabelFirstPeak_th05_60s"].head(7500).plot()
# sub_merge_df1["LabelFirstPeak_th10_60s"].head(7500).plot()
#
# sub_merge_df["LabelFirstPeak_th05_60s"].plot()
# sub_merge_df["LabelFirstPeak_th10_60s"].plot()
# source_label_df



pl.Config.set_tbl_rows(200)
pd.set_option("display.max_rows", None)
with pl.Config(tbl_rows=-1):
    sub_merge_df1 = sub_merge_df.drop(
        columns=[
            "DateTime",
            "ActivePriceVolume",
            "MDDate",
            "FacActivePVBuy",
            "FacActivePVSell",
            "Timestamp",
            "FacPriceSpread",
            "FacOneBigOrderExtend",
            "M_HTSCSecurityID",
            "R_HTSCSecurityID",
            "LabelFirstPeak_th12_60s",
        ]
    )
    print(sub_merge_df1[sub_merge_df1["FacNetBidTrade"]!=0].iloc[400:900])

