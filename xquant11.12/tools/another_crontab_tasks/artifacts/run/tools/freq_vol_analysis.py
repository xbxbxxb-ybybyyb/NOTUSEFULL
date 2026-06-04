import os
import pandas as pd
import polars as pl
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
from artifacts.flying_functions import *
from artifacts.utils import FileLock
from L3FactorFrame.MarketDataManager import *
from xquant.factordata import FactorData
from datetime import datetime
import copy
from tqdm import tqdm
from xquant.marketdata import MarketData
from matplotlib import pyplot as plt
# ma = MarketData()
import ray


def analysis_freq_vol(symbol, date, trade_sample_every = "100ms", #单位毫秒
    vol_sample_every ='10s', #滑动窗口大小
    vol_sample_period="30s", #计算窗口大小
    sampling_period = 30): #傅里叶变换采样间隔30s):

    date1 = pd.to_datetime(date).strftime("%Y-%m-%d")

    # source_tick_df = ma.get_data_by_date("Stock", symbol, date)
    # source_tick_df = source_tick_df[(source_tick_df["MDTime"]>="093000000") & (source_tick_df["MDTime"]<="150000000")].reset_index(drop = True)

    # l3_df = pd.read_parquet('/dfs/group/800657/library/l3_data/{}/{}_{}.parquet'.format(symbol, symbol, date))
    tick_df, order_df, trade_df, cancel_df = get_l3_trade_order_date(symbol, date, merge_one_order = True)
    tick_df, order_df, trade_df, cancel_df = tick_df.to_pandas(), order_df.to_pandas(), trade_df.to_pandas(), cancel_df.to_pandas()
    tick_df["midprice"] = (tick_df["AskPrice"].apply(lambda x:x[0])+tick_df["BidPrice"].apply(lambda x:x[0]))/2
    tick_df["volume"] = tick_df["ttl_volume"]-tick_df["ttl_volume"].shift(1)
    trade_df = pl.from_pandas(trade_df).with_columns(pl.col("Timestamp")*1000.0). \
        with_columns(pl.from_epoch("Timestamp",time_unit="ms").alias("DateTime"))


    fp = FactorProvider('016884')
    label_name = "LabelFirstPeak_th12_60s"
    SYMBOL_LIST = [symbol]
    DATES = [date]
    # for symbol in tqdm(SYMBOL_LIST):
    label_df = fp.load_public_data_from_dfs(symbol=SYMBOL_LIST, factor_list=[label_name,],
                                                        start_time=DATES[0],
                                                        end_time=DATES[-1],
                                                        factor_type="label",
                                                        data_type="tick_l2p"
                                                        )
    factor_df = fp.load_public_data_from_dfs(symbol=SYMBOL_LIST, factor_list=["ReferenceMidPrice"],
                                                        start_time=DATES[0],
                                                        end_time=DATES[-1],
                                                        factor_type="factor",
                                                        data_type="tick_l2p"
                                                        )
    factor_label_df = pd.merge(label_df, factor_df, left_on = "timestamp", right_on = "timestamp")
    factor_label_df = factor_label_df.set_index("timestamp")
    factor_label_df.drop(columns=["R_HTSCSecurityID_x", "M_HTSCSecurityID_y", "R_HTSCSecurityID_y"], inplace=True)
    factor_label_df = factor_label_df.rename(columns={"M_HTSCSecurityID_x": "symbol"})
    factor_label_df["date"] = factor_label_df.index.date.astype(str)
    factor_label_df["date"] = factor_label_df["date"].apply(lambda x:x.replace("-", ""))
    factor_label_df["DateTime"] = factor_label_df.index


    ###########################逐笔成交数据采样，区分买卖方向#############################
    how_method_dict = {
        #                 'BreakingP0NumOrders': pl.col('BreakingP0NumOrders').sum(),
        #                 'OneBigOrder': pl.col('OneBigOrder').sum(),
        #                 'CumOrdersNetVolOverV0': pl.col('CumOrdersNetVolOverV0').sum(),
        #                 'PriceSpread': pl.col('PriceSpread').sum(),
        #                 'LevelOneChange': pl.col('LevelOneChange').sum(),
        "Pstd": pl.col("Price").std(),
        "P0": pl.col("Price").first(),
        "P1": pl.col("Price").last(),
        "Ret": pl.when(pl.col("Price").first() != 0).then(pl.col("Price").last() / pl.col("Price").first() - 1).otherwise(
            0.0),
        "PriceList": pl.col("Price").explode()
    }


    def df_fill_null(df):
        # 补齐缺失成交秒内的数据，用前值填充
        df_fill = df.select([
            pl.col("DateTime").min().alias("startTime"), pl.col("DateTime").max().alias("endTime")
        ]).select([
            pl.date_range(pl.col("startTime"), pl.col("endTime"), interval=trade_sample_every).alias("DateTime")
        ]).join(df, how="left", on=["DateTime"])  # .fill_null(strategy = "zero")
        df_fill = df_fill.with_columns([
            pl.all().exclude(["Volume", "Amount", "msg_buy_no", "msg_sell_no"]).fill_null(strategy="forward"),
            pl.col("Volume").fill_null(strategy="zero").alias("Volume"),
            pl.col("Amount").fill_null(strategy="zero").alias("Amount")
        ]
        )
        return df_fill


    if trade_sample_every:
        trade_df_sample_buy = trade_df.filter(pl.col("BSFlag") == 1).with_columns(pl.col("DateTime").set_sorted()). \
            group_by_dynamic(index_column='DateTime', every=trade_sample_every, closed="left", label="right").agg(
            [pl.all().exclude(["DateTime", "Volume", "Amount"]).last()] + [pl.col("Volume").sum(), pl.col("Amount").sum()]
        )
        trade_df_sample_sell = trade_df.filter(pl.col("BSFlag") == 2).with_columns(pl.col("DateTime").set_sorted()). \
            group_by_dynamic(index_column='DateTime', every=trade_sample_every, closed="left", label="right").agg(
            [pl.all().exclude(["DateTime", "Volume", "Amount"]).last()] + [pl.col("Volume").sum(), pl.col("Amount").sum()]
        )
        trade_df_sample = pl.concat([trade_df_sample_buy, trade_df_sample_sell]).sort("DateTime")

        # 补齐缺失成交秒内的数据，用前值填充
        trade_df_sample_buy_fill = df_fill_null(trade_df_sample_buy)
        trade_df_sample_sell_fill = df_fill_null(trade_df_sample_sell)
        trade_df_sample_fill = df_fill_null(trade_df_sample)

        before_buy_trade_df = trade_df_sample_buy_fill
        before_sell_trade_df = trade_df_sample_sell_fill
        before_all_trade_df = trade_df_sample_fill
    else:
        before_buy_trade_df = trade_df.filter(pl.col("BSFlag") == 1)
        before_sell_trade_df = trade_df.filter(pl.col("BSFlag") == 2)
        before_all_trade_df = trade_df

    # 通过采样窗口聚合数据，窗口内的数据用于波动率和傅里叶变换计算
    s_buy_trade_df = before_buy_trade_df. \
        with_columns(pl.col("DateTime").set_sorted()). \
        group_by_dynamic(index_column='DateTime', every=vol_sample_every, period=vol_sample_period, closed="left",
                         label="right"). \
        agg(**how_method_dict)

    s_sell_trade_df = before_sell_trade_df. \
        with_columns(pl.col("DateTime").set_sorted()). \
        group_by_dynamic(index_column='DateTime', every=vol_sample_every, period=vol_sample_period, closed="left",
                         label="right").agg(
        **how_method_dict)
    #
    s_all_trade_df = before_all_trade_df. \
        with_columns(pl.col("DateTime").set_sorted()). \
        group_by_dynamic(index_column='DateTime', every=vol_sample_every, period=vol_sample_period, closed="left",
                         label="right").agg(
        **how_method_dict)

    all_trade_df = s_all_trade_df.to_pandas().set_index("DateTime")
    buy_trade_df = s_buy_trade_df.to_pandas().set_index("DateTime").reindex(
        index=all_trade_df.index)  # .join(all_trade_df, on = "DateTime")
    sell_trade_df = s_sell_trade_df.to_pandas().set_index("DateTime").reindex(
        index=all_trade_df.index)  # .join(all_trade_df, on = "DateTime")
    all_trade_df = all_trade_df.reset_index()
    buy_trade_df = buy_trade_df.reset_index()
    sell_trade_df = sell_trade_df.reset_index()

    # buy_trade_df = buy_trade_df.filter((pl.col("DateTime") >= pd.to_datetime("{} 09:30:00".format(date))) & (
    #             pl.col("DateTime") <= pd.to_datetime("{} 14:50:00".format(date))))
    # sell_trade_df = sell_trade_df.filter((pl.col("DateTime") >= pd.to_datetime("{} 09:30:00".format(date))) & (
    #             pl.col("DateTime") <= pd.to_datetime("{} 14:50:00".format(date))))
    # all_trade_df = all_trade_df.filter((pl.col("DateTime") >= pd.to_datetime("{} 09:31:00".format(date))) & (
    #             pl.col("DateTime") <= pd.to_datetime("{} 14:50:00".format(date))))
    all_trade_df.shape

    ##########################傅里叶变换分析##############################
    from scipy.signal import find_peaks

    # 不应该用到未来数据
    day_mean = trade_df["Price"].mean()
    day_std = trade_df["Price"].std()
    f_result = []
    for i,(rowid, row) in enumerate(all_trade_df.iterrows()):
        # if i>10:
        #     break
        x = row["PriceList"]
        x = x/x[0]-1
    #     x = (x-np.mean(x))/np.sqrt(np.std(x))
        y = np.fft.fft(x)
    #     pd.DataFrame(x).plot()
    #     plt.show()
    #     show(x, y)
        ori_func = x
        ft = y
        n = len(ori_func)
        interval = sampling_period / n
        # plt.subplot(2, 1, 1)
        # plt.plot(np.arange(0, sampling_period, interval)[:n], ori_func, 'black')
        # plt.xlabel('Time'), plt.ylabel('Amplitude')
        # plt.subplot(2,1,2)
        frequency = np.arange(n / 2) / (n * interval)
        nfft = abs(ft[range(int(np.ceil(n / 2)))] / n )
        # plt.plot(frequency, nfft, 'red', marker = 'o')
        # plt.xlabel('Freq (Hz)'), plt.ylabel('Amp. Spectrum')
        # plt.show()
        tol_value = np.sum(nfft)
        if tol_value:
            peaks = find_peaks(nfft)[0]
            try:
                if len(peaks) >= 3:
                    f_result.append([row["DateTime"], 0, peaks[0],peaks[1],peaks[2],
                                     nfft[0]/tol_value, nfft[peaks[0]]/tol_value, nfft[peaks[1]]/tol_value, nfft[peaks[2]]/tol_value,
                                     nfft[0]/tol_value,  nfft[:peaks[0]+1].sum()/tol_value,  nfft[:peaks[1]+1].sum()/tol_value,  nfft[:peaks[2]+1].sum()/tol_value,
                                     tol_value
                                    ] )
                elif len(peaks) >= 2:
                    f_result.append([row["DateTime"], 0, peaks[0],peaks[1], 0,
                                     nfft[0]/tol_value, nfft[peaks[0]]/tol_value, nfft[peaks[1]]/tol_value, 0,
                                     nfft[0]/tol_value,  nfft[:peaks[0]+1].sum()/tol_value,  nfft[:peaks[1]+1].sum()/tol_value,  nfft[:peaks[1]+1].sum()/tol_value,
                                     tol_value
                                    ] )
                elif len(peaks) >= 1:
                    f_result.append([row["DateTime"], 0, peaks[0], 0, 0,
                                     nfft[0] / tol_value, nfft[peaks[0]] / tol_value, 0, 0,
                                     nfft[0] / tol_value, nfft[:peaks[0] + 1].sum() / tol_value,
                                     nfft[:peaks[0] + 1].sum() / tol_value, nfft[:peaks[0] + 1].sum() / tol_value,
                                     tol_value
                                     ])
            except:
                import traceback
                print(traceback.print_exc())

    columns = ["DateTime", "Peak0Loc", "Peak1Loc", "Peak2Loc", "Peak3Loc", "Peak0V", "Peak1V", "Peak2V", "Peak3V",
               "CumPeak0V", "CumPeak1V", "CumPeak2V", "CumPeak3V", "TolFreq"]
    f_result_df = pd.DataFrame(f_result, columns = columns)

    ###################波动率和收益率分析##########################
    std_result_df = pd.DataFrame()
    std_result_df["BuyPstd"] = buy_trade_df["Pstd"]
    std_result_df["SellPstd"] = sell_trade_df["Pstd"]
    std_result_df["AllPstd"] = all_trade_df["Pstd"].values
    std_result_df["Ret"] = all_trade_df["Ret"].values
    std_result_df["DateTime"] = buy_trade_df["DateTime"]
    std_result_df = std_result_df.set_index("DateTime")
    std_result_df = std_result_df.join(factor_label_df, how = "inner")
    std_result_df.index = std_result_df.index.time.astype(str)
    # std_result_df.plot()


    import plotly
    from plotly.subplots import make_subplots
    import plotly.graph_objects as go
    pyplt = plotly.offline.plot

    x = std_result_df.index
    price = std_result_df["ReferenceMidPrice"].values
    ret = std_result_df["Ret"].values*1000#std_result_df[label_name].values
    y1 = std_result_df["BuyPstd"].values
    y2 = -std_result_df["SellPstd"].values
    y3 = std_result_df["BuyPstd"].values-std_result_df["SellPstd"].values
    y4 = std_result_df["AllPstd"].values
    y5 = std_result_df[label_name].values


    df = pd.DataFrame([ret, price, y1, y2, y3, y4, y5]).T
    df.columns = ["ret", "price", "BuyPstd", "SellPstd", "Pstd_diff", "AllPstd", label_name]
    # display(df.corr())

    # fig = make_subplots(specs=[[{'secondary_y': True}]],
    #                         row_heights=[150],
    #                         rows=1, cols=1)

    # fig.add_trace(go.Scatter(name='Mid',
    #                          x=x, y=price, line_color="skyblue",
    #                          # text = df["probs"]
    #                          ), secondary_y=True, row=1, col=1)

    # fig.add_trace(go.Scatter(name='Ret',
    #                          x=x, y=ret, line_color="skyblue",
    #                          # text = df["probs"]
    #                          ), secondary_y=True, row=1, col=1)

    # fig.add_trace(go.Scatter(name='BuyRet',
    #                          x=x, y=y1, line_color="red",
    #                          # text = df["probs"]
    #                          ), secondary_y=False, row=1, col=1)

    # fig.add_trace(go.Scatter(name='SellRet',
    #                          x=x, y=y2, line_color="green",
    #                          # text = df["probs"]
    #                          ), secondary_y=False, row=1, col=1)

    # fig.add_trace(go.Scatter(name='BuySellStd',
    #                          x=x, y=y3, line_color="green",
    #                          # text = df["probs"]
    #                          ), secondary_y=False, row=1, col=1)

    # fig.update_layout(width=1000, height=800, title_text='MarketData with Signals & Trades',
    #                   xaxis_title="Date_", yaxis_title="Price",
    #                   legend=dict(y=0.5, traceorder='reversed', font_size=16))
    # fig.show()

    ######################结果存储#####################
    result_df = std_result_df.merge(f_result_df, left_on = "DateTime", right_on = "DateTime")
    result_df["trade_sample_every"] = trade_sample_every
    result_df["vol_sample_every"] = vol_sample_every
    result_df["vol_sample_period"] = vol_sample_period
    result_df["sampling_period"] = sampling_period

    base_dir = os.path.join("/dfs/group/800657/library/tmp_l3_event/freq_data", symbol)
    os.makedirs(base_dir, exist_ok=True)
    save_parquet_path = os.path.join(base_dir, "{}-{}.pqt".format(symbol, date))
    lock = FileLock("/tmp/{}-{}".format(symbol, date))
    lock.acquire()
    if os.path.exists(save_parquet_path):
        old_result_df = pl.read_parquet(save_parquet_path)
        old_result_df = old_result_df.filter(~((pl.col("trade_sample_every")==trade_sample_every) & \
                                             (pl.col("vol_sample_every") == vol_sample_every) & \
                                             (pl.col("vol_sample_period") == vol_sample_period) & \
                                             (pl.col("sampling_period") == sampling_period)))
        # print(old_result_df)
        result_df = pl.from_pandas(result_df)#.select(columns = old_result_df.columns)
        result_df = pl.concat([result_df, old_result_df])
        result_df.write_parquet(save_parquet_path)
    else:
        result_df = pl.from_pandas(result_df)
        result_df.write_parquet(save_parquet_path)
    lock.release()
    lock.close()

@ray.remote
def func(symbol, date, trade_sample_every,
                              vol_sample_every,
                              vol_sample_period,
                              sampling_period
                              ):
    try:
        analysis_freq_vol(symbol, date, trade_sample_every=trade_sample_every,  # 单位毫秒
                              vol_sample_every=vol_sample_every,  # 滑动窗口大小
                              vol_sample_period=vol_sample_period,  # 计算窗口大小
                              sampling_period = sampling_period)
    except:
        import traceback
        print("ERROR: ",symbol, date, trade_sample_every,vol_sample_every,vol_sample_period )
        print(traceback.print_exc())

if __name__=="__main__":
    debug = False
    symbol = "688256.SH"
    date = "20240612"
    trade_sample_every = "100ms" #单位毫秒
    vol_sample_every ='5s' #滑动窗口大小
    vol_sample_period="30s" #计算窗口大小
    sampling_period = int(vol_sample_period[:-1]) #傅里叶变换采样间隔30s

    # task = analysis_freq_vol(symbol, date, trade_sample_every=trade_sample_every,  # 单位毫秒
    #                           vol_sample_every=vol_sample_every,  # 滑动窗口大小
    #                           vol_sample_period=vol_sample_period,  # 计算窗口大小
    #                           sampling_period=int(vol_sample_period[:-1]))

    fa = FactorData()
    symbols = ["688012.SH","688041.SH","688047.SH","688256.SH","688271.SH","688498.SH","688506.SH", "688017.SH", "688981.SH", "688111.SH", "688008.SH"]
    dates = fa.tradingday("20240101", "20240617")
    tasks = []
    for symbol in symbols:
        for date in dates:
            for trade_sample_every in ["100ms", "", "10ms"]:
                for vol_sample_every in ['5s', '10s']:
                    for vol_sample_period in ['30s', '60s']:
                        task = func.remote(symbol, date, trade_sample_every=trade_sample_every,  # 单位毫秒
                              vol_sample_every=vol_sample_every,  # 滑动窗口大小
                              vol_sample_period=vol_sample_period,  # 计算窗口大小
                              sampling_period = int(vol_sample_period[:-1]))
                        tasks.append(task)
        ray.get(tasks)
        print("{} finisth!".format(symbol))