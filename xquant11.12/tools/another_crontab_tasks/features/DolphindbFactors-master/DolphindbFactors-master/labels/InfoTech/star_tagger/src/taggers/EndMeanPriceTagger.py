import datetime
import numpy as np
import pandas as pd


from .base_tagger import BaseTagger

class EndMeanPriceTagger(BaseTagger):
    def __init__(self, config):
        super().__init__(config)
        self.config = config
        self.config.label_name = self._init_label_name(config)

    def _init_label_name(self, config):
        label_name = "labelEQ{}calctypeEQ{}pricetypeEQ{}rsizeEQ{}dsizeEQ{}".format(
            config.base_name,
            config.calc_type,
            config.price_type,
            config.r_size,
            config.d_size,
        )
        return label_name

    def calculate(self, df):
        df.sort_index(inplace=True)
        base_px, iter_px = self._get_type(df, self.config.price_type)
        instances_len = len(base_px)
        tick_index_list = df.index
        rest = pd.DataFrame(index=df.index, columns=[self.config.label_name])
        for i in range(0, instances_len, self.config.step_increment):
            cur_px = base_px.iloc[i]
            if cur_px<0.001:
                continue
            start_j = tick_index_list[i]
            end_j = start_j+datetime.timedelta(seconds=self.config.d_size)
            if not self._is_valid_end(end_j):
                continue
            slice_tick_df = iter_px[(iter_px.index>=(end_j-datetime.timedelta(seconds=self.config.r_size)))&(iter_px.index<=end_j)]
            if slice_tick_df.empty:
                continue
            mean_price = np.nanmean(slice_tick_df)
            if np.isnan(mean_price):
                continue
            if self.config.calc_type=="pct":
                amp = (mean_price-cur_px)/cur_px
            elif self.config.calc_type=="abs":
                amp = mean_price - cur_px
            rest.iloc[i][self.config.label_name] = self.config.label_coeff * amp
        return rest
