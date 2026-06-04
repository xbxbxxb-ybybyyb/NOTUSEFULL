from tquant.strategy.day_factor_backtest.backtest.utility import *
from tquant.strategy.day_factor_backtest.backtest.segment_test import segment_test, segment_test_daily, \
    segment_performance_measure
from tquant import BasicData
from tquant import StockData
from tquant.index_data import IndexData
import tquant.strategy.day_factor_backtest.utility.dt as tdt
import os
import pandas as pd
import numpy as np
import pymysql
import datetime as dt
from FactorProvider.storage.db import DML_mysql
from FactorProvider.utils.utils import is_valid_date
from FactorProvider.setEnv import xquantEnv, sysFlag
import threading, time
import json

if sysFlag == "tquant":
    dml = DML_mysql('htsc_dwa_quant')
else:
    raise Exception('数据库连接失败！')
universe_set = {'sz50': 'index_50', 'hs300': 'index_300', 'zz500': 'index_500', 'zz800': 'index_800',
                'zz1000': 'index_1000', 'risk_universe': 'risk_universe',
                'alpha_universe': 'alpha_universe'}  # , 'index_800'
index_lookup = {'zz500': '000905.SH', 'hs300': '000300.SH', 'zz800': '000906.SH', 'zz1000': '000852.SH'}


class MarketFactorBacktest():
    """
    entrydate为最新收盘价日期
    trd_days为entrydate前最近3个交易日,顺序排列分别是 mddate, trd_days_1, entrydate
    回测指标的数据对应日期是mddate
    """

    def __init__(self, entrydate, mddate, middate, backtest_period, factor_name, universe, factor_data, filter=True, transaction_cost=0,
                 holding_period=1, segment_number=10, interest_type='cumprod', stock_close_pd=None, benchmark_price_ps=None):
        self.t1 = time.time()

        if universe not in ['hs300', 'zz500', 'zz800', 'zz1000', 'alpha_universe']:
            raise Exception('股票池只支持hs300、zz500、zz800、zz1000、alpha_universe')

        self.bd = BasicData()
        self.sd = StockData()
        self.ind = IndexData()

        self.mddate = mddate  # 第一个交易日，也是指标对应日期
        self.trd_days_1 = middate  # 第二个交易日
        self.entrydate = entrydate  # 第三个交易日，也是最新收盘价日期
        backtest_period_map = {'3m': 62, '1y': 250, '3y': 750}  # 三个回测周期与天数映射
        self.trd_day_count = backtest_period_map[backtest_period]  # 回测周期天数

        # 通过mddate算出回测区间起始日期
        self.backtest_period = backtest_period
        if self.backtest_period in ['3m', '1y', '3y']:
            self.start_date = self.bd.get_trading_day(self.mddate, -self.trd_day_count)[0]
        else:
            raise Exception("回测区间仅支持 3m/1y/3y")

        self.factor_name = factor_name
        self.universe = universe.lower()
        self.data_dict = {}
        self.filter = filter
        self.transaction_cost = transaction_cost
        self.holding_period = holding_period
        self.benchmark = universe.lower()
        self.segment_number = segment_number
        self.interest_type = interest_type
        self.seg_benchmark = self.benchmark

        # 生成表
        if self.universe == 'alpha_universe':
            self.table_name = 'shared_factor_backtest_statics_{}_{}'.format('universe', self.backtest_period)
        elif self.universe in ['hs300', 'zz500', 'zz800', 'zz1000']:
            self.table_name = 'shared_factor_backtest_statics_{}_{}'.format(self.universe, self.backtest_period)

        print('【系统因子评价】当前参数组合---->股票池：{}，回测周期：{}，因子：{}，交易费用：{}，日期：{}' \
              .format(self.universe, self.backtest_period, self.factor_name,
                      self.transaction_cost, self.mddate))

        # md_dict->计算指标函数所需数据；data_daily->写入数据库数据
        self.md_dict = dict()
        self.data_daily = dict()
        self.data_daily['factor_name'] = self.factor_name
        self.data_daily['mddate'] = self.mddate
        self.data_daily['transaction_cost'] = self.transaction_cost
        self.data_daily['entrydate'] = entrydate


        # 入参factor_data是全是场标的，过滤出股票池

        # 因子值、收盘价、基准
        self.data_dict['factor_pd'] = factor_data
        # 两个交易日数据收盘价，及持有期收益  'close', 'adjfactor', 'close_adj', 'hpr_1_close_shift'
        self.md_dict['hpr_1_close_shift'] = stock_close_pd.shift(-1) / stock_close_pd - 1
        self.data_dict['stock_close_pd'] = stock_close_pd
        self.data_dict['benchmark_price_ps'] = benchmark_price_ps
        print('【系统因子评价】prepare data    ----> OK')

    def get_shared_factor_stats(self, factor_name, transaction_cost, fields):

        if not isinstance(fields, list):
            raise Exception("fields 字段应该为list形式")
        if transaction_cost not in [0, 0.0013, 0.0023]:
            raise Exception("交易成本仅支持 0 ， 0.0013， 0.0023")
        thread = threading.currentThread()
        thread_id = str(thread.ident)
        time_stamp = str(int(round(time.time() * 1000)))
        c_name = "conn_" + time_stamp + "_" + thread_id
        fields_str = ','.join(i for i in fields)
        sql_use = "select {} from {} where mddate>={} and mddate<{} and factor_name='{}' and " \
                  "transaction_cost={}".format(
            fields_str, self.table_name, self.start_date, self.mddate, factor_name, self.transaction_cost)
        df = dml.getAllByPandas(c_name, sql_use)
        dml.close(c_name)
        return df

    def calc_ic_daily(self):
        # IC
        factor_data_daily = self.data_dict['factor_pd'].iloc[[0], :]  # 入参的factor_data是两天，计算当天IC只需1天数据
        holding_period_return_daily = self.md_dict['hpr_1_close_shift'].iloc[[0], :]

        # 计算IC主要函数
        data_dict = dict()
        data_dict['factor_data_daily'] = factor_data_daily
        data_dict['holding_period_return_daily'] = holding_period_return_daily
        data_dict = align_data_inner(data_dict)
        ic_daily = calc_factor_ic(data_dict['factor_data_daily'], data_dict['holding_period_return_daily'],
                                  ic_type='original')
        self.data_daily['ic'] = ic_daily[0]

        # 计算IC_mean,ICIR
        ic_his = self.get_shared_factor_stats(factor_name=self.factor_name,
                                              transaction_cost=self.transaction_cost, fields=['ic'])
        ic_daily = pd.DataFrame(ic_daily, columns=['ic'])
        ic_s = ic_his.append(ic_daily, ignore_index=True)
        # 数据库没数据时，ic_mean/ir赋空值，只有补历史开始时会用到，常态化运行可考虑删除
        if len(ic_s) < self.trd_day_count:
            ic_mean = ir = np.nan
        else:
            ic_mean = ic_s.mean().values[0]
            ic_std = ic_s.std().values[0]
            ir = ic_mean / ic_std if ic_std != 0 else np.nan
        self.data_daily['ic_mean'] = ic_mean
        self.data_daily['ir'] = ir
        print('【系统因子评价】IC、IC_mean、IR ----> OK')

    def seg_test(self):
        """
        计算因子值mddate的分层收益
        """
        # 计算分层收益
        segment_test_res = segment_test(factor_pd=self.data_dict['factor_pd'],
                                        stock_close_pd=self.data_dict['stock_close_pd'],
                                        benchmark_price_ps=self.data_dict['benchmark_price_ps'], holding_period=1,
                                        segment_num=10, handle_insufficient=False, handle_return_outlier=False,
                                        return_bucket_ic=False,
                                        transaction_cost=self.transaction_cost, max_quantile='Q1')
        if not self.transaction_cost:
            segment_test_res = segment_test_res[0].iloc[[0], :]
        else:
            segment_test_res = segment_test_res[1].iloc[[0], :]

        segment_test_res = segment_test_res.round(8)
        segment_test_res = segment_test_res.astype('str').values[0].tolist()
        segment_test_res = ','.join(segment_test_res)
        self.data_daily['seg_excessret'] = str(segment_test_res)

        print('【系统因子评价】seg_excessret   ----> OK')

    def seg_performance_measure(self):
        """
        计算年化收益、年化波动率、夏普比率、最大回撤，胜率
        """
        # 整理入参数据
        seg_return = self.get_shared_factor_stats(factor_name=self.factor_name,
                                                  transaction_cost=self.transaction_cost,
                                                  fields=['mddate', 'seg_excessret'])
        segment_test_res_end_date = pd.Series([self.mddate, self.data_daily['seg_excessret']],
                                              index=['mddate', 'seg_excessret'])
        seg_return = seg_return.append(segment_test_res_end_date, ignore_index=True)

        # 数据库没数据时，excessret_std/sharpe/mdd/hit_rate赋空值，只有补历史开始时会用到，常态化运行可考虑删除
        if len(seg_return) < self.trd_day_count:
            seg_performance_dict = {'excessret': segment_test_res_end_date['seg_excessret'].split(',')[-1],
                                    'excessret_std': np.nan, 'sharpe': np.nan, 'mdd': np.nan, 'hit_rate': np.nan}
        else:
            seg_return.set_index('mddate', inplace=True)
            seg_return_df = pd.DataFrame()
            for index, seg_return_daily in seg_return.iterrows():
                index = dt.datetime.strptime(index, '%Y%m%d')
                seg_return_daily = seg_return_daily['seg_excessret'].split(',')
                seg_return_daily_ser = pd.Series(seg_return_daily, name=index)
                seg_return_df = seg_return_df.append(seg_return_daily_ser)
            seg_return_df = seg_return_df.astype('float')
            seg_return_df.columns = ['Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'Q6', 'Q7', 'Q8', 'Q9', 'Q10', 'Index', 'Q1-Index']

            # 计算指标主要函数
            seg_return_stat = segment_performance_measure(seg_return_df, interest_type='cumprod')
            seg_return_stat_market = seg_return_stat[['Return(Ann.)', 'Vol(Ann.)', 'Sharpe', 'MDD', 'HitRate']]
            seg_return_stat_market = seg_return_stat_market.rename(
                columns={'Return(Ann.)': 'excessret', 'Vol(Ann.)': 'excessret_std',
                         'Sharpe': 'sharpe', 'MDD': 'mdd', 'HitRate': 'hit_rate'})
            seg_return_stat_market_max = seg_return_stat_market.loc[['Q1-Index'], :]
            seg_performance_dict = seg_return_stat_market_max.to_dict(orient='list')
            seg_performance_dict = {k: seg_performance_dict[k][0] for k in seg_performance_dict}
        self.data_daily.update(seg_performance_dict)

        print('【系统因子评价】excessret、excessret_std、sharpe、mdd、hit_rate ----> OK')

    def data_to_mysql(self):
        # 数据入库
        thread = threading.currentThread()
        thread_id = str(thread.ident)
        time_stamp = str(int(round(time.time() * 1000)))
        c_name = "conn_" + time_stamp + "_" + thread_id  # 链接名

        df = pd.DataFrame(columns=['factor_name', 'mddate', 'entrydate', 'transaction_cost', 'ic', 'ic_mean', 'ir', \
                                   'excessret', 'excessret_std', 'sharpe', 'mdd', 'hit_rate', 'seg_excessret'])
        df_ = pd.DataFrame(self.data_daily, index=[0])
        df = df.append(df_, sort=False)
        df.replace([np.inf, -np.inf], 0.0, inplace=True)

        df = df.round(4)
        df = df.where(df.notnull(), None)
        columns = df.columns.tolist()
        values = list(df.itertuples(name=False, index=False))

        param = ",".join([i for i in columns])
        values_insert = ','.join(['%s'] * len(columns))
        values_update = ','.join([str(i) + "=values(" + str(i) + ")" for i in columns])

        sql = "insert into {}({}) values ({}) on duplicate key update {}".format(self.table_name, param, values_insert,
                                                                                 values_update)

        try:
            dml.insertMany(c_name, sql, values)
            dml.commit(c_name)
        except Exception as e:
            dml.rollback(c_name)
            raise Exception('数据插入失败 --> 股票池：{}，回测周期：{}，因子：{}，交易费用：{}，日期：{}，异常：{}' \
                            .format(self.universe, self.backtest_period, self.factor_name, self.transaction_cost,
                                    self.mddate, e))
        finally:
            dml.close(c_name)
            self.t2 = time.time()
            print('entry over, time: {}s'.format(round(self.t2 - self.t1, 1)))
            print('==============================================================================================')


if __name__ == "__main__":

    # 补数起止日期
    s_date = '20150101'
    e_date = '20150331'
    from tquant import BasicData

    bd = BasicData()
    trd_days = bd.get_trading_day(s_date, e_date)

    # 入参
    factor_name = "ev2"

    for universe in ['hs300']:  # in ['hs300', 'zz500', 'zz800', 'zz1000', 'alpha_universe']:
        for backtest_period in ['3m']:  # in ['3m', '1y', '3y']:

            for date in trd_days:

                for transaction_cost in [0, 0.0013, 0.0023]:
                    # factor_data = ?????? # 待传入

                    # ---测试用区间上边界,计算因子值，可删-----------------------------------------------------------------------------------------
                    # 获取股票池标的，过滤停牌和涨跌停

                    from tquant import StockData
                    from tquant import IndexData

                    ind = IndexData()
                    sd = StockData()
                    end_date = bd.get_trading_day(date, -3)[0]  # 测试用date可能不是交易日
                    days_factor_data = bd.get_trading_day(date, -3)[:2]

                    # 因子值传参永远是全市场
                    stock_list = sd.get_plate_info('MARKET', end_date, 'ALLA_HIS')['stock'].tolist()
                    factor_data = sd.get_factor_valuation_metrics(stock_list, days_factor_data, factor_name)
                    factor_data.index.names = ['MDDate', 'HTSCSecurityID']
                    # ---测试用区间下边界,计算因子值，可删-----------------------------------------------------------------------------------------

                    instance = MarketFactorBacktest(date, backtest_period, factor_name, universe, factor_data,
                                                    transaction_cost=transaction_cost,
                                                    holding_period=1, segment_number=10, interest_type='cumprod',
                                                    filter=True)

                    # 计算函数
                    instance.calc_ic_daily()
                    instance.seg_test()
                    instance.seg_performance_measure()
                    instance.data_to_mysql()
