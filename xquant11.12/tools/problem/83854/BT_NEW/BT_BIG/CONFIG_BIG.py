import os
import datetime
import pandas as pd
from xquant.pyfile.ftp import pyfileFTP


order_capacity_path = "/data/user/666888/OrderCapacity/"
trade_path = "/data/user/666888/TradeData/"
root_path = "/data/user/666888/BT_Trade_OrderCapacity/"


class BacktestConfig:
    def __init__(self):
        print("------Instantiating BT Config Starts------")
        self.trade_portfolio = ["big"]
        self.today = datetime.datetime.now() - datetime.timedelta(days=4)
        self._create_time()
        self._load_portfolio_from_ftp()

        self.factor_config = "AlgoFactor48.py"
        self.factor_name = [
            "factorMAVolumeDistance10_20", "factorTransBuyVolumeDistance5_40", "factorDistanceToHigh100",
            "factorDistanceBetweenVWAPPrice40", "factorTransVolumeWeightedSwing5_10", "factorDistanceToLow40",
            "factorBuyPower", "factorTransSellVolumeDistance5_10", "factorDistanceToLow100",
            "factorDistanceBetweenVWAPPrice200", "factorSellPower", "factorCrossPriceChangeRatio", "factorMomentum",
            "factorEmaOrderVolumePressure", "factorTransPressureVol", "factorDistanceBetweenVWAPPrice100",
            "factorTransPressure", "factorOrderMomentum", "factorSpeed", "factorDistanceToVwap100",
            "factorMAVolumeDistance20", "factorTransSellBuy5", "factorMAVolumeDistance10_100", "factorDistanceToVwap20",
            "factorBuyPowerSpeed", "factorSellPowerSpeed", "factorDistanceToAvePrice",  "factorDistanceToVwap40",
            "factorMAVolumeDistance3", "factorVolumeMagnification", "factorTransVolumeWeightedSwing5_40",
            "factorMAVolumeDistance40_80", "factorOrderPressure", "factorMAVolumeDistance100_200",
            "factorDistanceToVwapPriceWeighted", "factorDistanceBetweenVWAPPrice20", "factorMAVolumeDistance100",
            "factorEmaOrderAmountPressure", "factorMAVolumeDistance40", "factorCrossPriceChangeSpeed",
            "factorTransSellBuy10", "factorTransBuyVolumeDistance5_10", "factorMAVolumeDistance20_40",
            "factorTransSellVolumeDistance5_40", "factorMAVolumeDistance10_40", "factorMAVolumeDistance200",
            "factorDistanceToHigh40", "factorBoll"
        ]
        self.tag_name = [["1minLong", "1minShort"], ["2minLong", "2minShort"], ["5minLong", "5minShort"]]

        self.model_name = "big_universe"
        self.model_path = "/data/user/666888/ModelProduction/" + self.model_name + "/"
        self.signal_path = "output/" + self.model_name + "/"
        self.factor_pickle_output_dir = 'output/trade_review_factor_pickle/'

        print("Trade portfolio is {}".format(self.trade_portfolio))
        print("Pre date (We use tick data of pre date to calc factor) is {} and trading date is {}"
              .format(self.StartDateTime, self.EndDateTime))
        print("------Instantiating BT Config Over------")

    def _create_time(self):
        self.today_str = self.today.strftime('%Y%m%d')

        if self.today.weekday() == 0:
            predays = 3
        else:
            predays = 1
        pre_date = self.today - datetime.timedelta(days=predays)
        self.StartDateTime = "{}{}".format(pre_date.strftime("%Y%m%d"), "093015")
        self.EndDateTime = "{}{}".format(self.today.strftime("%Y%m%d"), "145659")

    def _load_portfolio_from_ftp(self):
        ftp = pyfileFTP()

        all_stocks = set()
        for portfolio in self.trade_portfolio:
            file_name = "{}_{}.xlsx".format(self.today_str, portfolio)
            if os.path.exists("/data/user/013150/ftp_uploads_bt/"):
                path = "/data/user/013150/ftp_uploads_bt/" + file_name
                if os.path.exists(path):
                    pass
                else:
                    ftp.downloadFile("013150/" + file_name, path)
            else:
                raise Exception("No ftp_uploads_bt directory!")

            print("The portfolio loading path is", path)
            df = pd.read_excel(path)
            trade_codes = list([_code for _code in df.iloc[:, 0]])
            all_stocks = all_stocks.union(set(trade_codes))

        self.codes = list(all_stocks)


def main():
    config = BacktestConfig()
    print(config.codes)


if __name__ == '__main__':
    main()
