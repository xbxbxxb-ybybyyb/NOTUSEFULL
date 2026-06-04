import os
import sys
import time
import pandas as pd
import numpy as np
import traceback
sys.path.append('../')
sys.path.append('./')
from web_entry.utils import web_calculation, Kafka_producer, record_error_info, trans_enddate
import tquant.strategy.factor_tester.tester_analysis as Tester
from SmartFactor.util.util import get_fac_class
from SmartFactor.util.data_context import get_factor_lib
from tquant import PsFactorData

# 挂载路径
excess_return_path = '/app/mount/factor_return/'

def load_fac_attr_from_env(factor_name, file_path):
    fac = get_fac_class(factor_name, file_path)
    fac.factor_name = os.environ.get("factor_name")
    fac.factor_type = os.environ.get("freq")
    fac.security_type = 'stock' if os.environ.get("security_type") == "1" else None
    fac.day_lag = int(float(os.environ.get("day_lag"))) if os.environ.get("day_lag") != 'null' else None
    fac.quarter_lag = int(float(os.environ.get("quarter_lag"))) if os.environ.get("quarter_lag") != 'null' else None
    fac.external_data_memory_id_dict = {}  # 用户依赖的外部数据的共享内存的id，与路径一一对应
    fac.used_shared_memory = 0
    depend_factor_list = os.environ.get("depend_factor").strip(' ').split(',')
    depend_factor_descrip = []
    tps = PsFactorData()
    for factor_dict in depend_factor_list:
        depend_factor_name, isUser = factor_dict.strip(' ').split(':')
        if str(isUser.strip(' ')) == '0':
            factor_lib = get_factor_lib([depend_factor_name])
        elif str(isUser.strip(' ')) == '1':
            factor_lib = tps.get_library_name_by_factor(depend_factor_name, 'release')
        else:
            raise Exception("环境变量depend_factor中所传的isUser不是0或1")
        depend_factor_descrip.append('.'.join([factor_lib, depend_factor_name]))
    fac.depend_factor = depend_factor_descrip

    # 解析环境变量股票池的值
    fac_security_pool = []

    if os.environ.get("stock_universe"):
        stock_universe_str = os.environ.get("stock_universe")
        stock_universe_list = stock_universe_str.split(",")
        for stock_name in stock_universe_list:
            if stock_name.lower() in ['alpha_universe', 'hs300', 'zz500', 'sz50', 'zz800', 'zz1000']:
                fac_security_pool = stock_name
                break
            fac_security_pool.append(stock_name)
    else:
        raise Exception("环境变量中未获取到stock_universe")
    fac.security_pool = fac_security_pool
    return fac


# nsw 为了能够发布成功 将ret_threshold 从0调整到-1，corr_threshold从0.7 改到1.1 测试完发布前记得改回来,in_sample_diff从1改为100
# out_sample_diff从0.6改为100.6
# start_date='20150102', end_date='20201231'

# 测试用参数
# start_date='20180102', end_date='20191231', price_type='vwap', rho=4e-4, top_range=0.1,
#                    neutralize=True, turnover_mode=True, ret_weight=False, vwap_13_type=0,
#                    is_day_factor=True, local=True, in_sample_diff=100.0, out_sample_diff=100.6,
#                    ret_threshold=-1, corr_threshold=1.1, ret_oos=0, excess_return_path=excess_return_path
# 生产用参数
def __factor_tester(start_date='20190401', end_date='20190630', price_type='vwap', rho=4e-4, top_range=0.1,
                    neutralize=True, turnover_mode=True, ret_weight=False, vwap_13_type=0,
                    is_day_factor=True, local=True, in_sample_diff=1.0, out_sample_diff=0.6,
                    ret_threshold=0, corr_threshold=0.7, ret_oos=0, excess_return_path=excess_return_path):
    """

    :param price_type: 用户获取因子在行情下的超额收益率，默认vwap
    :param rho: 成本相关，平均交易成本。乘以换手率算实际交易成本
    :param top_range: 因子分层后取前百分之多少，计算收益率
    :param nentralize: 因子行业中性化
    :param turnover_mode: 是否计算换手率，换手率乘以rho为实际交易成本
    :param ret_weight: 计算分层因子收益率时是否按因子值的排名加权，默认为False
    :param sample_diff_standard: 对收益率采样10次，收益率最好的5次减去最差的5次的收益率差值，与平均收益的比值，不能超过该阈值，默认为100%
    :param ret_threshold: 样本内平均收益必须达到的最小值，默认为0.0
    :param corr_threshold: 和其他因子的相关性不得超过的值，默认为0.7
    :param ret_oos: 样本外平均收益必须达到的最小值，默认为0.0
    :return:
    """
    # factor_type = os.environ.get('factor_type')
    freq = os.environ.get('freq')
    factor_name = os.environ.get('factor_name')
    file_path = os.environ.get('file_path')
    calc_env = 'release'
    factor_cls = load_fac_attr_from_env(factor_name, file_path)
    factor_data = \
    web_calculation(factor_cls, start_date, end_date, file_path, calc_env=calc_env, mode='show', factor_type=freq,
                    dynamic_load_attr=False)[factor_name]
    # factor_data.drop('Factor', axis=1, inplace=True)
    # factor_data = factor_data.iloc[:, 0].unstack()
    factor_data.dropna(axis=0, inplace=True, how='all')
    factor_data[~np.isfinite(factor_data)] = np.nan

    factor_result = {}
    factor_result[factor_name] = factor_data

    if freq == 'DAY':
        test_result, statu = Tester.test(start_date, end_date, factor_result, price_type, rho, top_range, neutralize,
                                  turnover_mode, ret_weight, vwap_13_type, is_day_factor, local, in_sample_diff,
                                  out_sample_diff, ret_threshold, corr_threshold, ret_oos, excess_return_path)
        print("test_result: ", test_result)
    else:
        test_result = False
        statu = 3

    return test_result, statu


def standard_factor_tester(ret_oos=0, start_date='20190101',end_date='20201231', price_type='vwap', rho=4e-4, top_range=0.1,
                 neutralize=True, turnover_mode=True,ret_weight=False, vwap_13_type=0, is_day_factor=True, local=True,
                 excess_return_path=excess_return_path):
    # 测试用项目：
    # dev 核心区 xxh001空间testGit项目 dev测试区量化专用空间 devtest0331项目
    # sit 核心区 量化空间 sitprd项目   sit测试区量化空间sittest项目
    # uat 量化研究空间 lianghuauat项目
    # prd 生产测试空间 lianghuaprd项目
    # TODO: 等到全总对一下环境变量 在这边走不同的检测分支 目前仅有相同模式下 不同门槛的两个因子检测标准

    return __factor_tester(start_date=start_date, end_date=end_date, price_type=price_type, rho=rho,
                           top_range=top_range,
                           neutralize=neutralize, turnover_mode=turnover_mode, ret_weight=ret_weight,
                           vwap_13_type=vwap_13_type,
                           is_day_factor=is_day_factor, local=local, in_sample_diff=1.0,
                           out_sample_diff=0.6,
                           ret_threshold=0, corr_threshold=0.7, ret_oos=ret_oos,
                           excess_return_path=excess_return_path)


def lowthres_factor_tester(ret_oos=0, start_date='20190101',end_date='20201231', price_type='vwap', rho=4e-4, top_range=0.1,
                 neutralize=True, turnover_mode=True,ret_weight=False, vwap_13_type=0, is_day_factor=True, local=True,
                 excess_return_path=excess_return_path):

    return __factor_tester(start_date=start_date, end_date=end_date, price_type=price_type, rho=rho,
                           top_range=top_range,
                           neutralize=neutralize, turnover_mode=turnover_mode, ret_weight=ret_weight,
                           vwap_13_type=vwap_13_type,
                           is_day_factor=is_day_factor, local=local, in_sample_diff=100.0,
                           out_sample_diff=100.6,
                           ret_threshold=-100, corr_threshold=1.1, ret_oos=ret_oos,
                           excess_return_path=excess_return_path)
def factor_tester():
    scene = os.environ.get('scene')
    kafka = Kafka_producer(scene)
    # start_date = "20190101"
    # end_date = "20201231"
    start_date = os.environ.get("sample_outer_startdate").replace('/', '')
    end_date = trans_enddate(os.environ.get("sample_outer_enddate")).replace('/', '')
    start_mes = {'uuid': os.environ.get('uuid'),
                 'factorId': os.environ.get('factor_id'),
                 'createTime': time.strftime('%Y-%m-%d %H:%M%S'),
                 'testjobStatus': 1}
    print("start_mes:", start_mes)
    kafka.send_json_data(start_mes)
    print("start_mes send mes success !")

    custom_standard = os.environ.get("custom_standard")
    if custom_standard == "2":
        test_result, statu = standard_factor_tester(start_date=start_date, end_date=end_date)
    elif custom_standard == "3":
        test_result, statu = lowthres_factor_tester(start_date=start_date, end_date=end_date)
    else:
        raise Exception("因子检测目前支持两套自定义标准，2：标准模式，3 ：低门槛测试模式，暂不支持{}".format(custom_standard))

    # if test_result:
    #     testjobStatus = 2
    # else:
    #     testjobStatus = 3
    end_mes = {'uuid': os.environ.get('uuid'),
               'factorId': os.environ.get('factor_id'),
               'createTime': time.strftime('%Y-%m-%d %H:%M%S'),
               'testjobStatus': statu}
    print("start_mes:", end_mes)
    kafka.send_json_data(end_mes)
    print("end_mes send mes success !")


if __name__ == "__main__":
    start_time = time.time()
    try:
        factor_tester()
    except Exception as e:
        traceback.print_exc()
        factor_name = os.environ.get("factor_name", "unknow")
        record_error_info(factor_name, traceback.format_exc())
        raise e
    finally:
        end_time = time.time()
        print('produceTime', end_time - start_time)
