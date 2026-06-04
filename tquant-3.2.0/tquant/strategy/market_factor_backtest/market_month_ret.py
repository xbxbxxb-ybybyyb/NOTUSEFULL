from tquant.strategy.day_factor_backtest.backtest.utility import *
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

if sysFlag == "tquant":
    dml = DML_mysql('htsc_dwa_quant')
else:
    raise Exception('数据库连接失败！')


class Month_return:
    def __init__(self, factor_name, mddate, universe, filter=True, transaction_cost=0):
        self.factor_name = factor_name
        self.mddate = mddate
        self.mdmonth = mddate[:6]
        self.universe = universe.lower()
        self.filter = filter
        self.transaction_cost = transaction_cost
        self.benchmark = universe.lower()
        self.table_name = 'shared_factor_monthly_ret'

        self.bd = BasicData()

        if universe not in ['hs300', 'zz500', 'zz800', 'zz1000', 'alpha_universe']:
            raise Exception('股票池只支持hs300、zz500、zz800、zz1000、alpha_universe')
        if transaction_cost not in [0, 0.0013, 0.0023]:
            raise Exception("交易成本仅支持 0 ， 0.0013， 0.0023")

        first_day_this_month = dt.datetime.strptime(self.mdmonth, '%Y%m')
        first_day_next_month = dt.datetime(first_day_this_month.year + (first_day_this_month.month == 12),
                                           first_day_this_month.month == 12 or first_day_this_month.month + 1, 1)
        last_day_this_month = first_day_next_month + dt.timedelta(days=-1)
        self.month_start_date = first_day_this_month.strftime('%Y%m%d')
        self.month_end_date = last_day_this_month.strftime('%Y%m%d')
        self.start_date = self.bd.get_trading_day(self.month_start_date, self.month_end_date)[0]
        self.end_date = self.bd.get_trading_day(self.month_start_date, self.month_end_date)[-1]

    def get_shared_factor_stats(self, factor_name, transaction_cost, fields):

        if self.universe == 'alpha_universe':
            t_name = 'shared_factor_backtest_statics_{}_{}'.format('universe', '3m')
        elif self.universe in ['hs300', 'zz500', 'zz800', 'zz1000']:
            t_name = 'shared_factor_backtest_statics_{}_{}'.format(self.universe, '3m')
        if not isinstance(fields, list):
            raise Exception("fields 字段应该为list形式")

        thread = threading.currentThread()
        thread_id = str(thread.ident)
        time_stamp = str(int(round(time.time() * 1000)))
        c_name = "conn_" + time_stamp + "_" + thread_id
        fields_str = ','.join(i for i in fields)
        sql_use = "select {} from {} where mddate>={} and mddate<={} and factor_name='{}' and " \
                  "transaction_cost={}".format(
            fields_str, t_name, self.start_date, self.end_date, factor_name, self.transaction_cost)
        seg_return = dml.getAllByPandas(c_name, sql_use)
        dml.close(c_name)
        if len(seg_return) == 0:
            print(sql_use)
            raise Exception('无分层收益数据，需先计算分层收益')
        seg_return.set_index('mddate', inplace=True)

        return seg_return

    def month_ret(self):
        # 计算月度收益
        seg_return = self.get_shared_factor_stats(self.factor_name, self.transaction_cost,
                                                  fields=['mddate', 'seg_excessret'])
        seg_return_df = pd.DataFrame()
        for index, seg_return_daily in seg_return.iterrows():
            index = dt.datetime.strptime(index, '%Y%m%d')
            seg_return_daily = seg_return_daily['seg_excessret'].split(',')
            seg_return_daily_ser = pd.Series(seg_return_daily, name=index)
            seg_return_df = seg_return_df.append(seg_return_daily_ser)
        seg_return_df = seg_return_df.astype('float')
        seg_return_df.columns = ['Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'Q6', 'Q7', 'Q8', 'Q9', 'Q10', 'Index', 'Q1-Index']
        seg_return_df = seg_return_df['Q1-Index']

        seg_return_df = seg_return_df * 100  # 单位转换成 %
        # 日年化收益求和，与因子评价默认求和一致
        monthly_ret = seg_return_df.sum()
        self.monthly_ret = round(monthly_ret, 8)
        print(
            '月份：{}, 股票池：{}, 费用：{}, 月收益：{}'.format(self.mdmonth, self.universe, self.transaction_cost, self.monthly_ret))

    def data_to_mysql(self):

        thread = threading.currentThread()
        thread_id = str(thread.ident)
        time_stamp = str(int(round(time.time() * 1000)))
        c_name = "conn_" + time_stamp + "_" + thread_id  # 链接名

        if self.universe == 'alpha_universe':
            df = pd.DataFrame({
                'factor_name': self.factor_name,
                'mdmonth': self.mdmonth,
                'universe': 'universe',
                'filter': self.filter,
                'transaction_cost': self.transaction_cost,
                'monthly_ret': self.monthly_ret
            }, index=[0])

        else:
            df = pd.DataFrame({
                'factor_name': self.factor_name,
                'mdmonth': self.mdmonth,
                'universe': self.universe,
                'filter': self.filter,
                'transaction_cost': self.transaction_cost,
                'monthly_ret': self.monthly_ret
            }, index=[0])

        df.replace([np.inf, -np.inf], 0.0, inplace=True)
        df = df.round(8)
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
            print('数据插入成功--> 因子：{}，日期：{}，股票池：{}，交易费用：{}' \
                  .format(self.factor_name, self.mdmonth, self.universe, self.transaction_cost))
        except Exception as e:
            dml.rollback(c_name)
            raise Exception('数据插入失败 --> 因子：{}，日期：{}，股票池：{}，交易费用：{}，异常：{}' \
                            .format(self.factor_name, self.mdmonth, self.universe, self.transaction_cost, e))
        finally:
            dml.close(c_name)


if __name__ == "__main__":
    factor_name = "alpha8"
    start_date = '20200630'
    end_date = '20201203'
    filter = True

    bd = BasicData()
    trd_days = bd.get_trading_day(start_date, end_date)
    for universe in ['hs300']:  # ['hs300', 'zz500', 'zz800', 'zz1000', 'alpha_universe']
        for mddate in trd_days:
            for transaction_cost in [0]:  # [0, 0.0013, 0.0023]:
                instance = Month_return(factor_name, mddate, universe, filter=filter, transaction_cost=transaction_cost)
                instance.month_ret()
                instance.data_to_mysql()

