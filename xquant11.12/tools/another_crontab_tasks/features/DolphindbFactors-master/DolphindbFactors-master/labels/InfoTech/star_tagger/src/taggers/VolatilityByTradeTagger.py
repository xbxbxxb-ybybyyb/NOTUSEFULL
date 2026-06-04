import datetime
import numpy as np
import pandas as pd


from .base_tagger import BaseTagger

class VolatilityByTradeTagger(BaseTagger):
    def __init__(self, config):
        super().__init__(config)
        self.config = config
        self.config.label_name = self._init_label_name(config)
    
    def _init_label_name(self, config):
        label_name = "labelEQ{}typeEQ{}dsizeEQ{}".format(
            config.base_name,
            config.type_method,
            config.d_size
        )
        return label_name

    def _calculate_tag(self, slice_trade_df):
        """
        :param cur_px: the last px we can see.
        :param seq: the px in prediction duration.
        """
        # 可能会出现缺失的情况
        if self.config.price_method=="max":
            slice_df_price = slice_trade_df.TradePrice.apply(max)
        elif self.config.price_method=="mean":
            slice_df_price = slice_trade_df.TradePrice.apply(np.mean)
        elif self.config.price_method=="vwap":
            slice_df_price = slice_trade_df.TradeMoney.apply(sum)/slice_trade_df.TradeQty.apply(sum)
        elif self.config.price_method=="qtyweight":
            ## TO DO
            pass
        if self.config.std_object=="return":
            ret = slice_df_price.shift(-1)/slice_df_price-1
        elif self.config.std_object=="price":
            ret = slice_df_price
        ret.replace([np.inf,-np.inf], np.nan, inplace=True)
        try:
            ret_std = 0 if ret.isnull().all() else np.nanstd(ret)
            # if ret_std>100/1e3:
            #     print(ret_std)
        except:
            print("error", ret, ret.isnull().all())
        return ret_std


    def calculate(self, tick_df, trade_df):
        # base_px, iter_px = self._get_type(df, self.config.type_method)
        instances_len = len(tick_df)
        rest = pd.DataFrame(index=tick_df.index, columns=[self.config.label_name])
        tick_index_list = tick_df.index
        # trade_index_list = trade_df.index
        for i in range(0, instances_len, self.config.step_increment):
            start_j = tick_index_list[i]
            end_j = start_j+datetime.timedelta(seconds=self.config.d_size)
            slice_trade_df = trade_df[(trade_df.index>=start_j)&(trade_df.index<=end_j)]
            amp = self._calculate_tag(slice_trade_df)

            label = self.config.label_coeff*amp
            rest.iloc[i][self.config.label_name] = label
        return rest



        