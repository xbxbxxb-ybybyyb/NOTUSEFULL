import numpy as np
import pandas as pd
from src.utils import *

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
            key = hash(hash(tagger_cls)+hash(str(tagger_param)))
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