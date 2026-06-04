import datetime
import numpy as np

class BaseTagger():
    def __init__(self, config):
        self.config = config

    def _calculate_tag(self, cur, seq):
        pass

    def _is_valid_end(self, now_time):
        # now_time = df.index[0]
        am_start_time =  datetime.datetime(now_time.year, now_time.month, now_time.day, 9, 30)
        am_end_time =  datetime.datetime(now_time.year, now_time.month, now_time.day, 11, 30)
        pm_start_time =  datetime.datetime(now_time.year, now_time.month, now_time.day, 13, 00)
        pm_end_time =  datetime.datetime(now_time.year, now_time.month, now_time.day, 14, 57)
        condition = ((now_time >= am_start_time) & (now_time<am_end_time)) | ((now_time >= pm_start_time) & (now_time<pm_end_time))
        return condition

    def _get_type(self, df, price_type):
        df.sort_index(inplace=True)
        if price_type=="midprice":
            mid_price = df.apply(lambda x: np.nanmean([x.Sell1Price, x.Buy1Price]), axis=1).sort_index()
            base_price = mid_price
            target_price = mid_price
            return base_price, target_price
        elif price_type=="vwap":
            volume = df["TotalVolumeTrade"].diff(1)
            value = df["TotalValueTrade"].diff(1)
            vwap_price = value/volume
            vwap_price.fillna(0, inplace=True)
            return vwap_price, vwap_price
        elif price_type=="lastpx":
            base_price = df["LastPx"]
            target_price = df["LastPx"]
            return base_price, target_price
        elif price_type=="sbprice":
            base_price = df["Sell1Price"]
            target_price = df["Buy1Price"]
            return base_price, target_price
        elif price_type=="bsprice":
            base_price = df["Buy1Price"]
            target_price = df["Sell1Price"]
            return base_price, target_price
    def run(self, df):
        pass