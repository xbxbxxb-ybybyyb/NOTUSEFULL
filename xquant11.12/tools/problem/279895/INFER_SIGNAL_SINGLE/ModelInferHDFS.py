import json
import time
import math
import os
import re
import math
import random
import datetime as dt
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import r2_score
from tensorflow.contrib import rnn
from xquant.marketdata import MarketData
from INFER_SIGNAL_SINGLE.DeepNNDataSetLongShort import DeepNNDataSet


class ModelCNNLSTMLongShort:
    def __init__(self, paraModel):
        self.paraModel = paraModel
        self.signature_key = "inference_signature"
        self.stock_code = self.paraModel["stock_code"]    
        self.num_factors = self.paraModel["num_factors"]
        self.model_path = self.paraModel["model_path"]
        self.model_input = self.paraModel["factor_indexs"]
        self.log_fd = self.paraModel["log_fd"]
        self.tagNames = self.paraModel["tagNames"]
        self.sliceLags = self.paraModel["sliceLags"]
        self.open_tick_num = self.paraModel["open_tick_num"]
        self.triggerRatio = self.paraModel["triggerRatio"]
        self.factorNames = self.paraModel["factorNames"]

    def infer(self):
        tf.reset_default_graph()
        config = tf.ConfigProto()
        config.gpu_options.allow_growth = True
        with tf.Session(config=config) as sess:
            self.log_fd.logger.debug(self.model_path + " exists. Loading Model")
            meta_graph_def = tf.saved_model.loader.load(sess, ['model_' + self.stock_code],
                                                        self.model_path)
            signature = meta_graph_def.signature_def

            y_regression = sess.graph.get_tensor_by_name(signature[self.signature_key].outputs["y_regression"].name)
            loss = sess.graph.get_tensor_by_name(signature[self.signature_key].inputs["loss"].name)
            x = sess.graph.get_tensor_by_name(signature[self.signature_key].inputs["x"].name)
            y = sess.graph.get_tensor_by_name(signature[self.signature_key].inputs["y"].name)
            rnn_keepProb = sess.graph.get_tensor_by_name(signature[self.signature_key].inputs["rnn_keepProb"].name)
            dnn_keepProb = sess.graph.get_tensor_by_name(signature[self.signature_key].inputs["dnn_keepProb"].name)

            with open(self.model_path + '/ModelSet.json', "r") as f:
                model_set = json.load(f)

            window_size = model_set['WindowSize']
            open_tick_num = model_set['OpenTickNum']
            
            tag_names = []
            for tag_name_list in self.tagNames:
                for tag_name in tag_name_list:
                    tag_names.append(tag_name)
                    
            feed_dict_tensors = [x, rnn_keepProb, dnn_keepProb]
            factor_data = self.paraModel["test_factor_data"]
            tag_data = self.paraModel["test_tag_data"]
            timestamp = self.paraModel["test_timestamp"] 
            
            outSamplePredict = None
            outSampleLabel = None    
            
            daily_prediction ={}
            for d in timestamp["timestamp"].keys():
                cvt_d_key = d
                daily_prediction[cvt_d_key] = {"factors": {}, "signals":{}}
                for i in range(len(self.factorNames)):
                    daily_prediction[cvt_d_key]["factors"][self.factorNames[i]] = factor_data[d][:, i].tolist()  
                daily_prediction[cvt_d_key]["factors"]["Timestamp"] = timestamp["timestamp"][d]
                daily_prediction[cvt_d_key]["factors"]["Ticktime"] = []
                for time in timestamp["timestamp"][d]:
                    daily_prediction[cvt_d_key]["factors"]["Ticktime"].append(dt.datetime.fromtimestamp(time).strftime('%Y-%m-%d %H:%M:%S').split()[1]) 
                predictSubTag = {}
                for key in tag_data:
                    predictSubTag[key] = tag_data[key][d]
                predictSubTag["timestamp"] = timestamp["timestamp"][d]
                        
                predict_slice_datas = []
                for index in range(len(window_size)):
                    mean_load = model_set['mean' + str(index)]
                    std_load = model_set['std' + str(index)]
                    up_load = model_set['up' + str(index)]
                    down_load = model_set['down' + str(index)]
                    
                    predictNNData = preprocess_test_data(factor_data[d], mean_load, std_load, up_load, down_load)
                    predictDeepNNDataSet = DeepNNDataSet(predictNNData, predictSubTag, window_size[index], self.tagNames[index],
                                                           open_tick_num=self.open_tick_num, log_fd=self.log_fd)
                    if predictDeepNNDataSet.num_examples == 0:
                        continue
                    batchPredict = predictDeepNNDataSet.next_batch_infer(predictDeepNNDataSet.num_examples)

                    for dim in range(batchPredict[1].shape[1]):
                        batchPredict[1][:, dim] = convert_tag(batchPredict[1][:, dim], model_set, self.tagNames[index][dim], 2 * index + dim)
                    
                    predict_slice_datas.append(batchPredict)
                if len(predict_slice_datas) == 0:
                    continue    
                predict_factor_data = predict_slice_datas[0][0]
                predict_tag_data = predict_slice_datas[0][1]
                predict_timestamp = predict_slice_datas[0][2]
                for index in range(1, len(predict_slice_datas)):
                    predict_factor_data = np.concatenate((predict_factor_data, predict_slice_datas[index][0]), axis=1) 
                    predict_tag_data = np.concatenate((predict_tag_data, predict_slice_datas[index][1]), axis=1)  
                   
                predict = inference_tensor(y_regression, feed_dict_tensors, predict_factor_data, 10000)
                label = np.array(predict_tag_data)
            
                for dim in range(predict.shape[1]):
                    predict[:, dim] = invert_predict(predict[:, dim], model_set, tag_names[dim], dim)
                    label[:, dim] = invert_predict(label[:, dim], model_set, tag_names[dim], dim)
                
                if outSamplePredict is None:
                    outSamplePredict = predict
                    outSampleLabel = label
                else:
                    outSamplePredict =  np.concatenate((outSamplePredict, predict), axis=0)
                    outSampleLabel = np.concatenate((outSampleLabel, label), axis=0)
                
                daily_prediction[cvt_d_key]["signals"]["Timestamp"] = predict_timestamp["timestamp"] 
                daily_prediction[cvt_d_key]["signals"]["Ticktime"] = []
                
                for time in predict_timestamp["timestamp"]:
                    daily_prediction[cvt_d_key]["signals"]["Ticktime"].append(dt.datetime.fromtimestamp(time).strftime('%Y-%m-%d %H:%M:%S').split()[1])    
                for i in range(len(tag_names)):
                    daily_prediction[cvt_d_key]["signals"][tag_names[i]] = predict[:, i].tolist()
                    daily_prediction[cvt_d_key]["signals"][tag_names[i] + "Tag"] = label[:, i].tolist() 
                      
            test_loss = np.sqrt(np.mean(np.power((outSamplePredict - outSampleLabel), 2)))
            long_pre = None
            short_pre = None
            long_tag = None
            short_tag = None
            
            for index in range(0, outSamplePredict.shape[1], 2):
                if long_pre is None:
                    long_pre = outSamplePredict[:, index].reshape(-1, 1)
                    long_tag = outSampleLabel[:, index].reshape(-1, 1)
                else:
                    long_pre = np.concatenate((long_pre, outSamplePredict[:, index].reshape(-1, 1)), axis=1)
                    long_tag = np.concatenate((long_tag, outSampleLabel[:, index].reshape(-1, 1)), axis=1)
                    
                if short_pre is None:
                    short_pre = outSamplePredict[:, index + 1].reshape(-1, 1)
                    short_tag = outSampleLabel[:, index + 1].reshape(-1, 1)
                else:
                    short_pre = np.concatenate((short_pre, outSamplePredict[:, index + 1].reshape(-1, 1)), axis=1)
                    short_tag = np.concatenate((short_tag, outSampleLabel[:, index + 1].reshape(-1, 1)), axis=1)
                        
            outSamplePredictLong = np.mean(long_pre, axis=1)
            outSampleLabelLong =  np.mean(long_tag, axis=1)
            outSamplePredictShort = np.mean(short_pre, axis=1) 
            outSampleLabelShort = np.mean(short_tag, axis=1)
            tag_rqs = {}
            for i in range(len(tag_names)):
                tag_rqs["predict_" + tag_names[i] + "_rq"] = float(r2_score(outSampleLabel[:, i], outSamplePredict[:, i]) )
                self.log_fd.logger.debug ("%s rq: %f", tag_names[i], tag_rqs["predict_" + tag_names[i] + "_rq"])
                
            predict_long_rq = r2_score(outSampleLabelLong, outSamplePredictLong)            
            predict_short_rq = r2_score(outSampleLabelShort, outSamplePredictShort)
            
            self.log_fd.logger.debug ("predict long rq: %f", predict_long_rq)
            self.log_fd.logger.debug ("predict short rq: %f", predict_short_rq)
                                      
            test_TriggerTimesLong = sum(outSamplePredictLong > self.triggerRatio)
            if test_TriggerTimesLong != 0:
                test_winRateLong = sum(outSampleLabelLong[outSamplePredictLong > self.triggerRatio] > self.triggerRatio)  / test_TriggerTimesLong
            else:
                test_winRateLong = 0
        
            test_TriggerTimesShort = sum(outSamplePredictShort < -self.triggerRatio)
            if test_TriggerTimesShort != 0:
                test_winRateShort = sum(outSampleLabelShort[outSamplePredictShort < -self.triggerRatio] < -self.triggerRatio) / test_TriggerTimesShort
            else:
                test_winRateShort = 0

            self.log_fd.logger.debug('test loss %.6f, winRate Long %.2f, Long times %d, winRate Short %.2f, Short times %d',
                test_loss, test_winRateLong, test_TriggerTimesLong, test_winRateShort, test_TriggerTimesShort)
            tag_acc = {}
            for i in range(len(tag_names)):
                tag_acc["predict_" + tag_names[i] + "_acc"] = {}
                concat_infer = np.concatenate((outSamplePredict[:, i].reshape(-1, 1), outSampleLabel[:, i].reshape(-1, 1)), axis=1)
                concat_infer = concat_infer[np.argsort(concat_infer[:, 0])]
                top_10_acc = 0
                top_20_acc = 0
                top_50_acc = 0
                
                bottom_10_acc = 0
                bottom_20_acc = 0
                bottom_50_acc = 0
                
                top_10_rst = concat_infer[-int(concat_infer.shape[0] / 10):]
                mis_num = 0
                for rst in top_10_rst:
                    if rst[0] * rst[1] < 0:
                       mis_num = mis_num + 1
                top_10_acc = 1.0 - mis_num * 1.0 / int(concat_infer.shape[0] / 10)
                
                top_20_rst = concat_infer[-int(concat_infer.shape[0] / 20):]
                mis_num = 0
                for rst in top_20_rst:
                    if rst[0] * rst[1] < 0:
                       mis_num = mis_num + 1
                top_20_acc = 1.0 - mis_num * 1.0 / int(concat_infer.shape[0] / 20)
                
                top_50_rst = concat_infer[-int(concat_infer.shape[0] / 50):]
                mis_num = 0
                for rst in top_50_rst:
                    if rst[0] * rst[1] < 0:
                       mis_num = mis_num + 1
                top_50_acc = 1.0 - mis_num * 1.0 / int(concat_infer.shape[0] / 50)
                
                bottom_10_rst = concat_infer[:int(concat_infer.shape[0] / 10),]
                mis_num = 0
                for rst in bottom_10_rst:
                    if rst[0] * rst[1] < 0:
                       mis_num = mis_num + 1
                bottom_10_acc = 1.0 - mis_num * 1.0 / int(concat_infer.shape[0] / 10)
                
                bottom_20_rst = concat_infer[:int(concat_infer.shape[0] / 20),]
                mis_num = 0
                for rst in bottom_20_rst:
                    if rst[0] * rst[1] < 0:
                       mis_num = mis_num + 1
                bottom_20_acc = 1.0 - mis_num * 1.0 / int(concat_infer.shape[0] / 20) 
                
                bottom_50_rst = concat_infer[:int(concat_infer.shape[0] / 50),]
                mis_num = 0
                for rst in bottom_50_rst:
                    if rst[0] * rst[1] < 0:
                       mis_num = mis_num + 1
                bottom_50_acc = 1.0 -mis_num * 1.0 / int(concat_infer.shape[0] / 50)
                tag_acc["predict_" + tag_names[i] + "_acc"]["top_10_acc"] = top_10_acc
                tag_acc["predict_" + tag_names[i] + "_acc"]["top_20_acc"] = top_20_acc
                tag_acc["predict_" + tag_names[i] + "_acc"]["top_50_acc"] = top_10_acc
                tag_acc["predict_" + tag_names[i] + "_acc"]["bottom_10_acc"] = bottom_10_acc
                tag_acc["predict_" + tag_names[i] + "_acc"]["bottom_20_acc"] = bottom_20_acc
                tag_acc["predict_" + tag_names[i] + "_acc"]["bottom_50_acc"] = bottom_50_acc
                tag_acc["predict_" + tag_names[i] + "_acc"]["bottom_50_acc"] = bottom_50_acc
                tag_acc["predict_" + tag_names[i] + "_acc"]["bottom_50"] = np.mean(concat_infer[:int(concat_infer.shape[0] / 50), 0])
                tag_acc["predict_" + tag_names[i] + "_acc"]["top_50"] = np.mean(concat_infer[-int(concat_infer.shape[0] / 50):, 0])
                tag_acc["predict_" + tag_names[i] + "_acc"]["predict_value"] = [concat_infer[int(0 * concat_infer.shape[0] / 10)][0], 
                                                                        concat_infer[int(1 * concat_infer.shape[0] / 10)][0],
                                                                        concat_infer[int(2 * concat_infer.shape[0] / 10)][0],
                                                                        concat_infer[int(3 * concat_infer.shape[0] / 10)][0],
                                                                        concat_infer[int(4 * concat_infer.shape[0] / 10)][0],
                                                                        concat_infer[int(5 * concat_infer.shape[0] / 10)][0],
                                                                        concat_infer[int(6 * concat_infer.shape[0] / 10)][0],
                                                                        concat_infer[int(7 * concat_infer.shape[0] / 10)][0],
                                                                        concat_infer[int(8 * concat_infer.shape[0] / 10)][0],
                                                                        concat_infer[int(9 * concat_infer.shape[0] / 10)][0],
                                                                        concat_infer[int(concat_infer.shape[0] - 1)][0]]
                
                self.log_fd.logger.debug('predict %s: min %.3f, max %.3f', tag_names[i], np.min(outSampleLabel[:, i]), np.max(outSampleLabel[:, i]))
                self.log_fd.logger.debug ('predict: min_ave_50 %.3f, max_ave_50 %.3f', tag_acc["predict_" + tag_names[i] + "_acc"]["bottom_50"], tag_acc["predict_" + tag_names[i] + "_acc"]["top_50"])
                self.log_fd.logger.debug ('predict %s: %.6f, %.6f, %.6f, %.6f, %.6f, %.6f, %.6f, %.6f, %.6f, %.6f, %.6f', tag_names[i], 
                                                        concat_infer[int(0 * concat_infer.shape[0] / 10)][0], 
                                                        concat_infer[int(1 * concat_infer.shape[0] / 10)][0],
                                                        concat_infer[int(2 * concat_infer.shape[0] / 10)][0],
                                                        concat_infer[int(3 * concat_infer.shape[0] / 10)][0],
                                                        concat_infer[int(4 * concat_infer.shape[0] / 10)][0],
                                                        concat_infer[int(5 * concat_infer.shape[0] / 10)][0],
                                                        concat_infer[int(6 * concat_infer.shape[0] / 10)][0],
                                                        concat_infer[int(7 * concat_infer.shape[0] / 10)][0],
                                                        concat_infer[int(8 * concat_infer.shape[0] / 10)][0],
                                                        concat_infer[int(9 * concat_infer.shape[0] / 10)][0],
                                                        concat_infer[int(concat_infer.shape[0] - 1)][0])
                self.log_fd.logger.debug ('predict %s: top_10_acc %.3f, top_20_acc %.3f, top_50_acc %.3f, bottom_10_acc %.3f, bottom_20_acc %.3f, bottom_50_acc %.3f', tag_names[i], top_10_acc, top_20_acc, top_50_acc, bottom_10_acc, bottom_20_acc, bottom_50_acc)
            
            concat_infer = np.concatenate((outSamplePredictLong.reshape(-1, 1), outSampleLabelLong.reshape(-1, 1)), axis=1)
            concat_infer = concat_infer[np.argsort(concat_infer[:, 0])]
            top_10_acc = 0
            top_20_acc = 0
            top_50_acc = 0
            
            bottom_10_acc = 0
            bottom_20_acc = 0
            bottom_50_acc = 0
            
            top_10_rst = concat_infer[-int(concat_infer.shape[0] / 10):]
            mis_num = 0
            for rst in top_10_rst:
                if rst[0] * rst[1] < 0:
                   mis_num = mis_num + 1
            top_10_acc = 1.0 - mis_num * 1.0 / int(concat_infer.shape[0] / 10)
            
            top_20_rst = concat_infer[-int(concat_infer.shape[0] / 20):]
            mis_num = 0
            for rst in top_20_rst:
                if rst[0] * rst[1] < 0:
                   mis_num = mis_num + 1
            top_20_acc = 1.0 - mis_num * 1.0 / int(concat_infer.shape[0] / 20)
            
            top_50_rst = concat_infer[-int(concat_infer.shape[0] / 50):]
            mis_num = 0
            for rst in top_50_rst:
                if rst[0] * rst[1] < 0:
                   mis_num = mis_num + 1
            top_50_acc = 1.0 - mis_num * 1.0 / int(concat_infer.shape[0] / 50)
            
            bottom_10_rst = concat_infer[:int(concat_infer.shape[0] / 10),]
            mis_num = 0
            for rst in bottom_10_rst:
                if rst[0] * rst[1] < 0:
                   mis_num = mis_num + 1
            bottom_10_acc = 1.0 - mis_num * 1.0 / int(concat_infer.shape[0] / 10)
            
            bottom_20_rst = concat_infer[:int(concat_infer.shape[0] / 20),]
            mis_num = 0
            for rst in bottom_20_rst:
                if rst[0] * rst[1] < 0:
                   mis_num = mis_num + 1
            bottom_20_acc = 1.0 - mis_num * 1.0 / int(concat_infer.shape[0] / 20) 
            
            bottom_50_rst = concat_infer[:int(concat_infer.shape[0] / 50),]
            mis_num = 0
            for rst in bottom_50_rst:
                if rst[0] * rst[1] < 0:
                   mis_num = mis_num + 1
            bottom_50_acc = 1.0 -mis_num * 1.0 / int(concat_infer.shape[0] / 50)
            tag_acc["predict_long_acc"] = {}
            tag_acc["predict_long_acc"]["top_10_acc"] = top_10_acc
            tag_acc["predict_long_acc"]["top_20_acc"] = top_20_acc
            tag_acc["predict_long_acc"]["top_50_acc"] = top_10_acc
            tag_acc["predict_long_acc"]["bottom_10_acc"] = bottom_10_acc
            tag_acc["predict_long_acc"]["bottom_20_acc"] = bottom_20_acc
            tag_acc["predict_long_acc"]["bottom_50_acc"] = bottom_50_acc
            tag_acc["predict_long_acc"]["bottom_50_acc"] = bottom_50_acc
            tag_acc["predict_long_acc"]["bottom_50"] = np.mean(concat_infer[:int(concat_infer.shape[0] / 50), 0])
            tag_acc["predict_long_acc"]["top_50"] = np.mean(concat_infer[-int(concat_infer.shape[0] / 50):, 0])
            tag_acc["predict_long_acc"]["predict_value"] = [concat_infer[int(0 * concat_infer.shape[0] / 10)][0], 
                                                                    concat_infer[int(1 * concat_infer.shape[0] / 10)][0],
                                                                    concat_infer[int(2 * concat_infer.shape[0] / 10)][0],
                                                                    concat_infer[int(3 * concat_infer.shape[0] / 10)][0],
                                                                    concat_infer[int(4 * concat_infer.shape[0] / 10)][0],
                                                                    concat_infer[int(5 * concat_infer.shape[0] / 10)][0],
                                                                    concat_infer[int(6 * concat_infer.shape[0] / 10)][0],
                                                                    concat_infer[int(7 * concat_infer.shape[0] / 10)][0],
                                                                    concat_infer[int(8 * concat_infer.shape[0] / 10)][0],
                                                                    concat_infer[int(9 * concat_infer.shape[0] / 10)][0],
                                                                    concat_infer[int(concat_infer.shape[0] - 1)][0]]
            self.log_fd.logger.debug('outSampleLabel Long: min %.3f, max %.3f',
                np.min(outSampleLabelLong), np.max(outSampleLabelLong))
            self.log_fd.logger.debug ('predict: min_ave_50 %.3f, max_ave_50 %.3f', tag_acc["predict_long_acc"]["bottom_50"], tag_acc["predict_long_acc"]["top_50"])
            self.log_fd.logger.debug ('outSamplePredict Long:: %.6f, %.6f, %.6f, %.6f, %.6f, %.6f, %.6f, %.6f, %.6f, %.6f, %.6f', 
                                                    concat_infer[int(0 * concat_infer.shape[0] / 10)][0], 
                                                    concat_infer[int(1 * concat_infer.shape[0] / 10)][0],
                                                    concat_infer[int(2 * concat_infer.shape[0] / 10)][0],
                                                    concat_infer[int(3 * concat_infer.shape[0] / 10)][0],
                                                    concat_infer[int(4 * concat_infer.shape[0] / 10)][0],
                                                    concat_infer[int(5 * concat_infer.shape[0] / 10)][0],
                                                    concat_infer[int(6 * concat_infer.shape[0] / 10)][0],
                                                    concat_infer[int(7 * concat_infer.shape[0] / 10)][0],
                                                    concat_infer[int(8 * concat_infer.shape[0] / 10)][0],
                                                    concat_infer[int(9 * concat_infer.shape[0] / 10)][0],
                                                    concat_infer[int(concat_infer.shape[0] - 1)][0])
            self.log_fd.logger.debug ('outSamplePredict Long: top_10_acc %.3f, top_20_acc %.3f, top_50_acc %.3f, bottom_10_acc %.3f, bottom_20_acc %.3f, bottom_50_acc %.3f', top_10_acc, top_20_acc, top_50_acc, bottom_10_acc, bottom_20_acc, bottom_50_acc)
    
            concat_infer = np.concatenate((outSamplePredictShort.reshape(-1, 1), outSampleLabelShort.reshape(-1, 1)), axis=1)
            concat_infer = concat_infer[np.argsort(concat_infer[:, 0])]
            top_10_acc = 0
            top_20_acc = 0
            top_50_acc = 0
            
            bottom_10_acc = 0
            bottom_20_acc = 0
            bottom_50_acc = 0
            
            top_10_rst = concat_infer[-int(concat_infer.shape[0] / 10):]
            mis_num = 0
            for rst in top_10_rst:
                if rst[0] * rst[1] < 0:
                   mis_num = mis_num + 1
            top_10_acc = 1.0 - mis_num * 1.0 / int(concat_infer.shape[0] / 10)
            
            top_20_rst = concat_infer[-int(concat_infer.shape[0] / 20):]
            mis_num = 0
            for rst in top_20_rst:
                if rst[0] * rst[1] < 0:
                   mis_num = mis_num + 1
            top_20_acc = 1.0 - mis_num * 1.0 / int(concat_infer.shape[0] / 20)
            
            top_50_rst = concat_infer[-int(concat_infer.shape[0] / 50):]
            mis_num = 0
            for rst in top_50_rst:
                if rst[0] * rst[1] < 0:
                   mis_num = mis_num + 1
            top_50_acc = 1.0 - mis_num * 1.0 / int(concat_infer.shape[0] / 50)
            
            bottom_10_rst = concat_infer[:int(concat_infer.shape[0] / 10),]
            mis_num = 0
            for rst in bottom_10_rst:
                if rst[0] * rst[1] < 0:
                   mis_num = mis_num + 1
            bottom_10_acc = 1.0 - mis_num * 1.0 / int(concat_infer.shape[0] / 10)
            
            bottom_20_rst = concat_infer[:int(concat_infer.shape[0] / 20),]
            mis_num = 0
            for rst in bottom_20_rst:
                if rst[0] * rst[1] < 0:
                   mis_num = mis_num + 1
            bottom_20_acc = 1.0 - mis_num * 1.0 / int(concat_infer.shape[0] / 20) 
            
            bottom_50_rst = concat_infer[:int(concat_infer.shape[0] / 50),]
            mis_num = 0
            for rst in bottom_50_rst:
                if rst[0] * rst[1] < 0:
                   mis_num = mis_num + 1
            bottom_50_acc = 1.0 -mis_num * 1.0 / int(concat_infer.shape[0] / 50)
            tag_acc["predict_short_acc"] = {}
            tag_acc["predict_short_acc"]["top_10_acc"] = top_10_acc
            tag_acc["predict_short_acc"]["top_20_acc"] = top_20_acc
            tag_acc["predict_short_acc"]["top_50_acc"] = top_10_acc
            tag_acc["predict_short_acc"]["bottom_10_acc"] = bottom_10_acc
            tag_acc["predict_short_acc"]["bottom_20_acc"] = bottom_20_acc
            tag_acc["predict_short_acc"]["bottom_50_acc"] = bottom_50_acc
            tag_acc["predict_short_acc"]["bottom_50_acc"] = bottom_50_acc
            tag_acc["predict_short_acc"]["bottom_50"] = np.mean(concat_infer[:int(concat_infer.shape[0] / 50), 0])
            tag_acc["predict_short_acc"]["top_50"] = np.mean(concat_infer[-int(concat_infer.shape[0] / 50):, 0])
            tag_acc["predict_short_acc"]["predict_value"] = [concat_infer[int(0 * concat_infer.shape[0] / 10)][0], 
                                                            concat_infer[int(1 * concat_infer.shape[0] / 10)][0],
                                                            concat_infer[int(2 * concat_infer.shape[0] / 10)][0],
                                                            concat_infer[int(3 * concat_infer.shape[0] / 10)][0],
                                                            concat_infer[int(4 * concat_infer.shape[0] / 10)][0],
                                                            concat_infer[int(5 * concat_infer.shape[0] / 10)][0],
                                                            concat_infer[int(6 * concat_infer.shape[0] / 10)][0],
                                                            concat_infer[int(7 * concat_infer.shape[0] / 10)][0],
                                                            concat_infer[int(8 * concat_infer.shape[0] / 10)][0],
                                                            concat_infer[int(9 * concat_infer.shape[0] / 10)][0],
                                                            concat_infer[int(concat_infer.shape[0] - 1)][0]]  
              
            self.log_fd.logger.debug('outSampleLabel Short: min %.3f, max %.3f',
                np.min(outSampleLabelShort), np.max(outSampleLabelShort))
            self.log_fd.logger.debug ('predict: min_ave_50 %.3f, max_ave_50 %.3f', tag_acc["predict_short_acc"]["bottom_50"], tag_acc["predict_short_acc"]["top_50"])
            self.log_fd.logger.debug ('outSamplePredict Short: %.6f, %.6f, %.6f, %.6f, %.6f, %.6f, %.6f, %.6f, %.6f, %.6f, %.6f', 
                                                    concat_infer[int(0 * concat_infer.shape[0] / 10)][0], 
                                                    concat_infer[int(1 * concat_infer.shape[0] / 10)][0],
                                                    concat_infer[int(2 * concat_infer.shape[0] / 10)][0],
                                                    concat_infer[int(3 * concat_infer.shape[0] / 10)][0],
                                                    concat_infer[int(4 * concat_infer.shape[0] / 10)][0],
                                                    concat_infer[int(5 * concat_infer.shape[0] / 10)][0],
                                                    concat_infer[int(6 * concat_infer.shape[0] / 10)][0],
                                                    concat_infer[int(7 * concat_infer.shape[0] / 10)][0],
                                                    concat_infer[int(8 * concat_infer.shape[0] / 10)][0],
                                                    concat_infer[int(9 * concat_infer.shape[0] / 10)][0],
                                                    concat_infer[int(concat_infer.shape[0] - 1)][0])
            self.log_fd.logger.debug ('outSamplePredict Short: top_10_acc %.3f, top_20_acc %.3f, top_50_acc %.3f, bottom_10_acc %.3f, bottom_20_acc %.3f, bottom_50_acc %.3f', top_10_acc, top_20_acc, top_50_acc, bottom_10_acc, bottom_20_acc, bottom_50_acc)                
            return daily_prediction

def preprocess_test_data(data, scale_mean, scale_std, up_limit, down_limit):
    return (np.clip(data, down_limit, up_limit) - np.array(scale_mean)) / np.array(scale_std)


def inference_loss(loss_tensor, feed_dict_tensors, batch_data, batch_size):
    num = int(np.floor(batch_data[0].shape[0] / batch_size))
    res = int(batch_data[0].shape[0] % batch_size)

    out_loss = []

    if num > 0:
        for i in range(num):
            feed_dict_data = [batch_data[0][(i * batch_size):((i + 1) * batch_size), :],
                              batch_data[1][(i * batch_size):((i + 1) * batch_size)],
                              1.0,
                              1.0]
            if loss_tensor != None:
                loss = loss_tensor.eval(
                    feed_dict={tensor: value for tensor, value in zip(feed_dict_tensors, feed_dict_data)})
                out_loss.append(loss)

    if res > 0:

        feed_dict_data = [batch_data[0][(num * batch_size):(num * batch_size + res), :],
                          batch_data[1][(num * batch_size):(num * batch_size + res)],
                          1.0,
                          1.0]
        if loss_tensor != None:
            loss = loss_tensor.eval(
                feed_dict={tensor: value for tensor, value in zip(feed_dict_tensors, feed_dict_data)})
            out_loss.append(loss)

    if len(out_loss) > 0:
        out_loss = float(np.mean(out_loss))

    return out_loss


def inference_tensor(eval_tensor, feed_dict_tensors, batch_data, batch_size):
    num = int(np.floor(batch_data.shape[0] / batch_size))
    res = int(batch_data.shape[0] % batch_size)

    out_predict = []

    if num > 0:
        for i in range(num):
            feed_dict_data = [batch_data[(i * batch_size):((i + 1) * batch_size), :],                             
                              1.0,
                              1.0]

            if eval_tensor != None:
                eval_data = eval_tensor.eval(
                    feed_dict={tensor: value for tensor, value in zip(feed_dict_tensors, feed_dict_data)})
                out_predict += eval_data.tolist()

    if res > 0:
        feed_dict_data = [batch_data[(num * batch_size):(num * batch_size + res), :],                          
                          1.0,
                          1.0]

        if eval_tensor != None:
            eval_data = eval_tensor.eval(
                feed_dict={tensor: value for tensor, value in zip(feed_dict_tensors, feed_dict_data)})
            out_predict += eval_data.tolist()

    out_predict = np.array(out_predict)

    return out_predict


def invert_predict(predict, params, tag_name, dim):
    tag_convert_method = params[tag_name + '_tag_convert_method' + str(dim)]
    if tag_convert_method == 'max_min':
        max_min_scale_params = np.array(params[tag_name + '_max_min_scale_params' + str(dim)])
        max_min_offset_params = np.array(params[tag_name + '_max_min_offset_params' + str(dim)])

        return (predict - max_min_offset_params) / max_min_scale_params
    # elif tag_convert_method == 'scale':
        # scale_params = np.array(params[tag_name + '_scale_params' + str(dim)])
        # return predict / scale_params
    elif tag_convert_method == 'max_abs':
        max_abs_params = np.array(params[tag_name + '_max_abs_params' + str(dim)])
        return predict * max_abs_params
    elif tag_convert_method == 'scale_median':
        median = np.array(params[tag_name + '_median_params' + str(dim)])
        return predict  + median
    return predict


def convert_tag(tag, params, tag_name, dim):
    tag_convert_method = params[tag_name + '_tag_convert_method' + str(dim)]
    if tag_convert_method == 'max_min':
        max_min_scale_params = np.array(params[tag_name + '_max_min_scale_params' + str(dim)])
        max_min_offset_params = np.array(params[tag_name + '_max_min_offset_params' + str(dim)])
        return tag * max_min_scale_params + max_min_offset_params
    elif tag_convert_method == 'scale':
        scale_params = np.array(params[tag_name + '_scale_params' + str(dim)])
        return tag * scale_params
    elif tag_convert_method == 'max_abs':
        max_abs_params = np.array(params[tag_name + '_max_abs_params' + str(dim)])
        return tag / max_abs_params
    elif tag_convert_method == 'scale_median':
        scale_params = np.array(params[tag_name + '_scale_params' + str(dim)])
        median = np.array(params[tag_name + '_median_params' + str(dim)])
        return tag * scale_params  - median
    return tag
