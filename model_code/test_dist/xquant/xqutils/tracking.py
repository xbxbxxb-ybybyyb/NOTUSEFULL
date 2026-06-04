import sys
import time
import datetime
import os
from xquant.xqutils.utils import Kafka_producer,KAFKA_TOPIC
def factor_statistic(module: str = '', genus: str = ''):
    """
    监控日志装饰器
    :return:
    :param module:  类型如下
            bigdata	大数据文件操作
            marketdata	高频行情访问模块
            tensorflow	tensorflow库操作
            factordata	量化因子访问模块
    :param genus:   所属类名
    :return:
    """
    def printStar(func):
        def _call(*args, **kw):
            # 日志输出
            # $statistic - log：为固定的埋点开始标识
            # module：为埋点模块名称（必填）
            # submodule：为埋点子模块名称（可选）
            # subject：为操作类型（可选）
            # platform：为平台标识（必填），预定义值见下文
            subject = func.__name__
            if len(genus)>0:
                subject = genus + "." + subject
            start_time = time.time()
            startTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f = func(*args, **kw)
            end_time = str(round(time.time() - start_time, 2))
            if kw.get("library_name",False):
                library_name = kw.get("library_name",False)
            else:
                library_name = args[1]
            try:
                # size = str(round(sys.getsizeof(f)/1024/1024,4))
                size = str(sys.getsizeof(f))
            except:
                size = "0"
            if os.environ.get('BIG_DATA_PREPATH', False) or not os.environ.get('ENV_VERSION', False):
                print("$factor_statistic,module=%s,subject=%s,size=%s,libraryName=%s,startTime=%s,time=%s,platform=XQUANT-Cloud" % (module, subject,size,library_name,startTime,end_time))
            else:
                try:
                    # value = {"tag": "factor_statistic", "message":"$factor_statistic,module=%s,subject=%s,size=%s,libraryName=%s,startTime=%s,time=%s,platform=XQUANT-Cloud" % (module, subject,size,library_name,startTime,str(round(time.time()-start_time,2)))}
                    value = {
                        "tag": "factor_statistic",
                        "message":{
                            "module":module,
                            "subject":subject,
                            "size":size,
                            "libraryName":library_name,
                            "startTime":startTime,
                            "time":str(round(time.time()-start_time,2)),
                            "platform":"XQUANT-Cloud"
                        }
                    }
                    producer = Kafka_producer(KAFKA_TOPIC)
                    producer.sendjsondata(value)
                except:
                    pass
            return f
        return _call
    return printStar