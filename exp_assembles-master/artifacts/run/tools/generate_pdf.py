from artifacts.signal_evaluate import TradingEvaluate
from artifacts.utils import save_and_append_xlsx
from matplotlib.backends.backend_pdf import PdfPages
from decimal import Decimal, ROUND_DOWN
import pandas as pd
import matplotlib.pyplot as plt
import os
import ray
import time
from xquant.factordata import FactorData
import datetime as dt

avgret_field_pattern = ['模型名称', '日期', '标的', '止盈线', '止损线', '预测阈值',
                        '日均触发次数', '平均回报', '胜率', '盈亏比', '买入次数', '卖出次数',
                        '税后获胜次数', '获胜平均回报', '亏损平均回报', '单日最大亏损', '平均持仓时间',
                        '止盈回报', '止损回报', '反转信号回报', '超时回报',
                        '止盈占比', '止损占比', '反转占比', '超时占比',
                        ]

def plot_winloss_table(symbol_name, win_limit, loss_limit, signal_evaluate_df_detail,
                       version_alias, start_date, end_date, weight_by_daynum=False, verbose = 1,
                       save_base_dir = "./"
                       ):
    os.makedirs(os.path.join(save_base_dir, version_alias), exist_ok=True)
    cache_file_name = os.path.join(save_base_dir, version_alias, "avgret_detail_all.pkl")
    file_path = os.path.join(save_base_dir, version_alias, f"{version_alias}_{symbol_name}_win{float(win_limit)}_loss{float(loss_limit)}.xlsx")
    pred_min_list = []
    for ridx, row in signal_evaluate_df_detail.iterrows():
        orders = row["orders"]
        preds = orders["pred"]
        preds = [abs(i) for i in preds]
        pred_min = min(preds)
        pred_min_list.append(pred_min)
    print("pred_min_list:", pred_min_list)
    min_pred = min(pred_min_list)
    dec_number = Decimal(min_pred)
    num = dec_number.quantize(Decimal('0.0'), rounding=ROUND_DOWN)
    num = float(num)
    pred_list = []
    while round(num,1) <= 2.8:
        pred_list.append(round(num,1))
        num += 0.1
    print("pred_list: ", pred_list)
    if len(pred_list) == 0:
        print(signal_evaluate_df_detail)
        print("pred_list 为空，请调整pred的阈值！")

    tradingOrder_df_agg_list = []
    res_df_list = []
    for pred in pred_list:
        tradingOrder_list = []
        for ridx, row in signal_evaluate_df_detail.iterrows():
            orders = row["orders"]
            orders = orders[(orders["pred"] >= pred) | (orders["pred"] <= -pred)]
            if len(orders[(orders["pred"] >= pred)])==0 or len(orders[(orders["pred"] <= -pred)])==0:
                continue
            tradingOrder = TradingEvaluate(orders)
            tradingOrder["symbol"] = row["symbol"]
            tradingOrder["date"] = row["date"]
            tradingOrder_list.append(tradingOrder)

        if len(tradingOrder_list) == 0:
            continue
        tradingOrder_df = pd.DataFrame(tradingOrder_list)
        tradingOrder_df_zh = tradingOrder_df.rename(columns = {
        'pred': '预测阈值',
        'orders': '订单明细',
        'predUp': '阈值上限',
        'predDw': '阈值下限',
        'numAaverageDay':'开平仓次数',
        'triggerTimes': '日均触发次数',
        'longTimes': '买入次数',
        'shortTimes': '卖出次数',
        'winTimes': '税后获胜次数',
        'winRate': '胜率',
        'averageRetTrigger': '平均回报',
        'averageRetWin': '获胜平均回报',
        'averageRetLoss': '亏损平均回报',
        'averageRetProfitLossRatio': '盈亏比',
        'maxLoss': '单日最大亏损',
        'averagePositionTime': '平均持仓时间',
        'win_mean': '止盈回报',
        'loss_mean': '止损回报',
        'reversal_mean': '反转信号回报',
        'timeout_mean': '超时回报',
        'loss_count': '止损占比',
        'reversal_count': '反转占比',
        'timeout_count': '超时占比',
        'win_count': '止盈占比',
        'symbol': '标的',
        'date': '日期',
         })
        save_and_append_xlsx(tradingOrder_df_zh, sheet_name=f"pred_{pred}", overwrite_col="日期", output_path=file_path)
        tradingOrder_df_zh["预测阈值"] = float(pred)
        tradingOrder_df_zh["模型名称"] = version_alias
        tradingOrder_df_zh["标的"] = symbol_name
        tradingOrder_df_zh["止盈线"] = float(win_limit)
        tradingOrder_df_zh["止损线"] = float(loss_limit)
        tradingOrder_df_zh = tradingOrder_df_zh.reindex(columns=avgret_field_pattern)
        res_df_list.append(tradingOrder_df_zh)

        if not weight_by_daynum:
            # 按天取平均
            tradingOrder_df["weight"] = 1 / tradingOrder_df["numAaverageDay"].count()
        else:
            # 按每天的开平仓次数加权
            tradingOrder_df["weight"] = tradingOrder_df["numAaverageDay"] / tradingOrder_df["numAaverageDay"].sum()

        column_type_dict = tradingOrder_df.dtypes.to_dict()
        result_agg_dict = {}
        for column in column_type_dict:
            if column in ["weight"]:
                continue
            if column in ["triggerTimes", "longTimes", "shortTimes", "winTimes"]:
                result_agg_dict[column] = tradingOrder_df[column].mean()
                continue
            if str(column_type_dict[column]).startswith("float") or str(column_type_dict[column]).startswith("int"):
                result_agg_dict[column] = (tradingOrder_df[column] * tradingOrder_df["weight"]).sum()
        result_agg_dict["pred"] = pred
        result_agg_dict['date_count'] = len(tradingOrder_df)
        tradingOrder_df_agg = pd.DataFrame([result_agg_dict])
        tradingOrder_df_agg_list.append(tradingOrder_df_agg)

    if res_df_list:
        tradingOrder_zh = pd.concat(res_df_list)
        if os.path.exists(cache_file_name):
            df_cache = pd.read_pickle(cache_file_name)
            df_all = pd.concat([df_cache, tradingOrder_zh])
            df_all = df_all.drop_duplicates(subset=["模型名称", "日期", "标的", "止盈线", "止损线", "预测阈值"], keep="last")
            df_all.to_pickle(cache_file_name)
        else:
            tradingOrder_zh.to_pickle(cache_file_name)


    result_df = pd.concat(tradingOrder_df_agg_list).round(5)
    result_df = result_df.rename(columns = {
        'date_count': '有效天数',
        'pred': '预测阈值',
        'triggerTimes': '日均触发次数',
        'longTimes': '买入次数',
        'shortTimes': '卖出次数',
        'winTimes': '税后获胜次数',
        'winRate': '胜率',
        'averageRetTrigger': '平均回报',
        'averageRetWin': '获胜平均回报',
        'averageRetLoss': '亏损平均回报',
        'averageRetProfitLossRatio': '盈亏比',
        'maxLoss': '单日最大亏损',
        'averagePositionTime': '平均持仓时间',
        'win_mean': '止盈回报',
        'loss_mean': '止损回报',
        'reversal_mean': '反转信号回报',
        'timeout_mean': '超时回报',
        'loss_count': '止损占比',
        'reversal_count': '反转占比',
        'timeout_count': '超时占比',
        'win_count': '止盈占比',
    }).reindex(
        columns=['预测阈值', '有效天数', '日均触发次数', '买入次数', '卖出次数', '税后获胜次数', '胜率', '平均回报', '获胜平均回报', '亏损平均回报', '盈亏比', '单日最大亏损',
                 '平均持仓时间',
                 '止盈回报', '止损回报', '反转信号回报', '超时回报', '止盈占比', '止损占比', '反转占比', '超时占比'])
    if verbose > 0:
        print(result_df)
    return result_df

def plot_summary_pdf(summary_df, pdf):
    # 创建一个新的图表
    columns = summary_df.columns
    fig, ax = plt.subplots(figsize=(len(columns) + 0.3, len(summary_df) + 0.3))
    ax = plt.gca()
    ax.axis('off')  # 关闭坐标轴
    # ax.text(0.2, 0.95, f"{'=' * 10} {symbol_name} win{win_limit} loss{loss_limit} 税后收益 {'=' * 10}  ", fontsize=20)
    ax.text(0.2, 0.95, f"{'=' * 10} 止盈止损线税后收益汇总 {'=' * 10}  ", fontsize=20)

    table = ax.table(cellText=summary_df.values, colLabels=summary_df.columns, loc='center',
                     colWidths=[0.05] * len(summary_df.columns),  # 为每列设置宽度
                     # cellPadding = [0.1]*len(summary_df.columns),
                     cellLoc='left',
                     # fontsize=8, bbox=[0, 0, 1, 1]
                     fontsize=4)  # 设置字体大小
    # table.set(pad = 0.01)
    # plt.tight_layout(pad=0.1)
    table.auto_set_column_width(col=list(range(len(summary_df.columns))))
    table.scale(xscale=1, yscale=2)

    pdf.savefig()
    plt.close()


def genarate_pdf(exp_list, symbol_list, start_date, end_date, input_base_dir, summary_fields=None, save_base_dir = "./", weight_by_daynum = True):
    for label_name, exp_name, version_alias in exp_list:
        input_base_dir = os.path.join(input_base_dir, version_alias)
        pdf_path_base = os.path.join(save_base_dir, "pdf", end_date)
        if not os.path.exists(pdf_path_base):
            os.makedirs(pdf_path_base)
        pdf_path = os.path.join(pdf_path_base, f"{version_alias}_winloss.pdf")
        pdf_path_summary = os.path.join(pdf_path_base, f"{version_alias}_winloss_summary.pdf")
        # TODO 新增汇总逻辑
        @ray.remote(max_calls=5)
        def func_inner(symbol_name, input_base_dir):
            df_list = []
            for win_limit, loss_limit in [(1.5, 2), (4, 2), (6, 2)]:
                pkl_path = f"{input_base_dir}/{symbol_name}_win{'%d' % (win_limit * 10)}_loss{'%d' % (loss_limit * 10)}_detail.pkl"
                if os.path.exists(pkl_path):
                    # print(f"开始为{version_alias}-{symbol_name}-{win_limit}-{loss_limit}输出PDF...")
                    try:
                        signal_evaluate_df_detail = pd.read_pickle(pkl_path)
                        signal_evaluate_df_detail = signal_evaluate_df_detail[
                            (signal_evaluate_df_detail["date"] >= start_date) & (signal_evaluate_df_detail["date"] <= end_date)]
                        sdate = signal_evaluate_df_detail['date'].min()
                        edate = signal_evaluate_df_detail['date'].max()
                        if signal_evaluate_df_detail.empty:
                            print(f"{version_alias}-{symbol_name}-{win_limit}-{loss_limit}文件为空！")
                            continue
                        res_df = plot_winloss_table(symbol_name, win_limit, loss_limit, signal_evaluate_df_detail,
                                                    version_alias, start_date, end_date, save_base_dir=save_base_dir,
                                                    weight_by_daynum=weight_by_daynum)
                        res_df["标的"] = symbol_name
                        res_df["止盈线"] = win_limit / 1000
                        res_df["止损线"] = loss_limit / 1000
                        res_df["开始日期"] = sdate
                        res_df["结束日期"] = edate
                        df_list.append(res_df)
                    except:
                        print(f"{pkl_path}文件损坏")
                        continue
                # else:
                #     print(f"{version_alias}-{symbol_name}-{win_limit}-{loss_limit}不存在pkl文件:\n {pkl_path}")
                #     res_df = pd.DataFrame()
            if df_list:
                df = pd.concat(df_list)
                return df
            else:
                return pd.DataFrame()
        tasks = []
        for symbol_name in symbol_list:
            pd.set_option("display.max_colwidth", None)
            tasks.append(func_inner.remote(symbol_name, input_base_dir))
        df_summary_list = ray.get(tasks)

        if df_summary_list:
            result_df = pd.concat(df_summary_list)
            if result_df.empty:
                return
            with PdfPages(pdf_path) as pdf:
                symbol_lines = sorted(list(set(result_df["标的"].tolist())))
                win_lines = sorted(list(set(result_df["止盈线"].tolist())))
                loss_lines = sorted(list(set(result_df["止损线"].tolist())))
                for symbol_name in symbol_lines:
                    for win_limit in win_lines:
                        for loss_limit in loss_lines:
                            sub_result_df = result_df[(result_df["标的"]==symbol_name) & \
                                                      (result_df["止盈线"] == win_limit) & \
                                                      (result_df["止损线"] == loss_limit)
                                                      ]
                            sdate = sub_result_df["开始日期"].iloc[0]
                            edate =sub_result_df["结束日期"].iloc[0]
                            # 创建一个新的图表
                            columns = sub_result_df.columns
                            fig, ax = plt.subplots(figsize=(len(columns) + 0.3, len(sub_result_df) + 0.3))
                            ax = plt.gca()
                            ax.axis('off')  # 关闭坐标轴
                            ax.text(0.2, 0.95,
                                    f"{'=' * 10} {symbol_name} {sdate} {edate} 止盈止损线 win{win_limit}，loss{loss_limit}（税后收益） {'=' * 10}  ",
                                    fontsize=20)

                            table = ax.table(cellText=sub_result_df.values, colLabels=sub_result_df.columns, loc='center',
                                             colWidths=[0.05] * len(sub_result_df.columns),  # 为每列设置宽度
                                             # cellPadding = [0.1]*len(result_df.columns),
                                             cellLoc='left',
                                             # fontsize=8, bbox=[0, 0, 1, 1]
                                             fontsize=4)  # 设置字体大小
                            # table.set(pad = 0.01)
                            # plt.tight_layout(pad=0.1)
                            table.auto_set_column_width(col=list(range(len(sub_result_df.columns))))
                            table.scale(xscale=1, yscale=2)

                            pdf.savefig()
                            plt.close()

            # pdf_fileds = ['日均触发次数', '买入次数', '卖出次数', '税后获胜次数', '胜率', '平均回报', '获胜平均回报', '亏损平均回报', '盈亏比', '单日最大亏损','平均持仓时间',
            #       '止盈回报', '止损回报', '反转信号回报', '超时回报', '止盈占比', '止损占比', '反转占比', '超时占比']
            # if summary_fields:
            #     assert isinstance(summary_fields, list), "summary_fields参数为list类型。"
            #     select_cols = [i for i in summary_fields if i in pdf_fileds]
            #     select_cols = ["标的", "预测阈值", "止盈线", "止损线"] + select_cols
            #     if len(select_cols) == 0:
            #         print("pdf输出列有以下字段：\n{}，\n请检查后重新输入！".format(pdf_fileds))
            #         return
            # else:
            #     select_cols = ["标的", "预测阈值", "止盈线", "止损线"]
            # df_summary = df_summary.reindex(columns=select_cols)
            # with PdfPages(pdf_path_summary) as pdf_summary:
            #     plot_summary_pdf(df_summary, pdf_summary)


if __name__ == "__main__":
    exp_list = [
            # ("LabelFirstPeak_th10_120s", "l2p_kc_basket", "l2p_kc_basket"),
            ("LabelFirstPeak_th10_120s", "l2p_kc2_log", "l2p_kc2_log"),
            # ("LabelFirstPeak_th10_120s", "l2p_688981.SH_v1.1", "l2p_688981.SH_v1.1"),
            # ("LabelFirstPeak_th10_120s", "l2p_688111.SH_v1.1", "l2p_688111.SH_v1.1"),
            # ("LabelFirstPeak_th10_120s", "l2p_kc100_v1", "l2p_kc100_v1"),
            # ("LabelFirstPeak_th10_120s", "unite_kc", "unite_kc"),
            # ("LabelFirstPeak_th10_120s", "tick_kc_basket", "tick_kc_basket"),
            # ("LabelFirstPeak_th10_120s", "tick_688017.SH", "tick_688017.SH"),
            # ("LabelFirstPeak_th10_120s", "l2p_688036.SH", "l2p_688036.SH"),
            # ("LabelFirstPeak_th10_120s", "l2p_HS800_high", "l2p_HS800_high"),
            # ("LabelFirstPeak_th10_120s", "l2p_HS800_low", "l2p_HS800_low"),
            # # L3
            # ("LabelFirstPeak_th12_60s", "l3_zzkc_flying4_log2", 'l3_zzkc_flying4_log2'),
            # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4_levelone", 'LabelFirstPeak_th12_60s_factor98_levelone_log2'),
            # ("LabelFirstPeakAdjust0_th12_60s", "exp_l3_zzkc_flying4_levelone", 'LabelFirstPeakAdjust0_th12_60s_factor98_levelone_log2'),
            # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98_log2'),
        ]
    base_dir = "/dfs/group/800657/library/tmp_l3_event/signal_evaluate_longshort1"
    start_date = "2024-07-01"
    end_date = "2024-08-19"
    symbol_list = ["688012.SH", "688041.SH", "688047.SH", "688256.SH", "688271.SH", "688498.SH", "688506.SH",
                   "688017.SH", '688981.SH', "688390.SH", "688525.SH", "688036.SH", "688008.SH", "688036.SH"]
    save_base_dir = "/dfs/group/800657/winloss_data/"
    os.makedirs(save_base_dir, exist_ok=True)
    for label_name, exp_name, version_alias in exp_list[:1]:
        # TODO 为每个模型添加测试的标的
        if exp_name == "l2p_HS800_high" and version_alias == "l2p_HS800_high":
            symbol_list = ["002920.SZ", "300033.SZ", "300223.SZ", "300308.SZ", "300394.SZ", "300474.SZ", "300896.SZ"]
        elif exp_name == "l2p_HS800_low" and version_alias == "l2p_HS800_low":
            symbol_list = ["000977.SZ", "300418.SZ", "002281.SZ"]
        elif exp_name == "l2p_kc2_log" and version_alias == "l2p_kc2_log":
            symbol_list = ['688256.SH', '688036.SH', '688390.SH', '688012.SH', '688047.SH', '688041.SH', '688981.SH',
                           '688111.SH', '688491.SH']
            symbol_list = ["688256.SH"]
        elif exp_name in ["signal_df_0802", "signal_df_0802_resnet"]:
            symbol_list = ["688981.SH", "688256.SH"]
        elif exp_name == "exp_l3_zzkc_flying4_levelone":
            symbol_list = ['688256.SH', '688036.SH', '688390.SH', '688012.SH', '688047.SH', '688041.SH', '688981.SH',
                           '688111.SH', '688491.SH']
        elif exp_name == "l3_zzkc_flying4_log2" and version_alias == "l3_zzkc_flying4_log2":
            symbol_list = ['688256.SH', '688036.SH', '688390.SH', '688012.SH', '688047.SH', '688041.SH', '688981.SH',
                           '688111.SH', '688491.SH']
        elif exp_name == "exp_l3_zzkc_flying4":
            symbol_list = ['688256.SH', '688036.SH', '688390.SH', '688012.SH', '688047.SH', '688041.SH', '688981.SH',
                           '688111.SH', '688491.SH']
        genarate_pdf([[label_name, exp_name, version_alias]], symbol_list,
                     start_date, end_date,
                     input_base_dir="/dfs/group/800657/library/tmp_l3_event/l3_signal_evaluate_mid",
                     save_base_dir = save_base_dir, weight_by_daynum=True)

