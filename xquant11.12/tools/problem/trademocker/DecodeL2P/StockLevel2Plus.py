#-*- coding:utf-8 -*-
# author: 015629
# datetime:2021/1/20 14:20
import os
import traceback
import gc
import gzip
from collections import defaultdict
import numpy as np
import datetime as dt
import pandas as pd
from DecodeL2P.Config import CELL_SIZE
from DecodeL2P.Config import LOG_NUMERICAL_COLUMNS, LOG_ALIGN_COLUMNS, LOG_TICK_HBASE_COLUMNS
from xquant.factordata import FactorData


def decode_level2plus_log_line(line):
    """"""
    arr = line.split(" ")
    for i in range(len(arr)):
        if arr[i].startswith("symbol="):
            symbol = arr[i][7:-1]
        elif arr[i].startswith("askVolume="):
            askVolume = np.array(arr[i][10:-1].split(","), dtype=np.float64)
        elif arr[i].startswith("askPrice="):
            askPrice = np.array(arr[i][9:-1].split(","), dtype=np.float64)
        elif arr[i].startswith("bidVolume="):
            bidVolume = np.array(arr[i][10:-1].split(","), dtype=np.float64)
        elif arr[i].startswith("bidPrice="):
            bidPrice = np.array(arr[i][9:-1].split(","), dtype=np.float64)
        elif arr[i].startswith("cumQty="):
            totalVolume = arr[i][7:-1]
        elif arr[i].startswith("turnOver="):
            totalAmount = arr[i][9:-1]
        elif arr[i].startswith("lastPx="):
            lastPrice = arr[i][7:-1]
        elif arr[i].startswith("numTrade="):
            numTrades = arr[i][9:-1]
        elif arr[i].startswith("highPx="):
            highPrice = arr[i][7:-1]
        elif arr[i].startswith("lowPx="):
            lowPrice = arr[i][6:-1]
        elif arr[i].startswith("timestamp="):
            time = arr[i][10:-1]
        elif arr[i].startswith("isMocked="):
            isMocked = arr[i][9:-1]
        elif arr[i].startswith("volume="):
            volume = arr[i][7:-1]
        elif arr[i].startswith("turnover="):
            amount = arr[i][9:-1]
        elif arr[i].startswith("CBSymbol="):
            cbond = arr[i][9:]

        else:
            continue

    strategyId = arr[1][1:-1]

    level2plus_tick = [time, symbol, askVolume, askPrice, bidVolume, bidPrice, totalVolume, totalAmount, volume, amount,
                       lastPrice, numTrades, highPrice, lowPrice, isMocked]

    return strategyId, symbol, cbond, level2plus_tick


class PARSE_LOG():
    def __init__(self, file_path, hbase_library):
        self.file_path = file_path
        self.hbase_library = hbase_library
        self.id_symbols = []
        self.l2p_ticks = defaultdict()

        self.fa = FactorData()

        if not os.path.exists(self.file_path):
            os.makedirs(self.file_path)

    def read_date(self, logfile):
        try:
            logfile = self.file_path + "log/{}".format(logfile)
            with gzip.open(logfile, "rb") as f:
                for line in f:
                    arr = line.decode().strip()
                    if "GenLvl2Tick:" in arr:
                        strategyId, stock, cbond, l2p_tick = decode_level2plus_log_line(arr)
                        if (strategyId, stock, cbond) not in self.id_symbols:
                            self.id_symbols.append((strategyId, stock, cbond))

                        if strategyId not in self.l2p_ticks:
                            self.l2p_ticks[strategyId] = dict()

                        if (stock, cbond) not in self.l2p_ticks[strategyId]:
                            self.l2p_ticks[strategyId][(stock, cbond)] = []

                        self.l2p_ticks[strategyId][(stock, cbond)].append(l2p_tick)

                    else:
                        continue

            print(f'read file {logfile} success')
        except:
            print(f'read file {logfile} failed, reason: {traceback.format_exc()}')

    def save_to_csv(self, file_dir, date, save_csv=False, save_hbase=False):
        try:
            root_path = file_dir + "level2plus/{}/".format(date)
            if not os.path.exists(root_path):
                os.makedirs(root_path)

            for i, (strategyId, stock, cbond) in enumerate(self.id_symbols):
                print(i + 1, stock, cbond)
                ticks = pd.DataFrame(self.l2p_ticks[strategyId][(stock, cbond)], columns=['Time', 'Code', 'AskVolume', 'AskPrice',
                                                'BidVolume', 'BidPrice', "TotalVolume", "TotalAmount", "Volume", "Amount", "LastPrice",
                                                "NumTrades", "HighPrice", "LowPrice", "IsMock"]
                )
                ticks[LOG_NUMERICAL_COLUMNS] = ticks[LOG_NUMERICAL_COLUMNS].apply(pd.to_numeric)
                ticks = ticks[ (ticks["Volume"] >= 0) & (ticks["Amount"] >= 0)]
                ticks["IsMock"] = ticks["IsMock"].apply(lambda x: 0 if x == "false" else 1)
                ticks = ticks[ticks["IsMock"] == 0]
                ticks["Date"] = str(date)
                ticks["Time"] = ticks["Time"].apply(lambda x: "".join(x.split(":")) + "000")
                ticks["Timestamp"] = (ticks["Date"] + ticks["Time"]).apply(lambda x: dt.datetime.strptime(x + "000", "%Y%m%d%H%M%S%f").timestamp())
                ticks = ticks.sort_values(by=["Timestamp"], ascending=True)

                ticks = ticks.replace("null", np.nan)
                ticks = ticks.dropna(how="all")
                ticks = ticks.reset_index(drop=True)
                ticks = ticks.reindex(columns=LOG_ALIGN_COLUMNS)

                # 正股Tick落库时加上CBond后缀
                symbol = "{}{}".format(stock[:6], cbond[:6])

                if not ticks.empty:
                    """"""
                    if save_csv:
                        save_path = root_path + "{}_l2p_tick.csv".format(symbol)
                        ticks.to_csv(save_path, index=False)

                    if save_hbase:
                        ticks.columns = LOG_TICK_HBASE_COLUMNS
                        self.fa.update_factor_value(self.hbase_library, ticks, symbol, str(date), cell_size=CELL_SIZE)
                else:
                    print(" level2plus tick empty: {}-{} ".format(symbol, date))

            print(f'save to csv files success')
        except:
            print(f'save to csv files failed, reason: {traceback.format_exc()}')

        gc.collect()


def main():
    date = dt.datetime.now().strftime("%Y%m%d")
    date = "20210518"
    hbase_library = "ZGLevel2PlusTicks"
    dst_file_path = "/data/user/015629/WuKong/SimLog/"
    save_csv = False
    save_hbase = True
    target_file = 'ConvertibleDebtStrategy-{}-{}-{}.log.gz'.format(date[:4], date[4:6], date[6:])
    parse_log = PARSE_LOG(dst_file_path, hbase_library)
    parse_log.read_date(target_file)
    parse_log.save_to_csv(dst_file_path, date, save_csv, save_hbase)


if __name__ == "__main__":
    main()

