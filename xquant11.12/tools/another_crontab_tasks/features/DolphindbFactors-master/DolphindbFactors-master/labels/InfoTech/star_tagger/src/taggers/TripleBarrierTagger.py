import datetime
import numpy as np
import pandas as pd


from .base_tagger import BaseTagger

class TripleBarrierTagger(BaseTagger):
    def __init__(self, config):
        super().__init__(config)
        self.config = config
        self.config.label_name = self._init_label_name(config)

    def _init_label_name(self, config):
        label_name = "labelEQ{}typeEQ{}dsizeEQ{}alphaEQ{}".format(
            config.base_name,
            config.type_method,
            config.d_size,
            config.label_triple_barrier_alpha
        )
        # label_name = "labelEQ{}typeEQ{}dsizeEQ{}".format(
        #     config.base_name,
        #     config.type_method,
        #     config.d_size
        # )
        return label_name

    def _judge_boundary(self, amp, up_th, down_th):
        """
        """
        up_ = amp*self.config.label_coeff > up_th
        down_ = amp*self.config.label_coeff < down_th
        return up_ or down_

    def _calculate_tag(self, cur_px, seq):
        """
        :param cur_px: the last px we can see.
        :param seq: the px in prediction duration.
        """
        amp = 0
        for i in range(len(seq)):
            amp = (seq[i]-cur_px)/cur_px
            if self._judge_boundary(amp, self.up_th, self.down_th):
                return amp
        return amp
    
    def calculate_volatility(self, df):
        volatility = (self.config.label_coeff *
                      np.log(df[self.config.volatility_px] /
                             df[self.config.volatility_px].shift(self.config.num_diff_tick))
                      ).ewm(span=self.config.label_triple_barrier_span).std()
        return volatility


    def calculate(self, df):
        df["midprice"] = (df["Buy1Price"]+df["Sell1Price"])/2.0
        base_px, iter_px = self._get_type(df, self.config.type_method)
        instances_len = len(base_px)
        index_list = df.index
        rest = pd.DataFrame(index=df.index, columns=[self.config.label_name])
        volatility = self.calculate_volatility(df)
        for i in range(0, instances_len, self.config.step_increment):
            for j in range(i+1, instances_len, 1):
                if index_list[j] - index_list[i]>= datetime.timedelta(seconds=self.config.d_size):
                    cur_px = base_px[i]
                    seq_start, seq_end = i+1, j
                    if i+1 == j:
                        break
                    self.up_th = self.config.label_triple_barrier_alpha*volatility[i]
                    self.down_th = -self.config.label_triple_barrier_alpha*volatility[i]
                    amp = self._calculate_tag(cur_px, iter_px[seq_start:seq_end])

                    # 根据任务类型构建label
                    label = self.config.label_coeff*amp
                    rest.iloc[i][self.config.label_name] = label
                    break
        return rest
        # return df['midprice']
