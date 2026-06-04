import os
import datetime
import pandas as pd
from xquant.xqutils.xqfile import FTPFile
from CONFIG import MODEL_NAME, MODEL_PATH
from CONFIG import FTP_UPLOAD_BT, FTP_PORTFOLIO_PATH


class BacktestConfig:
    def __init__(self, trade_portfolio="800", today=None, stock_pool=[]):
        if isinstance(trade_portfolio, str):
            self.trade_portfolio = [trade_portfolio]
        elif isinstance(trade_portfolio, list):
            self.trade_portfolio = trade_portfolio

        self.stock_pool = stock_pool
        self.today = today
        if self.today is None:
            self.today = datetime.datetime.now() - datetime.timedelta(days=3)
        else:
            self.today = datetime.datetime.strptime(self.today, "%Y%m%d")
        self._create_time()

        self._load_portfolio_from_ftp()

        self.model_name = MODEL_NAME
        self.model_path = MODEL_PATH
        self.signal_path = "Model" + self.model_name + "/"
        self.factor_pickle_output_dir = ""

        print("Trade Portfolio: {}".format(self.trade_portfolio))
        print("Pre Date: {}, Trading Date: {}".format(self.start_date, self.end_date))

    def _create_time(self):
        self.today_str = self.today.strftime('%Y%m%d')
        if self.today.weekday() == 0:
            pre_days = 3
        else:
            pre_days = 1
        pre_date = self.today - datetime.timedelta(days=pre_days)
        self.start_date = "{}{}".format(pre_date.strftime("%Y%m%d"), "093015")
        self.end_date = "{}{}".format(self.today.strftime("%Y%m%d"), "145659")

    def _load_portfolio_from_ftp(self):
        ftp = FTPFile()
        all_stocks = set(self.stock_pool)
        for portfolio in self.trade_portfolio:
            file_name = "{}_{}.xlsx".format(self.today_str, portfolio)
            if os.path.exists(FTP_UPLOAD_BT):
                path = FTP_UPLOAD_BT + file_name
                if os.path.exists(path):
                    pass
                else:
                    ftp.downloadFile(FTP_PORTFOLIO_PATH + file_name, path)
            else:
                raise Exception("No Local Ftp Download Directory!")

            print("Local Portfolio Path: ", path)
            df = pd.read_excel(path)
            trade_codes = [code for code in df.iloc[:, 0]]

            ### 和给定股票池取并集
            all_stocks = all_stocks.union(trade_codes)

        self.codes = list(all_stocks)
        print(self.codes)


if __name__ == '__main__':
    today = "20200226"
    config = BacktestConfig("big", today)
    print(config.codes)
