import pandas as pd
fac = pd.read_hdf('/data/user/015618/Production20200221/Apollo/AlphaDataBase/Data_alpha_universe.h5','factor')
print(fac.loc[20200220,['002919.SZ', '600615.SH']])
fac.loc[20200220,['002919.SZ', '600615.SH']] = 1
store = pd.HDFStore('/data/user/015616/Production/Production20200221/Apollo/AlphaDataBase/Data_alpha_universe.h5')
store['factor'] = fac
store.close()
print(fac.loc[20200220,['002919.SZ', '600615.SH']])