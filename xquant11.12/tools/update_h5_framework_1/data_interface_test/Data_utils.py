# _*_ coding:utf-8 _*_

from db import OPMysql,DML_mysql
import pandas as pd
import datetime as dt
from log import Log
import numpy as np
import re
import cx_Oracle
logger = Log("Data_utils")

class data_interface:

    def __init__(self,conn):
        self.conn = conn

    def to_df(self,security,data):
        """
        数据转换为DataFrame,security有一支股票则返回列索引为行情因子，行索引为[datetime.datetime]
        security大于一支股票则返回列索引为股票代码，行索引为[行情因子，datetime.datetime]的MultiIndex DataFrame
        :param security: 股票代码
        :param data: 从数据库取得的数据，结构为list
        :return: DataFrame
        """
        if len(security) == 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            df[data[0][0]] = df[data[0][0]].apply(pd.to_datetime)
            # data[0][0] 为tradingdaydata[0][1]为tradingcode
            df.set_index(data[0][0],inplace=True)
            df.drop(data[0][1],axis=1,inplace=True)
        else:
            df_s = pd.DataFrame(data[1:], columns=data[0])
            df_s[data[0][0]] = df_s[data[0][0]].apply(pd.to_datetime)
            df_s.set_index(list(data[0][:2]), inplace=True)
            df = pd.DataFrame()
            for col in df_s.columns:
                df_fac = df_s[col].unstack()
                df_fac['factor'] = col
                df = df.append(df_fac)
            df.reset_index(inplace=True)
            df.set_index(['factor', data[0][0]], inplace=True)
        return df

    def trade_minute(self,time):
        # time 分钟时间 如：Timestamp('2018-01-19 11:29:00')
        # 股市交易时间为每周一到周五上午时段9:30-11:30，下午时段13:00-15:00
        str_date = dt.datetime.strftime(time, '%Y%m%d')
        am_start = str_date + '093100'
        am_start = pd.Timestamp(am_start)
        am_end = str_date + '113000'
        am_end = pd.Timestamp(am_end)
        pm_start = str_date + '130000'
        pm_start = pd.Timestamp(pm_start)
        pm_end = str_date + '150000'
        pm_end = pd.Timestamp(pm_end)
        if time > pm_end:
            time = pm_end
        elif time < am_start:
            # time 在当天交易开始前，则默认其时间为上个交易日的闭市时间15:00
            time = pm_end - dt.timedelta(1)
        elif time > am_end and time < pm_start:
            time = am_end
        return time

    def get_pre_trade_minute(self,time):
        date = dt.datetime.strftime(time, '%Y%m%d')
        if self.Judge_Tradingday(date) == 'No_tradingday':
            date = self.get_Lasttradingday(date)
            time = pd.Timestamp(str(date) + '150000')
        return time

    def get_minute_time(self,time, freq, count):
        """
        获取 time 之前几个 freq 的分钟级时间
        :param time: 分钟时间 如：Timestamp('2018-01-19 11:29:00')
        :param freq: 单位时间长度，1m 表示长度为1分钟
        :param count: 数量，正整数
        :return:
        """
        jd = False
        time1 = self.trade_minute(time)
        if time1 != time:
            jd = True
        pre_trade_minute = self.get_pre_trade_minute(time1)
        print(pre_trade_minute)
        if pre_trade_minute != time1:
            jd = True
        if freq[-1] != 'm' and int(freq[:-1]) > 0:
            raise Exception("Support only minutes and freq > 0!")
        t = abs(int(freq[:-1])) * abs(count)
        if jd:
            minute_datas = [pre_trade_minute]
            t = t - 1
        else:
            minute_datas = []
        for i in range(t):
            pre_trade_minute = pre_trade_minute - dt.timedelta(minutes=1)
            pre_trade_minute = self.trade_minute(pre_trade_minute)
            pre_trade_minute = self.get_pre_trade_minute(pre_trade_minute)
            minute_datas.append(pre_trade_minute)
        print(minute_datas)
        start_date = minute_datas[-1]
        return start_date

    def get_Lasttradingday(self,date):
        """
        获取上一个交易日期
        :param date: 查询日期
        :param sql_config:oracle 配置项
        :return:
        """
        sql_use = "select lasttradingday from quant_data.qd_tradingdays where tradingday =%s" % str(date)
        lasttradingday_ = self.sql_parser(self.queryUserTableData(sql_use))
        lasttradingday = int(lasttradingday_.iloc[0][0])
        return lasttradingday

    def Judge_Tradingday(self,date):
        sql_tradingday = "select istradingday from quant_data.qd_tradingdays where tradingday = %s" % date
        is_tradingday = self.sql_parser(self.queryUserTableData(sql_tradingday))
        if is_tradingday.empty:
            return "No_tradingday"
        else:
            is_trading = int(is_tradingday.iloc[0][0])
        if is_trading:
            return "Tradingday"
        else:
            return "No_tradingday"

    def queryUserTableData(self,sql_use):
        # logger.info("Create connect to Oracle...")
        conn = cx_Oracle.connect("center_read/Htsc_Htzx@168.9.2.43/qdb04", encoding="UTF-8", nencoding="UTF-8")
        cur = conn.cursor()
        # logger.info("Execute the sql...")
        cur.execute(sql_use)
        index = cur.description
        column_name = []
        for i in index:
            column_name.append(i[0])
        result = []
        result.append(column_name)
        for res in cur.fetchall():
            result.append(list(res))
        # logger.info("Close the cursor and connect...")
        cur.close()
        conn.close()
        return str(result)

    def sql_parser(self,data):
        NaN = np.nan
        try:
            _data = eval(data)
        except SyntaxError as _exp:
            print(_exp)
            if 'triple-quoted string' in _exp.msg:
                data = re.sub(r"'{3,}", '', data)
                data = re.sub(r'"{3,}', '', data)
                _data = eval(data)
            else:
                raise SyntaxError
        try:
            res = pd.DataFrame(_data[1:], columns=_data[0])
        except OverflowError:
            res = pd.DataFrame(_data, columns=_data[0])
            res = res.drop([0], axis=0).reset_index(drop=True)
        return res

    def get_prev_sdate(self,sdate, day_num):
        print("从Oracle读取交易日数据：",dt.datetime.now())
        sql_use = "select * from (select a.* from quant_data.qd_tradingdays a where tradingday <= %s and istradingday=1 order by tradingday desc) where rownum <= %d" % (
            str(sdate), day_num)
        df = self.sql_parser(self.queryUserTableData(sql_use))
        prev_sdate = list(df.tail(1).loc[:, 'TRADINGDAY'])[0]
        print("根据count获取start_date:",dt.datetime.now())
        return prev_sdate

    def get_prices(self,security, start_date=None, end_date=None, frequency='daily',
                   fields=None, price_type='pre', count=None):
        """获取历史数据，可查询多个标的多个数据字段，返回数据格式为 DataFrame"""
        print("开始时间：",dt.datetime.now())
        if (start_date and count):
            raise Exception("It can only and have to select one parameter start_date or count !")
        elif not start_date and not count:
            if frequency == 'daily' or frequency[-1] == 'd':
                start_date = '20150101'
            else:
                start_date = '20150101000000'
        elif not start_date and count:
            if count > 0 and count < 1:
                count = int(count + 1)
            else:
                count = int(count)
            edate = pd.Timestamp(str(end_date))
            if frequency == 'daily':
                start_date = self.get_prev_sdate(end_date,count)
                # sdate = edate - dt.timedelta(count - 1)
                # start_date = dt.datetime.strftime(sdate, "%Y%m%d")
            elif frequency[-1] == 'd' and int(frequency[:-1]) > 0:
                start_date = self.get_prev_sdate(end_date, count * int(frequency[:-1]))
                # sdate = edate - int(frequency[:-1]) * dt.timedelta(count - 1)
                # start_date = dt.datetime.strftime(sdate, "%Y%m%d")
            elif (frequency[-1] == 'm' and int(frequency[:-1]) > 0) or frequency == 'minute':
                # 股市交易时间为每周一到周五上午时段9:30-11:30，下午时段13:00-15:00
                sdate = pd.Timestamp(start_date)
                if frequency == 'minute':
                    start_date = self.get_minute_time(sdate,'1m',count)
                else:
                    start_date = self.get_minute_time(sdate,frequency,count)
            else:
                raise Exception("Frequency param value should be daily , Xd ,minute, Xm . X is positive integer!")
        if end_date is None and (frequency == 'daily' or frequency[-1] == 'd'):
            end_date = '20151231'
        elif end_date is None and (frequency == 'minute' or frequency[-1] == 'm'):
            end_date = pd.Timestamp('20151231000000')
        elif end_date and (frequency == 'minute' or frequency[-1] == 'm'):
            end_date = pd.Timestamp(end_date)
        if not isinstance(security, tuple):
            security = tuple(security)
        if not fields:
            fields = ['open', 'close', 'high', 'low', 'volume'] # 'money' 表内无此字段
        elif not isinstance(fields, list):
            fields = [fields]
        if frequency[-1] == 'd' and int(frequency[:-1]) > 1:
            available_fields = []
            default_fields = ['open', 'close', 'high', 'low', 'volume'] # 'money' 表内无此字段
            for i in fields:
                if i in default_fields:
                    available_fields.append(i)
            if not available_fields:
                raise Exception("Frequency greater than 1d or 1m ,factor not in default factor_list!")
        factors = ''
        for fac in fields:
            factors += fac + ','
        if frequency == 'daily' or frequency[-1] == 'd':
            if len(security) == 1:
                # 约定 sql语句前两个字段为tradingday,tradingcode
                sql = "select tradingday,tradingcode,%s from factor_d_marketindex where tradingday >= %d and tradingday <= %d " \
                      "and tradingcode = '%s'" % (factors[:-1], int(start_date), int(end_date), security[0])
            else:
                sql = "select tradingday,tradingcode,%s from factor_d_marketindex where tradingday >= %d and tradingday <= %d " \
                      "and tradingcode in %s" % (factors[:-1],int(start_date),int(end_date),str(security))
            logger.info(sql)
            print("从数据库读取数据：", dt.datetime.now())
            dml = DML_mysql(self.conn)
            data = dml.getAll(sql)
            print("成功获取数据数据：", dt.datetime.now())
            df = self.to_df(security,data)
            print("转换为DataFrame：", dt.datetime.now())
        else:
            # 分钟级的行情数据暂无
            pass
        return df













