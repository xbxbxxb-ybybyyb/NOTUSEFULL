import os
import sys
import pandas as pd

cmd='cp -fr /data/group/800020/AlphaDataCenter/* /data/group/800469/AlphaDataCenter/'
os.system(cmd)

t = pd.read_pickle('/data/user/012620/AlphaDataCenter/factor_day_path_dict.pkl')
pd.to_pickle(t,'/data/group/800469/AlphaDataCenter/Department/DepartSample/factor_day_path_dict.pkl')

t = pd.read_pickle('/data/user/012620/AlphaDataCenter/factor_label_path_dict.pkl')
pd.to_pickle(t,'/data/group/800469/AlphaDataCenter/Department/DepartSample/factor_label_path_dict.pkl')