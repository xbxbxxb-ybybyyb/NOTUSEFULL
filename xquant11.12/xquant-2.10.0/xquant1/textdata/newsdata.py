# _*_ coding:utf-8 _*_
import numpy as np
import threading
import time
import json
from .newsutils import Connect_hive
import pandas as pd
import datetime as dt
from xquant1.factordata.db import DML_mysql
# from xquant.factordata.storageConfig import DUBBO_CONFIG,DUBBO_APPLICATIONCONFIG_NEWSDATA_GETNEWSBODY
from xquant1.conf.DubboConf import DUBBO_CONFIG
try:
    from ht_dubbo_client import ZookeeperRegistry, DubboClient, DubboClientError, ApplicationConfig
except:
    pass
from xquant1.xqutils.utils import statisticLog

DUBBO_APPLICATIONCONFIG_NEWSDATA_GETNEWSBODY = DUBBO_CONFIG["DUBBO_CONFIG_NEWSDATA_GETNEWSBODY"]
DUBBO_CONFIG_IP = DUBBO_CONFIG["DUBBO_CONFIG_IP"]

try:
    config = ApplicationConfig(DUBBO_APPLICATIONCONFIG_NEWSDATA_GETNEWSBODY)
    service_interface_getnewsdata = "com.htsc.xquant.dataagent.service.dubbo.ZxNewsInfoService"
    registry = ZookeeperRegistry(DUBBO_CONFIG_IP, config)
    user_provider_getnewsdata = DubboClient(service_interface_getnewsdata, registry, version="1.0.0")
except:
    pass


class NewsData:
    @statisticLog('textdata', "NewsData")
    def __init__(self):
        self.CH = Connect_hive()
        self.dml_xquant_wind = DML_mysql('xquant_wind')

    # def get_news_list(self,date):
    #     """
    #      获取指定日期的新闻列表信息
    #     :param date: 日期, int(20190414), string ('20190414')
    #     :return: 返回新闻列表信息, dataframe, 包含'ID','MEDIANAME','PUBDATE','TEXTTITLE'列
    #     """
    #     if isinstance(date, int):
    #         date = str(date)
    #     date = dt.datetime.strftime(dt.datetime.strptime(date, '%Y%m%d'), '%Y-%m-%d')
    #     sql_use = "select ID,MEDIANAME,PUBDATE,TEXTTITLE from TEXT_BASICINFO tb " \
    #               "where tb.textcategory in (select constcode from cnt_text where constcode like '30%') " \
    #               "and to_date(tb.pubdate) = '{}'".format(date)
    #     result = self.CH.getAll(sql_use)
    #     df = pd.DataFrame(result[1:], columns=result[0])
    #     return df
    #
    # def get_news_abstract(self,id):
    #     """
    #     获取指定新闻ID的新闻文本
    #     :param id: 新闻ID，即get_news_list方法返回的ID
    #     :return:新闻文本string
    #     """
    #     if isinstance(id, int):
    #         id = str(id)
    #     sql_use = "select ABSTRACT from TEXT_BASICINFO where ID = %s" % id
    #     data = self.CH.getAll(sql_use)
    #     result = data[1][0]
    #     return result
    @statisticLog('textdata',"NewsData")
    def getNewsInfoByStockCode(self,stockcode,year_list=[]):
        """
        单股票历史新闻查询
        select * from text_basicinfo a inner join pub_securitiesmain b on a.COMCODE=b.COMCODE where b.secucategory='A股' and b.exchangecode in (101,105) and b.TRADINGCODE = '603766';
        select a.id,a.texttitle,a.authors,a.resourceid,a.pubdate,a.entrytime,a.updatetime from text_basicinfo a inner join pub_securitiesmain b on a.COMCODE=b.COMCODE where b.secucategory='A股' and b.exchangecode in (101,105) and b.TRADINGCODE = '002658' order by a.ENTRYTIME desc
        :param stockcode:股票
        :param year_list:年份
        :return:
        """
        if not isinstance(stockcode,str):
            raise Exception("stockcode 请传入单只股票（str类型）！")
        if not isinstance(year_list,list):
            raise Exception("date_list 请传入list！")
        sql = self.__split_sql(year_list,stockcode)
        c_name = str(int(time.time())) + str(threading.get_ident())
        data = self.dml_xquant_wind.getAll(c_name, sql)
        df = pd.DataFrame(data[1:], columns=data[0])
        # df[df.isnull()] = np.NAN
        df.replace([''], [np.nan], inplace=True)
        df.set_index('id', inplace=True)
        self.dml_xquant_wind.close(c_name)
        return df

    def __split_sql(self,year_list,stockcode):
        """
        过滤年份
        :param year_list: 年份列表
        :return:
        """
        if not year_list:
            sql = "select a.id,a.texttitle,a.authors,a.resourceid,a.pubdate,a.entrytime,a.updatetime from text_basicinfo a " \
                  "inner join pub_securitiesmain b on a.COMCODE=b.COMCODE where b.secucategory='A股' and " \
                  "b.exchangecode in (101,105) and b.TRADINGCODE = '{0}' order by a.ENTRYTIME desc".format(stockcode)
            return sql
        sql = "select a.id,a.texttitle,a.authors,a.resourceid,a.pubdate,a.entrytime,a.updatetime from text_basicinfo a " \
              "inner join pub_securitiesmain b on a.COMCODE=b.COMCODE where b.secucategory='A股' and " \
              "b.exchangecode in (101,105) and b.TRADINGCODE = '{0}' and (".format(stockcode)
        for d in year_list:
            try:
                date_begin = d + "0101 00:00"
                date_end = d + "1231 23:59"
            except:
                raise Exception("年份  {0}  类型错误！请传入str类型".format(d))
            try:
                news_start_time = dt.datetime.strptime(date_begin, '%Y%m%d %H:%M')
                news_end_time = dt.datetime.strptime(date_end, '%Y%m%d %H:%M')
            except:
                raise Exception("年份格式为YYYY 如'2018'！")
            news_start_time = news_start_time.strftime('%Y-%m-%d %H:%M:%S')
            news_end_time = news_end_time.strftime('%Y-%m-%d %H:%M:%S')
            sql += "a.ENTRYTIME between '{0}' and '{1}' or ".format(news_start_time, news_end_time)
        sql = sql[:-4] + ") order by a.ENTRYTIME desc"
        return sql

    @statisticLog('textdata', "NewsData")
    def getNewsInfoByEntryTime(self,newsInsertDate, beginTime, endTime):
        """
        获取某天某一段时间内入库的新闻基本信息
        :param newsInsertDate:新闻入库日期，单值输入，输入格式“YYYYMMDD”
        :param beginTime:查询新闻入库开始时间，格式为HH:MM，如 09:30
        :param endTime:查询新闻入库结束时间，格式为HH:MM，如 09:30
        :return:
        """
        newsInsertDate_tuple = self._is_valid_date(newsInsertDate,beginTime,endTime)
        sql = "select id,texttitle,authors,resourceid,pubdate,entrytime,updatetime from text_basicinfo where entrytime between '%s' and '%s'"%newsInsertDate_tuple
        # print(sql)
        c_name = str(int(time.time())) + str(threading.get_ident())
        data = self.dml_xquant_wind.getAll(c_name, sql)
        df = pd.DataFrame(data[1:], columns=data[0])
        # df[df.isnull()] = np.NAN
        df.replace([''], [np.nan], inplace=True)
        df.set_index('id', inplace=True)
        self.dml_xquant_wind.close(c_name)
        return df


    def _is_valid_date(self,newsInsertDate,starttime,endtime):
        if not isinstance(newsInsertDate,str):
            raise Exception("newsInsertDate需传入str类型！格式为YYYYMMDD！")
        if not isinstance(starttime,str) or not isinstance(endtime,str):
            raise Exception("beginTime和endTime 请传入字符串格式，格式为HH:MM，如 09:30！")
        news_start_time = newsInsertDate + " " + starttime
        news_end_time = newsInsertDate + " " + endtime
        try:
            news_start_time = dt.datetime.strptime(news_start_time,'%Y%m%d %H:%M')
            news_end_time = dt.datetime.strptime(news_end_time,'%Y%m%d %H:%M')
        except:
            raise Exception("newsInsertDate 格式为YYYYMMDD 如'20180101'，beginTime和endTime 格式为HH:MM，如'09:30'！")
        news_start_time = news_start_time.strftime('%Y-%m-%d %H:%M:%S')
        news_end_time = news_end_time.strftime('%Y-%m-%d %H:%M:%S')
        return news_start_time,news_end_time

    def __dubbo_getnewsbody(self,str_newsID):
        """
        dubbo接口
        :return:
        """
        try:
            json_dict = {"request":{"ids":str_newsID}}
            json_str = json.dumps(json_dict)
            get_result = user_provider_getnewsdata.getNewsInfo(json_str)
            get_result = json.loads(get_result)
            return get_result, 200
        except Exception as e:
            return str(e), 500

    @statisticLog('textdata', "NewsData")
    def getNewsBody(self,newsID_list):
        """
        根据id获取新闻全文（调dubbo接口）
        :param newsID:新闻ID
        :return:
        {"request":{"ids":"10433560967,11901278527,11756781357"}}
          0 表示成功  -1 表示失败
        {"result":"提示失败原因","resultCode":-1}
        {"response":{"新闻id1":"新闻内容","新闻id2":"新闻内容"...},"resultCode":0}
        zookeeper://168.61.2.23:2181?backup=168.61.2.24:2181,168.61.2.25:2181 用这个zk
        com.htsc.xquant.dataagent.service.dubbo.ZxNewsInfoService
        getNewsInfo
        """
        if not isinstance(newsID_list,list):
            raise Exception("newsID_list 请传入列表！")
        try:
            str_newsID = ",".join(newsID_list)
        except:
            raise Exception("newsID 为str类型！")
        result = self.__dubbo_getnewsbody(str_newsID)
        if result[1] != 200:
            raise Exception(str(result[0]) + "调用dubbo接口失败，无法查询新闻内容！")
        else:
            if result[0].get("resultCode") == -1:
                raise Exception("调用dubbo接口失败，无法查询新闻内容！", result[0].get("result"))
        info_dict = result[0].get("response")
        column = ("newsID","newsBody")
        if not info_dict:
            return pd.DataFrame(columns=column)
        info_list = []
        for info in info_dict:
            info_list.append((info,info_dict[info]))
        df = pd.DataFrame(info_list,columns=column)
        df.set_index("newsID",inplace=True)
        return df


# def _get_news(date,count=None):
#     """
#     获取新闻数据
#     :param date: 字符串或int或范围列表如：'20190414'或20190414或 ['20190410','20190414'] 或[20190410,20190414]
#     :param count: 不为0的整数，与date配合使用，date为str或int类型的日期时，count为正则取date往前推的count天的数据(含date)，count为负则取date往后推的count天的数据(含date)
#     :return:
#     """
#     if not isinstance(date,list):
#         if isinstance(date,int):
#             date = str(date)
#         date = dt.datetime.strptime(date, '%Y%m%d')
#         if count:
#             if count > 0:
#                 edate = dt.datetime.strftime(date,'%Y-%m-%d')
#                 sdate = date - dt.timedelta(round(count)-1)
#                 sdate = dt.datetime.strftime(sdate,'%Y-%m-%d')
#                 sql_use = "select ID,MEDIANAME,PUBDATE,TEXTTITLE,ABSTRACT from TEXT_BASICINFO tb " \
#                           "where tb.textcategory in (select constcode from cnt_text where constcode like '30%') " \
#                           "and (to_date(tb.pubdate) >= '{0}' and to_date(tb.pubdate) <= '{1}')".format(sdate, edate)
#             elif count < 0:
#                 sdate = dt.datetime.strftime(date,'%Y-%m-%d')
#                 edate = date - dt.timedelta(round(count) + 1)
#                 edate = dt.datetime.strftime(edate,'%Y-%m-%d')
#                 sql_use = "select ID,MEDIANAME,PUBDATE,TEXTTITLE,ABSTRACT from TEXT_BASICINFO tb " \
#                           "where tb.textcategory in (select constcode from cnt_text where constcode like '30%') " \
#                           "and (to_date(tb.pubdate) >= '{0}' and to_date(tb.pubdate) <= '{1}')".format(sdate, edate)
#             else:
#                 raise Exception("count 取值不为0的整数 ！")
#         else:
#             date = dt.datetime.strftime(date,'%Y-%m-%d')
#             sql_use = "select ID,MEDIANAME,PUBDATE,TEXTTITLE,ABSTRACT from TEXT_BASICINFO tb " \
#                       "where tb.textcategory in (select constcode from cnt_text where constcode like '30%') " \
#                       "and to_date(tb.pubdate) = '{}'".format(date)
#     else:
#         if count:
#             raise Exception("date参数为str或int类型的日期时，与date配合使用！")
#         if len(date) == 2:
#             for i in range(2):
#                 if isinstance(date[i], int):
#                     date[i] = str(date[i])
#             t1 = dt.datetime.strftime(dt.datetime.strptime(date[0],'%Y%m%d'),'%Y-%m-%d')
#             t2 = dt.datetime.strftime(dt.datetime.strptime(date[1],'%Y%m%d'),'%Y-%m-%d')
#             if t1 > t2:
#                 sdate,edate = t2,t1
#             else:
#                 sdate, edate = t1, t2
#             sql_use = "select ID,MEDIANAME,PUBDATE,TEXTTITLE,ABSTRACT from TEXT_BASICINFO tb " \
#                       "where tb.textcategory in (select constcode from cnt_text where constcode like '30%') " \
#                       "and (to_date(tb.pubdate) >= '{0}' and to_date(tb.pubdate) <= '{1}')".format(sdate,edate)
#         else:
#             raise Exception("列表参数有两个日期 -- 开始日期、结束日期。")
#     result = CH.getAll(sql_use)
#     df = pd.DataFrame(result[1:],columns=result[0])
#     df.sort_values('pubdate',inplace=True)
#     return df

    def getNegNewsByStock(self,stockcode, year_list=[]):
        """
        负面新闻
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
                  "max(a.secuabbr) as secuabbr,max(title) as title ," \
                  "max(medianame) as medianame,b.newscode ," \
                  "min(date_format(publishtime,'%Y-%m-%d %H:%i:%s') )as publishtime " \
                  "from TOPIC_ENT_NEWSTEXTFCDB b inner join PUB_SECURITIESMAIN a " \
                  "on a.comcode=b.comcode where b.isvalid=1 and a.tradingcode ='{0}' " \
                  "and a.SECUCATEGORY='A股' and a.EXCHANGECODE in (101,105)" \
                  " group by a.tradingcode,newscode".format(stockcode)
        else:
            sql = "select (case when EXCHANGECODE=101 then concat(a.tradingcode,'.SH') " \
                  "when EXCHANGECODE=105 then concat(a.tradingcode,'.SZ') end) as tradingcode," \
                  "max(a.secuabbr) as secuabbr,max(title) as title ," \
                  "max(medianame) as medianame,b.newscode ," \
                  "min(date_format(publishtime,'%Y-%m-%d %H:%i:%s') )as publishtime " \
                  "from TOPIC_ENT_NEWSTEXTFCDB b inner join PUB_SECURITIESMAIN a " \
                  "on a.comcode=b.comcode where b.isvalid=1 and a.tradingcode ='{0}' " \
                  "and a.SECUCATEGORY='A股' and a.EXCHANGECODE in (101,105) " \
                  "and date_format(publishtime,'%Y') in (".format(stockcode)
            for i in year_list:
                try:
                    int(i)
                except:
                    raise Exception("{%s}年份格式不正确！请重新输入！"%i)
                sql += "'%s'," % i
            sql = sql[:-1] +") group by a.tradingcode,newscode"
        c_name = str(int(time.time())) + str(threading.get_ident())
        df = self.dml_xquant_wind.getAllByPandas(c_name, sql)
        df[df.isnull()] = np.NAN
        df.replace([''], [np.nan], inplace=True)
        self.dml_xquant_wind.close(c_name)
        return df

    def getNegNewsByTime(self,beginTime, endTime):
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
              "max(a.secuabbr) as secuabbr,max(title) as title ,max(medianame) as medianame," \
              "b.newscode ,min(date_format(publishtime,'%Y-%m-%d %H:%i:%s') )as publishtime " \
              "from TOPIC_ENT_NEWSTEXTFCDB b inner join PUB_SECURITIESMAIN a on " \
              "a.comcode=b.comcode where b.isvalid=1 and a.SECUCATEGORY='A股' " \
              "and a.EXCHANGECODE in (101,105) and publishtime between {0} and date_add({1}, interval 1 day) " \
              "group by a.tradingcode,newscode".format(beginTime,endTime)

        c_name = str(int(time.time())) + str(threading.get_ident())
        df = self.dml_xquant_wind.getAllByPandas(c_name, sql)
        df[df.isnull()] = np.NAN
        df.replace([''], [np.nan], inplace=True)
        self.dml_xquant_wind.close(c_name)
        return df