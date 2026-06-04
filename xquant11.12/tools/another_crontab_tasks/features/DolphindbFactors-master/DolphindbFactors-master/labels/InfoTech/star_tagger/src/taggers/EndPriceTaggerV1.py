import datetime
import numpy as np
import pandas as pd


from .base_tagger import BaseTagger

class EndPriceTagger(BaseTagger):
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

    def _calculate_tag(self, seq):
        """
        :param cur_px: the last px we can see.
        :param seq: the px in prediction duration.
        """
        amp = seq[-1]
        return amp

    def calculate(self, df):
        base_px, iter_px = self._get_type(df, self.config.type_method)
        instances_len = len(base_px)
        rest = pd.DataFrame(index=df.index, columns=[self.config.label_name])
        tick_index_list = df.index
        for i in range(0, instances_len, self.config.step_increment):
            start_j = tick_index_list[i]
            end_j = start_j+datetime.timedelta(seconds=self.config.d_size)
            slice_tick_df = base_px[(base_px.index>=start_j)&(base_px.index<=end_j)]
            if slice_tick_df.empty:
                continue
            amp = self._calculate_tag(slice_tick_df)
            label = amp
            rest.iloc[i][self.config.label_name] = label
        return rest
        