import datetime
from xquant.pyfile.ftp import pyfileFTP
import pandas as pd
import os
import CalcFactor.stock_pools as stock_pool 



from CalcFactor.xiufu_stocks import *

i = 5
if i==1:
    xiufu = xiufu_1
if i==2:
    xiufu = xiufu_2
if i==3:
    xiufu = xiufu_3
if i==4:
    xiufu = xiufu_4
if i==5:
    xiufu = xiufu_5

    

    
#i=100
class CalcConfig:
    def __init__(self):
        print("------Instantiating Calc Config------")
        self.factor_pickle_output_dir = 'output/calc_factor_2017_{}/'.format(str(i))

        # self.StartDateTime = 20170101093015
        # self.EndDateTime =   20190312145659
        self.StartDateTime = 20190524093015
        self.EndDateTime =   20190531145659 
        # self.StartDateTime = 20190101093015
        # self.EndDateTime =   20190404145659         
        self.codes = stock_pool.all_stocks
        # self.codes = ["601598.SH"]                
        # self.StartDateTime = xiufu["start_time"]
        # # self.EndDateTime =  xiufu["end_time"]       
        
        
        self.factor_config = "AlgoFactor48.py"
        
        self.factor_name =  ["factorMAVolumeDistance10_20", "factorTransBuyVolumeDistance5_40", "factorDistanceToHigh100", 
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
        
        # self.model_path = "/data/user/ModelProduction/2018-10-01/"
        
        self.factor_address = "/data/user/AppleData48"
        # self.codes = stock_pool.extend_stocks
        # self.codes = xiufu["stocks"] # [stock[0] for stock in xiufu["stocks"]] 


        # self.codes.remove("603977.SH")
        #self.signal_path =           "output/2018-10-01/"

        # self.codes = stock_pool.extend_stocks
        

def main():
    config = CalcConfig()

if __name__ == '__main__':
    main()
