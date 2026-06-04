from generate_parquet_utils import main_generate_parquet_l3, main_generate_parquet_l2p, start_generate_and_evaluate_signal
import ray

if __name__ == '__main__':
    start_date = "20240801"
    end_date = "20240812"
    exp_list = [
        # ("LabelLongOneMin", "exp_l3_zzkc_flying4", 'LabelLongOneMin_factor98_amp_sample'),
        # ("LabelShortOneMin", "exp_l3_zzkc_flying4", 'LabelShortOneMin_factor98_amp_sample'),
        # ("LabelLongOneMin", "exp_l3_zzkc_flying4", 'LabelLongOneMin_factor98_sample'),
        # ("LabelShortOneMin", "exp_l3_zzkc_flying4", 'LabelShortOneMin_factor98_sample'),
        # ("LabelLongTwoMin", "exp_l3_zzkc_flying4", 'LabelLongTwoMin_factor98_amp_sample'),
        # ("LabelShortTwoMin", "exp_l3_zzkc_flying4", 'LabelShortTwoMin_factor98_amp_sample'),
        # ("LabelLongTwoMin", "exp_l3_zzkc_flying4", 'LabelLongTwoMin_factor98_sample'),
        # ("LabelShortTwoMin", "exp_l3_zzkc_flying4", 'LabelShortTwoMin_factor98_sample'),
        # ###未采样训练
        # ("LabelLongOneMin", "exp_l3_zzkc_flying4", 'LabelLongOneMin_factor98_amp'),
        # ("LabelShortOneMin", "exp_l3_zzkc_flying4", 'LabelShortOneMin_factor98_amp'),
        # ("LabelLongOneMin", "exp_l3_zzkc_flying4", 'LabelLongOneMin_factor98'),
        # ("LabelShortOneMin", "exp_l3_zzkc_flying4", 'LabelShortOneMin_factor98'),
        # ("LabelLongTwoMin", "exp_l3_zzkc_flying4", 'LabelLongTwoMin_factor98_amp'),
        # ("LabelShortTwoMin", "exp_l3_zzkc_flying4", 'LabelShortTwoMin_factor98_amp'),
        # ("LabelLongTwoMin", "exp_l3_zzkc_flying4", 'LabelLongTwoMin_factor98'),
        # ("LabelShortTwoMin", "exp_l3_zzkc_flying4", 'LabelShortTwoMin_factor98'),
        #######################20240622###################
        # # 和l3训练脚本相似，仅去掉了open_flying过滤数据, 但是flying_factor仍然作为特征输入
        # ("LabelLongOneMin", "exp_l3_zzkc", 'LabelLongOneMin_factor98_sample'),  # 用flying因子参与训练,必须新起一个实验名，不然共用dataset
        # ("LabelShortOneMin", "exp_l3_zzkc", 'LabelShortOneMin_factor98_sample'),
        # ("LabelLongTwoMin", "exp_l3_zzkc", 'LabelLongTwoMin_factor98_sample'),
        # ("LabelShortTwoMin", "exp_l3_zzkc", 'LabelShortTwoMin_factor98_sample'),
        # #######################20240625###################
        # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98'),
        # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98_amp'),#事件用幅度代替0、1值
        # ("LabelFirstPeak_th12_60s", "exp_l3_kc_flying4", 'LabelFirstPeak_th12_60s_factor98_lowpca'),
        # ("LabelFirstPeak_th12_60s", "exp_l3_kc_flying4", 'LabelFirstPeak_th12_60s_factor98_highpca'),
        # #######################20240626###################
        # ("LabelFirstPeak_th05_120s", "exp_l3_kc_flying4", 'LabelFirstPeak_th05_120s_factor98_lowpca'),
        # ("LabelFirstPeak_th05_120s", "exp_l3_kc_flying4", 'LabelFirstPeak_th05_120s_factor98_highpca'),
        # #######################20240626###################
        # ("LabelFirstPeak_th10_60s", "exp_l3_kc_flying4", 'LabelFirstPeak_th10_60s_factor98_lowpca'),
        # ("LabelFirstPeak_th10_60s", "exp_l3_kc_flying4", 'LabelFirstPeak_th10_60s_factor98_highpca'),
        # #######################20240627###################
        # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98_log2'),  # 对数底为2
        # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98_amp_log2'),  # 对数底为2
        # ("LabelFirstPeak_th12_60s", "exp_l3_kc_flying4", 'LabelFirstPeak_th12_60s_factor98_lowpca_log2'),  # 对数底为2
        # ("LabelFirstPeak_th12_60s", "exp_l3_kc_flying4", 'LabelFirstPeak_th12_60s_factor98_highpca_log2'),  # 对数底为2
        # #######################20240628###################
        # ("LabelLongTwoMin", "exp_l3_zzkc_flying4", 'LabelLongTwoMin_factor98_log2'),
        # ("LabelShortTwoMin", "exp_l3_zzkc_flying4", 'LabelShortTwoMin_factor98_log2'),
        # ("LabelLongOneMin", "exp_l3_zzkc_flying4", 'LabelLongOneMin_factor98_log2'),
        # ("LabelShortOneMin", "exp_l3_zzkc_flying4", 'LabelShortOneMin_factor98_log2'),
        # #######################20240630###################
        # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98_huber1'),
        # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98_huber2'),
        # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98_huber3'),
        # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98_huber4'),

        #######################20240630###################
        # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98_huber0.5'),  # huber损失函数
        # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98_log2_huber1'),

        #######################20240702###################
        # ("vwap01_long_ret_60s", "exp_l3_zzkc_flying4", 'vwap01_long_ret_60s_factor98_sample_log2_huber1'), #对样本进行采样
        # ("vwap01_short_ret_60s", "exp_l3_zzkc_flying4", 'vwap01_short_ret_60s_factor98_sample_log2_huber1'),
        # ("smooth_long_ret_60s", "exp_l3_zzkc_flying4", 'smooth_long_ret_60s_factor98_sample_log2_huber1'),
        # ("smooth_short_ret_60s", "exp_l3_zzkc_flying4", 'smooth_short_ret_60s_factor98_sample_log2_huber1'),
        # ("dol_long_ret_60s", "exp_l3_zzkc_flying4", 'dol_long_ret_60s_factor98_sample_log2_huber1'),
        # ("dol_short_ret_60s", "exp_l3_zzkc_flying4", 'dol_short_ret_60s_60s_factor98_sample_log2_huber1'),
        #######################20240702###################
        # ("vwap01_long_ret_60s", "exp_l3_zzkc_flying4", 'vwap01_long_ret_60s_factor98_sample_log2_trim'),  # 截取0.5以下的标签
        # ("vwap01_short_ret_60s", "exp_l3_zzkc_flying4", 'vwap01_short_ret_60s_factor98_sample_log2_trim'),
        # ("smooth_long_ret_60s", "exp_l3_zzkc_flying4", 'smooth_long_ret_60s_factor98_sample_log2_trim'),
        # ("smooth_short_ret_60s", "exp_l3_zzkc_flying4", 'smooth_short_ret_60s_factor98_sample_log2_trim'),
        # ("dol_long_ret_60s", "exp_l3_zzkc_flying4", 'dol_long_ret_60s_factor98_sample_log2_trim'),
        # ("dol_short_ret_60s", "exp_l3_zzkc_flying4", 'dol_short_ret_60s_60s_factor98_sample_log2_trim'),
        # #######################20240705##################
        # ("vwap01_long_ret_60s", "exp_l3_zzkc_flying4", 'vwap01_long_ret_60s_factor98_sample_log2'),  # 对样本进行采样
        # ("vwap01_short_ret_60s", "exp_l3_zzkc_flying4", 'vwap01_short_ret_60s_factor98_sample_log2'),
        # ("smooth_long_ret_60s", "exp_l3_zzkc_flying4", 'smooth_long_ret_60s_factor98_sample_log2'),
        # ("smooth_short_ret_60s", "exp_l3_zzkc_flying4", 'smooth_short_ret_60s_factor98_sample_log2'),
        # ("dol_long_ret_60s", "exp_l3_zzkc_flying4", 'dol_long_ret_60s_factor98_sample_log2'),
        # ("dol_short_ret_60s", "exp_l3_zzkc_flying4", 'dol_short_ret_60s_60s_factor98_sample_log2'),
        # ##################20240716##################
        # ("LabelFirstPeak_th10_60s", "exp_l3_zzkc_flying4_levelone", 'LabelFirstPeak_th10_60s_factor98_levelone_log2'),
        # # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4_levelone", 'LabelFirstPeak_th12_60s_factor98_levelone_amp_log2'),
        # ("LabelFirstPeakAdjust0_th12_60s", "exp_l3_zzkc_flying4_levelone", 'LabelFirstPeakAdjust0_th12_60s_factor98_levelone_log2'),
        # # # #######################20240813##################
        # ("LabelFirstPeak_th10_60s", "exp_l3_hs300_flying5_levelone", 'LabelFirstPeak_th10_60s_factor98_levelone_log2'),
        # # # #######################20240813##################
        # ("LabelFirstPeak_th05_120s", "exp_l3_hs300_flying5_levelone", 'LabelFirstPeak_th05_120s_factor98_levelone_lowspread_log2'),
        # ("LabelFirstPeak_th10_60s", "exp_l3_hs300_flying5_levelone", 'LabelFirstPeak_th10_60s_factor98_levelone_midspread_log2'),
        # ("LabelFirstPeak_th10_60s", "exp_l3_hs300_flying5_levelone", 'LabelFirstPeak_th10_60s_factor98_levelone_highspread_log2'),
        # # # #######################20240813##################
        # ("LabelFirstPeakAdjust0_th12_60s", "exp_l3_zzkc_flying5_levelone", 'LabelFirstPeakAdjust0_th12_60s_factor98_levelone_flying5_amp_log2'),
        # ("LabelFirstPeak_th10_60s", "exp_l3_zzkc_flying5_levelone", 'LabelFirstPeak_th10_60s_factor98_levelone_amp_log2'),
        # ("LabelFirstPeakAdjust0_th10_60s", "exp_l3_zzkc_flying5_levelone", 'LabelFirstPeakAdjust0_th10_60s_factor98_levelone_facevent_amp_log2'),
        # ("LabelFirstPeak_th10_60s", "exp_l3_zzkc_flying5_levelone", 'LabelFirstPeak_th10_60s_factor98_levelone_log2'),
        # ("LabelFirstPeakAdjust0_th12_60s", "exp_l3_zzkc_flying5_levelone", 'LabelFirstPeakAdjust0_th12_60s_factor98_levelone_facevent_amp_log2'),
        # ##################20240814##################
        # ("LabelFirstPeak_th05_120s", "exp_l3_hs300_flying5_levelone", 'LabelFirstPeak_th05_120s_factor98_levelone_lowspread_log2'),
        # ("LabelFirstPeak_th10_120s", "exp_l3_hs300_flying5_levelone", 'LabelFirstPeak_th10_120s_factor98_levelone_lowspread_log2'),
        # ("LabelFirstPeak_th10_60s", "exp_l3_hs300_flying5_levelone", 'LabelFirstPeak_th10_60s_factor98_levelone_midspread_log2'),
        # ("LabelFirstPeak_th10_60s", "exp_l3_hs300_flying5_levelone", 'LabelFirstPeak_th10_60s_factor98_levelone_highspread_log2'),
        # ("LabelFirstPeakAdjust0_th12_60s", "exp_l3_hs300_flying5_levelone", 'LabelFirstPeakAdjust0_th12_60s_factor98_levelone_lowspread_log2'),
        # ("LabelFirstPeakAdjust0_th12_60s", "exp_l3_hs300_flying5_levelone", 'LabelFirstPeakAdjust0_th12_60s_factor98_levelone_midspread_log2'),
        # ("LabelFirstPeakAdjust0_th12_60s", "exp_l3_hs300_flying5_levelone", 'LabelFirstPeakAdjust0_th12_60s_factor98_levelone_highspread_log2'),
        # ("LabelFirstPeak_th10_120s", "exp_l3_hs300_flying5_levelone",  'LabelFirstPeak_th10_120s_factor98_levelone_lowspread_amp_log2'),
        # ("LabelFirstPeakAdjust0_th12_60s", "exp_l3_hs300_flying5_levelone", 'LabelFirstPeakAdjust0_th10_60s_factor98_levelone_lowspread_amp_log2'),
        # ##################20240814##################
        # ("LabelFirstPeakAdjust0_th12_60s", "exp_l3_zzkc_flying5_levelone", 'LabelFirstPeakAdjust0_th12_60s_factor98_levelone_flying5_log2'),
        # ("LabelFirstPeakAdjust0_th12_60s", "exp_l3_zzkc_flying5_levelone", 'LabelFirstPeakAdjust0_th12_60s_factor98_levelone_flying5_amp_log2'),
        # ##################20240815##################
        # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_normflying5_levelone", 'LabelFirstPeak_th12_60s_factor98_levelone_flying5_log2'),
        # ("LabelFirstPeakAdjust0_th12_60s", "exp_l3_zzkc_normflying5_levelone", 'LabelFirstPeakAdjust0_th12_60s_factor98_levelone_flying5_log2'),
        # ("LabelFirstPeakAdjust0_th12_60s", "exp_l3_zzkc_normflying5_levelone",  'LabelFirstPeakAdjust0_th12_60s_factor98_levelone_flying5_amp_log2'),
        # # ##################20240815##################
        # ("LabelFirstPeak_th05_120s", "exp_l3_hs300_normflying5_levelone", 'LabelFirstPeak_th05_120s_factor98_levelone_lowspread_log2'),
        # ("LabelFirstPeak_th10_120s", "exp_l3_hs300_normflying5_levelone", 'LabelFirstPeak_th10_120s_factor98_levelone_lowspread_log2'),
        # ("LabelFirstPeak_th10_60s", "exp_l3_hs300_normflying5_levelone", 'LabelFirstPeak_th10_60s_factor98_levelone_midspread_log2'),
        # ("LabelFirstPeak_th10_60s", "exp_l3_hs300_normflying5_levelone", 'LabelFirstPeak_th10_60s_factor98_levelone_highspread_log2'),
        # ("LabelFirstPeakAdjust0_th12_60s", "exp_l3_hs300_normflying5_levelone", 'LabelFirstPeakAdjust0_th12_60s_factor98_levelone_lowspread_log2'),
        # ("LabelFirstPeakAdjust0_th12_60s", "exp_l3_hs300_normflying5_levelone", 'LabelFirstPeakAdjust0_th12_60s_factor98_levelone_midspread_log2'),
        # ("LabelFirstPeakAdjust0_th12_60s", "exp_l3_hs300_normflying5_levelone", 'LabelFirstPeakAdjust0_th12_60s_factor98_levelone_highspread_log2'),
        # ("LabelFirstPeak_th10_120s", "exp_l3_hs300_normflying5_levelone",  'LabelFirstPeak_th10_120s_factor98_levelone_lowspread_amp_log2'),
        # ("LabelFirstPeakAdjust0_th12_60s", "exp_l3_hs300_normflying5_levelone", 'LabelFirstPeakAdjust0_th10_60s_factor98_levelone_lowspread_amp_log2'),
        # # ##################20240816##################
        # ("LabelFirstPeakAdjust0_th12_60s", "exp_l3_zzkc_flying5_levelone", 'LabelFirstPeakAdjust0_th12_60s_factor98_levelone_zz500amt_facevent_amp_log2'),
        ("LabelFirstPeakAdjust0_th12_60s", "exp_l3_zzkc_flying5_levelone", 'LabelFirstPeakAdjust0_th12_60s_factor98_zz500amt_levelone_amp_log2'),
    ]
    ray.init(local_mode = False)
    start_date, end_date = "20240701", "20240701"
    symbol_list = ["688052.SH", "688012.SH", "688981.SH", "688017.SH", "688256.SH", "688047.SH", "688041.SH", "688498.SH", "688008.SH"]
    data_type = "tick_l2p"
    model_type = "pickle"
    start_generate_and_evaluate_signal(exp_list, symbol_list, start_date, end_date,
                                       model_type = model_type, data_type = data_type,
                                       l3_flag = True
                                       )

