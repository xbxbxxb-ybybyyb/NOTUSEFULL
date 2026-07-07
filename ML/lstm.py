import torch
import torch.nn as nn
import torch.optim as optim
import random
from torch.nn.utils.rnn import pad_sequence

# ====== 模拟数据 ======
def generate_dataset(num_samples=1000, k=20, min_len=1000, max_len=5000):
    data, targets, lengths = [], [], []
    for _ in range(num_samples):
        T = random.randint(min_len, max_len)   # 随机长度
        x = torch.randn(T, k)                  # 随机特征
        y = torch.randn(1)                     # 随机目标值（回归）
        data.append(x)
        targets.append(y)
        lengths.append(T)
    return data, torch.stack(targets), lengths

data, targets, lengths = generate_dataset()
print(lengths)
#exit(0)

# ====== 构造 batch ======
# pad_sequence 会自动补齐到最长序列
batch = pad_sequence(data, batch_first=True)   # (1000, max_len, k)
lengths = torch.tensor(lengths)                # (1000,)

# ====== 定义模型 ======
class LSTMRegressor(nn.Module):
    def __init__(self, input_size, hidden_size=128, num_layers=2, bidirectional=True):
        super().__init__()
        self.lstm = nn.LSTM(input_size=input_size,
                            hidden_size=hidden_size,
                            num_layers=num_layers,
                            batch_first=True,
                            bidirectional=bidirectional)
        self.fc = nn.Linear(hidden_size * (2 if bidirectional else 1), 1)

    def forward(self, x, lengths):
        packed = nn.utils.rnn.pack_padded_sequence(x, lengths.cpu(),
                                                   batch_first=True, enforce_sorted=False)
        packed_out, (h, c) = self.lstm(packed)
        if self.lstm.bidirectional:
            last_hidden = torch.cat([h[-2], h[-1]], dim=1)
        else:
            last_hidden = h[-1]
        return self.fc(last_hidden)

model = LSTMRegressor(input_size=20, hidden_size=64)
optimizer = optim.Adam(model.parameters(), lr=1e-3)
loss_fn = nn.MSELoss()

print('start train')
# ====== 训练循环 ======
epochs = 5
for epoch in range(epochs):
    model.train()
    print('train done', flush='True')
    optimizer.zero_grad()
    y_pred = model(batch, lengths)
    print('y_pred done', flush='True')
    loss = loss_fn(y_pred.squeeze(), targets.squeeze())
    print('loss_fn done', flush='True')
    loss.backward()
    print('backward done', flush='True')
    optimizer.step()
    print(f"Epoch {epoch+1}, Loss={loss.item():.4f}")
