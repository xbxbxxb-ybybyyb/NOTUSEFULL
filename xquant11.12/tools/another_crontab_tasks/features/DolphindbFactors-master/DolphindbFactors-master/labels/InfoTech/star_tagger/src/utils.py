import datetime

def MDTime_2_time(t):
    t = int(t)
    hour = int(t // 1e7)
    minute = int((t - hour * 1e7) // 1e5)
    second = int((t - hour * 1e7 - minute * 1e5) // 1e3)
    t = datetime.time(hour, minute, second)
    return t

def MDDate_2_date(t):
    t = int(t)
    m = (t // 100) % 100
    y = t // 10000
    d = t % 100
    t = datetime.date(y, m, d)
    return t

def combine(date, time):
    dt = datetime.datetime.combine(date, time)
    return dt

class Args(dict):
    def __init__(self, **kwargs):
        super(Args, self).__init__(**kwargs)

    def __getattr__(self, name):
        value = self[name]
        if isinstance(value, dict):
            value = Args(**value)
        return value

    def __setattr__(self, name, value):
        self[name] = value
        return value

    def __getstate__(self):
        return

    def __setstate__(self, state):
        return

def filter_valid_data(df):
    now_time = df.index[0]
    am_start_time =  datetime.datetime(now_time.year, now_time.month, now_time.day, 9, 30)
    am_end_time =  datetime.datetime(now_time.year, now_time.month, now_time.day, 11, 30)
    pm_start_time =  datetime.datetime(now_time.year, now_time.month, now_time.day, 13, 00)
    pm_end_time =  datetime.datetime(now_time.year, now_time.month, now_time.day, 14, 57)
    condition = ((df.index >= am_start_time) & (df.index<=am_end_time)) | ((df.index >= pm_start_time) & (df.index<pm_end_time))
    return df[condition]

def filter_valid_data_by_datetime(df):
    am_start_time =  datetime.time(9, 30, 0)
    am_end_time =  datetime.time(11, 30, 0)
    pm_start_time =  datetime.time(13, 00, 00)
    pm_end_time =  datetime.time(14, 57, 00)
    condition = ((df.index >= am_start_time) & (df.index<=am_end_time)) | ((df.index >= pm_start_time) & (df.index<pm_end_time))
    # condition = ((df.MDTime >= am_start_time) & (df.MDTime<=am_end_time)) | ((df.MDTime >= pm_start_time) & (df.MDTime<=pm_end_time))
    return df[condition]


def fileter_invalid_data_by_tradingday(df, trading_date_list):
    df["MDDate"] = df.index.date 
    df = df[df.MDDate.apply(lambda x: str(x).replace("-","")).isin(trading_date_list)]
    df.drop(columns=["MDDate"], inplace=True)
    return df

def is_valid_data(now_time):
    # now_time = df.index[0]
    am_start_time =  datetime.datetime(now_time.year, now_time.month, now_time.day, 9, 30)
    am_end_time =  datetime.datetime(now_time.year, now_time.month, now_time.day, 11, 30)
    pm_start_time =  datetime.datetime(now_time.year, now_time.month, now_time.day, 13, 00)
    pm_end_time =  datetime.datetime(now_time.year, now_time.month, now_time.day, 14, 57)
    condition = ((now_time >= am_start_time) & (now_time<am_end_time)) | ((now_time >= pm_start_time) & (now_time<pm_end_time))
    return condition