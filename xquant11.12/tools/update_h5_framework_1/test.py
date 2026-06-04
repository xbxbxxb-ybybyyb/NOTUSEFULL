from Wind.utils import *
import pandas as pd
pd.set_option('display.max_columns',None)

h5_path = "/app/data/wdb_h5/WIND/AShareMonthlyReportsofBrokers/AShareMonthlyReportsofBrokers.h5"
h5_path2 = "/app/data/wdb_h5/WIND_TEST/AShareEODDerivativeIndicator/AShareEODDerivativeIndicator.h5"
df = read_data([20191202,20191202],alt=h5_path2)
print(df.head())
#df.to_csv('INDUSTRY.csv')
#with pd.HDFStore(h5_path) as h5_store:
#    factor = "CITIC_I"
#    date_ticker = pd.Timestamp('20140604')
#    record_num = h5_store.remove(factor,'dt=date_ticker')
    
        



