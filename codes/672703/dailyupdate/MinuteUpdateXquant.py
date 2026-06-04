import os
import pandas as pd
import numpy as np
import scipy.io as sio
from copy import deepcopy
import time
import datetime
import sys
import warnings
warnings.filterwarnings("ignore")
from xquant.marketdata import MarketData
from xquant.factordata import FactorData
mdp = MarketData(dfs=None)


class MinuteUpdateXquant(object):
    """
    update minute data from xquant
    """
    def __init__(self,
                 date_list=None,
                 minute_store_path='/data/group/800020/AlphaDataCenter/Basic/minute/',
                 universe_path='/data/group/800020/AlphaDataCenter/PoolManagement/'
                 ):

        self.date_list = date_list
        self.minute_store_path = minute_store_path
        self.universe_path = universe_path        
        universe = sio.loadmat(self.universe_path + 'universe.mat')['universe']
        self.stock_list = sorted([x[0][0] for x in universe])

        self.standard_minutes = np.load(self.universe_path + 'standard_minutes.npy')

        self.field_map = {'open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume','amount':'Amount'}


    def to_timestamp(self, df_date, df_time):
        td1 = pd.to_datetime(df_date.values, format='%Y%m%d')
        td2 = pd.to_datetime(df_time.values, format='%H%M%S%f')
        td = pd.DataFrame({'year': td1.year, 'month': td1.month, 'day': td1.day, 'hour': td2.hour, 'minute': td2.minute,
                       'second': td2.second, 'microsecond': td2.microsecond})
        return td
    
    def generate_dummy_minute_data(self, date, standard_minutes):
        td1 = pd.to_datetime(date, format='%Y%m%d')
        td2 = pd.to_datetime(standard_minutes, format='%H%M%S%f')
        td = pd.DataFrame({'year': td1.year, 'month': td1.month, 'day': td1.day, 'hour': td2.hour, 'minute': td2.minute,
                       'second': td2.second, 'microsecond': td2.microsecond})
        res =  pd.DataFrame(index=pd.DatetimeIndex(pd.to_datetime(td)), columns=['open', 'high', 'low', 'close','volume', 'amount'])

        return res

    def CleanMinuteData(self, stock, date, standard_minutes):

        minute_data = mdp.get_data_by_date("Kline1M4ZT",stock, date)

        if len(minute_data) == 0:
            new_minute_data = self.generate_dummy_minute_data(date, standard_minutes)
            return 1, new_minute_data, None    
    
        minute_data = minute_data[['MDDate', 'MDTime', 'OpenPx', 'ClosePx', 'HighPx', 'LowPx', 'TotalVolumeTrade', 'TotalValueTrade']]
        minute_data.columns = ['MDDate', 'MDTime', 'open','close','high','low','volume','amount']
    
        minute_data.index = pd.to_datetime(self.to_timestamp(minute_data['MDDate'], minute_data['MDTime']))

        if len(minute_data[str(date) + ' 09:25:00':str(date) + ' 09:25:00']) == 0:
            print('Call Auction Not Exsited : ', stock, date)
            call_auction = None
        else:
            call_auction = minute_data.loc[str(date) + ' 09:25:00']
    
        # 当日出现全是nan， 大概率停牌了
        if len(minute_data.dropna()) == 0:
            new_minute_data = self.generate_dummy_minute_data(date, standard_minutes)
            return 2, new_minute_data, call_auction

        # nan价格向下填充， 量额填0
        minute_data[['open','high','low','close']] = minute_data[['open','high','low','close']].fillna(method = 'ffill')
        minute_data[['volume','amount']] = minute_data[['volume','amount']].fillna(0)
        minute_data[['open','high','low','close']] = minute_data[['open','high','low','close']].fillna(method = 'bfill')

        morning = minute_data.between_time(start_time='9:30:00', end_time='11:30:00')
        afternoon = minute_data.between_time(start_time='13:00:00', end_time='15:00:00')
    
        # 上午数据不足120个的情况（不应该出现）
        if len(morning.dropna()) != 120:
            print(stock, date, 'morning missing' , stock, date)
            new_minute_data = self.generate_dummy_minute_data(date, standard_minutes)
            return 3, new_minute_data, call_auction
    
        # 下午数据不足121个的情况（不应该出现）
        if len(afternoon.dropna()) != 121:
            print(stock, date, 'afternoon missing', stock, date)
            new_minute_data = self.generate_dummy_minute_data(date, standard_minutes)
            return 4, new_minute_data, call_auction

        # 将15:00的信息返回到14:59上
        volume_end = afternoon[str(date) + ' 14:59:00':str(date) + ' 15:00:00']['volume'].sum()
        amount_end = afternoon[str(date) + ' 14:59:00':str(date) + ' 15:00:00']['amount'].sum()
        price_end = afternoon.loc[str(date) + ' 15:00:00'][['open','high','low','close']].values.tolist()
        minute1459 = pd.DataFrame(index = [pd.to_datetime(str(date) + ' 14:59:00')], columns=['open','high','low','close','volume','amount'], 
                                data = [price_end +[volume_end, amount_end]])    
        afternoon = pd.concat([afternoon[:str(date) + ' 14:58:00'], minute1459]) 

        new_minute_data = pd.concat([morning, afternoon])

        # 全天成交量为0 没有交易
        if (morning['volume'].sum() == 0) & (afternoon['volume'].sum() == 0):
            print('no trade ', stock, date)
            new_minute_data = self.generate_dummy_minute_data(date, standard_minutes)
            return 5, new_minute_data, call_auction

        # 上午成交量为0 上午停牌
        if morning['volume'].sum() == 0:
            print('morning suspension', stock, date)
            return 6, new_minute_data, call_auction
   
        # 下午成交量为0 下午停牌
        if afternoon['volume'].sum() == 0:
            print('afternoon suspension', stock, date)
            return 7, new_minute_data, call_auction
    
        return 0, new_minute_data, call_auction


    def update_one_date(self, date):

        # if os.path.exists(self.minute_store_path + 'Minute_Status.pkl'):
            # history = pd.read_pickle(self.minute_store_path + 'Minute_Status.pkl')
            # if date in history.index:
                # print('Date already exsited', date)
                # return
        
        result_dict = {}
        status_dict = {}
        call_auction_dict = {}

        t = time.time()

        for stock in self.stock_list:
            flag, minute, call_auction = self.CleanMinuteData(stock, date, self.standard_minutes)
            status_dict[stock] = flag
            result_dict[stock] = minute
            call_auction_dict[stock] = call_auction

        # Start Saving .. 
        all_minute_today = pd.concat(result_dict)

        for var, save_var in self.field_map.items():
            all_minute_today[var].unstack().transpose().to_pickle(self.minute_store_path + save_var + '/' + date + '.pkl')

        #CallAuction = pd.concat(call_auction_dict,axis=1)
        #CallAuction.to_pickle('CallAuction/' + date + '.pkl')

        status_today = pd.Series(status_dict, name=pd.to_datetime(date))
        status_today = status_today.to_frame().transpose()

        if not os.path.exists(self.minute_store_path + 'Minute_Status.pkl'):
            status_today.to_pickle(self.minute_store_path + 'Minute_Status.pkl')
        else:
            history = pd.read_pickle(self.minute_store_path + 'Minute_Status.pkl')
            if date in history.index:
                history = history[history.index!=date]
                print('Minute_Status Updated Again Today.')
            new = pd.concat([history, status_today])
            new = new.sort_index()
            new.to_pickle(self.minute_store_path + 'Minute_Status.pkl')

        print('*********** Minute Data Finish Cleaning, used ', time.time()-t, date)


    def update_data(self):
        if self.date_list is None:
            print(' no trade date to update minute data ')
            return
        else:
            if isinstance(self.date_list, str):
                self.update_one_date(self.date_list)
            else:
                for date in self.date_list:
                    self.update_one_date(date)


if __name__ == '__main__':

    #start_date = '20191104'
    #end_date = '20191114'
    #date_list = FactorData().tradingday(start_date, end_date)

    #today = datetime.datetime.today().strftime('%Y%m%d')
    
    date_list = ['20200102'] 
    # instance = MinuteUpdateXquant(date_list)
    # instance.update_data()