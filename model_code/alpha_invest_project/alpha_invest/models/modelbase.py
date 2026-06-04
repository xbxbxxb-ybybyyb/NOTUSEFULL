# -*- coding: utf-8 -*-
from sklearn.model_selection import StratifiedShuffleSplit
import pickle
import numpy as np
import pandas as pd
from alpha_invest import alpha_logger


class ModelMananger:
    def __init__(self, original_datax, original_datay, model_name, model_root_path = "./", **kwags):
        """
        规范：原始因子数据original_datax为multiindex格式，index为date， stock；value为各个因子列
        规范：原始标签数据为multiindex格式，index为date，stock；value为标签列
        :param original_datax:
        :param original_datay:
        :param model_name:
        :param model_root_path:
        """
        self.original_datax = original_datax
        self.original_datay = original_datay
        self.model_name = model_name
        self.dates = list(set(self.original_datax.index.get_level_values(0).tolist()))
        self.tardingcodes = list(set(self.original_datax.index.get_level_values(1).tolist()))
        self.factor_names = self.original_datax.columns
        self.label_name = self.original_datay.columns[0]

    # """
    # X_data,Y_data,data_source,idx_data=datasetLoad2(rootPath)#未划分训练集测试集的数据(不包括背景点)
    # Y_data=np_utils.categorical_probas_to_classes(Y_data)
    # X_train,X_test,Y_train,Y_test,idx_train,idx_test=datasetSplit(X_data,Y_data,idx_data,num_calss=16,test_size=tes_size)
    # data_source: 21025*200, 有训练集和测试集的index编号
    # 手动分割训练集和测试集
    # """
    # def datasetSplit(self,data,lab,idx_of_data,num_calss,test_size):
    #     from keras.utils import np_utils
    #     ssp = StratifiedShuffleSplit(lab,n_iter=1,test_size=test_size)
    #     for trainlab,testlab in ssp:
    #         print("train:\n%s\ntest:\n%s" % (trainlab,testlab))
    #     X_train=data[trainlab]
    #     X_test=data[testlab]
    #     Y_train=np_utils.to_categorical(lab[trainlab],num_calss)
    #     Y_test=np_utils.to_categorical(lab[testlab],num_calss)
    #     idx_train=idx_of_data[trainlab]
    #     idx_test=idx_of_data[testlab]
    #     return X_train,X_test,Y_train,Y_test,idx_train,idx_test

    def save_model(self):
        pass

    def load_model(self):
        pass

    def transform_datax2D(self):
        """
        将multiindex原始因子数据，转换成（stock*date， factor）二维数据
        :return:
        """
        day_factor_cell = []
        for fac in self.original_datax.columns:
            temp_factor = self.original_datax[fac].unstack()
            day_factor_cell.append(temp_factor.values)
            alpha_logger.debug("{} factor shape: {}".format(fac, temp_factor.shape))
        day_factor_cell = np.array(day_factor_cell).transpose([2, 1, 0])
        alpha_logger.debug("{} day_factor_cell tensor source shape: {}".format(fac, day_factor_cell.shape))
        day_factor_cell = day_factor_cell.reshape([len(self.tardingcodes)*len(self.dates), len(self.factor_names)])
        alpha_logger.debug("{} day_factor_cell tensor final shape: {}".format(fac, day_factor_cell.shape))
        return day_factor_cell


    def transform_datax3D(self):
        """
        将multiindex原始因子数据，转换成（stock， date， factor）三维数据
        :return:
        """
        pass

    def transform_datay(self):
        """
        将multiindex原始标签数据，转换成（stock*date， 1）二维数据
        :return:
        """
        day_label_cell = self.original_datay.unstack().values
        day_label_cell = day_label_cell.transpose([1, 0])
        alpha_logger.debug("{} day_label_cell tensor source shape: {}".format(self.label_name, day_label_cell.shape))
        day_label_cell = day_label_cell.reshape([len(self.tardingcodes)*len(self.dates), 1])
        alpha_logger.debug("{} day_label_cell tensor final shape: {}".format(self.label_name, day_label_cell.shape))
        return day_label_cell

    def transforme_torch_dataset_ts(self, window = 10, is_channel_in_front = False):
        """
        将数据转换为时序数据集
        :param window: 时序数据的窗口大小
        :param is_channel_in_front: 特征是否在最前面
        :return:
        """
        from torch.utils.data import Dataset, DataLoader
        import torch
        class TSDataSet(Dataset):
            def __init__(self, df_x, df_y, window=10, is_channel_in_front = False):
                x = df_x.values
                y = df_y.values
                self.stocks = sorted(set(df_x.index.get_level_values(1)))
                self.dates = sorted(set(df_x.index.get_level_values(0)))
                self.factors = df_x.columns.tolist()
                self.window = window
                self.channel_in_front = is_channel_in_front

                # 转为3D
                x = x.reshape((len(self.dates), len(self.stocks), len(self.factors)))
                y = y.reshape((len(self.dates), len(self.stocks), 1))

                if self.channel_in_front:
                    x = np.transpose(x, (2, 0, 1))
                    y = np.transpose(y, (2, 0, 1))

                self.x_train = torch.tensor(x, dtype=torch.float32)
                self.y_train = torch.tensor(y, dtype=torch.float32)

            def __len__(self):
                # idx = len(stocks)*(len(dates)-window+1)
                return (len(self.dates) - self.window + 1) * len(self.stocks)

            def __getitem__(self, idx):
                stock_id = int(idx / (len(self.dates) - self.window + 1))
                date_id = idx - stock_id * (len(self.dates) - self.window + 1)

                if not self.channel_in_front:
                    if self.y_train.shape[2] == 1:
                        return self.x_train[date_id:date_id + self.window, stock_id, :], self.y_train[
                            date_id + self.window - 1, stock_id, 0]
                    else:
                        return self.x_train[date_id:date_id + self.window, stock_id, :], self.y_train[
                                                                                         date_id + self.window - 1,
                                                                                         stock_id, :]
                else:
                    if self.y_train.shape[0] == 1:
                        return self.x_train[:, date_id:date_id + self.window, stock_id], self.y_train[
                            0, date_id + self.window - 1, stock_id]
                    else:
                        return self.x_train[:, date_id:date_id + self.window, stock_id], self.y_train[:,
                                                                                         date_id + self.window - 1,
                                                                                         stock_id]

        return TSDataSet(self.original_datax, self.original_datay, window = window, is_channel_in_front = is_channel_in_front)

    def transforme_torch_dataset(self, ):
        """
        将数据转换为时序数据集
        :param window: 时序数据的窗口大小
        :param is_channel_in_front: 特征是否在最前面
        :return:
        """
        from torch.utils.data import Dataset, DataLoader
        import torch
        class DataSet(Dataset):
            def __init__(self, df_x, df_y, window=10, is_channel_in_front = False):
                self.df_y = df_y
                x = df_x.values
                y = df_y.values
                self.stocks = sorted(set(df_x.index.get_level_values(1)))
                self.dates = sorted(set(df_x.index.get_level_values(0)))
                self.factors = df_x.columns.tolist()
                self.window = window
                self.channel_in_front = is_channel_in_front

                # 转为3D
                x = x.reshape((len(self.dates), len(self.stocks), len(self.factors)))
                y = y.reshape((len(self.dates), len(self.stocks), 1))


                self.x_train = torch.tensor(x, dtype=torch.float32)
                self.y_train = torch.tensor(y, dtype=torch.float32)

            def get_label_index(self):
                return self.df_y.index

            def __len__(self):
                # idx = len(stocks)*(len(dates)-window+1)
                return len(self.dates) * len(self.stocks)

            def __getitem__(self, idx):
                stock_id = int(idx / len(self.dates))
                date_id = idx - stock_id * len(self.dates)

                if self.y_train.shape[2] == 1:
                    return self.x_train[date_id, stock_id, :], self.y_train[
                        date_id, stock_id, 0]
                else:
                    return self.x_train[date_id, stock_id, :], self.y_train[date_id, stock_id, :]
        return  DataSet(self.original_datax, self.original_datay)

    def split_torch_dataset(self, torch_dataset, train_split_ratio = 0.7, random_split = True):
        """
        划分训练和测试集
        :param train_split_ratio:
        :return:
        """
        import torch
        train_split_ratio = float(train_split_ratio)
        train_size = int(len(torch_dataset) * train_split_ratio)
        test_size = len(torch_dataset) - train_size
        print("dataset train size: {}, valid size: {}!".format(train_size, test_size))

        if random_split:
            train_dataset, test_dataset = torch.utils.data.random_split(torch_dataset,
                                                                                  [train_size, test_size])
        else:
            #按顺序切分
            train_indices = list(range(0, train_size))
            test_indices =  list(range(train_size, train_size+test_size))
            train_dataset = torch.utils.data.Subset(torch_dataset, train_indices)
            test_dataset = torch.utils.data.Subset(torch_dataset, test_indices)
        return train_dataset, test_dataset

    def train(self, **kwargs):
        model  = None
        return {'model': model}

    def predict(self, **kwargs):
        infer_result =  None
        return infer_result


if __name__=="__main__":
    if True:
        original_datax = pd.read_pickle("original_datax.pkl")
        original_datay = pd.read_pickle("original_datay.pkl")
    else:
        from alpha_invest.datasets.dataset import DataSetManager
        ds = DataSetManager("20190101", "20191231")
        df_factor = ds.get_factor_data(["close", "open"])
        df_lable = ds.get_label_data(holding_period = 1, label_type='vwap_excess_300')

        stocks = df_lable.columns
        date = df_lable.index
        factor_names = df_factor.keys()
        original_datax = []
        for fac in df_factor:
            temp_factor = df_factor[fac].reindex(columns = stocks, index = date).stack(dropna = False)
            temp_factor.columns = [fac]
            original_datax.append(temp_factor)

        original_datax = pd.concat(original_datax, axis = 1)
        original_datax.columns = factor_names
        original_datay = df_lable.stack(dropna = False)
        original_datay = original_datay.to_frame(name = "vwap_excess_300")
        pickle.dump(original_datax, open("./original_datax.pkl", "wb"))
        pickle.dump(original_datay, open("./original_datay.pkl", "wb"))

    model_mgr = ModelMananger(original_datax, original_datay, model_name = "test_model")
    datax = model_mgr.transform_datax2D()
    datay = model_mgr.transform_datay()