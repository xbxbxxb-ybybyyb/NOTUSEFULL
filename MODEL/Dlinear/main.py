import torch
import DLinear
import torch.nn as nn
from DataProvider import DataProvider
from EarlyStopping import EarlyStopping

# 模型参数
class Configs:
    seq_len = 240
    pred_len = 1
    batch_size = 32
    kernel_size = 5      # 求trend的滑动窗口，感觉可调？？？   奇数！！！
    enc_in = 3      # features数量，要和DataProvider中feature定义长度保持一致
    c_out = 1       # label数量，……一致
    individual = False      # 是否独立建模

configs = Configs()
scaler = True
num_epoch = 1000
lr = 5 * 1e-4
patience = 10
model_path = '/data/user/000055/zjs_project/DLinear_model/best_model.pth'
early_stopping = EarlyStopping(patience=patience, verbose=True, path=model_path)

train_loader, valid_loader, test_loader, feature_scaler, label_scaler = \
    DataProvider(configs.seq_len, configs.pred_len, configs.batch_size, scaler)
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model = DLinear.Model(configs)
model = model.to(device)

# 损失函数
criterion = nn.MSELoss()
# 优化器
optimizer = torch.optim.Adam(model.parameters(), lr=lr)

# train
def train_one_epoch(model, dataloader, criterion, optimizer, device):
    model.train()
    total_loss = 0
    for batch in dataloader:
        x, y = batch
        x, y = x.to(device), y.to(device)
        # 前向传播
        preds = model(x)  # 输出形状：[Batch, pred_len, Channel]
        # 计算损失
        loss = criterion(preds, y)
        total_loss += loss.item()
        # 反向传播与优化
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    return total_loss / len(dataloader)

# valid
@torch.no_grad()
def validate(model, dataloader, criterion, device):
    model.eval()
    total_loss = 0
    for batch in dataloader:
        x, y = batch
        x, y = x.to(device), y.to(device)
        # 前向传播
        preds = model(x)
        # 计算损失
        loss = criterion(preds, y)
        total_loss += loss.item()
        
    return total_loss / len(dataloader)

for epoch in range(num_epoch):
    train_loss = train_one_epoch(model, train_loader, criterion, optimizer, device)
    val_loss = validate(model, valid_loader, criterion, device)
    print(f"Epoch {epoch+1}/{num_epoch}, Train Loss: {train_loss:.6f}, Val Loss: {val_loss:.6f}")
    # 调用早停机制
    early_stopping(val_loss, model)
    # 检查是否需要停止
    if early_stopping.early_stop:
        print("Early stopping triggered!")
        break








