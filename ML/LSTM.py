import torch
import sys
import pandas as pd
import numpy as np
import torch.nn as nn
import torch.optim as optim

# 定义LSTM模型结构
class LSTMModel(nn.Module):
    def __init__(self, input_dim, hidden_dim, layer_dim, output_dim):
        super(LSTMModel, self).__init__()
        self.layer_dim = layer_dim
        self.hidden_dim = hidden_dim
        # 定义LSTM层
        self.lstm = nn.LSTM(input_dim, hidden_dim, layer_dim, batch_first=True)
        # 定义输出层
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        # 初始化隐藏状态和细胞状态
        h0 = torch.zeros(self.layer_dim, x.size(0), self.hidden_dim).requires_grad_()
        c0 = torch.zeros(self.layer_dim, x.size(0), self.hidden_dim).requires_grad_()
        
        # 分离隐藏状态以避免梯度计算中的混淆
        if torch.cuda.is_available():
            h0 = h0.cuda()
            c0 = c0.cuda()

        # LSTM前向传播
        out, (hn, cn) = self.lstm(x, (h0.detach(), c0.detach()))
        # 只选择最后一个时间步的输出
        out = self.fc(out[:, -1, :])
        return out

# 检查是否有可用的GPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 创建模型实例，并移动到GPU（如果可用）
#a = pd.read_csv('playground/TMPDATA_TRADEAGG/process_l2/OUTPUT1M_2023_2024_V1/ETHUSDT_train.csv', index_col=0)
#a = pd.read_csv('EXPRFULL/prod_128.csv', index_col=0)
a = pd.read_pickle('/home/yzhan/playground/TMPDATA_TRADEAGG/process_l2/1MIN_BAR_2021/train.pkl')
#['open', 'close', 'high', 'low', 'meanp', 'volume', 'meanbs', 'sigmabss', 'skewbss', 'skewprc', 'skewqty', 'r1', 'r2', 'r3', 'r4', 'taker_buy_volume', 'taker_sell_volume', 'v0', 'v1', 'v2', 'v3', 'v4', 'v5', 'v6', 'v7', 'v8', 'v9', 'v10', 'v11', 'u0', 'u1', 'w0', 'w1', 'w2', 'w3', 'w4', 'w5', 'w6', 'w7', 'w8', 'w9', 'w10', 'w11', 'p50_open', 'p50_close', 'p50_high', 'p50_low', 'p50_meanp', 'p50_volume', 'p50_meanbs', 'p50_sigmabss', 'p50_skewbss', 'p50_skewprc', 'p50_skewqty', 'p50_r1', 'p50_r2', 'p50_r3', 'p50_r4', 'p50_taker_buy_volume', 'p50_taker_sell_volume', 'p50_v0', 'p50_v1', 'p50_v2', 'p50_v3', 'p50_v4', 'p50_v5', 'p50_v6', 'p50_v7', 'p50_v8', 'p50_v9', 'p50_v10', 'p50_v11', 'p50_u0', 'p50_u1', 'p50_w0', 'p50_w1', 'p50_w2', 'p50_w3', 'p50_w4', 'p50_w5', 'p50_w6', 'p50_w7', 'p50_w8', 'p50_w9', 'p50_w10', 'p50_w11', 'p90_open', 'p90_close', 'p90_high', 'p90_low', 'p90_meanp', 'p90_volume', 'p90_meanbs', 'p90_sigmabss', 'p90_skewbss', 'p90_skewprc', 'p90_skewqty', 'p90_r1', 'p90_r2', 'p90_r3', 'p90_r4', 'p90_taker_buy_volume', 'p90_taker_sell_volume', 'p90_v0', 'p90_v1', 'p90_v2', 'p90_v3', 'p90_v4', 'p90_v5', 'p90_v6', 'p90_v7', 'p90_v8', 'p90_v9', 'p90_v10', 'p90_v11', 'p90_u0', 'p90_u1', 'p90_w0', 'p90_w1', 'p90_w2', 'p90_w3', 'p90_w4', 'p90_w5', 'p90_w6', 'p90_w7', 'p90_w8', 'p90_w9', 'p90_w10', 'p90_w11', 'open_rolling', 'close_rolling', 'high_rolling', 'low_rolling', 'meanp_rolling', 'volume_rolling', 'meanbs_rolling', 'sigmabss_rolling', 'skewbss_rolling', 'skewprc_rolling', 'skewqty_rolling', 'r1_rolling', 'r2_rolling', 'r3_rolling', 'r4_rolling', 'taker_buy_volume_rolling', 'taker_sell_volume_rolling', 'v0_rolling', 'v1_rolling', 'v2_rolling', 'v3_rolling', 'v4_rolling', 'v5_rolling', 'v6_rolling', 'v7_rolling', 'v8_rolling', 'v9_rolling', 'v10_rolling', 'v11_rolling', 'u0_rolling', 'u1_rolling', 'w0_rolling', 'w1_rolling', 'w2_rolling', 'w3_rolling', 'w4_rolling', 'w5_rolling', 'w6_rolling', 'w7_rolling', 'w8_rolling', 'w9_rolling', 'w10_rolling', 'w11_rolling', 'p50_open_rolling', 'p50_close_rolling', 'p50_high_rolling', 'p50_low_rolling', 'p50_meanp_rolling', 'p50_volume_rolling', 'p50_meanbs_rolling', 'p50_sigmabss_rolling', 'p50_skewbss_rolling', 'p50_skewprc_rolling', 'p50_skewqty_rolling', 'p50_r1_rolling', 'p50_r2_rolling', 'p50_r3_rolling', 'p50_r4_rolling', 'p50_taker_buy_volume_rolling', 'p50_taker_sell_volume_rolling', 'p50_v0_rolling', 'p50_v1_rolling', 'p50_v2_rolling', 'p50_v3_rolling', 'p50_v4_rolling', 'p50_v5_rolling', 'p50_v6_rolling', 'p50_v7_rolling', 'p50_v8_rolling', 'p50_v9_rolling', 'p50_v10_rolling', 'p50_v11_rolling', 'p50_u0_rolling', 'p50_u1_rolling', 'p50_w0_rolling', 'p50_w1_rolling', 'p50_w2_rolling', 'p50_w3_rolling', 'p50_w4_rolling', 'p50_w5_rolling', 'p50_w6_rolling', 'p50_w7_rolling', 'p50_w8_rolling', 'p50_w9_rolling', 'p50_w10_rolling', 'p50_w11_rolling', 'p90_open_rolling', 'p90_close_rolling', 'p90_high_rolling', 'p90_low_rolling', 'p90_meanp_rolling', 'p90_volume_rolling', 'p90_meanbs_rolling', 'p90_sigmabss_rolling', 'p90_skewbss_rolling', 'p90_skewprc_rolling', 'p90_skewqty_rolling', 'p90_r1_rolling', 'p90_r2_rolling', 'p90_r3_rolling', 'p90_r4_rolling', 'p90_taker_buy_volume_rolling', 'p90_taker_sell_volume_rolling', 'p90_v0_rolling', 'p90_v1_rolling', 'p90_v2_rolling', 'p90_v3_rolling', 'p90_v4_rolling', 'p90_v5_rolling', 'p90_v6_rolling', 'p90_v7_rolling', 'p90_v8_rolling', 'p90_v9_rolling', 'p90_v10_rolling', 'p90_v11_rolling', 'p90_u0_rolling', 'p90_u1_rolling', 'p90_w0_rolling', 'p90_w1_rolling', 'p90_w2_rolling', 'p90_w3_rolling', 'p90_w4_rolling', 'p90_w5_rolling', 'p90_w6_rolling', 'p90_w7_rolling', 'p90_w8_rolling', 'p90_w9_rolling', 'p90_w10_rolling', 'p90_w11_rolling', 'ret1', 'ret2', 'ret4', 'ret10', 'ret20', 'ret40', 'ret80', 'ret160', 'ret320', 'ret640', 'ret1280', 'ret2560', 'ret5120', 'target']
del a['open']
del a['p50_open']
del a['p90_open']
del a['open_rolling']
del a['p50_open_rolling']
del a['p90_open_rolling']
del a['close']
del a['p50_close']
del a['p90_close']
del a['close_rolling']
del a['p50_close_rolling']
del a['p90_close_rolling']
del a['high']
del a['p50_high']
del a['p90_high']
del a['high_rolling']
del a['p50_high_rolling']
del a['p90_high_rolling']
del a['low']
del a['p50_low']
del a['p90_low']
del a['low_rolling']
del a['p50_low_rolling']
del a['p90_low_rolling']
del a['volume']
del a['p50_volume']
del a['p90_volume']
del a['volume_rolling']
del a['p50_volume_rolling']
del a['p90_volume_rolling']

#aa = a.copy()
a = a[(a['target'] >= -0.3) & (a['target'] <= 0.3)]
a['target'].to_csv('/tmp/rawy.csv')
a = (a - a.rolling(10000).mean()) / (a.rolling(10000).std() + 1e-5)
a['target'].to_csv('/tmp/adjy.csv')
#a = a.iloc[10000:200000, :]
#a['target'] = aa['target']
#print(a)
#exit(0)

print(a.shape)
print(list(a.columns))
#exit(0)
input_dim = a.shape[1] - 1
hidden_dim = 100
layer_dim = 1
output_dim = 1  # 回归任务，输出维度为1
model = LSTMModel(input_dim, hidden_dim, layer_dim, output_dim)
model.to(device)

# 创建优化器和损失函数
optimizer = optim.Adam(model.parameters(), lr=0.01)
loss_fn = nn.MSELoss()

a = a.replace(np.inf, np.nan)
a = a.replace(-np.inf, np.nan)
a = a.fillna(0)
a['target'] = a['target']#* 100
sz = a.shape[0]
isz = sz * 7 // 10

test = a.iloc[isz:, :]
a = a.iloc[:isz, :]
#print(a.iloc[0:3, :])
#exit(0)


BSZ = 30
aa = a.values
tt = test.values

for epoch in range(1, 11):  # 进行10个epoch的训练
    bsz = 32 
    for e in range(BSZ + 32, a.shape[0] - bsz, bsz):
      #local = a.iloc[e:e + bsz, :]

      # 假设输入数据，实际应用中应替换为你的数据
      data = torch.zeros(bsz, BSZ, input_dim, device=device)  # [batch_size, sequence_length, input_size]
      targets = torch.zeros(bsz, output_dim, device=device)  # [batch_size, output_size]

      for v in range(bsz):
        #print(e - 60 + 1 - v)
        #print(e + 1 - v)
        #data[v, :, :] = torch.tensor(a.iloc[e - 60 + 1 - v:e + 1 - v, 0:50].values)
        data[v, :, :] = torch.tensor(aa[e - BSZ + 1 - v:e + 1 - v, 0:input_dim])
        targets[v] = aa[e - v, input_dim]

      model.train()
      optimizer.zero_grad()  # 清除梯度
      outputs = model(data)
      loss = loss_fn(outputs, targets)
      #print(outputs)
      #print(targets)
      loss.backward()  # 反向传播
      optimizer.step()  # 更新权重
      if ((e - BSZ - 32) % 40000 == 0):
        print(f'Epoch: {epoch} | Loss: {loss.item()}')
        sys.stdout.flush() 
      #if (e > 3000):break
    # 假设输入数据，实际应用中应替换为你的数据
    bsz = test.shape[0] - BSZ 
    ss = 10
    #bsz = 200000
    data = torch.zeros(bsz // ss, BSZ, input_dim, device=device)  # [batch_size, sequence_length, input_size]
    targets = torch.zeros(bsz // ss, output_dim, device=device)  # [batch_size, output_size]
    for vv in range(bsz // ss):
      v = vv * ss
      data[vv, :, :] = torch.tensor(tt[v:v + BSZ, 0:input_dim])
      #print(vv)
      targets[vv] = tt[v + BSZ - 1, input_dim]
      #print(targets[vv])
    #exit(0)
      

    
    outputs = model(data)
    #loss = loss_fn(outputs, targets)
    o = (outputs.cpu()).flatten().detach().numpy()
    print(o)
    t = targets.cpu().flatten().numpy()
    print(t)
    #correlation = torch.corr(o, t, value='pearson')
    #print(correlation)
    #print(targets.cpu().numpy())
    print(np.corrcoef(list(o), list(t)))
    #break
      



## 假设输入数据，实际应用中应替换为你的数据
#bsz = 32 
#data = torch.randn(bsz, 100, input_dim, device=device)  # [batch_size, sequence_length, input_size]
#print(data)
#targets = torch.randn(bsz, output_dim, device=device)  # [batch_size, output_size]
#
#for epoch in range(1, 11):  # 进行10个epoch的训练
#    model.train()
#    optimizer.zero_grad()  # 清除梯度
#    outputs = model(data)
#    loss = loss_fn(outputs, targets)
#    loss.backward()  # 反向传播
#    optimizer.step()  # 更新权重
#
#    print(f'Epoch: {epoch} | Loss: {loss.item()}')

