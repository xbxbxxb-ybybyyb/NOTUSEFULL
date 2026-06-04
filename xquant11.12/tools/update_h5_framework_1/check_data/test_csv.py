import pandas as pd

pd.set_option('display.max_columns',None)
pd.set_option('display.max_rows',None)
df = pd.read_csv('AShareBalanceSheet.csv')
print(df)
#print(sum(df['deviation_rate']))
