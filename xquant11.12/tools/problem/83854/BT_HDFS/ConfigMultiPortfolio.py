import datetime
from xquant.pyfile.ftp import pyfileFTP
import pandas as pd
import os
import BT_HDFS.stock_pools as stock_pool


order_capacity_path = "/app/data/666888/OrderCapacity/"
trade_path = "/app/data/666888/TradeData/"
root_path = "/app/data/666888/BT_Trade_OrderCapacity/"


class BacktestConfig:
    def __init__(self):
        print("------Instantiating BT Config Start------")
        self.factor_pickle_output_dir = 'output/trade_review_factor_pickle/'
        self.trade_portfolio =  ["800"]
        self.today = datetime.datetime.now() - datetime.timedelta(days=1)
        self._create_time()
        self.factor_config = "AlgoFactor48.py"

        self.factor_name = ["factorMAVolumeDistance10_20", "factorTransBuyVolumeDistance5_40", "factorDistanceToHigh100", 
                    "factorDistanceBetweenVWAPPrice40", "factorTransVolumeWeightedSwing5_10", "factorDistanceToLow40", 
                    "factorBuyPower", "factorTransSellVolumeDistance5_10", "factorDistanceToLow100", "factorDistanceBetweenVWAPPrice200", 
                    "factorSellPower", "factorCrossPriceChangeRatio", "factorMomentum", "factorEmaOrderVolumePressure", 
                    "factorTransPressureVol", "factorDistanceBetweenVWAPPrice100", "factorTransPressure", "factorOrderMomentum", 
                    "factorSpeed", "factorDistanceToVwap100", "factorMAVolumeDistance20", "factorTransSellBuy5", "factorMAVolumeDistance10_100", 
                    "factorDistanceToVwap20", "factorBuyPowerSpeed", "factorSellPowerSpeed", "factorDistanceToAvePrice", 
                    "factorDistanceToVwap40", "factorMAVolumeDistance3", "factorVolumeMagnification", "factorTransVolumeWeightedSwing5_40", 
                    "factorMAVolumeDistance40_80", "factorOrderPressure", "factorMAVolumeDistance100_200", "factorDistanceToVwapPriceWeighted", 
                    "factorDistanceBetweenVWAPPrice20", "factorMAVolumeDistance100", "factorEmaOrderAmountPressure", "factorMAVolumeDistance40", 
                    "factorCrossPriceChangeSpeed", "factorTransSellBuy10", "factorTransBuyVolumeDistance5_10", "factorMAVolumeDistance20_40", 
                    "factorTransSellVolumeDistance5_40", "factorMAVolumeDistance10_40", "factorMAVolumeDistance200", 
                    "factorDistanceToHigh40", "factorBoll"]
        self.tag_name = [["1minLong", "1minShort"], ["2minLong", "2minShort"], ["5minLong", "5minShort"]]
        
        
        self.factor_address = "output/trade_review_factor_pickle/"
        self._load_portlio_from_ftp()
        # self.codes = stock_pool.all_stocks
        # self.codes.remove("000725.SZ")
        # self.codes = ["000725.SZ"]
           #"/app/data/666888/ModelProduction/2018-10-01/20190102/"
        self.model_name = "2019-03-01"
        # self.model_path = "/data/user/ModelProduction/2019-01-01/"
        self.model_path = "/data/user/ModelProduction/" + self.model_name + "/"
        self.signal_path = "output/" + self.model_name + "/"

        print("Trade Portfolio is {}".format(self.trade_portfolio))
        print("Pre date (We use tick data of pre date to calc factor) is {} and trading date is {}".format(self.StartDateTime, self.EndDateTime))
        print("------Instantiating BT Config Over------")

    # @property
    # def codes():
        # return self.codes

    def _create_time(self):
        self.today_str = self.today.strftime('%Y%m%d')

        if self.today.weekday() == 0:
            predays = 3
        else:
            predays = 1
        pre_date = self.today - datetime.timedelta(days=predays)
        self.StartDateTime = "{}{}".format(pre_date.strftime("%Y%m%d"), "093015")
        self.EndDateTime = "{}{}".format(self.today.strftime("%Y%m%d"), "145659")


    def _load_portlio_from_ftp(self):
        ftp = pyfileFTP()
        # portfolio = self.trade_portfolio
        # zz800_codes = stock_pool.zz_800
        # all_stocks = set(zz800_codes)
        all_stocks = set(stock_pool.all_stocks)
        for portfolio in self.trade_portfolio:
            file_name = "{}_{}.xlsx".format(self.today_str, portfolio)
            if os.path.exists("/app/data/666888/ftp_uploads/"):
                path = "/app/data/666888/ftp_uploads/"+file_name
                if os.path.exists(path):
                    pass
                else:
                    ftp.downloadFile("666888/"+file_name, path)
            elif os.path.exists("/data/user/ftp_uploads/"):
                path = "/data/user/ftp_uploads/" +file_name
                if os.path.exists(path):
                    pass
                else:
                    ftp.downloadFile("666888/"+file_name, path)

            print("path is ", path)       
            df = pd.read_excel(path)

            print("combining {}'s trade and capacity".format(portfolio))
            trade_codes = list([_code for _code in df.iloc[:, 0]])


            all_stocks = all_stocks.union(set(trade_codes))
        self.codes = list(all_stocks)
       # self.codes.remove("000725.SZ")   
       # self.volumes = list([int(_code) for _code in df.iloc[:, 3]] )
       # combine(codes, volumes, start_date, end_date, portfolio)           


def main():
    config = BacktestConfig()
    print(config.codes)


if __name__ == '__main__':
    main()
