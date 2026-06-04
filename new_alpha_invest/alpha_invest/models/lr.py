from sklearn.linear_model import LogisticRegression
from alpha_invest.models.modelbase import ModelManager
from alpha_invest import alpha_logger
from alpha_invest.datasets.tag import transform_label_2binray


class LR(ModelManager):
    def __init__(self, **kwargs):
        model_name = None
        self.model = LogisticRegression(random_state=0)
        super(LR, self).__init__(**kwargs)

    def transform_datay(self):
        """
        将multiindex原始标签数据，转换成（stock*date， 1）二维数据，并且将标签转换成0，1变量
        :return:
        """
        self.original_datay = transform_label_2binray(self.original_datay)
        day_label_cell = self.original_datay.unstack().values
        day_label_cell = day_label_cell.transpose([1, 0])
        alpha_logger.debug("{} day_label_cell tensor source shape: {}".format(self.label_name, day_label_cell.shape))
        day_label_cell = day_label_cell.reshape([len(self.tradingcodes)*len(self.dates), 1])
        alpha_logger.debug("{} day_label_cell tensor final shape: {}".format(self.label_name, day_label_cell.shape))
        return day_label_cell

    def train_loop(self, dataX, dataY):
        self.model.fit(dataX, dataY)
        return self.model

    def infer(self, dataX, proba = True):
        if proba:
            #每个样本给出各个分类的预测概率
            preds = self.model.predict_proba(dataX)
        else:
            preds = self.model.predict
        return preds
