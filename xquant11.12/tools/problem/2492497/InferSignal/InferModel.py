#-*- coding:utf-8 -*-
# author: 015629
# datetime:2021/6/7 16:04
import json
import numpy as np
import tensorflow as tf
from InferSignal.SampleDataSet import SampleDataSet


class InferModel(object):
    def __init__(self, paraModel):
        self.paraModel = paraModel
        self.code = self.paraModel["code"]
        self.model_path = self.paraModel["model_path"]
        self.tagNames = self.paraModel["tagNames"]
        self.sliceLags = self.paraModel["sliceLags"]
        self.open_tick_num = self.paraModel["open_tick_num"]
        self.factor_names_dict = self.paraModel["factor_names_dict"]
        self.factor_indexes = self.paraModel["factor_indexes"]
        self.signature_key = "inference_signature"
        self.model_prefix = "AlgoShaolin-600519.SH-20180824093015-20181024145659_model"
        self.tag_index_dict = {"tag1minLong": 0, "tag1minShort": 0, "tag2minLong": 1, "tag2minShort": 1, "tag5minLong": 2, "tag5minShort": 2}

    def infer(self):
        ################################### Start Infer Signal ########################################
        factor_data = self.paraModel["test_factor_data"]
        tag_data = self.paraModel["test_tag_data"]
        timestamp = self.paraModel["test_timestamp"]

        outSamplePredict = None
        outSampleLabel = None

        daily_prediction = {}
        for cvt_d_key in timestamp["timestamp"].keys():
            daily_prediction[cvt_d_key] = {"signals": {}}

            predict_daily = None
            label_daily = None

            for tag_name in self.tagNames:
                window_size = self.sliceLags.get(tag_name)
                local_model_path = self.model_path + "{}{}{}/".format(self.model_prefix, tag_name.split("tag")[1], self.sliceLags.get(tag_name))
                mean_load, std_load, up_load, down_load = self.load_model_set(local_model_path, tag_name)
                tag_factor_data_d = factor_data[cvt_d_key][:, self.factor_indexes.get(tag_name)]
                predictNNData = self.preprocess_test_data(tag_factor_data_d, mean_load, std_load, up_load, down_load)

                predictSubTag = dict()
                predictSubTag["timestamp"] = timestamp["timestamp"][cvt_d_key]
                predictSubTag[tag_name] = tag_data[tag_name][cvt_d_key]
                predictSampleDataSet = SampleDataSet(predictNNData, predictSubTag, window_size, tag_name, open_tick_num=self.open_tick_num)
                if predictSampleDataSet.num_examples == 0:
                    continue
                batchPredict = predictSampleDataSet.next_batch_infer(predictSampleDataSet.num_examples)

                predict_factor_data = batchPredict[0]
                predict_tag_data = batchPredict[1]
                predict_timestamp = batchPredict[2]

                tf.reset_default_graph()
                config = tf.ConfigProto(device_count={"CPU": 1},
                                        inter_op_parallelism_threads=1,
                                        intra_op_parallelism_threads=1)

                with tf.Session(config=config) as sess:
                    meta_graph_def = tf.saved_model.loader.load(sess, ["model_test"], local_model_path)
                    signature = meta_graph_def.signature_def

                    y_regression = sess.graph.get_tensor_by_name(signature[self.signature_key].outputs["y_regression"].name)
                    x = sess.graph.get_tensor_by_name(signature[self.signature_key].inputs["x"].name)
                    y = sess.graph.get_tensor_by_name(signature[self.signature_key].inputs["y"].name)
                    rnn_keepProb = sess.graph.get_tensor_by_name(signature[self.signature_key].inputs["rnn_keepProb"].name)
                    dnn_keepProb = sess.graph.get_tensor_by_name(signature[self.signature_key].inputs["dnn_keepProb"].name)

                    feed_dict_tensors = [x, y, rnn_keepProb, dnn_keepProb]
                    predict = self.inference_tensor(y_regression, feed_dict_tensors, (predict_factor_data, predict_tag_data), 10000, sess)

                if predict.ndim == 1:
                    predict = predict.reshape(-1, 1)

                label = predict_tag_data 

                if predict_daily is None:
                    predict_daily = predict
                else:
                    predict_daily = np.concatenate((predict_daily, predict), axis=1)
                if label_daily is None:
                    label_daily = label
                else:
                    label_daily = np.concatenate((label_daily, label), axis=1)

            if outSamplePredict is None:
                outSamplePredict = predict_daily
                outSampleLabel = label_daily
            else:
                outSamplePredict = np.concatenate((outSamplePredict, predict_daily), axis=0)
                outSampleLabel = np.concatenate((outSampleLabel, label_daily), axis=0)

            daily_prediction[cvt_d_key]["signals"]["timestamp"] = predict_timestamp["timestamp"]

            for i in range(len(self.tagNames)):
                daily_prediction[cvt_d_key]["signals"][self.tagNames[i].replace("tag", "prediction")] = predict_daily[:, i].tolist()
                daily_prediction[cvt_d_key]["signals"][self.tagNames[i]] = label_daily[:, i].tolist()

        return daily_prediction

    def load_model_set(self, model_path, tag_name):
        index = self.tag_index_dict.get(tag_name)
        try:
            with open(model_path + "ModelSet{}.json".format(tag_name.split("tag")[1]), "rb") as f:
                data = f.read()
                model_set = json.loads(data)

            mean_load = model_set["mean{}".format(index)]
            std_load = model_set["std{}".format(index)]
            up_load = model_set["up{}".format(index)]
            down_load = model_set["down{}".format(index)]
        except Exception as e:
            mean_load, std_load, up_load, down_load = None, None, None, None
            print(" {} ModelSet File Not Found At {}, {} ".format(tag_name, model_path, e))

        return mean_load, std_load, up_load, down_load

    @staticmethod
    def preprocess_test_data(data, scale_mean=None, scale_std=None, up_limit=None, down_limit=None):
        if scale_mean is not None and scale_std is not None and up_limit is not None and down_limit is not None:
            return (np.clip(data, down_limit, up_limit) - np.array(scale_mean)) / np.array(scale_std)
        else:
            return data

    @staticmethod
    def inference_tensor(eval_tensor, feed_dict_tensors, batch_data, batch_size, sess):
        """  batch_data[0]: factor_data, x; batch_data[1]: label_data, y, label_data is unnecessary
        """
        num = int(np.floor(batch_data[0].shape[0] / batch_size))
        res = int(batch_data[0].shape[0] % batch_size)

        out_predict = []

        if num > 0:
            for i in range(num):
                feed_dict_data = [batch_data[0][(i * batch_size):((i + 1) * batch_size), :],
                                  batch_data[1][(i * batch_size):((i + 1) * batch_size), :],
                                  1.0,
                                  1.0]

                if eval_tensor is not None:
                    eval_data = eval_tensor.eval(
                        feed_dict={tensor: value for tensor, value in zip(feed_dict_tensors, feed_dict_data)},
                        session=sess)
                    out_predict += eval_data.tolist()

        if res > 0:
            feed_dict_data = [batch_data[0][(num * batch_size):(num * batch_size + res), :],
                              batch_data[1][(num * batch_size):(num * batch_size + res), :],
                              1.0,
                              1.0]

            if eval_tensor is not None:
                eval_data = eval_tensor.eval(
                    feed_dict={tensor: value for tensor, value in zip(feed_dict_tensors, feed_dict_data)}, session=sess)
                out_predict += eval_data.tolist()

        out_predict = np.array(out_predict)

        return out_predict





