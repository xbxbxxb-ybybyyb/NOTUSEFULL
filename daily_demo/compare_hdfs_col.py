import pandas as pd
import numpy as np
from pandas.testing import assert_frame_equal

#df1 = pd.read_parquet("3.parquet")
#df2 = pd.read_parquet("13.parquet")
df1 = pd.read_pickle("~/1.pkl")
df2 = pd.read_pickle("~/2.pkl")



#df1 = df1.reindex(columns = df2.columns)

#df1 = df1.replace('None', np.nan).dropna(axis = 1)
#df2 = df2.replace('None', np.nan).dropna(axis = 1)



print(set(df1.columns.tolist())-set(df2.columns.tolist()))
print(set(df2.columns.tolist())-set(df1.columns.tolist()))

df2 = df2.reindex(columns = df1.columns)

print(set(df1['MDTime'].tolist())-set(df2['MDTime'].tolist()))
print(set(df2['MDTime'].tolist())-set(df1['MDTime'].tolist()))

df2 = df2[df2['MDTime'].isin(df1['MDTime'])]

print(df1.shape, df2.shape)
#raise Exception()
for col in df1.columns:
    try:
        assert_frame_equal(df1.loc[:, [col]], df2.loc[:, [col]])
    except:
        import traceback
        print(col)
        print(traceback.print_exc())


