import polars as pl
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
from xquant.factordata import FactorData
import os
# from xquant.xqutils.perf_profile import profile
# @profile
def get_l2p_data(symbol, start_date, end_date):
    fp = FactorProvider("016869")
    if symbol.endswith("SH"):
        mkt_type = "sh_stock_tick_l2p_persec"
    elif symbol.endswith("SZ"):
        mkt_type = "sz_stock_tick_l2p_persec"
    else:
        raise Exception()
    try:
        start_date = start_date.replace("-", "")
        end_date = end_date.replace("-", "")
        l2p_df = fp.get_market_data(symbol,start_date,end_date,tableName=mkt_type)
    except:
        print("get_l2p_data ERROR:", symbol, start_date, end_date)
        return
    if len(l2p_df)==0:
        return pl.DataFrame()
    l2p_df = pl.from_pandas(l2p_df[["M_MDDate", "M_MDTime", "M_BuyPrice","M_SellPrice", "M_BuyOrderQty","M_SellOrderQty", "M_OpenPx" ]])
    l2p_df = l2p_df.with_columns(Bid1P = pl.col("M_BuyPrice").list[0],
                                Ask1P = pl.col("M_SellPrice").list[0],
                                M_BuyPrice = pl.col("M_BuyPrice").list.slice(0,5),
                                M_SellPrice = pl.col("M_SellPrice").list.slice(0, 5))
    l2p_df = l2p_df.with_columns(
        pl.concat_str(
        pl.col("M_MDDate").cast(str).str.slice(0,11), pl.col("M_MDTime")).alias("DateTime")
    )
    l2p_df = l2p_df.with_columns(
        pl.col("DateTime").str.strptime(dtype=pl.Datetime, format="%Y-%m-%d %H:%M:%S", strict=False).dt.cast_time_unit("ns"),
        pl.col("M_SellPrice").list[0].alias("Ask1P"),
        pl.col("M_BuyPrice").list[0].alias("Bid1P")
    )
    return l2p_df


def load_polars_label(symbol_name, start_date, end_date, label_name = None):
    fa = FactorData()
    base_save_dir = "/dfs/group/800657/library/tag_data"
    df_list = []
    dates = fa.tradingday(start_date, end_date)
    for date in dates:
        try:
            save_parquet_path = os.path.join(base_save_dir, "{}/{}-{}.pqt".format(symbol_name, symbol_name, date))
            if label_name == None:
                sub_df = pl.read_parquet(save_parquet_path)
                sub_df = sub_df.drop(["__index_level_0__"])
                sub_df = sub_df.with_columns(SYMBOL = pl.lit(symbol_name))
                assert len(sub_df.columns)==98
            else:
                sub_df = pl.read_parquet(save_parquet_path, columns = ["DateTime", label_name])
            df_list.append(sub_df)
        except FileNotFoundError as e:
            pass
        except Exception as e:
            from traceback import print_exc
            print(symbol_name, date, sub_df.shape, print_exc())
    df = pl.concat(df_list)
    return df



def load_polars_order_book(symbol_name, start_date, end_date):
    """
    加载逐笔盘口数据，展开10档数据
    :param symbol_name:
    :param start_date:
    :param end_date:
    :return:
    """
    def resample_1s(edf_ms, event_list = []):
        ###################对1s内的数据采样保留第一条#############################
        how_method_dict = {}
        for col in edf_ms.columns:
            if col not in ["timestamp"]:
                how_method_dict[col] = pl.col(col).first()
        # polars的resample不会补全缺失的秒
        edf_resample_1s = edf_ms.with_columns(pl.col("timestamp").set_sorted()). \
            group_by_dynamic(index_column='timestamp', every='1s', closed="left", label="right").agg(
            **how_method_dict)
        return edf_resample_1s
    import os
    from xquant.factordata import FactorData
    import polars  as pl
    fa = FactorData()
    base_save_dir = "/dfs/group/800657/library/l3_data"
    df_list = []
    dates = fa.tradingday(start_date, end_date)
    for date in dates:
        try:
            save_parquet_path = os.path.join(base_save_dir, "{}/{}_{}.parquet".format(symbol_name, symbol_name, date))
            sub_df = pl.read_parquet(save_parquet_path)
            sub_df = sub_df.with_columns(symbol = pl.lit(symbol_name), date = pl.lit(date))
            ###################展开40档盘口数据###################
            sub_df = sub_df.filter(
                (pl.col("mdtime") >= int(date + '093030000')) & (pl.col("mdtime") <= int(date + '113000000')) |
                (pl.col("mdtime") >= int(date + '130000000')) & (pl.col("mdtime") <= int(date + '145600000')))
            sub_df = sub_df.select(["symbol", "date", "mdtime", "asks_price", "bids_price", "asks_qty", "bids_qty"]).with_columns(
                pl.col("asks_price").list[0].alias("ask0_p"),
                pl.col("asks_price").list[1].alias("ask1_p"),
                pl.col("asks_price").list[2].alias("ask2_p"),
                pl.col("asks_price").list[3].alias("ask3_p"),
                pl.col("asks_price").list[4].alias("ask4_p"),
                pl.col("asks_price").list[5].alias("ask5_p"),
                pl.col("asks_price").list[6].alias("ask6_p"),
                pl.col("asks_price").list[7].alias("ask7_p"),
                pl.col("asks_price").list[8].alias("ask8_p"),
                pl.col("asks_price").list[9].alias("ask9_p"),
                pl.col("bids_price").list[0].alias("bid0_p"),
                pl.col("bids_price").list[1].alias("bid1_p"),
                pl.col("bids_price").list[2].alias("bid2_p"),
                pl.col("bids_price").list[3].alias("bid3_p"),
                pl.col("bids_price").list[4].alias("bid4_p"),
                pl.col("bids_price").list[5].alias("bid5_p"),
                pl.col("bids_price").list[6].alias("bid6_p"),
                pl.col("bids_price").list[7].alias("bid7_p"),
                pl.col("bids_price").list[8].alias("bid8_p"),
                pl.col("bids_price").list[9].alias("bid9_p"),
                pl.col("asks_qty").list[0].alias("ask0_v"),
                pl.col("asks_qty").list[1].alias("ask1_v"),
                pl.col("asks_qty").list[2].alias("ask2_v"),
                pl.col("asks_qty").list[3].alias("ask3_v"),
                pl.col("asks_qty").list[4].alias("ask4_v"),
                pl.col("asks_qty").list[5].alias("ask5_v"),
                pl.col("asks_qty").list[6].alias("ask6_v"),
                pl.col("asks_qty").list[7].alias("ask7_v"),
                pl.col("asks_qty").list[8].alias("ask8_v"),
                pl.col("asks_qty").list[9].alias("ask9_v"),
                pl.col("bids_qty").list[0].alias("bid0_v"),
                pl.col("bids_qty").list[1].alias("bid1_v"),
                pl.col("bids_qty").list[2].alias("bid2_v"),
                pl.col("bids_qty").list[3].alias("bid3_v"),
                pl.col("bids_qty").list[4].alias("bid4_v"),
                pl.col("bids_qty").list[5].alias("bid5_v"),
                pl.col("bids_qty").list[6].alias("bid6_v"),
                pl.col("bids_qty").list[7].alias("bid7_v"),
                pl.col("bids_qty").list[8].alias("bid8_v"),
                pl.col("bids_qty").list[9].alias("bid9_v"),
                pl.col("mdtime").cast(pl.String).str.strptime(dtype=pl.Datetime, format="%Y%m%d%H%M%S%3f").dt.cast_time_unit("ns")
            ).drop(["asks_price", "bids_price", "asks_qty", "bids_qty"]).rename({"mdtime":"timestamp"})
            sub_df = resample_1s(sub_df)
            df_list.append(sub_df)
        except FileNotFoundError as e:
            print(e)
            pass
        except Exception as e:
            from traceback import print_exc
            print(symbol_name, date, sub_df.shape, print_exc())
    df = pl.concat(df_list)
    return df



