import os
#os.environ["DSWMAP_username"] = "013150"

import calendar
from tquant.strategy.day_factor_backtest.backtest.factor_test import SingleFactorTest
from tquant.strategy.day_factor_backtest.backtest.utility import *
from tquant.strategy.day_factor_backtest.backtest.report_generator import generate_pdf
from tquant import BasicData
from FactorProvider.conf.LoadConf import SendFile

class FactorBacktest(SingleFactorTest):
    """
    Algorithm group single daily factor backtest wrapper
    """

    def run_backtest(self, factor_data, name='test_factor', result_folder='test_factor', factor_data_num=0,msg_type='backtest_factor'):
        """"""
        # self.load_factor(factor_data=factor_data, name=name)
        # self.shoot(result_folder=result_folder)
        # if msg_type == "backtest_trace":
        #     return
        #
        # #### new metrics
        # self.algo_shoot()
        # import pickle
        # pickle.dump(self.output_dict, open('output_dict.pkl', 'wb'))
        self.excel_name = 'backtest.xlsx'
        self.pickle_name = 'factor.pkl'
        self.day_ret = ''
        self.output_dict = pd.read_pickle('output_dict.pkl')
        self.generate_report(factor_data, factor_data_num)

    def generate_report(self, factor_data, factor_data_num):
        excel_saver(self.output_dict, self.excel_name)
        save_pickle(self.output_dict, self.pickle_name)

        pprint('Generating pdf report')
        # calculate correlation with existing factors
        factor_data.index = map(lambda x: x.strftime('%Y%m%d'), factor_data.index)

        self.pdf_name = generate_pdf(self.pickle_name, factor_data_num=factor_data_num)
        pprint('* Finished - %s *' % (self.name))


def DayFactorBacktest(start_date, end_date, factor_name, factor_data, result_folder='./',
                      universe='alpha_universe', benchmark='alpha_universe', transaction_cost=0, holding_period=1,
                      segment_number=10, median=True, standard=True, fillna=True, seg_by_industry=True,
                      industry_type='CITIC_I', msg_type='backtest_factor',valid_rat=0.8):
    # msg_type 根据回测模式不同有以下参数决定是否返回及返回哪些回测指标的信息：web_release版本: 'backtest_system', web_develop版本: 'backtest_user',
    # web_tiny_release版本: 'backtest_trace', 默认直接调用不返回kafka消息：'backtest_factor'
    bd = BasicData()
    try:
        dt.datetime.strptime(start_date, '%Y/%m')
        origin_start_date = start_date.split('/')
        start_date = '{}{}{}'.format(origin_start_date[0], origin_start_date[1], '01')
    except:
        start_date = start_date
    try:
        dt.datetime.strptime(end_date, '%Y/%m')
        origin_end_date = end_date.split('/')
        last_day_of_month = str(calendar.monthrange(int(origin_end_date[0]), int(origin_end_date[1]))[1])
        end_date = '{}{}{}'.format(origin_end_date[0], origin_end_date[1], last_day_of_month)
    except:
        end_date = end_date
    if not isinstance(factor_data, pd.DataFrame):
        raise Exception("factor_data 为行索引为pd.DatetimeIndex，列名为标的代码的DataFrame！")
    factor_not_nan = factor_data.dropna(how='all')
    factor_data_num = len(factor_not_nan)
    date_list = bd.get_trading_day(start_date, end_date)
    if factor_data_num / len(date_list) < valid_rat:
        raise Exception("所选的日期区间[{0}:{1}]超过{2}".format(start_date, end_date, str(round((1-valid_rat), 2)*100)+"%的日期因子值全为nan!"))
    if factor_data_num < 42:
        raise Exception("有效数据的日期为 {0} 天，所选的日期区间中至少42天必须有因子值!".format(factor_data_num))
    instance = FactorBacktest(start_date, end_date, universe=universe, holding_period=holding_period,
                              benchmark=benchmark, transaction_cost=transaction_cost, segment_number=segment_number,
                              seg_by_industry=seg_by_industry, interest_type='cumprod', ret_price='vwap',
                              ret_shift=False, ic_type='original', median=median, standard=standard, fillna=fillna,
                              industry_type=industry_type)
    instance.run_backtest(factor_data, name=factor_name, result_folder=result_folder,factor_data_num=factor_data_num,msg_type=msg_type)
    if instance.day_ret:
        day_ret = round(instance.day_ret*100, 3)
    else:
        day_ret = instance.day_ret

    if msg_type in ["backtest_user", "backtest_system", "backtest_trace"]:
        mes_data = {"msgType": msg_type,
                    "factorName": factor_name,
                    "factorId": os.environ.get('factor_id'),
                    "ic": instance.IC,
                    "ir": instance.IR,
                    "dayRet": day_ret,
                    "weekRet": round(instance.week_ret*100, 3),
                    "monthRet": round(instance.month_ret*100, 3),
                    "dayBenchmarkRet": round(instance.day_benchmark_ret*100, 3),
                    "weekBenchmarkRet": round(instance.week_benchmark_ret*100, 3),
                    "monthBenchmarkRet": round(instance.month_benchmark_ret*100, 3),
                    "universe": universe,
                    "startDate": start_date,
                    "endDate": end_date,
                    "segmentNumber": segment_number,
                    "transactionCost": transaction_cost,
                    "holdingPeriod": holding_period,
                    "benchmark": benchmark,
                    "uuid": os.environ.get('uuid'),
                    "calcDate": "{}_{}".format(start_date, end_date),
                    "createTime": time.strftime('%Y-%m-%d %H:%M:%S')}
        if msg_type in ["backtest_user", "backtest_system"]:
            file_name = instance.pdf_name.split("/")[-1]
            pdfurl, fileName = SendFile(instance.pdf_name, file_name, os.environ["exec_env"])
            mes_data["pdfurl"] = pdfurl
            mes_data["fileName"] = fileName
        return mes_data


if __name__ == '__main__':
    t0 = time.time()
    msg_type = "backtest_user"

    start_date = '20190101'
    end_date = '20200630'
    factor_name = 'ZaoYinTrader'
    result_folder = './'
    # 需要取因子数据
    factor_data = pd.read_pickle('ZaoYinTrader.pkl')
    factor_data = factor_data[
        (factor_data.index >= pd.Timestamp(str(start_date))) & (factor_data.index <= pd.Timestamp(str(end_date)))]
    DayFactorBacktest(start_date, end_date, factor_name, factor_data, result_folder)

    print("spend time %s" % (time.time() - t0))
