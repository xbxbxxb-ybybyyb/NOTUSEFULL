# -*- coding: utf-8 -*-
import os
import csv
import sys
import datetime
import gzip
import traceback
import numpy as np
import pandas as pd
from collections import defaultdict
from ftplib import FTP
from xquant.factordata import FactorData

HOST = "168.8.2.68"
FTP_USERNAME = "xquant"
FTP_PASSWORD = "Xquant-32"
PORT = 21
FTP_FILE_PATH = "/XQuant/XTraderStrategyLog/"
DST_FILE_PATH = "/data/user/666888/Apollo/production_log/"


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
            sys.exit(0)


class PARSE_LOG():
    def __init__(self, file_path):
        self.file_path = file_path
        self.symbols = dict()
        self.predictions = defaultdict(list)
        self.NewOrderPlaced = defaultdict(dict)
        self.OrderCompleted = defaultdict(dict)
        os.chdir(self.file_path)

    def read_date(self, logfile):
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
                                    datetime.date(int(logfile[-17:-13]), int(logfile[-12:-10]), int(logfile[-9:-7])),
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
                                min5Short = arr[i][10:]
                            # elif arr[i].startswith("Ema="):
                                # ema = arr[i][4:-1]
                            # elif arr[i].startswith("TargetToOrder="):
                                # target = arr[i][14:]
                            else:
                                continue
                        self.predictions[symbol].append((timestamp, tick_time, symbol, min1Long, min1Short, min2SLong,
                                                         min2Short, min5SLong, min5Short))
                    elif "NewOrderPlaced:" in arr:
                        for i in range(len(arr)):
                            if arr[i].startswith("tick_time="):
                                tick_time = arr[i + 3]
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
                            elif arr[i].startswith("portfioloNo="):
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
                            if arr[i].startswith("TIME="):
                                tick_time = arr[i][5:-1]
                                if len(tick_time) != 8:
                                    tick_time += ':00'
                            elif arr[i].startswith("Symbol="):
                                symbol = arr[i][7:-1]
                            elif arr[i].startswith("ClOrdId="):
                                ClOrdId = arr[i][8:-1]
                            elif arr[i].startswith("OrderType="):
                                OrderType = arr[i][10:-1]
                            elif arr[i].startswith("Qty="):
                                Qty = arr[i][4:-1]
                            elif arr[i].startswith("CumQty="):
                                CumQty = arr[i][7:-1]
                            elif arr[i].startswith("CumAmt="):
                                CumAmt = arr[i][7:-1]
                            elif arr[i].startswith("AvgPrice="):
                                AvgPrice = arr[i][9:-1]
                            elif arr[i].startswith("Status="):
                                Status = arr[i][7:-1]
                            elif arr[i].startswith("Price="):
                                Price = arr[i][6:-1]
                            elif arr[i].startswith("Side="):
                                Side = arr[i][5:-1]
                            elif arr[i].startswith("PortfolioNo="):
                                PortfolioNo = arr[i][12:]
                            elif arr[i].startswith("OrderPlacedSuccessTime="):
                                OrderPlacedSuccessTime = arr[i][23:-1]
                            elif arr[i].startswith("OrderCancelledTime="):
                                OrderCancelledTime = arr[i][19:-1]
                            elif arr[i].startswith("OrderCompletedTime="):
                                OrderCompletedTime = arr[i][19:-1]
                            elif arr[i].startswith("OrderPlacedTime="):
                                OrderPlacedTime = arr[i][16:-1]
                            else:
                                continue
                        if PortfolioNo not in self.OrderCompleted[symbol]:
                            self.OrderCompleted[symbol][PortfolioNo] = []
                        self.OrderCompleted[symbol][PortfolioNo].append(
                            (tick_time, symbol, ClOrdId, OrderType, Qty, Price, Side, CumQty, CumAmt,
                             AvgPrice, Status, OrderPlacedTime, OrderPlacedSuccessTime, OrderCancelledTime,
                             OrderCompletedTime, PortfolioNo)
                        )
                    else:
                        continue
                    self.symbols[symbol] = ''
            print(f'read file {logfile} success')
        except:
            print(
                f'read file {logfile} failed, reason: {traceback.format_exc()}')
            sys.exit(0)

    def save_to_csv(self, date):
        factor_data = FactorData()
        try:
            file_dir = self.target_file[-17:-7]
            file_dir = ''.join(file_dir.split('-'))
            if file_dir not in os.listdir():
                os.mkdir(file_dir)
            os.chdir(self.file_path + os.sep + file_dir)
            if 'orders' not in os.listdir():
                os.mkdir('orders')

            op = os.getcwd()
            for symbol in self.symbols:
                signal_df = pd.DataFrame(
                    sorted(set(self.predictions[symbol]), key=lambda x: x[0]),
                    columns=['timestamp', 'ticktime', 'symbol', 'prediction1minLong', 'prediction1minShort',
                             'prediction2minLong', 'prediction2minShort', 'prediction5minLong', 'prediction5minShort']
                )[['timestamp', 'ticktime', 'prediction1minLong', 'prediction1minShort', 'prediction2minLong',
                   'prediction2minShort', 'prediction5minLong', 'prediction5minShort']]
                signal_df = signal_df.replace("null", np.nan)
                signal_df[['timestamp', 'prediction1minLong', 'prediction1minShort', 'prediction2minLong',
                   'prediction2minShort', 'prediction5minLong', 'prediction5minShort']] = \
                signal_df[['timestamp', 'prediction1minLong', 'prediction1minShort', 'prediction2minLong',
                   'prediction2minShort', 'prediction5minLong', 'prediction5minShort']].apply(pd.to_numeric)
                signal_df = signal_df.dropna(how="all")
                signal_df = signal_df.loc[signal_df["ticktime"] >= "09:31:15"]
                signal_df = signal_df.loc[(signal_df["ticktime"] <= "11:30:00") | (signal_df["ticktime"] >= "13:01:15")]
                signal_df = signal_df.reset_index(drop=True)
                factor_data.update_factor_value("ApolloProductionSignals", signal_df, symbol, date)

                os.chdir(op + os.sep + 'orders')
                for p_no in self.NewOrderPlaced[symbol]:
                    if p_no not in os.listdir():
                        os.mkdir(p_no)
                        os.mkdir(p_no + os.sep + 'neworder')
                        os.mkdir(p_no + os.sep + 'completeorder')
                    with open(p_no + os.sep + 'neworder' + os.sep + symbol + "_neworder.csv", "w",
                              newline='') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(['Ticktime', 'symbol', 'ClOrdId',
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
                        writer.writerow(['Ticktime', 'symbol', 'ClOrdId',
                                         'OrderType', 'Qty', 'Price', 'Side', 'CumQty', 'CumAmt', 'AvgPrice', 'Status',
                                         'OrderPlacedTime', 'OrderPlacedSuccessTime', 'OrderCancelledTime',
                                         'OrderCompletedTime', 'PortfolioNo'])
                        writer.writerows(self.OrderCompleted[symbol][p_no])
            print(f'save to csv files success')
        except:
            print(f'save to csv files failed, reason: {traceback.format_exc()}')
            sys.exit(0)

    def delete_logfile(self, logfile):
        os.chdir(self.file_path)
        os.remove(logfile)


def main():
    today = datetime.date.today().strftime('%Y-%m-%d')
    # today = '2019-12-09'

    FILE = 'ApolloStrategy-' + today + '.log.gz'

    ftp = FTP_OP(host=HOST, username=FTP_USERNAME,
                 password=FTP_PASSWORD, port=PORT)
    ftp.download_file(ftp_file_path=FTP_FILE_PATH,
                      dst_file_path=DST_FILE_PATH, target_file=FILE)

    parse_log = PARSE_LOG(DST_FILE_PATH)
    parse_log.read_date(FILE)
    parse_log.save_to_csv(''.join(today.split('-')))
    # parse_log.delete_logfile(FILE)


if __name__ == "__main__":
    main()
