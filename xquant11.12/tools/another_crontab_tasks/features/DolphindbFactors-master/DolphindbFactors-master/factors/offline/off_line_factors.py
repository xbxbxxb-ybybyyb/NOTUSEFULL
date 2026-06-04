import pandas as pd
import os
offline_factors = pd.read_csv("bad_perf_factors.csv")
offline_factors.columns = ['factors','a','b','c']
offline_factors = list(set(offline_factors['factors'].values.tolist()))
print(len(offline_factors))
print(offline_factors)
for root,dir,files in os.walk("../all/all_factors/"):
    for file in files:
        if file[:-4] in offline_factors:
            os.system("mv {} {}".format(os.path.join(root, file), "./offline_factors/"))
            #print("mv {} {}".format(os.path.join(root, file), "./offline_factors/"))

