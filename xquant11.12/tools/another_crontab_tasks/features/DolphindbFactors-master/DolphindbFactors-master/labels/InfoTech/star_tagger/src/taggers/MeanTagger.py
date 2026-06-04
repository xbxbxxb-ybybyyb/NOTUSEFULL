import datetime
import numpy as np
import pandas as pd


from .base_tagger import BaseTagger

class MeanTagger(BaseTagger):
    def __init__(self, config):
        super().__init__(config)
        self.config = config
        self.config.label_name = self._init_label_name(config)

    def _init_label_name(self, config):
        label_name = "labelEQ{}typeEQ{}dsizeEQ{}".format(
            config.base_name,
            config.type_method,
            config.d_size,
        )
        return label_name

    def calculate(self, df):
        df.sort_index(inplace=True)
        df["midprice"] = df.apply(lambda x: np.nanmean([x.Sell1Price, x.Buy1Price]), axis=1).sort_index()
        base_px, iter_px = self._get_type(df, self.config.type_method)
        instances_len = len(base_px)
        tick_index_list = df.index
        rest = pd.DataFrame(index=df.index, columns=[self.config.label_name])
        # volatility = self.calculate_volatility(df)
        for i in range(0, instances_len, self.config.step_increment):
            cur_px = base_px[i]
            if cur_px<0.001:
                continue
            start_j = tick_index_list[i]
            end_j = start_j+datetime.timedelta(seconds=self.config.d_size)
            slice_tick_df = base_px[(base_px.index>=start_j)&(base_px.index<=end_j)]
            
            # label3
            mean_price = np.nanmean(slice_tick_df)
            if np.isnan(mean_price):
                continue
            amp = (mean_price-cur_px)/cur_px
            rest.iloc[i][self.config.label_name] = self.config.label_coeff * amp

        return rest
