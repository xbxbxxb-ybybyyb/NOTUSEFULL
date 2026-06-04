# -*- coding: utf-8 -*-
import os
import csv
import sys
import datetime
import gzip
import shutil
import traceback
import numpy as np
import pandas as pd
from collections import defaultdict
from ftplib import FTP
from xquant.xqutils.helper import link
from xquant.factordata import FactorData
fd = FactorData()
lm = link.LinkMessage()


class FTP_OP(object):
    def __init__(self, host, username, password, port):
        self.host = host
        self.username = username
        self.password = password
        self.port = port

    def ftp_connect(self):
        ftp = FTP()
        ftp.set_debuglevel(0)
        ftp.connect(host=self.host, port=self.port)
        ftp.login(self.username, self.password)
        print(f"ftp is connected")
        return ftp

    def download_file(self, ftp_file_path, dst_file_path, target_file):
        buffer_size = 10240
        ftp = self.ftp_connect()
        file_list = ftp.nlst(ftp_file_path)
        if target_file in file_list:
            ftp_file = os.path.join(ftp_file_path, target_file)
            write_file = os.path.join(dst_file_path, target_file)
            if not os.path.exists(dst_file_path):
                os.makedirs(dst_file_path)
            if not os.path.exists(write_file):
                with open(write_file, "wb") as f:
                    ftp.retrbinary('RETR {0}'.format(
                        ftp_file), f.write, buffer_size)
                print(f"target file {target_file} is downloaded")
            else:
                print(
                    f"target file {target_file} is not downloaded, for it has been under {dst_file_path}")
            ftp.quit()
        else:
            print(
                f'target file {target_file} does not exist under {ftp_file_path}')
            ftp.quit()


class PARSE_LOG():
    def __init__(self, file_path):
        self.file_path = file_path
        self.symbols = dict()
        self.predictions = defaultdict(list)
        self.NewOrderPlaced = defaultdict(dict)
        self.OrderCompleted = defaultdict(dict)
        self.SpecialEvent = defaultdict(list)
        os.chdir(self.file_path)

    def read_date(self, logfile, date):
        try:
            self.target_file = logfile
            with gzip.open(logfile, 'rb') as f:
                for line in f:
                    arr = line.decode().strip().split(' ')
                    if "Prediction:" in arr:
                        for i in range(len(arr)):
                            if arr[i].startswith("Time="):
                                tick_time = arr[i][5:-1]
                                if len(tick_time) != 8:
                                    tick_time += ':00'
                                timestamp = datetime.datetime.combine(
                                    datetime.datetime.strptime(date, "%Y%m%d").date(),
                                    datetime.time(int(tick_time[:2]), int(tick_time[3:5]), int(tick_time[6:8]))
                                ).timestamp()
                            elif arr[i].startswith("Symbol="):
                                symbol = arr[i][7:-1]
                            elif arr[i].startswith("1minLong="):
                                min1Long = arr[i][9:-1]
                            elif arr[i].startswith("1minShort="):
                                min1Short = arr[i][10:-1]
                            elif arr[i].startswith("2minLong="):
                                min2SLong = arr[i][9:-1]
                            elif arr[i].startswith("2minShort="):
                                min2Short = arr[i][10:-1]
                            elif arr[i].startswith("5minLong="):
                                min5SLong = arr[i][9:-1]
                            elif arr[i].startswith("5minShort="):
                                min5Short = arr[i][10:-1]
                            else:
                                continue
                        self.predictions[symbol].append((timestamp, tick_time, min1Long, min1Short, min2SLong,
                                                         min2Short, min5SLong, min5Short))
                    elif "NewOrderPlaced:" in arr:
                        for i in range(len(arr)):
                            if arr[i].startswith("tick_time="):
                                tick_time = arr[i+3]
                            elif arr[i].startswith("symbol="):
                                symbol = arr[i][7:-1]
                            elif arr[i].startswith("clOrdId="):
                                ClOrdId = arr[i][8:-1]
                            elif arr[i].startswith("comments="):
                                OrderType = arr[i][9:]
                            elif arr[i].startswith("orderQty="):
                                Quantity = arr[i][9:-1]
                            elif arr[i].startswith("orderPrice="):
                                Price = arr[i][11:-1]
                            elif arr[i].startswith("orderSide="):
                                Side = arr[i][10:-1]
                            elif arr[i].startswith("portfolioNo="):
                                PortfolioNo = arr[i][12:-1]
                            else:
                                continue
                        if PortfolioNo not in self.NewOrderPlaced[symbol]:
                            self.NewOrderPlaced[symbol][PortfolioNo] = []
                        self.NewOrderPlaced[symbol][PortfolioNo].append(
                            (tick_time, symbol, ClOrdId, OrderType, Quantity, Price, Side, PortfolioNo)
                        )

                    elif "OrderCompleted:" in arr:
                        for i in range(len(arr)):
                            if arr[i].startswith("tickTime="):
                                tick_time = arr[i][9:-1]
                            if arr[i].startswith("transactionTime="):
                                transaction_time = arr[i][16:-1]
                            elif arr[i].startswith("symbol="):
                                symbol = arr[i][7:]
                            elif arr[i].startswith("clOrdId="):
                                ClOrdId = arr[i][8:-1]
                            elif arr[i].startswith("avgPx="):
                                AvgPrice = arr[i][6:-1]
                            elif arr[i].startswith("cumQty="):
                                CumQty = arr[i][7:-1]
                            elif arr[i].startswith("orderSide="):
                                Side = arr[i][10:-1]
                            elif arr[i].startswith("netPosition="):
                                NetPosition = arr[i][12:-1]
                            elif arr[i].startswith("ordStatus="):
                                Status = arr[i][10:-1]
                            elif arr[i].startswith("portfolioNo="):
                                PortfolioNo = arr[i][12:-1]
                            else:
                                continue
                        if PortfolioNo not in self.OrderCompleted[symbol]:
                            self.OrderCompleted[symbol][PortfolioNo] = []
                        self.OrderCompleted[symbol][PortfolioNo].append(
                            (tick_time, transaction_time, symbol, ClOrdId, AvgPrice, CumQty, Side, NetPosition, Status, PortfolioNo)
                        )

                    elif "SpecialEventAnalyze:" in arr:
                        for i in range(len(arr)):
                            if arr[i].startswith("timestamp="):
                                tick_time = arr[i][10:-1]
                            elif arr[i].startswith("symbol="):
                                symbol = arr[i][7:-1]
                            elif arr[i].startswith("SpecialEvent="):
                                SpecialEvent = arr[i][13:-1]
                            elif arr[i].startswith("positionType="):
                                positionType = arr[i][13:-1]
                            elif arr[i].startswith("lastPx="):
                                lastPx = arr[i][7:-1]
                            elif arr[i].startswith("preClosePx="):
                                preClosePx = arr[i][11:-1]
                            elif arr[i].startswith("reachLimitAndFallTickCount="):
                                reachLimitAndFallTickCount = arr[i][27:]
                            else:
                                continue
                        self.SpecialEvent[symbol].append((tick_time, symbol, SpecialEvent, positionType, lastPx,
                                                         preClosePx, reachLimitAndFallTickCount))

                    else:
                        continue
                    self.symbols[symbol] = ''
            print(f'read file {logfile} success')
        except:
            print(
                f'read file {logfile} failed, reason: {traceback.format_exc()}')
            sys.exit(0)

    def save_to_csv(self, file_dir, date):
        try:
            if file_dir not in os.listdir():
                os.mkdir(file_dir)
            os.chdir(self.file_path + os.sep + file_dir)

            if 'signals' not in os.listdir():
                os.mkdir('signals')

            op = os.getcwd()
            for symbol in self.symbols:
                ###################################### Save Live Signals to HBASE
                signal_df = pd.DataFrame(
                    sorted(set(self.predictions[symbol]), key=lambda x: x[0]),
                    columns=['timestamp', 'ticktime', 'prediction1minLong', 'prediction1minShort',
                             'prediction2minLong', 'prediction2minShort', 'prediction5minLong', 'prediction5minShort']
                )

                signal_df = signal_df.replace("null", np.nan)
                signal_df[['timestamp', 'prediction1minLong', 'prediction1minShort', 'prediction2minLong',
                           'prediction2minShort', 'prediction5minLong', 'prediction5minShort']] = \
                    signal_df[['timestamp', 'prediction1minLong', 'prediction1minShort', 'prediction2minLong',
                               'prediction2minShort', 'prediction5minLong', 'prediction5minShort']].apply(pd.to_numeric)
                signal_df = signal_df.dropna(how="all")
                # signal_df = signal_df.loc[signal_df["ticktime"] >= "09:31:15"]
                # signal_df = signal_df.loc[(signal_df["ticktime"] <= "11:30:00") | (signal_df["ticktime"] >= "13:01:15")]
                # signal_df.drop_duplicates("ticktime", keep="first", inplace=True)
                signal_df = signal_df.reset_index(drop=True)
                fd.update_factor_value("EverestProductionSignals", signal_df, symbol, str(date))
                ###################################### Save Live Signals to HBASE

                os.chdir(op + os.sep + 'signals')
                if "predictions" not in os.listdir():
                    os.mkdir("predictions")
                with open("predictions" + os.sep + symbol + "_signals.csv",
                          "w", newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(["timestamp", "tick_time", "min1Long", "min1Short", "min2Long",
                                     "min2Short", "min5Long", "min5Short"])
                    writer.writerows(self.predictions[symbol])

            os.chdir(self.file_path + os.sep + file_dir)
            if 'specialEvents' not in os.listdir():
                os.mkdir('specialEvents')

            op = os.getcwd()
            for symbol in self.symbols:
                os.chdir(op + os.sep + 'specialEvents')
                if "specialEvents" not in os.listdir():
                    os.mkdir("specialEvents")
                with open("specialEvents" + os.sep + symbol + "_specialEvents.csv",
                          "w", newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(["Timestamp", "Symbol", "SpecialEvent", "PositionType", "LastPx",
                                     "PreClosePx", "ReachLimitAndFallTickCount"])
                    writer.writerows(self.SpecialEvent[symbol])

            os.chdir(self.file_path + os.sep + file_dir)

            if 'orders' not in os.listdir():
                os.mkdir('orders')

            op = os.getcwd()
            for symbol in self.symbols:
                os.chdir(op + os.sep + 'orders')
                for p_no in self.NewOrderPlaced[symbol]:
                    if p_no not in os.listdir():
                        os.mkdir(p_no)
                        os.mkdir(p_no + os.sep + 'neworder')
                        os.mkdir(p_no + os.sep + 'completeorder')
                    with open(p_no + os.sep + 'neworder' + os.sep + symbol + "_neworder.csv", "w",
                              newline='') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(['Ticktime', 'Symbol', 'ClOrdId',
                                         'OrderType', 'Quantity', 'Price', 'Side', 'PortfolioNo'])
                        writer.writerows(self.NewOrderPlaced[symbol][p_no])
                for p_no in self.OrderCompleted[symbol]:
                    if p_no not in os.listdir():
                        os.mkdir(p_no)
                        os.mkdir(p_no + os.sep + 'neworder')
                        os.mkdir(p_no + os.sep + 'completeorder')
                    with open(p_no + os.sep + 'completeorder' + os.sep + symbol + "_completeorder.csv", "w",
                              newline='') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(['Ticktime', "TransactionTime", 'symbol', 'ClOrdId',
                                         'Price', 'CumQty', 'Side', 'NetPosition', 'Status', 'PortfolioNo'])
                        writer.writerows(self.OrderCompleted[symbol][p_no])
            print(f'save to csv files success')
        except:
            print(f'save to csv files failed, reason: {traceback.format_exc()}')
            sys.exit(0)

    def delete_logfile(self, logfile):
        os.chdir(self.file_path)
        os.remove(logfile)
        
def copy_live_log(src_path, dst_path, target_file):
    src_file_path = os.path.join(src_path, target_file)
    if not os.path.exists(src_file_path):
        raise Exception(" {} Not Exists ".format(src_file_path))

    dst_file_path = os.path.join(dst_path, target_file)
    shutil.copyfile(src_file_path, dst_file_path)
    print(" {} Copied Done ".format(dst_file_path))


def main():
    date = datetime.datetime.now().strftime("%Y%m%d")
    strategy_name = "Easy"
    target_file = strategy_name + 'Strategy-{}-{}-{}.log.gz'.format(date[:4], date[4:6], date[6:])
    output_dir = date

    host = "168.8.2.68"
    ftp_username = "xquant"
    ftp_password = "Xquant-32"
    port = 21
#    ftp_file_path = "/XQuant/XTraderStrategyLog/"
    ftp_file_path = "/data/group/XTraderStrategyLog/prd/"
    dst_file_path = "/data/user/015629/Easy/productionLog/"

    if not os.path.exists(dst_file_path + target_file):
        # ftp = FTP_OP(host=host, username=ftp_username, password=ftp_password, port=port)
        # ftp.download_file(ftp_file_path=ftp_file_path, dst_file_path=dst_file_path, target_file=target_file)
        copy_live_log(ftp_file_path, dst_file_path, target_file)

    parse_log = PARSE_LOG(dst_file_path)
    parse_log.read_date(target_file, date)
    parse_log.save_to_csv(output_dir, date)
    # parse_log.delete_logfile(target_file)

    lm.sendMessage(" Decode Easy Production Log Done: {} ".format(date))


if __name__ == "__main__":
    main()
