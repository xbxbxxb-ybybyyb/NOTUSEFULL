import datetime as dt
    
def get_signal_dates(start, end):
    signal_dates = []
    while end >= start:
        if start.weekday() < 5:
            signal_dates.append(start.strftime('%Y%m%d'))
        start = start + dt.timedelta(days=1)
    return signal_dates