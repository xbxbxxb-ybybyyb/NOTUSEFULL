import os
import pandas as pd

#key = 'alpha_yzhan_cross'
key = 'alpha_yzhan_meanbs'
pnldir = 'pnlcry10/'
N = 50000
CUT = 0.6
fn = []
for a in os.listdir(pnldir):
  if (a.find(key) >= 0):
    try:
      tmp = int(a.replace('alpha_yzhan_meanbs', ''))
      if (tmp > 1200):continue
    except:
      continue
      
    fn.append(a)

fn.sort()
#print(fn)

sigmp = {}
  
mp = {}
for a in fn:
  
  df = pd.read_csv(pnldir + '/' + a, index_col=0)
  #print(df)
  sign = 1
  if (df['0'].iloc[-1] < 0):sign = -1
  if (abs(df['0'].iloc[-1]) < 1e-7):continue

  if (sign < 0):
    df['0'] = df['0'] * (-1)
  
  df['diff'] = df['0'] - df['0'].shift(1)
  sigmp[a] = df['diff']

  sz = df.shape[0] // 2
  m1 = df['diff'].iloc[0:sz].mean()
  m2 = df['diff'].iloc[sz:].mean()
  ir1 = df['diff'].iloc[0:sz].mean() / (df['diff'].iloc[0:sz].std() + 1e-7)
  ir2 = df['diff'].iloc[sz:].mean() / (df['diff'].iloc[sz:].std() + 1e-7)
  mp[a] = [m1, m2, ir1, ir2]

  if (len(mp) == N):break


df = pd.DataFrame(mp)

df = df.T

dfr = df.rank(ascending=False)
#df['1r'] = df[1].rank()
print(df)
rank = (dfr.max(axis=1))

rank = rank.sort_values()
print(rank)
rank = rank.iloc[0:rank.shape[0] // 2]


libn = []
libs = []


for i in rank.index:
  if (len(libn) == 0):
    libn.append(i)
    libs.append(sigmp[i])
    continue
  
  maxc = -1
  
  for old in libs:
    cc = sigmp[i].corr(old)
    if (abs(cc) > maxc):maxc = abs(cc)
    if (maxc > CUT):break
  if (maxc > CUT):continue

  print(len(libn))
  libn.append(i)
  libs.append(sigmp[i])
  if (len(libn) == 100):break

#print(libn)
#print(df.index)
#print(pd.DataFrame(libn)[0])
res = (df.loc[pd.Index(libn)])
print(res)
res.to_csv('result_full1.csv')

