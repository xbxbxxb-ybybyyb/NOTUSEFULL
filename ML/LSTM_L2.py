import torch
import sys
import pandas as pd
import numpy as np
import torch.nn as nn
import torch.optim as optim

def regularization_loss(model):
    l2_lambda = 1e-5  # L2正则化系数
    l1_lambda = 1e-5    # L1正则化系数，如果不需要可以设置为0
 
    l2_reg = sum(l2_lambda * torch.norm(v, 2) for v in model.parameters() if v.requires_grad)
    l1_reg = sum(l1_lambda * torch.norm(v, 1) for v in model.parameters() if v.requires_grad)
    return l2_reg + l1_reg

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
#input_dim = 271
input_dim = 35
hidden_dim = 20
layer_dim = 2
output_dim = 1  # 回归任务，输出维度为1
model = LSTMModel(input_dim, hidden_dim, layer_dim, output_dim)
model.to(device)

# 创建优化器和损失函数
optimizer = optim.Adam(model.parameters(), lr=0.00001)
loss_fn = nn.MSELoss()

#a = pd.read_csv('playground/TMPDATA_TRADEAGG/process_l2/OUTPUT1M_2023_2024_V1/ETHUSDT_train.csv', index_col=0)
a = pd.read_csv('/home/yzhan/yzhan/DATA/train.csv', index_col=0)
print(a.shape)
a = a.replace(np.inf, np.nan)
a = a.replace(-np.inf, np.nan)
a = a.fillna(0)
a['target'] = a['target'] * 100
sz = a.shape[0]
isz = sz * 7 // 10

test = a.iloc[isz:, :]
a = a.iloc[:isz, :]
#print(a.iloc[0:3, :])
#exit(0)


BSZ = 60
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
      loss = loss_fn(outputs, targets) + 10 * regularization_loss(model)
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

