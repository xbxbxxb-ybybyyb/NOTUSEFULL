import os
import time
from datetime import datetime
import sys
import traceback
sys.path.append('../')
sys.path.append('./')

from web_entry.utils import get_psfactor_data, date_parser, web_calculation, Kafka_producer, trans_enddate, record_error_info, backtest_params_parser

from tquant.strategy.day_factor_backtest_new.FactorBacktest import DayFactorBacktest
from tquant import BasicData, StockData


shared_factor = os.environ.get('shared_factor')
shared_library = os.environ.get('shared_library')
factor_type = 'system' if shared_factor and str(shared_library) == '3' else 'space' # 判断是否是空间因子
save_mode = 'both' if factor_type == 'system' else 'parquet'

universe_set = ['index_50', 'index_300', 'index_500', 'risk_universe', 'alpha_universe']  # , 'index_800'
universe_dict = {'sz50': 'index_50', 'hs300': 'index_300', 'zz500': 'index_500', 'risk_universe': 'risk_universe',
                 'alpha_universe': 'alpha_universe'}
index_lookup = {'zz500': '000905.SH', 'sz50': '000016.SH', 'hs300': '000300.SH',
                'wind_alla': '881001.WI'}  # 'zz800': '000906.SH',
benchmark_set = ['zz500', 'sz50', 'hs300']  # ,'wind_alla'] , 'zz800'
prev_len = 21  # for holding period return
corr_len = 60  # style correlation
bd = BasicData()
sd = StockData()
# 获取系统当日日期， 早于晚八点计算前一天的数据，晚于晚八点 计算当天的数据
local_time = time.localtime()
cur_time = time.strftime('%H:%M:%S', local_time)
cur_date = time.strftime('%Y%m%d', local_time)
if cur_time < '20:00:00':
    calc_date = bd.get_trading_day(cur_date, -2)[0]
else:
    calc_date = cur_date

# 测试计算某一天的数据
if os.environ.get("exec_env") != "prd":
    calc_date = '20190329'


def daily_calculation(factor_name):
    factor_id = os.environ.get('factor_id')
    file_path = os.environ.get('file_path')
    now = datetime.now()
    json_msg = {"factorId": factor_id, "calcDate": datetime.strptime(calc_date, '%Y%m%d').strftime("%Y/%m/%d"),
                "createTime": now.strftime("%Y/%m/%d %H:%M:%S"),
                "calcjobStatus": "1"}
    kafka = Kafka_producer('calc')
    kafka.send_json_data(json_msg)
    status = '2'
    try:
        web_calculation(factor_name, calc_date, calc_date,
                        file_path, 'release', mode='save', save_mode=save_mode)
    except Exception as e:
        status = '3'
        raise e
    finally:
        now = datetime.now()
        json_msg = {"factorId": factor_id, "calcDate": datetime.strptime(calc_date, '%Y%m%d').strftime("%Y/%m/%d"),
                    "createTime": now.strftime("%Y/%m/%d %H:%M:%S"),
                    "calcjobStatus": status}
        kafka.send_json_data(json_msg)
        return True


def standard_online_module():
    msg_type = "backtest_trace"
    # start_date = os.environ.get('start_date').replace('/', '')
    start_date = bd.get_trading_day(calc_date, -42)[0]
    result_folder = '/home/appadmin/'
    factor_name = os.environ.get('factor_name')
    universe = os.environ.get('universe')
    benchmark = os.environ.get('benchmark')
    transaction_cost = float(os.environ.get('transaction_cost', 0.0))
    holding_period = int(os.environ.get('holding_period'))
    segment_number = int(os.environ.get('segment_number'))
    median = bool(int(os.environ.get('median')))
    standard = bool(int(os.environ.get('standard')))
    fillna = bool(int(os.environ.get('fillna')))
    seg_by_industry = bool(int(os.environ.get('seg_by_industry')))
    industry_type = os.environ.get('industry_type')
    neutralize = bool(int(os.environ.get('neutralize')))
    ret_stability = bool(int(os.environ.get('ret_stability'))) if os.environ.get('ret_stability') else True
    segment_switch = bool(int(os.environ.get('segment_switch'))) if os.environ.get('segment_switch') else True
    backtest_report_module = backtest_params_parser(segment_switch, seg_by_industry, ret_stability)
    if industry_type != "CITIC_I":
        industry_type = 'CITIC_I'
    scene = os.environ.get('scene')
    kafka = Kafka_producer(scene)

    library_type = 'release'

    daily_calculation(factor_name)

    # start_date, end_date = date_parser(start_date, end_date)
    # 空间因子的每日追踪 对当日及之前24天的时间窗口的因子数据进行回测
    factor_data = get_psfactor_data(start_date, calc_date, factor_name, library_type)

    mes_data = DayFactorBacktest(start_date, calc_date, factor_name, factor_data, result_folder, universe=universe,
                                 benchmark=benchmark, transaction_cost=transaction_cost, holding_period=holding_period,
                                 segment_number=segment_number, median=median, standard=standard, fillna=fillna,
                                 seg_by_industry=seg_by_industry, industry_type=industry_type, msg_type=msg_type,
                                 neutralize=neutralize, module=backtest_report_module)
    kafka.send_json_data(mes_data)
    print("kafka消息发送成功！内容如下：")
    print(mes_data)

    if shared_library == '3' and shared_factor:
        # 系统因子的每日指标计算 入库
        from tquant.strategy.market_factor_backtest.market_factor_entry_daily import backtest_factor_by_params_his
        date_list = bd.get_trading_day(calc_date, -3)
        factor_df = sd.get_factor_characteristic(factor_list=[shared_factor], date_list=date_list, sort=True)
        backtest_factor_by_params_his(factor_df=factor_df, start_date=calc_date, end_date=calc_date, factor_name=shared_factor)


def lowthres_online_module():
    factor_name = os.environ.get('factor_name')
    daily_calculation(factor_name)


if __name__ == "__main__":
    start_time = time.time()
    factor_name = os.environ.get('factor_name')
    if shared_library == '3' and shared_factor:
        kp = Kafka_producer(scene='date_range', topic='HTSC-QUANT-FACTOR-DATASYNC')
        kp.send_data_range(calc_date, calc_date, shared_factor, shared_library, 'start')

    try:
        online_standard = os.environ.get("online_standard")
        if online_standard == "2":
            standard_online_module()
        elif online_standard in ["0", "1"]:
            lowthres_online_module()
        else:
            raise Exception("因子追踪目前支持两套自定义标准，0：拒绝发布  1：每日更新+追踪，2：每日更新，暂不支持{}".format(online_standard))
        task_status = '2'
    except Exception as e:
        task_status = '4'
        record_error_info(factor_name, traceback.format_exc())
        raise e
    finally:
        if shared_library == '3' and shared_factor:
            kp.send_data_range(calc_date, calc_date, shared_factor, shared_library, 'stop', task_status=task_status)
        print("spend time %s" % (time.time() - start_time))
