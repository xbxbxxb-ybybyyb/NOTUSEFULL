import datetime as dt
import System.GetTradingDay as get_trading_day

# start, end = dt.datetime.now(), dt.datetime.now()


# today = int((dt.datetime.now()+dt.timedelta(-2)).strftime('%Y%m%d'))
today = int((dt.datetime.now() - dt.timedelta(1)).strftime('%Y%m%d'))
trading_days = get_trading_day.tradingDayList
for index in range(len(trading_days)):
    if trading_days[index] == today:
        next_day = str(trading_days[index+1])
        break
    elif trading_days[index] > today:
        next_day = str(trading_days[index])
        break


    

next_day = dt.datetime(int(next_day[0:4]), int(next_day[4:6]), int(next_day[6:8]))
start = next_day #+ dt.timedelta(-1)
start, end = start, next_day
