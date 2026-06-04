from StockDataset import StockDataset
from torch.utils.data import DataLoader
from sklearn.preprocessing import StandardScaler
import pandas as pd

def DataProvider(seq_len, pre_len, batch_size, scaler = True):
    
    data = pd.read_feather('/data/user/000055/zjs_project/data/feature.feather')
    data['label'] = data['volume']
    train_data = data[data['T'] < '2024-08-01']
    valid_data = data[(data['T'] >= '2024-08-01') & (data['T'] < '2024-11-01')]
    test_data = data[data['T'] >= '2024-11-01']

    feature = ['volume', 'O_Volume_B', 'O_Volume_S']
    label = ['label']

    feature_scaler = StandardScaler()
    feature_scaler.fit(train_data.loc[:, feature])
    label_scaler = StandardScaler()
    label_scaler.fit(train_data.loc[:, label])

    ######## 标准化 ######## 要做吗？
    if scaler:
        train_data.loc[:, feature] = feature_scaler.transform(train_data.loc[:, feature])
        valid_data.loc[:, feature] = feature_scaler.transform(valid_data.loc[:, feature])
        test_data.loc[:, feature] = feature_scaler.transform(test_data.loc[:, feature])
        train_data.loc[:, label] = label_scaler.transform(train_data.loc[:, label])
        valid_data.loc[:, label] = label_scaler.transform(valid_data.loc[:, label])
        test_data.loc[:, label] = label_scaler.transform(test_data.loc[:, label])

#    print(train_data)
#    print(valid_data)
#    print(test_data)

    train_dataset = StockDataset(train_data, seq_len, pre_len, feature, label)
    valid_dataset = StockDataset(valid_data, seq_len, pre_len, feature, label)
    test_dataset = StockDataset(test_data, seq_len, pre_len, feature, label)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=False)
    valid_loader = DataLoader(valid_dataset, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    
    return train_loader, valid_loader, test_loader, feature_scaler, label_scaler

if __name__ == '__main__':
    
    seq_len = 240
    pre_len = 3
    batch_size = 32
    train_loader, valid_loader, test_loader, feature_scaler, label_scaler = \
        DataProvider(seq_len, pre_len, batch_size, scaler=False)
    for batch_x, batch_y in train_loader:
        print("Batch X shape:", batch_x.shape)  # [batch_size, seq_len, len(features)]
        print(batch_x)
        print("Batch Y shape:", batch_y.shape)  # [batch_size, pred_len]
        print(batch_y)
        break
    
