"""时间格式的相互转换"""

import time
import datetime as dt


# -------------------------------------------------------------------------------
# -------------------------------- 使用 datetime --------------------------------
def transfer_datetime():
    now_time = dt.datetime.now()  # 获取当前时间

    tss1 = "2018-08-01 09:35:10"
    dt_array = dt.datetime.strptime(tss1, '%Y-%m-%d %H:%M:%S')
    dt_year = dt_array.year  # 获取年份
    int(dt_array.strftime("%Y%m%d%H%M%S"))  # 转换为20180801093510
    dt_array.strftime("%Y/%m/%d %H:%M:%S")  # 转换为其他显示格式 2018/08/01 09:35:10

    timeStamp = 1381419600  # 给定格式为时间戳
    dateArray = dt.datetime.fromtimestamp(timeStamp)
    dateArray.strftime("%Y-%m-%d %H:%M:%S")  # 转换为'2013-10-10 23:40:00'
    int(dateArray.strftime("%Y%m%d%H%M%S"))  # 转换为20131010234000


# ---------------------------------------------------------------------------
# -------------------------------- 使用 time --------------------------------
def transfer_time():
    tss1 = "2018-08-01 09:35:10"
    timeArray = time.strptime(tss1, "%Y-%m-%d %H:%M:%S")  # 转为时间数组
    time_year = timeArray.tm_year  # 获取年份
    int(time.strftime("%Y%m%d%H%M%S", time.strptime(tss1, "%Y-%m-%d %H:%M:%S")))  # 转换为20180801093510
    int(time.mktime(time.strptime(tss1, "%Y-%m-%d %H:%M:%S")))  # 转换为时间戳 1533087310
    time.strftime("%Y/%m/%d %H:%M:%S", timeArray)  # 转换为其他显示格式 2018/08/01 09:35:10

    # 将20180801093510 转换为 "2018-08-01 09:35:10"
    time.strftime("%Y-%m-%d %H:%M:%S", time.strptime(str(20180801093510), "%Y%m%d%H%M%S"))

    timeStamp = 1381419600  # 给定格式为时间戳
    timeArray = time.localtime(timeStamp)  # 转为时间数组
    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timeStamp))  # 转换为'2013-10-10 23:40:00'
    int(time.strftime("%Y%m%d%H%M%S", time.localtime(timeStamp)))  # 转换为20131010234000
    int(time.strftime("%H%M%S", time.localtime(timeStamp)))*1000  # 转换为md_time格式：234000000

    # 将"2018/8/1" 转换为 20180801
    int(time.strftime("%Y%m%d", time.strptime("2018/8/1", "%Y/%m/%d")))

    # 将20180801 转换为 "2018/8/1"
    time.strftime("%Y/%m/%d", time.strptime(str(20180801), "%Y%m%d"))


# ---------------------------------------------------------------------------
# -------------------------------- Helper Funcs --------------------------------
def timestamp_to_datetime(timestamp):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))


def timestamp_to_time(timestamp):
    return time.strftime("%H:%M:%S", time.localtime(timestamp))


def timestamp_to_date(timestamp):
    return time.strftime("%Y%m%d", time.localtime(timestamp))


def datetime_to_timestamp(date_time):
    return int(time.mktime(time.strptime(date_time, "%Y-%m-%d %H:%M:%S")))


def get_all_time(gap_second=1):
    """两个时间点内，按照gap_second间隔区分，中间所有的时间点"""
    cur_time = "09:30:00"
    ed_time = "15:00:00"
    all_time_list = [cur_time]
    while cur_time < ed_time:
        cur_time = time_delta(cur_time, gap_second=gap_second, is_adjust=True)
        all_time_list.append(cur_time)
    return all_time_list


def int2str_time(time_int=93050):
    h, m, s = int(time_int // 10000), int(time_int % 10000 // 100), int(time_int % 100)
    h, m, s = '0' * (2 - len(str(h))) + str(h), '0' * (2 - len(str(m))) + str(m), '0' * (2 - len(str(s))) + str(s)
    return f'{h}:{m}:{s}'


def time_delta(origin_time="10:29:00", gap_second=10, is_adjust=False):
    """一个时间，加上一个间隔秒数，得到的时间"""
    is_mode2 = (len(origin_time) == 6 and ":" not in origin_time)  # origin_time格式为"102900"这种
    if is_mode2:
        origin_time = f'{origin_time[0: 2]}:{origin_time[2: 4]}:{origin_time[4: 6]}'
    origin_array = dt.datetime.strptime("2020-01-01 " + origin_time, '%Y-%m-%d %H:%M:%S')
    out_array = origin_array + dt.timedelta(seconds=gap_second)
    out_time = out_array.strftime("%H:%M:%S")
    if is_adjust:  # 如果调整，剔除午盘中间的一个半小时的时间
        if origin_time <= "11:30:00" < out_time:
            morning_close_time = dt.datetime.strptime("20200101113000", '%Y%m%d%H%M%S')
            afternoon_open_time = dt.datetime.strptime("20200101130000", '%Y%m%d%H%M%S')
            adjust_second = (out_array - morning_close_time).seconds
            out_array = afternoon_open_time + dt.timedelta(seconds=adjust_second)
            out_time = out_array.strftime("%H:%M:%S")
    if is_mode2:
        out_time = out_time.replace(':', '')
    return out_time


def time_duration(st_time_str="093500", ed_time_str="093230", is_adjust=False):
    """两个时间之间间隔的分钟数"""
    st_min = int(st_time_str[0:2]) * 60 + int(st_time_str[2:4]) + int(st_time_str[4:6]) / 60
    ed_min = int(ed_time_str[0:2]) * 60 + int(ed_time_str[2:4]) + int(ed_time_str[4:6]) / 60
    gap_min = ed_min - st_min
    if is_adjust:  # 如果调整，剔除午盘中间的一个半小时的时间
        if st_time_str <= "113000" and ed_time_str >= "130000":
            gap_min -= 90
    return round(gap_min, 2)


def date_duration(st_date='20210101', ed_date='20210131'):
    """两个日期之间的间隔天数"""
    st_date1 = time.strptime(st_date, "%Y%m%d")
    ed_date1 = time.strptime(ed_date, "%Y%m%d")
    st_date1 = dt.datetime(st_date1[0], st_date1[1], st_date1[2])
    ed_date1 = dt.datetime(ed_date1[0], ed_date1[1], ed_date1[2])
    gap_date = (ed_date1 - st_date1).days
    return gap_date


def date_t(input_date):
    """输入为20200101，输出为2020-01-01"""
    input_date = str(input_date)
    return '{}-{}-{}'.format(input_date[0:4], input_date[4:6], input_date[6:8])


def minute_t2m(t):
    """输入为0:09:30，输出为 9.5（min）"""
    h, m, s = t.strip().split(":")
    return int(h) * 60 + int(m) + int(s) / 60


def minute_m2t(t):
    m = int(t)
    s = int((t - m) * 60)
    h = int(m / 60)
    m = m - h * 60
    ss = str(s)
    mm = str(m)
    if len(ss) == 1:
        ss = "0" + ss
    if len(mm) == 1:
        mm = "0" + mm
    return str(h) + ":" + mm + ":" + ss


def get_today():
    trade_date = dt.datetime.now().strftime("%Y%m%d")
    return trade_date
