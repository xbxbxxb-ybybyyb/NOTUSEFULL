import signal
import datetime as dt

def utils_set_timeout(num, callback):
    def wrap(func):
        def handle(signum, frame):  # 收到信号 SIGALRM 后的回调函数，第一个参数是信号的数字，第二个参数是the interrupted stack frame.
            raise Exception(callback)

        def to_do(*args, **kwargs):
            signal.signal(signal.SIGALRM, handle)  # 设置信号和回调函数
            signal.alarm(num)  # 设置 num 秒的闹钟
            r = func(*args, **kwargs)
            signal.alarm(0)  # 关闭闹钟
            return r

        return to_do

    return wrap



def is_valid_date(start_date,end_date=None,date_type=None):
    # start_date 单个日期，若end_date不为None则start_date 应小于end_date
    # date_type为日期类型 year,month,day,hour,minute,second
    if not end_date:
        if date_type == "year_month_day":
            try:
                if isinstance(start_date,int):
                    start_date = str(start_date)
                assert len(start_date) == 8
                dt.datetime.strptime(start_date, '%Y%m%d')
                return True
            except Exception as e:
                print("日期-{0}的格式有误，请传入正确格式如'20200201'".format(start_date))
                return False
        elif date_type == "year_month_day_hour_minute_second":
            if isinstance(start_date, int):
                start_date = str(start_date)
            if len(start_date) == 14:
                try:
                    dt.datetime.strptime(start_date, '%Y%m%d%H%M%S')
                    return True
                except:
                    print("日期-{0}的格式有误，请传入正确格式如'20200201103000'".format(start_date))
                    return False
            elif len(start_date) == 15:
                try:
                    dt.datetime.strptime(start_date, '%Y%m%d %H%M%S')
                    return True
                except:
                    print("日期-{0}的格式有误，请传入正确格式如'20200201 103000'".format(start_date))
                    return False
            else:
                print("日期-{0}的格式有误，请传入正确格式如'20200201103000'或'20200201 103000'".format(start_date))
                return False
        elif date_type == "year_month_day_hour_minute_second_f":
            if len(start_date) == 18:
                try:
                    dt.datetime.strptime(start_date, '%Y%m%d %H%M%S%f')
                    return True
                except:
                    print("日期-{0}的格式有误，请传入正确格式如'20200201 103000000'".format(start_date))
                    return False
            elif len(start_date) == 17:
                try:
                    dt.datetime.strptime(start_date, '%Y%m%d%H%M%S%f')
                    return True
                except:
                    print("日期-{0}的格式有误，请传入正确格式如'20200201103000000'".format(start_date))
                    return False
            else:
                print("日期-{0}的格式有误，请传入正确格式如'20200201103000000'或'20200201 103000000'".format(start_date))
                return False
        else:
            raise Exception("【date_type】请输入正确的date_type！")
    else:
        if date_type == "year_month_day":
            try:
                if isinstance(start_date, int):
                    start_date = str(start_date)
                if isinstance(end_date, int):
                    end_date = str(end_date)
                assert len(start_date) == 8
                assert len(end_date) == 8
                sdate = dt.datetime.strptime(start_date, '%Y%m%d')
                edate = dt.datetime.strptime(end_date, '%Y%m%d')
                if sdate > edate:
                    print("开始日期{0}大于结束日期{1}，请检查后输入！".format(start_date,end_date))
                    return False
                else:
                    return True
            except Exception as e:
                print("日期-{0}-{1}的格式有误，请传入正确格式如'20200201'".format(start_date,end_date))
                return False
        elif date_type == "year_month_day_hour_minute_second":
            if isinstance(start_date, int):
                start_date = str(start_date)
            if isinstance(end_date, int):
                end_date = str(end_date)
            if len(start_date) == 14:
                try:
                    sdate = dt.datetime.strptime(start_date, '%Y%m%d%H%M%S')
                    edate = dt.datetime.strptime(end_date, '%Y%m%d%H%M%S')
                    if sdate > edate:
                        print("开始日期{0}大于结束日期{1}，请检查后输入！".format(start_date, end_date))
                        return False
                    else:
                        return True
                except:
                    print("日期-{0}-{1}的格式有误，请传入正确格式如'20200201103000'".format(start_date,end_date))
                    return False
            elif len(start_date) == 15:
                try:
                    sdate = dt.datetime.strptime(start_date, '%Y%m%d %H%M%S')
                    edate = dt.datetime.strptime(start_date, '%Y%m%d %H%M%S')
                    if sdate > edate:
                        print("开始日期{0}大于结束日期{1}，请检查后输入！".format(start_date, end_date))
                        return False
                    else:
                        return True
                except:
                    print("日期-{0}-{1}的格式有误，请传入正确格式如'20200201 103000'".format(start_date,end_date))
                    return False
            else:
                print("日期-{0}的格式有误，请传入正确格式如'20200201103000'或'20200201 103000'".format(start_date))
                return False
        elif date_type == "year_month_day_hour_minute_second_f":
            if len(start_date) == 18:
                try:
                    sdate = dt.datetime.strptime(start_date, '%Y%m%d %H%M%S%f')
                    edate = dt.datetime.strptime(end_date, '%Y%m%d %H%M%S%f')
                    if sdate > edate:
                        print("开始日期{0}大于结束日期{1}，请检查后输入！".format(start_date, end_date))
                        return False
                    else:
                        return True
                except:
                    print("日期-{0}-{1}的格式有误，请传入正确格式如'20200201 103000000'".format(start_date, end_date))
                    return False
            elif len(start_date) == 17:
                try:
                    sdate = dt.datetime.strptime(start_date, '%Y%m%d%H%M%S%f')
                    edate = dt.datetime.strptime(end_date, '%Y%m%d%H%M%S%f')
                    if sdate > edate:
                        print("开始日期{0}大于结束日期{1}，请检查后输入！".format(start_date, end_date))
                        return False
                    else:
                        return True
                except:
                    print("日期-{0}-{1}的格式有误，请传入正确格式如'20200201103000000'".format(start_date,end_date))
                    return False
            else:
                print("日期-{0}-{1}的格式有误，请传入正确格式如'20200201103000000'或'20200201 103000000'".format(start_date, end_date))
                return False
        else:
            raise Exception("【date_type】请输入正确的date_type！")

