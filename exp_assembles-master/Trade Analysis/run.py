import os
from datetime import datetime
import sys

try:
    date = sys.argv[1]
except:
    date = datetime.now().strftime("%Y%m%d")

assert os.system("cd /data/user/013150/online_scripts/crontab_tasks && sh onnx_version.sh")==0

assert os.system('curl ftp://168.8.2.68/016869/dolphin_server/start.sh -u "ftphzh:ftphzh2602" -O && sh start.sh && cd /home/appadmin/server && sh startSingle.sh')==0

try:
    assert os.system("cd /data/user/013150/online_scripts/crontab_tasks && python3 /data/user/013150/online_scripts/crontab_tasks/trade_analysis_v2.py 000977.SZ 000977.SZ_trade_v1.1 {}".format(date))==0
except:
    os.system("cd /data/user/013150/online_scripts/crontab_tasks && python3 /data/user/013150/online_scripts/crontab_tasks/trade_analysis_v1.4_old.py 000977.SZ 000977.SZ_trade_v1.1 {}".format(date))

try:
    assert os.system("cd /data/user/013150/online_scripts/crontab_tasks && python3 /data/user/013150/online_scripts/crontab_tasks/trade_analysis_v2.py 688012.SH 688012.SH_trade_v1.2 {}".format(date))==0
except:
    os.system("cd /data/user/013150/online_scripts/crontab_tasks && python3 /data/user/013150/online_scripts/crontab_tasks/trade_analysis_v1.4_old.py 688012.SH 688012.SH_trade_v1.2 {}".format(date))
    
try:
    assert os.system("cd /data/user/013150/online_scripts/crontab_tasks && python3 /data/user/013150/online_scripts/crontab_tasks/trade_analysis_v2.py 688111.SH 688111.SH_trade_v1.1 {}".format(date))==0
except:
    os.system("cd /data/user/013150/online_scripts/crontab_tasks && python3 /data/user/013150/online_scripts/crontab_tasks/trade_analysis_v1.4_old.py 688111.SH 688111.SH_trade_v1.1 {}".format(date))
    
try:
    assert os.system("cd /data/user/013150/online_scripts/crontab_tasks && python3 /data/user/013150/online_scripts/crontab_tasks/trade_analysis_v2.py 002594.SZ 002594.SZ_trade_v1.1 {}".format(date))==0
except:
    os.system("cd /data/user/013150/online_scripts/crontab_tasks && python3 /data/user/013150/online_scripts/crontab_tasks/trade_analysis_v1.4_old.py 002594.SZ 002594.SZ_trade_v1.1 {}".format(date))
    
try:
    assert os.system("cd /data/user/013150/online_scripts/crontab_tasks && python3 /data/user/013150/online_scripts/crontab_tasks/trade_analysis_v2.py 688256.SH 688256.SH_trade_v1.1 {}".format(date))==0
except:
    os.system("cd /data/user/013150/online_scripts/crontab_tasks && python3 /data/user/013150/online_scripts/crontab_tasks/trade_analysis_v1.4_old.py 688256.SH 688256.SH_trade_v1.1 {}".format(date))

try:
    assert os.system("cd /data/user/013150/online_scripts/crontab_tasks && python3 /data/user/013150/online_scripts/crontab_tasks/trade_analysis_v2.py 688017.SH 688017.SH_trade_v1.1 {}".format(date))==0
except:
    os.system("cd /data/user/013150/online_scripts/crontab_tasks && python3 /data/user/013150/online_scripts/crontab_tasks/trade_analysis_v1.4_old.py 688017.SH 688017.SH_trade_v1.1 {}".format(date))

try:
    assert os.system("cd /data/user/013150/online_scripts/crontab_tasks && python3 /data/user/013150/online_scripts/crontab_tasks/trade_analysis_v2.py 688598.SH 688598.SH_trade_v1.2 {}".format(date))==0
except:
    os.system("cd /data/user/013150/online_scripts/crontab_tasks && python3 /data/user/013150/online_scripts/crontab_tasks/trade_analysis_v1.4_old.py 688598.SH 688598.SH_trade_v1.2 {}".format(date))

try:
    assert os.system("cd /data/user/013150/online_scripts/crontab_tasks && python3 /data/user/013150/online_scripts/crontab_tasks/trade_analysis_v2.py 688536.SH 688536.SH_trade_v1.1 {}".format(date))==0
except:
    os.system("cd /data/user/013150/online_scripts/crontab_tasks && python3 /data/user/013150/online_scripts/crontab_tasks/trade_analysis_v1.4_old.py 688536.SH 688536.SH_trade_v1.1 {}".format(date))

try:
    assert os.system("cd /data/user/013150/online_scripts/crontab_tasks && python3 /data/user/013150/online_scripts/crontab_tasks/trade_analysis_v2.py 688036.SH 688036.SH_trade_v1.1 {}".format(date))==0   
except:
    os.system("cd /data/user/013150/online_scripts/crontab_tasks && python3 /data/user/013150/online_scripts/crontab_tasks/trade_analysis_v1.4_old.py 688036.SH 688036.SH_trade_v1.1 {}".format(date))

try:
    assert os.system("cd /data/user/013150/online_scripts/crontab_tasks && python3 /data/user/013150/online_scripts/crontab_tasks/trade_analysis_v2.py 688521.SH 688521.SH_trade_v1.1 {}".format(date))==0
except:
    os.system("cd /data/user/013150/online_scripts/crontab_tasks && python3 /data/user/013150/online_scripts/crontab_tasks/trade_analysis_v1.4_old.py 688521.SH 688521.SH_trade_v1.1 {}".format(date))

try:
    assert os.system("cd /data/user/013150/online_scripts/crontab_tasks && python3 /data/user/013150/online_scripts/crontab_tasks/trade_analysis_v2.py 688385.SH 688385.SH_trade_v1.1 {}".format(date))==0
except:
    os.system("cd /data/user/013150/online_scripts/crontab_tasks && python3 /data/user/013150/online_scripts/crontab_tasks/trade_analysis_v1.4_old.py 688385.SH 688385.SH_trade_v1.1 {}".format(date))

try:
    assert os.system("cd /data/user/013150/online_scripts/crontab_tasks && python3 /data/user/013150/online_scripts/crontab_tasks/trade_analysis_v2.py 688599.SH 688599.SH_trade_v1.2 {}".format(date))==0
except:
    os.system("cd /data/user/013150/online_scripts/crontab_tasks && python3 /data/user/013150/online_scripts/crontab_tasks/trade_analysis_v1.4_old.py 688599.SH 688599.SH_trade_v1.2 {}".format(date))

try:
    assert os.system("cd /data/user/013150/online_scripts/crontab_tasks && python3 /data/user/013150/online_scripts/crontab_tasks/trade_analysis_v2.py 688303.SH 688303.SH_trade_v1.1 {}".format(date))==0
except:
    os.system("cd /data/user/013150/online_scripts/crontab_tasks && python3 /data/user/013150/online_scripts/crontab_tasks/trade_analysis_v1.4_old.py 688303.SH 688303.SH_trade_v1.1 {}".format(date))

