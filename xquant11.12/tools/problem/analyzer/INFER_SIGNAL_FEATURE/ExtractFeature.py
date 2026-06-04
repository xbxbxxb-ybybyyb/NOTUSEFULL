#-*- coding:utf-8 -*-
# author: 015629
# datetime:2021/1/18 16:20
import numpy as np
import pandas as pd
import datetime as dt
import tensorflow as tf

def extract_feature_by_name(model_path, factor_data, name, name_type="tensor"):
    """"""
    signature_key = "inference_signature"
    tf.reset_default_graph()
    config = tf.ConfigProto(device_count={"CPU": 1},
                            inter_op_parallelism_threads=1,
                            intra_op_parallelism_threads=1)

    # config = tf.ConfigProto()
    # config.gpu_options.allow_growth = True
    with tf.Session(config=config) as sess:

        meta_graph_def = tf.saved_model.loader.load(sess, ["model_test"], model_path)
        signature = meta_graph_def.signature_def

        y_regression = sess.graph.get_tensor_by_name(signature[signature_key].outputs["y_regression"].name)
        x = sess.graph.get_tensor_by_name(signature[signature_key].inputs["x"].name)
        rnn_keepProb = sess.graph.get_tensor_by_name(signature[signature_key].inputs["rnn_keepProb"].name)
        dnn_keepProb = sess.graph.get_tensor_by_name(signature[signature_key].inputs["dnn_keepProb"].name)

        if name_type == "tensor":
            tensor_name_list = [tensor.name for tensor in tf.get_default_graph().as_graph_def().node]
            assert name in tensor_name_list, " tensor name {} not found ".format(name)
            feature_output = sess.graph.get_tensor_by_name(name)

        elif name_type == "operation":
            operation_name_list = [operation.name for operation in sess.graph.get_operations()]
            assert name in operation_name_list, " operation name {} not found ".format(name)
            feature_output = sess.graph.get_operation_by_name(name).outputs[0]

        prediction, extract_feature = sess.run([y_regression, feature_output], {x: factor_data,
                                                                                rnn_keepProb: 1.0, dnn_keepProb: 1.0})

        return extract_feature
