import datetime
import numpy as np
import pandas as pd

from .base_tagger import BaseTagger

class EndPctTagger(BaseTagger):
    def __init__(self, config):
        super().__init__(config)
        self.config = config
        self.config.label_name = self._init_label_name(config)
    
    def _init_label_name(self, config):
        label_name = "labelEQ{}pricetypeEQ{}dsizeEQ{}".format(
            config.base_name,
            config.price_type,
            config.d_size
        )
        return label_name

    def calculate(self, df):
        base_px, iter_px = self._get_type(df, self.config.price_type)
        instances_len = len(base_px)
        rest = pd.DataFrame(index=df.index, columns=[self.config.label_name])
        tick_index_list = df.index
        for i in range(0, instances_len, self.config.step_increment):
            cur_px = base_px.iloc[i]
            if cur_px<0.001:
                continue
            start_j = tick_index_list[i]
            end_j = start_j+datetime.timedelta(seconds=self.config.d_size)
            if not self._is_valid_end(end_j):
                continue
            slice_tick_df = iter_px[(iter_px.index>=start_j)&(iter_px.index<=end_j)]
            if slice_tick_df.empty:
                continue
            tar_px = slice_tick_df[-1]
            if self.config.calc_type=="pct":
                amp = (tar_px-cur_px)/cur_px
            elif self.config.calc_type=="abs":
                amp = tar_px - cur_px
            rest.iloc[i][self.config.label_name] = self.config.label_coeff * amp
        return rest
        