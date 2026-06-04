# coding:utf-8
import traceback

from tquant.strategy.factor_tester.test_data_loader import *
from tquant.strategy.factor_tester.factor_test_analysis import FactorTestAnalysis


def factor_test_analysis(factor_name, factor_value, start_date, end_date, price_type, rho, top_range, neutralize,
                          turnover_mode, ret_weight, vwap_13_type, is_day_factor, local, in_sample_diff,
                          out_sample_diff, ret_threshold, corr_threshold, ret_oos, excess_return_path):
    print("factor_test_analysis: ", factor_name)
    factor_value, start_date, end_date = adapt_for_analysis(factor_value, start_date, end_date)
    factor_test_class = FactorTestAnalysis(factor_name, factor_value, excess_return_path, start_date, end_date,
                                            price_type=price_type, rho=rho, top_range=top_range, neutralize=neutralize,
                                            turnover_mode=turnover_mode, ret_weight=ret_weight,
                                            is_day_factor=is_day_factor, vwap_13_type=vwap_13_type, local=local,
                                            in_sample_diff=in_sample_diff, out_sample_diff=out_sample_diff,
                                            ret_threshold=ret_threshold, corr_threshold=corr_threshold, ret_oos=ret_oos)
    # neu_factors = get_factor_names(is_day_factor, factor_name)
    test_result = factor_test_class.launch_test()
    print("test_analysis_result:", test_result)
    flag = test_result["flag"]
    if flag:
        temp_save_daily_excess_return(factor_test_class.factor_name, factor_test_class.factor_excess, excess_return_path)
    print("factor_test_analysis: ", factor_name, " finished")
    return test_result


def day_factor_test(start_date, end_date, factor_result, price_type, rho, top_range, neutralize,
                    turnover_mode, ret_weight, vwap_13_type, is_day_factor, local, in_sample_diff, out_sample_diff,
                    ret_threshold, corr_threshold, ret_oos, excess_return_path):
    factor_name, factor_value = factor_result.popitem()
    factor_result[factor_name] = factor_value
    print("Start Factor Test:", factor_name)
    t1 = dt.datetime.now()
    try:
        test_result = factor_test_analysis(factor_name, factor_value, start_date, end_date,
                                            price_type=price_type, rho=rho, top_range=top_range,
                                            neutralize=neutralize, turnover_mode=turnover_mode, ret_weight=ret_weight,
                                            vwap_13_type=vwap_13_type, is_day_factor=is_day_factor, local=local,
                                            in_sample_diff=in_sample_diff, out_sample_diff=out_sample_diff,
                                            ret_threshold=ret_threshold, corr_threshold=corr_threshold,
                                            ret_oos=ret_oos, excess_return_path=excess_return_path)
        ret = process_test_result(factor_name, test_result, None)
        t2 = dt.datetime.now()
        print("Finish Factor Test:", factor_name, "costs", t2 - t1)
        return ret
    except Exception:
        traceback.print_exc()
        return False


def process_test_result(factor_name, analysis_result, symbol_result):
    flag_analysis, detail, reason_analysis = True, None, None
    flag_symbol, reason_symbol = True, None

    if analysis_result is not None:
        flag_analysis = analysis_result["flag"]
        detail = analysis_result["stat_result"]
        reason_analysis = analysis_result["reason"]

    if symbol_result is not None:
        flag_symbol = symbol_result["flag"]
        reason_symbol = symbol_result["reason"]

    if flag_analysis and flag_symbol:
        print("Factor Test Result:", factor_name, "True")
        return True

    print("Factor Test Result:", factor_name, "False")
    if analysis_result is not None:
        print("Factor Test Result is: {}, Reason: \n{}\n{}\n".format(flag_analysis, reason_analysis,
                                                                                    detail))
    if symbol_result is not None:
        print("Stock-Trade Team Factor Test Result is: {}, Reason:".format(flag_symbol))
        for time_range, test_result in reason_symbol.items():
            print(time_range, test_result)
    return False

def test(start_date='20150102', end_date='20201231', factor_result=None, price_type='vwap', rho=4e-4, top_range=0.1,
         neutralize=True, turnover_mode=True, ret_weight=False, vwap_13_type=0, is_day_factor=True, local=True,
         in_sample_diff=1.0, out_sample_diff=0.6, ret_threshold=0, corr_threshold=0.7, ret_oos=0,
         excess_return_path='/app/mount/factor_return'):
    """
    :param start_date:开始日期
    :param end_date: 结束日期
    :param factor_result: 待检测因子数据dict，key为因子名，value为因子数据
    :param price_type: 用户获取因子在行情下的超额收益率，默认vwap
    :param rho: 成本相关，平均交易成本。乘以换手率算实际交易成本
    :param top_range: 因子分层后取前百分之多少，计算收益率
    :param neutralize: 因子行业中性化
    :param turnover_mode: 是否计算换手率，换手率乘以rho为实际交易成本
    :param ret_weight: 计算分层因子收益率时是否按因子值的排名加权，默认为False
    :param vwap_13_type:
    :param is_day_factor:
    :param local:
    :param in_sample_diff: 样本内对收益率采样10次，收益率最好的5次减去最差的5次的收益率差值，与平均收益的比值，不能超过该阈值，默认为100%
    :param out_sample_diff: 样本外对收益率采样10次，收益率最好的5次减去最差的5次的收益率差值，与平均收益的比值，不能超过该阈值，默认为100%
    :param ret_threshold: 样本内平均收益必须达到的最小值，默认为0.0
    :param corr_threshold: 和其他因子的相关性不得超过的值，默认为0.7
    :param ret_oos: 样本外平均收益必须达到的最小值，默认为0.0
    :return:
    """
    check_factor_result(factor_result)
    return day_factor_test(start_date, end_date, factor_result, price_type, rho, top_range, neutralize,
                           turnover_mode, ret_weight, vwap_13_type, is_day_factor, local, in_sample_diff,
                           out_sample_diff, ret_threshold, corr_threshold, ret_oos, excess_return_path)
