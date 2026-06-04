import os
import pandas as pd
from xquant.pyfile.ftp import pyfileFTP


class CVConfig:
    def __init__(self):
        print("------Instantiating CV Config Starts------")

        self.portfolio = "big"

        # 日期
        self.today_str = "20190731"
        self.next_trading_day_str = "20190801"
        self.test_start_date_str = "2019-05-20"
        self.test_end_date_str = "2019-07-26"

        # 路径
        self.signalPath = "cv_signals/big_universe/20190101_48/"
        self.absolutePath = "/data/user/666888/ModelProduction/big_universe/"
        self.factorAddress = "/data/user/666888/AppleData48/"

        self.factorNames = [
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
        self.tagNames = [["1minLong", "1minShort"], ["2minLong", "2minShort"], ["5minLong", "5minShort"]]

        self._load_portfolio_from_ftp()

        print("------Instantiating CV Config Over------")

    def _load_portfolio_from_ftp(self):
        ftp = pyfileFTP()

        file_name = "{}_{}.xlsx".format(self.next_trading_day_str, self.portfolio)
        if os.path.exists("/data/user/666888/ftp_uploads_cv/"):
            path = "/data/user/666888/ftp_uploads_cv/" + file_name
            if os.path.exists(path):
                pass
            else:
                ftp.downloadFile("666888/{}/{}".format(self.next_trading_day_str, file_name), path)
        else:
            raise Exception("No ftp_uploads_cv directory!")

        print("The portfolio loading path is", path)

        portfolio_df = pd.read_excel(path)
        trade_codes = list([_code for _code in portfolio_df.iloc[:, 0]])
        self.codes = list(set(trade_codes))


def main():
    config = CVConfig()
    print(config.codes)


if __name__ == '__main__':
    main()
