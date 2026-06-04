import calendar
import os
from xquant.factordata import FactorData
fd = FactorData()
from xquant.futuredata import FutureData
fud = FutureData()
import datetime

def get_cf_future_listing_date(typer):
    import pandas as pd
    from xquant.futuredata import FutureData
    fd = FutureData()
    instrument_list = [typer+str(i)+str(j).zfill(2)+".CF" for i in range(21,25) for j in range(1,13)]
    df_list = []
    for ins in instrument_list:
        df = fd.get_instrument_info(ins)
        df_list.append(df[['windcode','listdate','delistdate']])
    res = pd.concat(df_list, axis=0)

    return list(res.values)


future = "IF"
for stock, start_date, end_date in get_cf_future_listing_date(future):
    cur_date = datetime.datetime.now().strftime("%Y%m%d")
    date_list = fd.tradingday(start_date, end_date)
    real_start_date = date_list[0]
    real_end_date = date_list[-1]
    if real_start_date>cur_date:
        continue
    elif real_end_date>cur_date:
        real_end_date = cur_date
    
    os.system("python3 cf_calc_factors.py {} {} {}".format(real_start_date, real_end_date, stock))
    os.system("python3 cf_calc_labels.py {} {} {}".format(real_start_date, real_end_date, stock))
#month_list = sorted([str(i)+str(j).zfill(2) for i in range(2021,2024) for j in range(1,13)])
#month_list.append('202401')
#month_list = [i for i in month_list if i>'202111']
#date_list = []
#for month in month_list:
#    sd = month+"01"
#    ed = month + str(calendar.monthrange(int(month[:4]), int(month[4:]))[1])
#    if month=='202401':
#        ed = month+"16"
#    date_list.append([sd, ed])
#stocks = ['IF00.CF']
#for stock in stocks:
#    for s,e in date_list:
#        print(s, e, stock)
#        os.system("python3 cf_calc_factors.py {} {} {}".format(s,e,stock))
