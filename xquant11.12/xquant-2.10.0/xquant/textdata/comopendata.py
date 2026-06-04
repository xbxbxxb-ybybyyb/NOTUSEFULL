from xquant.xqutils.utils import statisticLog
from xquant.factordata.db import DML_mysql
import time
import threading
import datetime as dt
import numpy as np
import pandas as pd


class ComOpenData():
    def __init__(self):
        self.dml_xquant_wind = DML_mysql('xquant_wind')

    def getLawsuitByStock(self,stockcode, year_list=[]):
        """
        :param stockcode:
        :param year_list:
        :return:
        """
        if not isinstance(stockcode,str):
            raise Exception("stockcode 请传入单只股票（str类型）！")
        if not isinstance(year_list,list):
            raise Exception("date_list 请传入list！")
        if stockcode.endswith(".SZ") or stockcode.endswith(".SH"):
            stockcode = stockcode.split(".")[0]
        if not year_list:
            sql = "select (case when EXCHANGECODE=101 then concat(a.tradingcode,'.SH') " \
                  "when EXCHANGECODE=105 then concat(a.tradingcode,'.SZ') end) as tradingcode," \
                  "max(c.CHINAME) as comname,max(title) as title ,max(casename) as casename ," \
                  "max(docnumber) as docnumber,b.caseid ," \
                  "min(date_format(publishtime,'%Y-%m-%d %H:%i:%s') )as publishtime " \
                  "from TOPIC_ENT_LAWSUITCOMP b inner join PUB_SECURITIESMAIN a " \
                  "on a.comcode=b.comcode inner join pub_companymain c on " \
                  "b.comcode=c.COMCODE where b.isvalid=1 " \
                  "and a.tradingcode='{0}' and a.SECUCATEGORY='A股' and " \
                  "a.EXCHANGECODE in (101,105) group by a.tradingcode,b.caseid".format(stockcode)
        else:
            sql = "select (case when EXCHANGECODE=101 then concat(a.tradingcode,'.SH') " \
                  "when EXCHANGECODE=105 then concat(a.tradingcode,'.SZ') end) as tradingcode," \
                  "max(c.CHINAME) as comname,max(title) as title ,max(casename) as casename ," \
                  "max(docnumber) as docnumber,b.caseid ," \
                  "min(date_format(publishtime,'%Y-%m-%d %H:%i:%s') )as publishtime " \
                  "from TOPIC_ENT_LAWSUITCOMP b inner join PUB_SECURITIESMAIN a " \
                  "on a.comcode=b.comcode inner join pub_companymain c on " \
                  "b.comcode=c.COMCODE where b.isvalid=1 " \
                  "and a.tradingcode='{0}' and a.SECUCATEGORY='A股' and " \
                  "a.EXCHANGECODE in (101,105) and date_format(publishtime,'%Y') in (".format(stockcode)

            for i in year_list:
                try:
                    int(i)
                except:
                    raise Exception("{%s}年份格式不正确！请重新输入！"%i)
                sql += "'%s'," % i
            sql = sql[:-1] +") group by a.tradingcode,b.caseid"
        c_name = str(int(time.time())) + str(threading.get_ident())
        df = self.dml_xquant_wind.getAllByPandas(c_name, sql)
        df[df.isnull()] = np.NAN
        df.replace([''], [np.nan], inplace=True)
        self.dml_xquant_wind.close(c_name)
        return df

    def getLawsuitByTime(self,beginTime, endTime):
        """
        :param beginTime:
        :param endTime:
        :return:
        """
        try:
            time.strptime(beginTime, "%Y%m%d")
        except:
            raise Exception("beginTime ：{%s} 传入格式不正确！请重新输入！"%str(beginTime))
        try:
            time.strptime(endTime, "%Y%m%d")
        except:
            raise Exception("endTime ：{%s} 传入格式不正确！请重新输入！"%str(endTime))
        sql = "select (case when EXCHANGECODE=101 then concat(a.tradingcode,'.SH') " \
              "when EXCHANGECODE=105 then concat(a.tradingcode,'.SZ') end) as tradingcode," \
              "max(c.CHINAME) as comname,max(title) as title ,max(casename) as casename ," \
              "max(docnumber) as docnumber,b.caseid ,min(date_format(publishtime,'%Y-%m-%d %H:%i:%s') )as publishtime " \
              "from TOPIC_ENT_LAWSUITCOMP b inner join PUB_SECURITIESMAIN a " \
              "on a.comcode=b.comcode inner join pub_companymain c " \
              "on b.comcode=c.COMCODE where b.isvalid=1 and a.SECUCATEGORY='A股' " \
              "and a.EXCHANGECODE in (101,105) " \
              "and publishtime between {0} and date_add({1}, interval 1 day) " \
              "group by a.tradingcode,b.caseid".format(beginTime,endTime)
        c_name = str(int(time.time())) + str(threading.get_ident())
        df = self.dml_xquant_wind.getAllByPandas(c_name, sql)
        df[df.isnull()] = np.NAN
        df.replace([''], [np.nan], inplace=True)
        self.dml_xquant_wind.close(c_name)
        return df

    def getDisHonestyRecordByStock(self,stockcode, year_list=[]):
        """
        :param stockcode:
        :param year_list:
        :return:
        """
        if not isinstance(stockcode,str):
            raise Exception("stockcode 请传入单只股票（str类型）！")
        if not isinstance(year_list,list):
            raise Exception("date_list 请传入list！")
        if stockcode.endswith(".SZ") or stockcode.endswith(".SH"):
            stockcode = stockcode.split(".")[0]
        if not year_list:
            sql = "select (case when EXCHANGECODE=101 then concat(b.tradingcode,'.SH') " \
                  "when EXCHANGECODE=105 then concat(b.tradingcode,'.SZ') end) as tradingcode," \
                  "a.comname,a.title,a.legalrepr,a.Executioncode,a.court,a.perform," \
                  "date_format(filingtime,'%Y-%m-%d %H:%i:%s') as filingtime,a.personsituation," \
                  "a.casecode, date_format(publishtime,'%Y-%m-%d %H:%i:%s') as publishtime " \
                  "from TOPIC_ENT_DISHONESTYCOM a inner join PUB_SECURITIESMAIN b " \
                  "on a.comcode=b.comcode where a.isvalid=1 and b.SECUCATEGORY='A股' " \
                  "and b.EXCHANGECODE in (101,105) and b.tradingcode='{0}' " \
                  "group by a.publishtime,a.title,a.legalrepr,a.comname,a.Executioncode," \
                  "a.court,a.perform,a.filingtime,a.personsituation,a.casecode, b.tradingcode".format(stockcode)
        else:
            sql = "select (case when EXCHANGECODE=101 then concat(b.tradingcode,'.SH') " \
                  "when EXCHANGECODE=105 then concat(b.tradingcode,'.SZ') end) as tradingcode," \
                  "a.comname,a.title,a.legalrepr,a.Executioncode,a.court,a.perform," \
                  "date_format(filingtime,'%Y-%m-%d %H:%i:%s') as filingtime,a.personsituation," \
                  "a.casecode, date_format(publishtime,'%Y-%m-%d %H:%i:%s') as publishtime " \
                  "from TOPIC_ENT_DISHONESTYCOM a inner join PUB_SECURITIESMAIN b " \
                  "on a.comcode=b.comcode where a.isvalid=1 and b.SECUCATEGORY='A股' " \
                  "and b.EXCHANGECODE in (101,105) and b.tradingcode='{0}' " \
                  "and date_format(publishtime,'%Y') in (".format(stockcode)
            for i in year_list:
                try:
                    int(i)
                except:
                    raise Exception("{%s}年份格式不正确！请重新输入！"%i)
                sql += "'%s'," % i
            sql = sql[:-1] +") group by a.publishtime,a.title,a.legalrepr,a.comname,a.Executioncode,a.court,a.perform,a.filingtime,a.personsituation,a.casecode, b.tradingcode"
        c_name = str(int(time.time())) + str(threading.get_ident())
        df = self.dml_xquant_wind.getAllByPandas(c_name, sql)
        df[df.isnull()] = np.NAN
        df.replace([''], [np.nan], inplace=True)
        self.dml_xquant_wind.close(c_name)
        return df


    def getDisHonestyRecordByTime(self,beginTime, endTime):
        """
        :param beginTime:
        :param endTime:
        :return:
        """
        try:
            time.strptime(beginTime, "%Y%m%d")
        except:
            raise Exception("beginTime ：{%s} 传入格式不正确！请重新输入！"%str(beginTime))
        try:
            time.strptime(endTime, "%Y%m%d")
        except:
            raise Exception("endTime ：{%s} 传入格式不正确！请重新输入！"%str(endTime))
        sql = "select (case when EXCHANGECODE=101 then concat(b.tradingcode,'.SH') " \
              "when EXCHANGECODE=105 then concat(b.tradingcode,'.SZ') end) as tradingcode," \
              "a.comname,a.title,a.legalrepr,a.Executioncode,a.court,a.perform," \
              "date_format(filingtime,'%Y-%m-%d %H:%i:%s') as filingtime,a.personsituation,a.casecode, " \
              "date_format(publishtime,'%Y-%m-%d %H:%i:%s') as publishtime from TOPIC_ENT_DISHONESTYCOM a " \
              "inner join PUB_SECURITIESMAIN b on a.comcode=b.comcode where a.isvalid=1 and b.SECUCATEGORY='A股' " \
              "and b.EXCHANGECODE in (101,105) and a.publishtime between {0} and date_add({1}, interval 1 day) " \
              "group by a.publishtime,a.title,a.legalrepr,a.comname,a.Executioncode,a.court,a.perform," \
              "a.filingtime,a.personsituation,a.casecode, b.tradingcode".format(beginTime,endTime)
        c_name = str(int(time.time())) + str(threading.get_ident())
        df = self.dml_xquant_wind.getAllByPandas(c_name, sql)
        df[df.isnull()] = np.NAN
        df.replace([''], [np.nan], inplace=True)
        self.dml_xquant_wind.close(c_name)
        return df




