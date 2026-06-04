import json
import gc
import numpy as np
import pickle
from Utils.HelpFunc import MyPrint
from InferSpark.SampleDataSet import SampleDataSet
from InferSpark.NumpyInferModel import NumpyInferModel
from xquant.xqutils.xqfile import HDFSFile


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

        self.models = dict()
        self.hf = HDFSFile()

    def infer(self):
        ################################### Start Infer Signal ########################################
        factor_data = self.paraModel["test_factor_data"]
        tag_data = self.paraModel["test_tag_data"]
        timestamp = self.paraModel["test_timestamp"]

        outSamplePredict = None
        outSampleLabel = None

        for tag_name in self.tagNames:
            input_shape = (self.sliceLags.get(tag_name), len(self.factor_indexes.get(tag_name)))
            model_weights = self.load_model_weights(tag_name)
            self.models[tag_name] = NumpyInferModel(inputs_shape=input_shape, model_weights=model_weights)

        daily_prediction = {}
        for cvt_d_key in timestamp["timestamp"].keys():
            daily_prediction[cvt_d_key] = {"signals": {}}

            predict_daily = None
            label_daily = None

            for tag_name in self.tagNames:
                window_size = self.sliceLags.get(tag_name)
                mean_load, std_load, up_load, down_load = self.load_model_set(tag_name)
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

                predict = self.models[tag_name].predict(predict_factor_data)

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

                gc.collect()

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

    def load_model_weights(self, tag_name):
        weights_path = self.model_path + "{}{}{}.pickle".format(self.model_prefix, tag_name.split("tag")[1], self.sliceLags.get(tag_name))
        try:
            with self.hf.open(weights_path, "rb") as f:
                data = f.read()
                model_weights = pickle.loads(data)
        except Exception as e:
            model_weights = dict()
            MyPrint(" {} Model Weights Not Found At {}, {} ".format(tag_name, weights_path, e))
        return model_weights

    def load_model_set(self, tag_name):
        model_path = self.model_path + "{}{}{}/".format(self.model_prefix, tag_name.split("tag")[1], self.sliceLags.get(tag_name))
        index = self.tag_index_dict.get(tag_name)
        try:
            with self.hf.open(model_path + "ModelSet{}.json".format(tag_name.split("tag")[1]), "rb") as f:
                data = f.read()
                model_set = json.loads(data)

            mean_load = model_set["mean{}".format(index)]
            std_load = model_set["std{}".format(index)]
            up_load = model_set["up{}".format(index)]
            down_load = model_set["down{}".format(index)]
        except Exception as e:
            mean_load, std_load, up_load, down_load = None, None, None, None
            MyPrint(" {} ModelSet File Not Found At {}, {} ".format(tag_name, model_path, e))

        return mean_load, std_load, up_load, down_load

    @staticmethod
    def preprocess_test_data(data, scale_mean=None, scale_std=None, up_limit=None, down_limit=None):
        if scale_mean is not None and scale_std is not None and up_limit is not None and down_limit is not None:
            return (np.clip(data, down_limit, up_limit) - np.array(scale_mean)) / np.array(scale_std)
        else:
            return data