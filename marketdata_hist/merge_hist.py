import os
import pandas as pd

files = os.listdir("./")

df_list = []
for fidx,file in enumerate(files[0:1200]):
    if 'pkl' not in file:
        continue
    print(file)
    tmp_df = pd.read_pickle(file)
    df_list.append(tmp_df)
    if len(df_list)%200==0:
        df = pd.concat(df_list, axis = 0)
        df.to_pickle("merge/dfdf_{}.pkl".format(fidx))
        df_list = []
    
