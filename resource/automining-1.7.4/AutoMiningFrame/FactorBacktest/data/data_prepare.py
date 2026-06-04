import pandas as pd
from sklearn.preprocessing import RobustScaler, MinMaxScaler, StandardScaler
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin


class OutlierClipper(BaseEstimator, TransformerMixin):
    def __init__(self, clip_type="3sigma", quantile=[0.02, 0.98]):
        BaseEstimator.__init__(self)
        TransformerMixin.__init__(self)
        self.clip_type = clip_type
        self.quantile = quantile

    def fit(self, feature_df):
        if self.clip_type == "3sigma":
            arr = feature_df.values
            factor_mean = arr.mean(axis=0)
            factor_std = arr.std(axis=0)
            self.factor_mean = factor_mean
            self.clip_lower = factor_mean - 3 * factor_std
            self.clip_upper = factor_mean + 3 * factor_std
        return self

    def transform(self, featured_df):
        featured_df = featured_df.clip(
            lower=self.clip_lower, upper=self.clip_upper, axis=1)
        return featured_df


class TagCalculator():

    def __init__(self, config):
        self._tagger_dict = dict()
        self._config = config
        self._register_taggers()

    def _register_taggers(self):
        """
        :param config: config contain multiple taggers' param. Each one is a dict.
        """
        for config in self._config:
            # tagger_name = config["name"]
            tagger_cls = config["class_name"]
            tagger_param = config["param"]
            tagger_conf = Args(**tagger_param)
            key = hash(hash(tagger_cls) + hash(str(tagger_param)))
            if key not in self._tagger_dict.keys():
                exec('from src.taggers.{} import {}'.format(tagger_cls, tagger_cls))
                tagger = eval('{}(tagger_conf)'.format(tagger_cls))
                self._tagger_dict.update({key: tagger})
        return self._tagger_dict

    def calculate(self, df, df1=None):
        label_rests = list()
        for _, tagger in self._tagger_dict.items():
            if df1 is not None:
                res = tagger.calculate(df, df1)
            else:
                res = tagger.calculate(df)
            res = res.astype(np.float64)
            res.dropna(axis=0, how='any', inplace=True)
            label_rests.append(res)
        return pd.concat(label_rests, axis=1, join='inner')


class ClipCalculator():
    def __init__(self, clip_type="3sigma", quantile=[0.02, 0.98]):
        self.clipper = OutlierClipper(clip_type, quantile)

    def train(self, feature_df):
        self.clipper.fit(feature_df)

    def transform(self, featured_df):
        return self.clipper.transform(featured_df)

    def train_transform(self, feature_df):
        self.train(feature_df)
        return self.transform(feature_df)

    def load_and_transform(self, file_path):
        # sess = onnxruntime.InferenceSession(file_path)
        # input_name = sess.get_inputs()[0].name
        # label_name = sess.get_outputs()[0].name
        # pred_onx = sess.run([label_name], {input_name: test_data.astype(np.float32)})[0]
        # return pred_onx
        pass


class NormCalculator():

    def __init__(self, scaler_type='robust'):
        self.scaler = None
        self._scaler_type = scaler_type

    @property
    def scaler_type(self):
        return self._scaler_type

    @scaler_type.setter
    def scaler_type(self, scaler_type):
        self._scaler_type = scaler_type

    def train(self, featured_df):
        # cols = featured_df.columns
        self.dim_1 = featured_df.shape[1]
        if self._scaler_type == 'z-score':
            scaler = StandardScaler()
        elif self._scaler_type == 'min-max':
            scaler = MinMaxScaler(feature_range=(0, 1))
        elif self._scaler_type == 'robust':
            scaler = RobustScaler()
        self.scaler = scaler.fit(featured_df)

    def transform(self, featured_df):
        cols = featured_df.columns
        featured_df_copy = featured_df.copy()
        featured_df_copy[cols] = self.scaler.transform(featured_df[cols])
        return featured_df_copy

    def train_transform(self, feature_df):
        self.train(feature_df)
        return self.transform(feature_df)
