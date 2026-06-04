#-*- coding:utf-8 -*-
# author: 015629
# datetime:2021/8/26 21:07
from NumpyModel.Model2Numpy import Model2Numpy


class NumpyInferModel(object):
    def __init__(self, inputs_shape, model_weights=None):
        self.input_shape = inputs_shape
        self.model_weights = model_weights
        self.np_model = Model2Numpy(self.input_shape)
        self.np_model.create_layers()
        self.np_model.set_tf_weights(self.model_weights)

    def predict(self, factor_data):
        return self.np_model.predict(factor_data)
