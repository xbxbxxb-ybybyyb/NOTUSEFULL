# -*- coding: utf-8 -*-
import pickle
import numpy as np
import pandas as pd
from alpha_invest import alpha_logger
import numba

from sklearn.model_selection._split import _BaseKFold, indexable, _num_samples
from sklearn.utils.validation import _deprecate_positional_args

# modified code for group gaps; source
# https://github.com/getgaurav2/scikit-learn/blob/d4a3af5cc9da3a76f0266932644b884c99724c57/sklearn/model_selection/_split.py#L2243
class PurgedGroupTimeSeriesSplit(_BaseKFold):
    """Time Series cross-validator variant with non-overlapping groups.
    Allows for a gap in groups to avoid potentially leaking info from
    train into test if the model has windowed or lag features.
    Provides train/test indices to split time series data samples
    that are observed at fixed time intervals according to a
    third-party provided group.
    In each split, test indices must be higher than before, and thus shuffling
    in cross validator is inappropriate.
    This cross-validation object is a variation of :class:`KFold`.
    In the kth split, it returns first k folds as train set and the
    (k+1)th fold as test set.
    The same group will not appear in two different folds (the number of
    distinct groups has to be at least equal to the number of folds).
    Note that unlike standard cross-validation methods, successive
    training sets are supersets of those that come before them.
    Read more in the :ref:`User Guide <cross_validation>`.
    Parameters
    ----------
    n_splits : int, default=5
        Number of splits. Must be at least 2.
    max_train_group_size : int, default=Inf
        Maximum group size for a single training set.
    group_gap : int, default=None
        Gap between train and test
    max_test_group_size : int, default=Inf
        We discard this number of groups from the end of each train split
    """

    @_deprecate_positional_args
    def __init__(self,
                 n_splits=5,
                 *,
                 max_train_group_size=np.inf,
                 max_test_group_size=np.inf,
                 group_gap=None,
                 verbose=False
                 ):
        super().__init__(n_splits, shuffle=False, random_state=None)
        self.max_train_group_size = max_train_group_size
        self.group_gap = group_gap
        self.max_test_group_size = max_test_group_size
        self.verbose = verbose

    def split(self, X, y=None, groups=None):
        """Generate indices to split data into training and test set.
        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data, where n_samples is the number of samples
            and n_features is the number of features.
        y : array-like of shape (n_samples,)
            Always ignored, exists for compatibility.
        groups : array-like of shape (n_samples,)
            Group labels for the samples used while splitting the dataset into
            train/test set.
        Yields
        ------
        train : ndarray
            The training set indices for that split.
        test : ndarray
            The testing set indices for that split.
        """
        if groups is None:
            raise ValueError(
                "The 'groups' parameter should not be None")
        X, y, groups = indexable(X, y, groups)
        n_samples = _num_samples(X)
        n_splits = self.n_splits
        group_gap = self.group_gap
        max_test_group_size = self.max_test_group_size
        max_train_group_size = self.max_train_group_size
        n_folds = n_splits + 1
        group_dict = {}
        u, ind = np.unique(groups, return_index=True)
        unique_groups = u[np.argsort(ind)]
        n_samples = _num_samples(X)
        n_groups = _num_samples(unique_groups)
        for idx in np.arange(n_samples):
            if (groups[idx] in group_dict):
                group_dict[groups[idx]].append(idx)
            else:
                group_dict[groups[idx]] = [idx]
        if n_folds > n_groups:
            raise ValueError(
                ("Cannot have number of folds={0} greater than"
                 " the number of groups={1}").format(n_folds,
                                                     n_groups))

        group_test_size = min(n_groups // n_folds, max_test_group_size)
        group_test_starts = range(n_groups - n_splits * group_test_size,
                                  n_groups, group_test_size)
        for group_test_start in group_test_starts:
            train_array = []
            test_array = []

            group_st = max(0, group_test_start - group_gap - max_train_group_size)
            for train_group_idx in unique_groups[group_st:(group_test_start - group_gap)]:
                train_array_tmp = group_dict[train_group_idx]

                train_array = np.sort(np.unique(
                    np.concatenate((train_array,
                                    train_array_tmp)),
                    axis=None), axis=None)

            train_end = train_array.size

            for test_group_idx in unique_groups[group_test_start:
            group_test_start +
            group_test_size]:
                test_array_tmp = group_dict[test_group_idx]
                test_array = np.sort(np.unique(
                    np.concatenate((test_array,
                                    test_array_tmp)),
                    axis=None), axis=None)

            test_array = test_array[group_gap:]

            if self.verbose > 0:
                pass

            yield [int(i) for i in train_array], [int(i) for i in test_array]

class DataSetManager:
    def __init__(self, original_datax, original_datay, data_type= 'daily',  **kwags):
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
        self.data_type = data_type
        if data_type == "daily":
            assert type(original_datax.index)==pd.MultiIndex and type(original_datay.index) == pd.MultiIndex, "data_type为Daily类型时，original_datax和original_datay为multiindex格式，index为date， stock；value为各个因子列。"
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
    #     from sklearn.model_selection import StratifiedShuffleSplit
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




    def transform_torch_dataset_ts(self, window = 10, is_channel_in_front = False):
        """
        将数据转换为时序数据集
        :param window: 时序数据的窗口大小
        :param is_channel_in_front: 特征是否在最前面
        :return:
        """
        data_type = self.data_type
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
                df_x和df_y都含有stock、mddate、mdtime三列，且已经按照stock、mddate、mdtime排序
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

                # 按标的和天对数据分段，每段有timestamp个原始时间戳，每段产生len(timestamp)-window+1个训练样本
                # key为每段开始时，第一个训练样本在全体训练样本中的编号，value为stock，mddate，timestamp_idx(每段第一个时间戳在整个df中的编号)
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
                                    ridx - timestamp_idx - window + 1)  # ridx-timestamp_idx+1表示两个因子时间戳间的mdtime个数，-window+1表示产生的训练样本个数
                            #                     print(timestamp_idx, ridx, sample_idx, stock, mddate, timestamp_idx)
                            timestamp_idx = ridx  # timestamp_idx, 实际时间戳的起始id
                            location_stats[sample_idx] = (stock, mddate, timestamp_idx)

                self.location_stats = location_stats
                self.location_stats_keys = np.array(list(location_stats.keys()))

                if self.channel_in_front:
                    raise Exception("Does not support channel_in_front True for Tick data!")
                    # self.x = np.transpose(self.x, (1, 0))
                    # self.y = np.transpose(self.y, (1, 0))
                #增加一维channel
                self.x = self.x.reshape(1, self.x.shape[0], self.x.shape[1])

            def __len__(self):
                if not self.channel_in_front:
                    return self.location_stats_keys[-1] + (
                                self.x.shape[1] - self.location_stats[self.location_stats_keys[-1]][2] - self.window+1)


            def __getitem__(self, idx):
                #TODO: 支持1D， 2D结构
                sample_start_idx = self.location_stats_keys[0]
                timestamp_start_idx = self.location_stats[sample_start_idx][2]

                # 找到该idx样本所属分段的起始位置
                sample_start_idx = find_sample_start_idx(idx, self.location_stats_keys)
                timestamp_start_idx = self.location_stats[sample_start_idx][2]

                offset = idx - sample_start_idx  # 相比样本的开始索引差多少
                if not self.channel_in_front:
                    x = self.x[:, timestamp_start_idx + offset: timestamp_start_idx + offset + self.window, :]
                    y = self.y[timestamp_start_idx + offset: timestamp_start_idx + offset + self.window, 0][-1]
                    return x, y
                else:
                    x = self.x[:, :, timestamp_start_idx + offset:timestamp_start_idx + offset + self.window]
                    y = self.y[timestamp_start_idx + offset:timestamp_start_idx + offset + self.window][-1]
                    return x, y

        if data_type == 'daily':
            return TSDailyDataSet(self.original_datax, self.original_datay, window = window,
                                  is_channel_in_front = is_channel_in_front)
        else:
            return TSTickDataSet(self.original_datax, self.original_datay, window=window,
                                  is_channel_in_front=is_channel_in_front)

    def transform_torch_dataset(self, ):
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

    ################################测试时间序列数据划分##############################################
    import torch

    x = pd.DataFrame([[1, 1, 1, 1], [2, 2, 2, 2], [3, 3, 3, 3], [4, 4, 4, 4]], columns=['fac1', 'fac2', 'fac3', 'fac4'])
    y = pd.DataFrame([1, 1, 1, 1], columns=['tag1'])

    x['mddate'] = '20190701'
    x['stock'] = '001'
    x['timestamp'] = range(10, 14)

    y['mddate'] = '20190701'
    y['stock'] = '001'
    y['timestamp'] = range(10, 14)

    x1 = deepcopy(x)
    x1['mddate'] = '20190702'
    y1 = deepcopy(y)
    y1['mddate'] = '20190702'

    x2 = deepcopy(x)
    x2['mddate'] = '20190703'
    y2 = deepcopy(y)
    y2['mddate'] = '20190703'

    xx = pd.concat([x, x1, x2], axis=0)
    yy = pd.concat([y, y1, y2], axis=0)

    dmanager_train = DataSetManager(xx, yy, data_type='tick')
    dataset_train = dmanager_train.transform_torch_dataset_ts(window=3, is_channel_in_front=True)

    train_loader = torch.utils.data.DataLoader(dataset=dataset_train, batch_size=1, shuffle=False, drop_last=False)

    for inputs, targets in train_loader:
        print(inputs, targets)