import datetime
import numpy as np
import pandas as pd


from .base_tagger import BaseTagger

class MultiTagger(BaseTagger):
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

    # def _judge_boundary(self, amp, up_th, down_th):
    #     """
    #     """
    #     if amp*self.config.label_coeff > up_th:
    #         return 1
    #     if amp*self.config.label_coeff < down_th:
    #         return -1
    #     return 0

    # def _calculate_tag(self, seq):
    #     """
    #     :param cur_px: the last px we can see.
    #     :param seq: the px in prediction duration.
    #     """
    #     amp1 = 0
    #     amp2 = 0
    #     tmpamp = 0
    #     for i in range(len(seq)):
    #         amp1 = seq[i]
    #         if self._judge_boundary(amp1, self.up_th, self.down_th)==1:
    #             if tmpamp>=0:
    #                 tmpamp = max(tmpamp, amp1)
    #             else:
    #                 return tmpamp
    #         elif self._judge_boundary(amp1, self.up_th, self.down_th)==-1:
    #             if tmpamp<=0:
    #                 tmpamp = min(tmpamp, amp1)
    #             else:
    #                 return tmpamp
    #     return tmpamp
    
    # def calculate_volatility(self, df):
    #     volatility = (self.config.label_coeff *
    #                   np.log(df[self.config.volatility_px] /
    #                          df[self.config.volatility_px].shift(self.config.num_diff_tick))
    #                   ).ewm(span=self.config.label_triple_barrier_span).std()
    #     return volatility

    # def _calculate_end_tag(self, seq):

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
            # # # label1
            # self.up_th = self.config.label_triple_barrier_alpha*volatility[i]
            # self.down_th = -self.config.label_triple_barrier_alpha*volatility[i]
            # tri_amp = self._calculate_tag((slice_tick_df-cur_px)/cur_px)
            # tri_amp *= self.config.label_coeff
            # # label2 
            # # end_amp = (slice_tick_df[-1]-cur_px)/cur_px
            # # end_amp *= self.config.label_coeff
            
            # label3
            std_amp = np.nanstd(slice_tick_df.pct_change(1))
            rest.iloc[i][self.config.label_name] = std_amp

        return rest
