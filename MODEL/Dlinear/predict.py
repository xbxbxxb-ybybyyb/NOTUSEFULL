import torch
import numpy as np
from DataProvider import DataProvider
import DLinear

class Configs:
    seq_len = 240
    pred_len = 1
    batch_size = 32
    kernel_size = 5      # 求trend的滑动窗口，感觉可调？？？
    enc_in = 3      # features数量，要和DataProvider中feature定义长度保持一致
    c_out = 1       # label数量，……一致
    individual = True      # 是否独立建模

configs = Configs()
scaler = True

train_loader, valid_loader, test_loader, feature_scaler, label_scaler = \
    DataProvider(configs.seq_len, configs.pred_len, configs.batch_size, scaler)
device = 'cuda' if torch.cuda.is_available() else 'cpu'

model = DLinear.Model(configs)  # 定义模型结构
model.load_state_dict(torch.load('/data/user/000055/zjs_project/DLinear_model/best_model.pth'))  # 加载模型参数
model = model.to(device)
model.eval()
# 进行预测
predictions = []
with torch.no_grad():
    for batch_x, batch_y in test_loader:
        batch_x = batch_x.to(device)
        outputs = model(batch_x)  # 模型预测
        predictions.append(outputs.cpu().numpy())

# 合并所有批次的预测结果
predictions = np.concatenate(predictions, axis=0)  # [Total_Samples, Pred_Length, num_targets]
#print(predictions.shape)
predictions = np.squeeze(predictions, -1)
#print(predictions)
#print(predictions.shape)
# inverse
inverse_predictions = []
# 对每列进行 inverse_transform
if configs.pred_len != 1:
    for i in range(configs.pred_len):
        col = predictions[:, i].reshape(-1, 1)  # 提取第 i 列并转换为 [batch_size, 1]
        inverse_col = label_scaler.inverse_transform(col)  # 对该列进行逆标准化
        inverse_predictions.append(inverse_col)
    inverse_predictions = np.hstack(inverse_predictions)
else:
    inverse_predictions = label_scaler.inverse_transform(predictions)
print(inverse_predictions)
print(inverse_predictions.shape)
np.save('/data/user/000055/zjs_project/DLinear_model/prediction3_test.npy', inverse_predictions)

# 保存为 CSV 文件
#df = pd.DataFrame(predictions_2d, columns=[f"Target_{i}" for i in range(predictions_2d.shape[1])])
#df.to_csv('predictions.csv', index=False)









