import datetime
from xquant.pyfile.ftp import pyfileFTP
import pandas as pd
import os
import BT.stock_pools as stock_pool 


order_capacity_path = "/app/data/666888/OrderCapacity/"
trade_path = "/app/data/666888/TradeData/"
root_path = "/app/data/666888/BT_Trade_OrderCapacity/"   



class BacktestConfig:
    def __init__(self):
        print("------Instantiating BT Config------")
        self.factor_pickle_output_dir = 'output/trade_review_factor_pickle/'
        self.trade_portfolio =  ["5161101+800arb"]
        self.today = datetime.datetime.now()     - datetime.timedelta(days=1)
        self._create_time()
        self.factor_config = "AlgoFactorConfig.py"
        
        self.factor_name = ['factorMAVolumeDistance40', 'factorDistanceBetweenVWAPPrice200', 'factorEmaSlicePressure', 
                      'factorTransPressureVol', 'factorDistanceToAvePrice', 'factorDistanceBetweenVWAPPrice100',
                      'factorOrderPressure', 'factorDistanceBetweenVWAPPrice40', 'factorDistanceBetweenVWAPPrice20', 
                      'factorMAVolumeDistance200', 'factorCrossPriceChangeSpeed', 'factorCrossPriceChangeRatio', 
                      'factorTransPressure', 'factorVolumeMagnification', 'factorMAVolumeDistance100', 'factorAccumSellPower', 
                      'factorAccumBuyPower', 'factorSpeed', 'factorMAVolumeDistance3', 'factorMAVolumeDistance20']
        self.tag_name = [["1minLong", "1minShort"], ["2minLong", "2minShort"], ["5minLong", "5minShort"]]
        
        self.model_path = "/data/user/ModelProduction/2018-10-01/"
        
        self.factor_address = "/data/user/AppleData"
        self._load_portlio_from_ftp()
        
        print("  Trade Portfolio is {}".format(self.trade_portfolio))
        print("  Pre date (We use tick data of pre date to cala factor) is {} and trading date is {}".format(self.StartDateTime, self.EndDateTime))
        
        
        
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
        zz800_codes = stock_pool.zz_800
        all_stocks = set(zz800_codes)
        
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
            trade_codes = list([_code for _code in df.iloc[:, 0]] )


            all_stocks = all_stocks.union(set(trade_codes))
        self.codes = list(all_stocks)
        self.codes.remove("000725.SZ") 
        self.codes = self.codes[1:30] 
       # self.volumes = list([int(_code) for _code in df.iloc[:, 3]] )
       # combine(codes, volumes, start_date, end_date, portfolio)           
    

def main():
    config = BacktestConfig()

if __name__ == '__main__':
    main()
