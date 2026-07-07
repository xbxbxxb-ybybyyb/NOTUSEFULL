import pandas as pd
import numpy as np
import random


N = 10

P = np.random.rand(N)
P = P / np.sum(P)#each state prob
#P[0] = P[1] = 0.5#equal prob test, if N=2 P=PP = 0.5, r=0.5 res = 0.666666

PP = np.random.rand(N, N) #transfer matrix
#PP = np.ones((N, N)) #transfer matrix
for i in range(N): PP[i, :] = PP[i, :] / np.sum(PP[i, :])


#find E(r^T) in two method T is first time state = 0

r = 0.8

def Method1(r, P, PP, N):
  minG = 0
  LEN = 100000
  inits = []
  for i in range(N): inits = inits + [i] * int(P[i] * LEN)
  while (len(inits) < LEN):inits.append(random.randint(0, N - 1))
  transfer = []
  for i in range(N): 
    local_inits = []
    for j in range(N): 
      local_inits = local_inits + [j] * int(PP[i][j] * LEN)
    while (len(local_inits) < LEN):local_inits.append(random.randint(0, N - 1))
    random.shuffle(local_inits)
    transfer.append(local_inits)

  random.shuffle(inits)
  s = 0#sum
  c = 0#cnt
  old = 0
  newv = 0
  for x in range(100000):
    local_s = 1
    t = inits[random.randint(0, LEN - 1)]
    while (t != minG):
      local_s *= r
      rr = random.randint(0, LEN - 1)
      t = transfer[t][rr]
    s += local_s
    c += 1.0
    newv = s / c
  return s / c

      
def Method2(r, P, PP, N):
  
  a = np.zeros((N-1, N-1))
  b = np.zeros((N-1, 1))
  
  for i in range(N-1):
    for j in range(N-1):
      a[i][j] = -r * PP[i+1][j+1]
    a[i][i] += 1
    b[i] = r * PP[i+1][0]
  from scipy.linalg import solve
  x = solve(a, b)
    
  res = 1 * P[0]
  for i in range(N-1):
    res += x[i][0] * P[i + 1]
  return res
    
#method1为模拟解
#method2为显式解，基本一样
#你需要根据你的场景填入数字
#它会返回 E(r^T), 其中，T为初始概率为P, 转移概率矩阵为PP[N][N] 的随
#机过程第一次如果进入状态0(你这里的minG), 的
#r=r,初始概率为P, 转移概率矩阵为PP[N][N], N为状态数 
E1 = Method1(r, P, PP, N)
E2 = Method2(r, P, PP, N)
print(E1)
print(E2)
