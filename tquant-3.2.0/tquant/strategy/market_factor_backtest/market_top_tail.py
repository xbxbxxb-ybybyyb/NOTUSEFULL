import pandas as pd
from tquant import StockData
from tquant import BasicData
from FactorProvider.storage.db import DML_mysql
from FactorProvider.utils.utils import is_valid_date
from FactorProvider.setEnv import xquantEnv, sysFlag
import threading, time

if sysFlag == "tquant":
    dml = DML_mysql('htsc_dwa_quant')
else:
    raise Exception('数据库连接失败！')

sd = StockData()
bd = BasicData()


def data_to_mysql(df, factor_name, mddate):
    # 数据入库
    thread = threading.currentThread()
    thread_id = str(thread.ident)
    time_stamp = str(int(round(time.time() * 1000)))
    c_name = "conn_" + time_stamp + "_" + thread_id  # 链接名

    columns = df.columns.tolist()
    values = list(df.itertuples(name=False, index=False))

    param = ",".join([i for i in columns])
    values_insert = ','.join(['%s'] * len(columns))
    values_update = ','.join([str(i) + "=values(" + str(i) + ")" for i in columns])

    sql = "insert into shared_factor_sec_rank({}) values ({}) on duplicate key update {}".format(param, values_insert,
                                                                                                 values_update)

    try:
        dml.insertMany(c_name, sql, values)
        dml.commit(c_name)
        print('数据插入成功! 因子：{}，日期：{}'.format(factor_name, mddate))
    except Exception as e:
        dml.rollback(c_name)
        raise Exception('数据插入失败! 因子：{}，日期：{}'.format(factor_name, mddate))
    finally:
        dml.close(c_name)


def top_tail_factors(mddate, factor_name, factor_data):
    top_tail = {}

    # top20顺序：top1,top2...
    factor_data.sort_values(factor_name, ascending=False, inplace=True)
    factor_data.dropna(0, inplace=True)
    top = factor_data.head(20).index.get_level_values(level=1).tolist()

    # tail20顺序：tail1,tail2...
    tail = factor_data.tail(20).index.get_level_values(level=1).tolist()
    tail.reverse()

    top_tail['top20'] = ','.join(top)
    top_tail['tail20'] = ','.join(tail)

    data_to_db = pd.DataFrame({
        'factor_name': [factor_name],
        'mddate': [mddate],
        'top20': top_tail['top20'],
        'tail20': top_tail['tail20']
    })

    data_to_mysql(data_to_db, factor_name, mddate)


if __name__ == "__main__":

    # 补数起止日期
    s_date = '20150101'
    e_date = '20150630'
    trd_days = bd.get_trading_day(s_date, e_date)

    for mddate in trd_days:
        # factor_data = ?????? # 待传入,一天的因子值

        # ---测试用区间上边界,计算因子值，可删-------------------------------------------------------------------------------
        # 获取股票池标的，过滤停牌和涨跌停
        stock_list = sd.get_plate_info('MARKET', mddate, 'ALLA')['stock'].tolist()
        stock_list = sd.stock_filter(stock_list, mddate, filter_type='STSPEND')['stock'].tolist()  # 过滤STPT + 停牌
        factor_data = sd.get_factor_valuation_metrics(stock_list, mddate, 'ev2')
        # ---测试用区间下边界,计算因子值，可删-------------------------------------------------------------------------------

        top_tail_factors(mddate, 'ev2', factor_data)
