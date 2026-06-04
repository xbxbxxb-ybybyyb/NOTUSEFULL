from generate_parquet_utils import main_generate_parquet_l3, main_generate_parquet_l2p, start_generate_and_evaluate_signal
import ray

if __name__ == "__main__":
    exp_list = [
        # #######################20240705##################
        # ("LabelFirstPeak_th10_120s", "unite_kc", "unite_kc"),
        # ("LabelFirstPeak_th10_120s", "tick_kc_basket", "tick_kc_basket"),
        # ("LabelFirstPeak_th10_120s", "l2p_kc100_v1", "l2p_kc100_v1"),
        # ("LabelFirstPeak_th10_120s", "tick_688017.SH", "tick_688017.SH"),
        ("LabelFirstPeak_th10_120s", "l2p_kc_basket", "l2p_kc_basket"),
        # ("LabelFirstPeak_th10_120s", "l2p_688981.SH_v1.1", "l2p_688981.SH_v1.1"),
        # ("LabelFirstPeak_th10_120s", "l2p_688111.SH_v1.1", "l2p_688111.SH_v1.1"),
        # ("LabelFirstPeak_th10_120s", "l2p_688036.SH", "l2p_688036.SH"),
        # ("LabelFirstPeak_th10_120s", "l2p_HS800_high", "l2p_HS800_high"),
        # ("LabelFirstPeak_th10_120s", "l2p_HS800_low", "l2p_HS800_low"),

        # ("vwap01_long_ret_60s", "exp_l3_zzkc_flying4", 'vwap01_long_ret_60s_factor98_sample_log2'),  # 对样本进行采样
        # ("vwap01_short_ret_60s", "exp_l3_zzkc_flying4", 'vwap01_short_ret_60s_factor98_sample_log2'),
        # ("smooth_long_ret_60s", "exp_l3_zzkc_flying4", 'smooth_long_ret_60s_factor98_sample_log2'),
        # ("smooth_short_ret_60s", "exp_l3_zzkc_flying4", 'smooth_short_ret_60s_factor98_sample_log2'),
        # ("dol_long_ret_60s", "exp_l3_zzkc_flying4", 'dol_long_ret_60s_factor98_sample_log2'),
        # ("dol_short_ret_60s", "exp_l3_zzkc_flying4", 'dol_short_ret_60s_60s_factor98_sample_log2'),
        # ("LabelFirstPeak_th10_60s", "KC_LabelFirstPeak_th10_60s_log", 'KC_LabelFirstPeak_th10_60s_log'),
        # ("LabelFirstPeak_th10_60s", "l2p_kc2_log", 'l2p_kc2_log'),
    ]
    ray.init(local_mode=False)
    symbol_list = ["688012.SH", "688041.SH", "688047.SH", "688256.SH", "688271.SH", "688498.SH", "688506.SH",
                   "688017.SH", '688981.SH', "688390.SH", "688525.SH", "688036.SH", "688008.SH", "688036.SH"]
    start_date = "20240812"
    end_date = "20240812"
    model_type = "onnx"
    data_type = "tick_l2p"

    for label_name, exp_name, version_alias in exp_list:
        if exp_name == "l2p_kc100_v1":
            symbol_list = ["688498.SH"]
        elif exp_name == "unite_kc":
            symbol_list = ["688256.SH"]
            data_type = "enhanced_tick_norm"
        elif exp_name == "tick_kc_basket":
            symbol_list = ["688256.SH", "688981.SH", "688012.SH"]
            data_type = "enhanced_tick_norm"
        elif exp_name == "tick_688017.SH":
            symbol_list = ["688017.SH"]
            data_type = "enhanced_tick_norm"
        elif exp_name == "l2p_kc_basket":
            symbol_list = ["688012.SH", "688390.SH", "688047.SH", "688271.SH", "688041.SH", "688256.SH"]
        elif exp_name == "l2p_688981.SH_v1.1":
            symbol_list = ["688981.SH"]
        elif exp_name == "l2p_688111.SH_v1.1":
            symbol_list = ["688111.SH"]
        elif exp_name == "l2p_688036.SH":
            symbol_list = ["688036.SH"]
        elif exp_name == "l2p_HS800_high":
            symbol_list = ["002920.SZ", "300033.SZ", "300223.SZ", "300308.SZ", "300394.SZ", "300474.SZ", "300896.SZ"]
        elif exp_name == "l2p_HS800_low":
            symbol_list = ["000977.SZ", "300418.SZ", "002281.SZ"]
        elif exp_name == "KC_LabelFirstPeak_th10_60s_log":
            symbol_list = ["688271.SH", "688052.SH", "688012.SH", "688981.SH", "688017.SH", "688256.SH", "688047.SH",
                           "688041.SH", "688498.SH"]
        elif exp_name == "l2p_kc2_log":
            symbol_list = ["688271.SH", "688052.SH", "688012.SH", "688981.SH", "688017.SH", "688256.SH", "688047.SH",
                           "688041.SH", "688498.SH"][:1]
        start_generate_and_evaluate_signal([[label_name, exp_name, version_alias]], symbol_list[:1], start_date, end_date, model_type = model_type, data_type = data_type)

