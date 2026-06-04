from xquant.thirdpartydata.multifactor.IO import *
# 若需读取universe_complete.h5的因子数据，则令alt="universe_complete"
alt = "AShareEODDerivativeIndicator"
#df = read_data([20131115,20131118],alt=alt)
#print(df.head())
# 日志：
# read data from: /app/data/wdb_h5/WIND/universe_complete/universe_complete.h5
# 返回
#                       HS300  Listing_date  OPENDOWNLIMIT  OPENUPLIMIT  SH50  SSO  STPT  SUSPEND  ZZ500
# dt         Ticker
# 2013-11-15 000001.SZ   0.89    19910403.0            1.0          1.0   NaN  1.0   1.0      1.0    NaN
#            000002.SZ   1.43    19910129.0            1.0          1.0   NaN  1.0   1.0      1.0    NaN
#            000004.SZ    NaN    19910114.0            1.0          1.0   NaN  1.0   1.0      1.0    NaN
#            000005.SZ    NaN    19901210.0            1.0          1.0   NaN  1.0   1.0      1.0    NaN
#            000006.SZ    NaN    19920427.0            1.0          1.0   NaN  1.0   1.0      1.0   0.19

# 参数columns，选择读取h5内指定的列
df1 = read_data([20191203],alt=alt)
print(df1.head())
# 返回
#                      HS300  Listing_date  OPENDOWNLIMIT
#dt         Ticker
#2013-11-15 000001.SZ   0.89    19910403.0            1.0
#           000002.SZ   1.43    19910129.0            1.0
#           000004.SZ    NaN    19910114.0            1.0
#           000005.SZ    NaN    19901210.0            1.0
#           000006.SZ    NaN    19920427.0            1.0
