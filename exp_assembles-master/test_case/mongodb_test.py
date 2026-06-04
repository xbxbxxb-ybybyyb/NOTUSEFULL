import sys
sys.path.append("..")
import pandas as pd
pd.set_option("display.max.columns", None)
from artifacts.save_to_mongo import MongoDB

mdb = MongoDB()
df = mdb.load_configs()
print(df)

for item in df.iloc[-1]:
    print(item)
assert len(df) > 0