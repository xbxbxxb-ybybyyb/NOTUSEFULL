from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
from xquant.marketdata import MarketData
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from tqdm import tqdm
import numpy as np
from xquant.factordata import FactorData
from artifacts.flying_functions import *

ma = MarketData()


def merge_norm_flying_factor(symbol, start_date, end_date, factor_name_list, label_name, flying_factor,
                             factor_config_path, tagger_limit=60, data_type="tick_l2p",
                             flying_base_dir="/dfs/group/800657/library/l3_event/event_data"):
    """
    读取事件数据，
    :param symbol:
    :param start_date:
    :param end_date:
    :param factor_name_list:
    :param label_name:
    :param tagger_limit:
    :param data_type:
    :param flying_base_dir:
    :return:
    """
    fa = FactorData()
    dates = fa.tradingday(start_date, end_date)
    fp = FactorProvider("016869")
    # ########################生成采样数据###########################
    feature_label_df = load_factor_label(
        fp,
        data_type,
        start_date,
        end_date,
        symbol,
        factor_name_list,
        [label_name],
        tagger_limit, verbose=0)
    flying_factor_df = load_flying_factors(symbol, dates=dates, use_pandas=False, flying_base_dir=flying_base_dir,
                                           verbose=0)
    if len(flying_factor_df) == 0:
        return pd.DataFrame()
    flying_factor_df = flying_factor_df.to_pandas()
    flying_factor_df = flying_factor_df.set_index("DateTime")

    merge_df = pd.merge(feature_label_df, flying_factor_df, left_index=True, right_index=True, how="inner")
    merge_df = merge_df[merge_df["open_flying"] != 0]
    new_feature_label_df = merge_df[factor_name_list + [label_name] + flying_factor]
    #     print("feature_label_df: ",feature_label_df.shape, ", new_feature_label_df: ", new_feature_label_df.shape)
    if new_feature_label_df.empty:
        return pd.DataFrame()
    T_test, X_test, Y_test = get_prepared(new_feature_label_df, label_name, w_size=1, parallel_mode=False)
    X_test = X_test  # [:, 0]
    Y_test = Y_test.flatten()
    #     print("T_test, X_test, Y_train: ", len(T_test), X_test.shape, Y_test.shape)
    # ########################标准化因子###########################
    open_flying_df = pd.DataFrame(X_test, columns=factor_name_list + flying_factor, index=new_feature_label_df.index)
    factor_config = pd.read_json(factor_config_path)
    for j in range(len(factor_name_list)):
        factor_mean = factor_config[factor_name_list[j]].loc['mean']
        factor_std = factor_config[factor_name_list[j]].loc['std']
        clip_lower = factor_mean - 3 * factor_std
        clip_upper = factor_mean + 3 * factor_std
        cliped_df = open_flying_df[factor_name_list[j]].clip(
            lower=clip_lower, upper=clip_upper)
        open_flying_df[factor_name_list[j]] = (cliped_df.values - factor_mean) / factor_std
    open_flying_df[label_name] = Y_test
    return open_flying_df


factor_list = pd.read_csv(
    "/dfs/group/800657/exp_results/exp_l3_kc50_th12_60s_flying4/l3_kc50_flying4/factors.csv").iloc[:, 0].tolist()
factor_list.remove("ReferenceMidPrice")
stock_list = ["688111.SH", "688256.SH", "688012.SH", "688041.SH"]
start_date, end_date = "20240101", "20240430"
label_name = "LabelFirstPeak_th15_60s"
flying_factor = ["FacPriceSpread", "FacOneBigOrder", "FacCumOrdersNetVolOverV0", "FacBreakingP0NumOrders"]


# with PdfPages('zz500data60.pdf') as pdf:
def func():
    total_result = []
    for factor in tqdm(factor_list[:-1]):
        for symbol in ["002432.SZ", "000423.SZ", "301236.SZ", "688029.SH", "688390.SH", "688521.SH"]:
            #             sub_result = factor_df[factor_df["M_HTSCSecurityID"]==symbol][factor].describe().to_dict()
            #             sub_result["factor"] = factor
            #             sub_result["symbol"] = symbol
            #             total_result.append(sub_result)
            open_flying_df = merge_norm_flying_factor(symbol, start_date, end_date, [factor], label_name, flying_factor,
                                                      factor_config_path="/dfs/group/800657/exp_results/kc_dataset/{}_factor_config.json".format(
                                                          symbol),
                                                      tagger_limit=60, data_type="tick_l2p",
                                                      flying_base_dir="/dfs/group/800657/library/l3_event/event_data")

            data = open_flying_df[factor].dropna()
            data = data.values
            #         plot_dist(data, symbol, factor)
            import seaborn as sns
            import matplotlib.pyplot as plt

            sns.distplot(data, bins=100, kde=False, norm_hist=False,
                         hist_kws={"weights": np.ones_like(data) / len(data)})
            #     open_flying_df[open_flying_df["M_HTSCSecurityID"]==symbol1][factor].plot.hist(bins = 100)

            # 计算均值和方差
            mean = data.mean()
            variance = data.var()
            print_str = ",".join(
                ["symbol:", symbol, "factor:", factor, "mean:", str(mean), "var:", str(variance), "corr:",
                 str(open_flying_df[[factor, label_name]].corr().iloc[0, 1])])
            print(print_str)

            # 绘制均值和方差的垂直线
            plt.axvline(mean, color='r', linestyle='dashed', linewidth=1.1, label='Mean')
            plt.axvline(mean + np.sqrt(variance), color='g', linestyle='dashed', linewidth=1.1, label='Std Deviation')
            plt.axvline(mean - np.sqrt(variance), color='g', linestyle='dashed', linewidth=1.1)

            # 添加标签和图例
            plt.xlabel(symbol)
            plt.ylabel(factor)
            plt.legend()
        #         plt.show()
        plt.text(0.1, -1.2, print_str, ha='center', va='center', fontsize=10)  # 在图表下方添加文本
        plt.close()
        #     plt.xlim(-1, 1)

#     result_df = pd.DataFrame(total_result)

