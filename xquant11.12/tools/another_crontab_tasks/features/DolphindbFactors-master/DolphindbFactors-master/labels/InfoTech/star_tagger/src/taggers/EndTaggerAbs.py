import datetime
import numpy as np
import pandas as pd


from .base_tagger import BaseTagger

class EndTaggerAbs(BaseTagger):
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

    def _calculate_tag(self, cur_px, seq):
        """
        :param cur_px: the last px we can see.
        :param seq: the px in prediction duration.
        """
        # amp = (seq[-1] - cur_px)/cur_px
        amp = seq[-1] - cur_px
        return amp

    def calculate(self, df):
        base_px, iter_px = self._get_type(df, self.config.type_method)
        instances_len = len(base_px)
        rest = pd.DataFrame(index=df.index, columns=[self.config.label_name])
        index_list = df.index
        for i in range(0, instances_len, self.config.step_increment):
            # if i==instances_len-1: break
            for j in range(i+1, instances_len, 1):
                if index_list[j] - index_list[i]> datetime.timedelta(seconds=self.config.d_size):
                    cur_px = base_px[i]
                    seq_start, seq_end = i+1, j
                    if i+1 == j:
                        break
                    amp = self._calculate_tag(cur_px, iter_px[seq_start: seq_end])

                    label = amp
                    rest.iloc[i][self.config.label_name] = label
                    break
        return rest
        