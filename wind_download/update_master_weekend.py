# -*- coding: utf-8 -*-
"""
# data update master
"""
from multifactor.data.utils import *
from weekend_job_wind_htsc import first_job
from update_wind import wind_weekend_job
import settings


def get_current_date():
    current_time = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    current_date = int(current_time[:8])
    h5_path = os.path.join(settings.BASE_DIR, 'CALENDAR/nature_days.h5')
    fdate_list_dt = IO.read_data([19980101, 20210101], alt=h5_path).index.get_level_values(0)
    fdate_list = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in fdate_list_dt]
    idx = fdate_list.index(current_date)
    return fdate_list[idx - 2], fdate_list[idx - 1], current_date


lst_workday, sdate, edate = get_current_date()
flag_root = os.path.join(settings.BASE_DIR, 'LOCAL_DATA/FLAG/' + str(edate))
if not os.path.exists(flag_root):
    os.mkdir(flag_root)

first_job(sdate, edate)
wind_weekend_job()

flag_path = os.path.join(flag_root, str(edate) + '_' + 'FDD.success')
with open(flag_path, 'w') as file:
    pass
