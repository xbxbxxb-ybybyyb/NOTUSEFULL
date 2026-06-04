import xgboost as xgb
from alpha_invest.models.modelbase import ModelMananger
from alpha_invest import alpha_logger
from alpha_invest.datasets.tag import transform_label_2binray


class XGB(ModelMananger):
    def __init__(self, **kwargs):
        super(XGB, self).__init__(**kwargs)

    def transform_datay(self):
        """
        将multiindex原始标签数据，转换成（stock*date， 1）二维数据，并且将标签转换成0，1变量
        :return:
        """
        self.original_datay = transform_label_2binray(self.original_datay)
        day_label_cell = self.original_datay.unstack().values
        day_label_cell = day_label_cell.transpose([1, 0])
        alpha_logger.debug("{} day_label_cell tensor source shape: {}".format(self.label_name, day_label_cell.shape))
        day_label_cell = day_label_cell.reshape([len(self.tardingcodes)*len(self.dates), 1])
        alpha_logger.debug("{} day_label_cell tensor final shape: {}".format(self.label_name, day_label_cell.shape))
        return day_label_cell

    def prepare_data(self, data_params):
        pass


    def train(self, model_params):
        dataX = model_params.pop("dataX")
        dataY = model_params.pop("dataY")
        dtrain = xgb.DMatrix(dataX, label=dataY)

        evals_result ={}
        num_boost_round = model_params.pop("num_boost_round")
        params = model_params.pop("params")
        self.model = xgb.train(params,
                dtrain,
                num_boost_round,
                evals=[(dtrain, "train")],
                evals_result=evals_result,
                **model_params)
        return self.model

    def predict(self, dataX, proba = False):
        dtest = xgb.DMatrix(dataX)
        preds = None
        if proba:
            raise Exception()
            #每个样本给出各个分类的预测概率
            # preds = self.model.predict_proba(dtest)
        else:
            preds = self.model.predict(dtest)
        return preds

