#-*- coding:utf-8 -*-
# author: 015629
# datetime:2021/1/19 9:01
cnn_feature_names = ["cnn_f{}".format(i+1) for i in range(64)]

lstm_feature_names = ["lstm_f{}".format(i+1) for i in range(64)]

dnn_feature_names = ["dnn_f{}".format(i+1) for i in range(64)]

single_feature_names = cnn_feature_names + lstm_feature_names + dnn_feature_names

tag_names = ['min1Long', 'min1Short', 'min2Long', 'min2Short', 'min5Long', 'min5Short']

feature_name_list = []
for tag in tag_names:
    for feature_name in single_feature_names:
        feature_name_list.append("{}_{}".format(tag, feature_name))