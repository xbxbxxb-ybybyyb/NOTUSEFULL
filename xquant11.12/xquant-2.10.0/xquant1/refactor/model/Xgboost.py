#!/usr/bin/python
'''
Created on 1 Apr 2015
@author: Jamie Hall
'''

from sklearn.grid_search import GridSearchCV
import numpy as np
import xgboost as xgb
from sklearn.datasets import load_iris
from sklearn.cross_validation import StratifiedShuffleSplit

"""
grid_search方法训练，对一组参数集合寻找最佳参数
参数：
    X_train：样本特征数据
    Y_train：样本标签数据
    xgb_params：xgboost参数
    cv_params：交叉验证参数
    scoring: 默认"accuracy"，模型评分函数
    cv：整数，默认2，K着交叉验证的次数
返回：
    sklearn的 grid_search模型
"""
def xgb_train(X_train, Y_train, xgb_params, cv_params, scoring = "accuracy", cv = 2):
    xgb_model = xgb.XGBClassifier(**xgb_params)
    grid_search = GridSearchCV(xgb_model, cv_params, scoring = "accuracy", n_jobs=1, cv=cv, verbose=2)
    grid_search.fit(X_train, Y_train)
    
    print('每轮迭代运行结果:{0}'.format(grid_search.grid_scores_))
    print('参数的最佳取值：{0}'.format(grid_search.best_params_))
    print('最佳模型得分:{0}'.format(grid_search.best_score_))
    
    print('$statistic-log,module=refactor,platform=XQUANT-Cloud')
    
    return grid_search

#"""
#    模型特征重要性
#返回：
#    feature_score：
#"""
#def get_feature_pred(bst, X_data, Y_data):   
#    booster = bst.get_booster()
#    dmatrix = xgb.DMatrix(X_data,y_data)
#    
#    feature_score = booster.predict(dmatrix, pred_contribs=True) #显示每个特征的得分，预测值，经过sigmoid函数后输出
#    leaf_score = booster.predict(dmatrix, pred_leaf=True)#每条数据落在那个叶子节点
#    return feature_score, leaf_score

    
    
if __name__=="__main__":
    X = load_iris()
    X_data = X["data"]
    Y_data = X["target"]
    
    cv_params = {"n_estimators": [100, 300, 500],
                "max_depth":[4],
                'min_child_weight':[5],
                'gamma': [0.1],
                'reg_alpha': [0.05], 
                'reg_lambda': [0.05],
                'learning_rate': [0.01]
                }
    xgb_params = {'objective':'multi:softmax','learning_rate': 0.1, 'n_estimators': 500, 'max_depth': 5, 'min_child_weight': 1, 'seed': 0,
                    'subsample': 0.8, 'colsample_bytree': 0.8, 'gamma': 0, 'reg_alpha': 0, 'reg_lambda': 1}
    
    grid_search = xgb_train(X_data, Y_data, xgb_params, cv_params) 
#%% 测试模型
    bst = grid_search.best_estimator_
    pred = bst.predict(X_data)
    pred_prob = bst.predict_proba(X_data)
    
    #测试准确率
    from sklearn.metrics import accuracy_score
    print("test accuracy:{0}".format(accuracy_score(pred, Y_data)))
    
    #获取每个特征的重要性
    importance = bst.feature_importances_


#    #获取
#    a,b = get_feature_pred(bst, X_data, y_data)