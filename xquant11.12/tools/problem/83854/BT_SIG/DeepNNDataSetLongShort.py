# -*- coding: utf-8 -*-
"""
Created on 2017/10/11 10:35

@author: 006547
"""
import numpy as np
from tensorflow.python.framework import random_seed
from sklearn.preprocessing.data import QuantileTransformer
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import MaxAbsScaler
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import RobustScaler
from sklearn.preprocessing import FunctionTransformer
import datetime as dt
import copy
import random
import re
import pandas as pd
import queue
import threading

class DeepNNDataSet(object):
    def __init__(self, factorData, subTagData, sliceLag, tagName, open_tick_num=0, seed=None, log_fd=None):                                      
        self._sliceLag = sliceLag
        self._tagName = tagName
        self._log_fd = log_fd
       
        if open_tick_num > 0:
            if isinstance(self._tagName, list):
                self._factorData, self._subTagData = self.extend_factor_tag(factorData, subTagData, sliceLag, open_tick_num, self._tagName)
            else:
                self._factorData, self._subTagData = self.extend_factor_tag(factorData, subTagData, sliceLag, open_tick_num, [self._tagName])
        else:
            self._factorData = factorData
            self._subTagData = subTagData
  
        self._tag_convert_method = 'scale'
        self._tag_transformer = []
        self._scale_factor = 1000.0       
        self.__median = None       
        self._tags = self.load_tags()
        self._iStartIndex = self.createIStartIndex(self._subTagData, self._sliceLag)       
        self._iIndex = np.array(self._iStartIndex)
        self._num_examples = self._iIndex.__len__()
        self._iBatchIndex = np.arange(self._num_examples)
        self._epochs_completed = 0
        self._index_in_epoch = 0
                              
    @property
    def factorData(self):
        return self._factorData

    @property
    def subTagData(self):
        return self._subTagData

    @property
    def iStartIndex(self):
        return self._iStartIndex

    @property
    def num_examples(self):
        return self._num_examples

    @property
    def epochs_completed(self):
        return self._epochs_completed
                   
    def set_tags(self, in_tags):
        self._tags = in_tags

    def get_tags(self):
        return self._tags

    def extend_factor_tag(self, factor_data, sub_tag, sliceLag, open_tick_num, tag_names):
        index = 0
        extend_factor = []
        extend_sub_tag = {}
        last_gen_timestamp = 0
        sub_tag_gen_len = sliceLag - open_tick_num
        extend_count = 0
        skip_factor_count = 0
        if sub_tag_gen_len <= 0:
            return factor_data, sub_tag
            
        tag_keys = sub_tag.keys()   
        for key in tag_keys:
            extend_sub_tag[key] = [] 

        while index < sub_tag["timestamp"].__len__():
            time = dt.datetime.fromtimestamp(sub_tag["timestamp"][index])
            if index == 0:
                last_gen_timestamp = sub_tag["timestamp"][index]
                sub_tag_gen = {}
                for key in tag_keys:
                    sub_tag_gen[key] = []
                for i in range(sub_tag_gen_len):
                    extend_factor.append(np.zeros(factor_data[0, :].shape, np.float))
                    for key in tag_keys:
                        sub_tag_gen[key].append(copy.deepcopy(sub_tag[key][0]))

                for i in range(sub_tag_gen_len):           
                    for tag_name in tag_names:
                        sub_tag_gen[tag_name][i] = float("nan") 
                        
                for key in tag_keys:                    
                    extend_sub_tag[key].extend(sub_tag_gen[key])
                        
                extend_count = extend_count + 1
            elif abs(sub_tag["timestamp"][index] - last_gen_timestamp) > 2.5 * 3600:
                sub_tag_gen = {}
                for key in tag_keys:
                    sub_tag_gen[key] = []
                last_gen_timestamp = sub_tag["timestamp"][index]

                for i in range(sub_tag_gen_len):
                    extend_factor.append(np.zeros(factor_data[index, :].shape, np.float))
                    for key in tag_keys:
                        sub_tag_gen[key].append(copy.deepcopy(sub_tag[key][index]))

                for i in range(sub_tag_gen_len):           
                    for tag_name in tag_names:
                        sub_tag_gen[tag_name][i] = float("nan")

                for key in tag_keys:                    
                    extend_sub_tag[key].extend(sub_tag_gen[key])
                        
                extend_count = extend_count + 1
                
            extend_factor.append(factor_data[index, :])
            for key in tag_keys:
                extend_sub_tag[key].append(sub_tag[key][index])
                
            index += 1  
                        
        return np.array(extend_factor), extend_sub_tag        

    def get_tag_converted_para(self):
        params = {}
  
        if isinstance(self._tagName, list):
            for i in range(len(self._tagName)):
                tag_key =str(self._tagName[i]) + "_"
                params[tag_key + 'tag_convert_method']  = self._tag_convert_method
                if self._tag_convert_method == 'max_min':
                    max_min_scale_params = self._tag_transformer[i].scale_[0]
                    max_min_offset_params = self._tag_transformer[i].min_[0]
                    params[tag_key + 'max_min_scale_params'] = max_min_scale_params
                    params[tag_key + 'max_min_offset_params'] = max_min_offset_params
                elif self._tag_convert_method == 'scale':
                    scale_params = self._scale_factor
                    params[tag_key + 'scale_params'] = scale_params
                elif self._tag_convert_method == 'max_abs':
                    max_abs_params = self._tag_transformer[i].scale_[0]
                    params[tag_key + 'max_abs_params'] = max_abs_params
                elif self._tag_convert_method == 'scale_median':
                    scale_params = self._scale_factor
                    params[tag_key + 'scale_params'] = scale_params
                    params[tag_key + 'median_params'] = self.__median[i]
        else:
            tag_key = str(self._tagName) + "_"
            params[tag_key + 'tag_convert_method']  = self._tag_convert_method
            if self._tag_convert_method == 'max_min':
                max_min_scale_params = []
                max_min_offset_params = []
                for transform in self._tag_transformer:
                    max_min_scale_params.append(transform.scale_[0])
                    max_min_offset_params.append(transform.min_[0])
                params[tag_key + 'max_min_scale_params'] = max_min_scale_params
                params[tag_key + 'max_min_offset_params'] = max_min_offset_params
            elif self._tag_convert_method == 'scale':
                scale_params = []
                for i in range(self._tags.shape[1]):
                    scale_params.append(self._scale_factor)
                params[tag_key + 'scale_params'] = scale_params
            elif self._tag_convert_method == 'max_abs':
                max_abs_params = []
                for transform in self._tag_transformer:
                    max_abs_params.append(transform.scale_[0])
                params[tag_key + 'max_abs_params'] = max_abs_params
            elif self._tag_convert_method == 'scale_median':
                scale_params = []
                for i in range(self._tags.shape[1]):
                    scale_params.append(self._scale_factor)
                params[tag_key + 'scale_params'] = scale_params
                params[tag_key + 'median_params'] = self.__median.tolist()
        return params

    def load_tags(self):
        tags = None
        if isinstance(self._tagName, list):
            for tagName in self._tagName:
                if tags is None:
                    tags = np.array(self._subTagData[tagName]).reshape(-1, 1)
                else:
                    tags = np.concatenate((tags, np.array(self._subTagData[tagName]).reshape(-1, 1)), axis=1)
        else:               
            tags = np.array(self._subTagData[self._tagName]).reshape(-1, 1)
                       
        return tags

    def convert_tags(self, in_tags):
        if self._tag_convert_method == 'max_min':
            return self.max_min_tag_convert(in_tags)
        elif self._tag_convert_method == 'scale':
            return self.scale_tag_convert(in_tags)
        elif self._tag_convert_method == 'max_abs':
            return self.max_abs_tag_convert(in_tags)
        elif self._tag_convert_method == 'scale_median':
            return self.scale_median_tag_convert(in_tags)
        return in_tags

    def invert_predict(self, predict):
        if self._tag_convert_method == 'max_min':
            return self.max_min_tag_invert(predict)
        elif self._tag_convert_method == 'scale':
            return self.scale_tag_invert(predict)
        elif self._tag_convert_method == 'max_abs':
            return self.max_abs_tag_invert(predict)
        elif self._tag_convert_method == 'scale_median':
            return self.scale_median_tag_invert(predict)
        return predict
    
    def scale_median_tag_convert(self, in_tags):
        scale_data = np.array(in_tags * self._scale_factor)
        self.__median = np.median(scale_data, axis=0)
        return scale_data - self.__median
    
    def scale_median_tag_invert(self, predict):     
        return np.array(predict + self.__median) /  self._scale_factor  
           
    def max_abs_tag_convert(self, in_tags):
        tags = np.array(in_tags)
        tag_dim = tags.shape[1]

        if len(self._tag_transformer) != tag_dim:
            self._tag_transformer = []
            for i in range(tag_dim):
                self._tag_transformer.append(MaxAbsScaler().fit(np.reshape(tags[:, i], [-1, 1])))

        transformed_tags = []
        for i in range(tag_dim):
            transformed_tags.append(self._tag_transformer[i].transform(np.reshape(tags[:, i], [-1, 1])))

        cvt_tags = transformed_tags[0]
        for i in range(1, tag_dim):
            cvt_tags = np.concatenate((cvt_tags, transformed_tags[i]), axis=1)

        return cvt_tags

    def max_abs_tag_invert(self, predict):
        predict_dim = predict.shape[1]
        inverted_predicts = []
        for i in range(predict_dim):
            inverted_predicts.append(self._tag_transformer[i].inverse_transform(np.reshape(predict[:, i], [-1, 1])))

        inverted_predict = inverted_predicts[0]
        for i in range(1, predict_dim):
            inverted_predict = np.concatenate((inverted_predict, inverted_predicts[i]), axis=1)

        return inverted_predict

    def max_min_tag_convert(self, in_tags):
        tags = np.array(in_tags)
        tag_dim = tags.shape[1]

        if len(self._tag_transformer) != tag_dim:
            self._tag_transformer = []
            for i in range(tag_dim):
                self._tag_transformer.append(MinMaxScaler().fit(np.reshape(tags[:, i], [-1, 1])))

        transformed_tags = []
        for i in range(tag_dim):
            transformed_tags.append(self._tag_transformer[i].transform(np.reshape(tags[:, i], [-1, 1])))

        cvt_tags = transformed_tags[0]
        for i in range(1, tag_dim):
            cvt_tags = np.concatenate((cvt_tags, transformed_tags[i]), axis=1)

        return cvt_tags

    def max_min_tag_invert(self, predict):
        predict_dim = predict.shape[1]
        inverted_predicts = []
        for i in range(predict_dim):
            inverted_predicts.append(self._tag_transformer[i].inverse_transform(np.reshape(predict[:, i], [-1, 1])))

        inverted_predict = inverted_predicts[0]
        for i in range(1, predict_dim):
            inverted_predict = np.concatenate((inverted_predict, inverted_predicts[i]), axis=1)

        return inverted_predict

    def scale_tag_invert(self, predict):
        return np.array(predict / self._scale_factor)

    def scale_tag_convert(self, in_tags):
        return np.array(in_tags * self._scale_factor)
            
    def next_batch_infer(self, batch_size):
        batchData = []
        batchLabel = []
        batchSubTag = {"timestamp": []}
            
        for index in self._iBatchIndex:
            iStart = self._iIndex[index]
            iEnd = iStart + self._sliceLag            
            batchData.append(np.reshape(self._factorData[iStart:iEnd, :], self._factorData[iStart:iEnd, :].size))
            batchLabel.append(self._tags[iEnd - 1])
            batchSubTag["timestamp"].append(self._subTagData["timestamp"][iEnd - 1])
            

        return np.array(batchData, dtype=np.float32), np.array(batchLabel, dtype=np.float32), batchSubTag   
        
    def createIStartIndex(self, subTagData, sliceLag):
        iStartIndex = []
        iStart = 0
        iEnd = sliceLag

        while iEnd <= subTagData["timestamp"].__len__():
            if abs(subTagData["timestamp"][iEnd - 1] - subTagData["timestamp"] [iStart]) < 1.5 * 3600:                                
                iStartIndex.append(iStart) 
            iStart += 1
            iEnd += 1        
        return np.array(iStartIndex, dtype=np.int32)
