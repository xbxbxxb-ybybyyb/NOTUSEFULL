from alpha_invest.datasets.dataset_loader import DatasetLoader

dloader = DatasetLoader()
dloader.load_factor_data(factor_path="/data/user/quanttest007/alpha_invest/merge_data.pkl", classify_or_not=False,
                         mock_data_flag=True, num_features=100,
                         tag_name="Tag5minRet")
factor_data_train, factor_data_test, label_data_train, label_data_test = dloader.train_test_split(
    train_test_split_date="20220601")
print(1)



from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
