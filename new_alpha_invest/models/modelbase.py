# -*- coding: utf-8 -*-
from sklearn.model_selection import StratifiedShuffleSplit
import pickle
import numpy as np
import pandas as pd
from alpha_invest import alpha_logger
import numba


class ModelManager:
    def __init__(self, original_datax, original_datay, model_name, model_root_path = "./", data_type= 'daily',  **kwags):
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
        if data_type == "daily":
            self.dates = list(set(self.original_datax.index.get_level_values(0).tolist()))
            self.tradingcodes = list(set(self.original_datax.index.get_level_values(1).tolist()))
            self.factor_names = self.original_datax.columns
            self.label_name = self.original_datay.columns[0]
        else:
            self.stocks = sorted(set(original_datax['stock']))
            self.dates = sorted(set(original_datax['mddate']))
            self.factor_names = original_datax.columns.tolist()
            self.label_name = original_datay.columns.tolist()

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
        day_factor_cell = day_factor_cell.reshape([len(self.tradingcodes)*len(self.dates), len(self.factor_names)])
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
        day_label_cell = day_label_cell.reshape([len(self.tradingcodes)*len(self.dates), 1])
        alpha_logger.debug("{} day_label_cell tensor final shape: {}".format(self.label_name, day_label_cell.shape))
        return day_label_cell

    def transform_torch_dataset_ts(self, window = 10, is_channel_in_front = False, data_type = 'daily'):
        """
        将数据转换为时序数据集
        :param window: 时序数据的窗口大小
        :param is_channel_in_front: 特征是否在最前面
        :return:
        """
        from torch.utils.data import Dataset, DataLoader
        import torch
        class TSDailyDataSet(Dataset):
            """
            日频数据转成时间序列格式
            """
            def __init__(self, df_x, df_y, window=10, is_channel_in_front = False):
                """
                :param df_x: 因子数据，行为日期股票的multiindex，列为各个因子
                :param df_y: 标签数据，行为日期股票的multiindex，列为单个标签
                :param window: 时间序列窗口的长度
                :param is_channel_in_front: channel表示因子维度，若为False，则因子位于第三维，若为True，则因子位于第一维
                """
                x = df_x.values
                y = df_y.values
                self.stocks = sorted(set(df_x.index.get_level_values(1)))
                self.dates = sorted(set(df_x.index.get_level_values(0)))
                self.factors = df_x.columns.tolist()
                self.window = window
                self.channel_in_front = is_channel_in_front

                # 转为3D
                x = x.reshape((len(self.dates), len(self.stocks), len(self.factors)))# x必须按日期和股票排序
                y = y.reshape((len(self.dates), len(self.stocks), 1))

                if self.channel_in_front:
                    x = np.transpose(x, (2, 0, 1))
                    y = np.transpose(y, (2, 0, 1))

                self.x_train = torch.tensor(x, dtype=torch.float32)
                self.y_train = torch.tensor(y, dtype=torch.float32)

            def __len__(self):
                """
                排除每个票最后几天无标签数据的情况。
                :return:
                """
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

        @numba.jit(nopython=True)
        def find_sample_start_idx(idx, location_stats_keys):
            for kidx, key in enumerate(location_stats_keys):
                if key <= idx:
                    sample_start_idx = key
                    #             print(sample_start_idx, timestamp_start_idx)
                else:
                    break
            return sample_start_idx

        class TSTickDataSet(Dataset):
            def __init__(self, df_x, df_y, window=10, is_channel_in_front=False):
                """
                要求：df_x和df_y的时间戳已对齐，有一样的行数；
                df_x和df_y都已经按照stock、mddate、mdtime排序
                :param df_x:
                :param df_y:
                :param window:
                :param is_channel_in_front:
                """
                assert len(df_x) == len(df_y), "请确保df_x和df_y的时间戳已对齐，有一样的行数，且都已经按照stock、mddate、timestamp排序！"
                defined_columns = ['stock', 'mddate', 'timestamp']
                assert defined_columns[0] in df_x.columns.tolist() and defined_columns[1] in df_x.columns.tolist() \
                    and defined_columns[2] in df_x.columns.tolist(), "请确保df_x中包含stock、mddate、timestamp三列！"
                assert defined_columns[0] in df_y.columns.tolist() and defined_columns[1] in df_y.columns.tolist() \
                       and defined_columns[2] in df_y.columns.tolist(), "请确保df_y中包含stock、mddate、timestamp三列！"


                df_x = df_x.reindex(columns=defined_columns + [col for col in df_x.columns if
                                                               col not in defined_columns])
                df_y = df_y.reindex(columns=defined_columns + [col for col in df_y.columns if
                                                               col not in defined_columns])


                self.x = df_x.iloc[:, 3:].values
                self.y = df_y.iloc[:, 3:].values
                self.stocks = sorted(set(df_x['stock']))
                self.dates = sorted(set(df_x['mddate']))
                self.factors = df_x.columns.tolist()
                self.window = window
                self.channel_in_front = is_channel_in_front

                # 按标的和票对数据分段，每段有timestamp个原始时间戳，每段产生len(timestamp)-window+1个训练样本
                # key为每段开始时，第一个训练样本在全局的编号，value为stock，mddate，timestamp_idx(每段第一个时间戳在全局的编号)
                location_stats = {}
                index_array = df_x.loc[:, ['stock', 'mddate', 'timestamp']].values
                for ridx, row in enumerate(index_array):
                    if ridx == 0:
                        stock = row[0]
                        mddate = row[1]
                        sample_idx = ridx  # 训练样本的起始id（训练样本小于因子时间戳个数）
                        timestamp_idx = ridx  # timestamp_idx, 因子时间戳的起始id
                        location_stats[sample_idx] = (stock, mddate, timestamp_idx)
                    else:
                        if row[0] == stock and row[1] == mddate:
                            continue
                        else:
                            stock = row[0]
                            mddate = row[1]
                            sample_idx = sample_idx + (
                                    ridx - timestamp_idx + 1 - window + 1)  # ridx-timestamp_idx+1表示两个因子时间戳间的mdtime个数，-window+1表示产生的训练样本个数
                            #                     print(timestamp_idx, ridx, sample_idx, stock, mddate, timestamp_idx)
                            timestamp_idx = ridx  # timestamp_idx, 实际时间戳的起始id
                            location_stats[sample_idx] = (stock, mddate, timestamp_idx)

                self.location_stats = location_stats
                self.location_stats_keys = np.array(list(location_stats.keys()))

                if self.channel_in_front:
                    self.x = np.transpose(self.x, (1, 0))
                    self.y = np.transpose(self.y, (1, 0))

            def __len__(self):
                return self.location_stats_keys[-1] + (
                            len(self.x) - self.location_stats[self.location_stats_keys[-1]][2] - self.window)

            def __getitem__(self, idx):
                #TODO: 支持1D， 2D结构
                sample_start_idx = self.location_stats_keys[0]
                timestamp_start_idx = self.location_stats[sample_start_idx][2]

                # 找到该idx样本所属分段的起始位置
                sample_start_idx = find_sample_start_idx(idx, self.location_stats_keys)
                timestamp_start_idx = self.location_stats[sample_start_idx][2]

                offset = idx - sample_start_idx  # 相比样本的开始索引差多少
                if not self.channel_in_front:

                    x = self.x[timestamp_start_idx + offset: timestamp_start_idx + offset + self.window, :].reshape(1, window, -1)
                    y = self.y[timestamp_start_idx + offset: timestamp_start_idx + offset + self.window, 0][-1]
                    return x, y
                else:
                    x = self.x[:, timestamp_start_idx + offset:timestamp_start_idx + offset + self.window].reshape(1, window, -1)
                    y = self.y[:, timestamp_start_idx + offset:timestamp_start_idx + offset + self.window][-1]
                    return x, y

        if data_type == 'daily':
            return TSDailyDataSet(self.original_datax, self.original_datay, window = window,
                                  is_channel_in_front = is_channel_in_front)
        else:
            return TSTickDataSet(self.original_datax, self.original_datay, window=window,
                                  is_channel_in_front=is_channel_in_front)

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

    model_mgr = ModelManager(original_datax, original_datay, model_name = "test_model")
    datax = model_mgr.transform_datax2D()
    datay = model_mgr.transform_datay()
