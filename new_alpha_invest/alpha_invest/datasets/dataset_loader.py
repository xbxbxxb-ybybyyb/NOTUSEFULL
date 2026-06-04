import pandas as pd
import numpy as np

class DatasetLoader:
    def __init__(self):
        """
        TODO: 数据集信息
        """
        pass

    def set_stock_list(self, stock_list):
        if type(stock_list) == set:
            stock_list = list(stock_list)
        elif type(stock_list)!=list:
            raise Exception("stock_list 为list类型！")
        self.stock_list = sorted(stock_list)

    def set_mddate_list(self, mddate_list):
        if type(mddate_list) == set:
            mddate_list = list(mddate_list)
        elif type(mddate_list)!=list:
            raise Exception("mddate_list 为list类型！")
        self.stock_list = sorted(mddate_list)

    def load_factor_data(self, classify_or_not = True, mock_data_flag = True, num_features = 40, tag_name = 'Tag5minRet', is_tag_percent = False, factor_path = '/data/user/013150/alpha_invest/data/merge_data.pkl', target_stock_list = None, target_mddate_list = None):
        """
        :param classify_or_not:
        :param mock_data_flag: 是否使用模拟数据
        :return: 要求：factor_data和label_data的时间戳已对齐，有一样的行数；
        factor_data和label_data都含有stock、mddate、mdtime三列，且已经按照stock、mddate、mdtime排序
        """
        def classic(label):
            th = 0.0012
            if is_tag_percent:
                th = th*100
            if -th < label < th:
                return 0
            elif label >= th:
                return 1
            else:
                return 2

        if not mock_data_flag:
            if factor_path.endswith("pkl") or factor_path.endswith("pickle"):
                merge_data = pd.read_pickle(factor_path)
            elif factor_path.endswith("pqt") or factor_path.endswith("parquet"):
                merge_data = pd.read_parquet(factor_path)
            else:
                raise Exception("不支持的数据格式！")
            label_columns = [col for col in merge_data.columns if col.startswith('tag') or col.startswith('Tag')]
            factor_columns = sorted(list(set(merge_data.columns.tolist()) - set(label_columns) - set(['stock', 'mddate', 'timestamp'])))
            assert tag_name in label_columns, 'tag_name不合法！'
            #丢弃标签为nan的数据
            merge_data.dropna(how = 'any', axis = 0, inplace = True, subset = [tag_name])

            label_data = merge_data.loc[:, ['stock', 'mddate', 'timestamp'] + label_columns]
            label_data = label_data.loc[:, ['stock', 'mddate', 'timestamp', tag_name]]
            factor_data = merge_data.loc[:, ['stock', 'mddate', 'timestamp'] + factor_columns]
            factor_data = factor_data.dropna(how='all', axis=1)
            factor_data = factor_data.fillna(0.0)
            factor_data = factor_data.iloc[:, :num_features+3]

            if target_stock_list:
                factor_data = factor_data[factor_data['stock'].isin(target_stock_list)]
                label_data = label_data[label_data['stock'].isin(target_stock_list)]
            if target_mddate_list:
                factor_data = factor_data[factor_data['mddate'].isin(target_mddate_list)]
                label_data = label_data[label_data['mddate'].isin(target_mddate_list)]

            if classify_or_not:
                class_num = 3
                label_data[tag_name] = label_data[tag_name].apply(lambda x: classic(x))
                print("label {} distribute count: [0: {}; 1: {}: 2,{} ]".format(tag_name, label_data[label_data[tag_name]==0].count().iloc[0],
                                                                            label_data[label_data[tag_name]==1].count().iloc[0],
                                                                            label_data[label_data[tag_name]==2].count().iloc[0]))

            self.set_mddate_list(set(factor_data['mddate']))
            self.set_stock_list(set(factor_data['stock']))
            self.factor_data = factor_data
            self.label_data = label_data

        else:
            factor_nums = num_features
            sub_df_list = []
            stocks = target_stock_list if target_stock_list else ['000001.SZ']
            mddate = target_mddate_list if target_mddate_list else ['20210701', '20210702', '20210703', '20210704', '20210705', '20210706', '20210707', '20210708', '20210709', '20210710', "20220601", "20220602"]
            for stock in stocks:
                for date in mddate:
                    n_samples = 1000
                    idx = np.linspace(0, n_samples - 1, num=n_samples)
                    X_train = np.random.random(size=(n_samples, factor_nums))
                    if classify_or_not:
                        y_train = np.random.choice([0, 1, 2], n_samples)
                    else:
                        y_train = np.random.uniform(-0.005, 0.005, n_samples).astype(np.float)

                    sub_df = pd.concat([pd.DataFrame(X_train), pd.DataFrame(y_train, columns=[tag_name])], axis=1)
                    sub_df["stock"] = stock
                    sub_df["mddate"] = date
                    sub_df['timestamp'] = list(range(n_samples))
                    sub_df_list.append(sub_df)
            dec_data = pd.concat(sub_df_list, axis=0)
            factor_data = dec_data.loc[:, ['stock', 'mddate', 'timestamp'] + list(range(factor_nums))]
            label_data = dec_data.loc[:, ['stock', 'mddate', 'timestamp'] + [tag_name]]
            print("factor_data:", factor_data.shape, "label_data:", label_data.shape)
        self.factor_data = factor_data
        self.label_data = label_data
        self.set_mddate_list(set(factor_data['mddate']))
        self.set_stock_list(set(factor_data['stock']))

        return self.factor_data, self.label_data

    def train_test_split(self, train_split_ratio = 0.9, train_test_split_date = None, factor_data = None, label_data = None):
        if not type(factor_data)==pd.DataFrame:
            factor_data = self.factor_data
        if not type(label_data)==pd.DataFrame:
            label_data = self.label_data
        # 按时间顺序切分
        if not train_test_split_date:
            train_test_split_date = factor_data.iloc[int(len(factor_data) * train_split_ratio)].loc['mddate']
        self.factor_data_train = factor_data[factor_data['mddate'] < train_test_split_date]
        self.factor_data_test = factor_data[factor_data['mddate'] >= train_test_split_date]
        self.label_data_train = label_data[label_data['mddate'] < train_test_split_date]
        self.label_data_test = label_data[label_data['mddate'] >= train_test_split_date]

        tag_name = label_data.columns[-1]
        print("Train: label {} distribute count: [0: {}; 1: {}: 2,{} ]".format(tag_name, self.label_data_train[
                                                                        self.label_data_train[tag_name] == 0].count().iloc[0],
                                                                        self.label_data_train[
                                                                            self.label_data_train[tag_name] == 1].count().iloc[0],
                                                                        self.label_data_train[
                                                                            self.label_data_train[tag_name] == 2].count().iloc[0]))

        print("Test: label {} distribute count: [0: {}; 1: {}: 2,{} ]".format(tag_name, self.label_data_test[
            self.label_data_test[tag_name] == 0].count().iloc[0],
                                                                        self.label_data_test[
                                                                            self.label_data_test[
                                                                                tag_name] == 1].count().iloc[0],
                                                                        self.label_data_test[
                                                                            self.label_data_test[
                                                                                tag_name] == 2].count().iloc[0]))

        return self.factor_data_train, self.factor_data_test, self.label_data_train, self.label_data_test
