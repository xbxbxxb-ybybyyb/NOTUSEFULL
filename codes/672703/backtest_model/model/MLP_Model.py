import os
import pandas as pd
from keras import models
from keras import layers
from keras import optimizers


class MLP_Model():
    
    def __init__(self,params):
        self._label_name = params['label_name']
        self._random_seed = 2333
        self._modelname =  params['modelname']
        self._model_path = params['model_path']
        self._prediction_path = params['prediction_path']

    def revise_model_path(self, path):
        self._model_path = path
    
    def revise_label(self, label):
        self._label_name = label

    def revise_random_seed(self, seed):
        self._random_seed = seed
        
    def get_model(self, sample, factor_list):
        
        y_train = sample[self._label_name].values

        x_train = sample[factor_list]

        mu = x_train.mean()
        std = x_train.std()
        std[std==0] = 1.e-6
        pd.DataFrame(index=['mu', 'std'], data=[mu, std]).T.to_pickle(os.path.join(self._model_path, 'mlgb_x_stats.pkl'))

        x_train = ((x_train - mu) / std).values


        model = models.Sequential()
        model.add(layers.Dense(128, activation='relu', input_shape=(x_train.shape[1],)))
        model.add(layers.BatchNormalization())
        model.add(layers.Dropout(0.5))
        model.add(layers.Dense(64, activation='relu'))
        model.add(layers.BatchNormalization())
        model.add(layers.Dropout(0.5))
        model.add(layers.Dense(64, activation='relu'))
        model.add(layers.BatchNormalization())
        model.add(layers.Dropout(0.25))
        model.add(layers.Dense(32, activation='relu'))
        model.add(layers.BatchNormalization())
        model.add(layers.Dropout(0.25))
        model.add(layers.Dense(1))
        model.compile(optimizer=optimizers.RMSprop(lr=1e-4), loss='mse', metrics=['mae'])
        model.fit(x_train, y_train, batch_size=512, epochs=20, verbose=0)
        model.save(os.path.join(self._model_path, 'mlgb_model.h5'))

        return model


    def label_predict(self, sample_daily, factor_list):
        model = models.load_model(os.path.join(self._model_path, 'mlgb_model.h5'))
        x_stats = pd.read_pickle(os.path.join(self._model_path, 'mlgb_x_stats.pkl'))
        x_test = ((sample_daily[factor_list] - x_stats['mu']) / x_stats['std']).values
        y_pred = model.predict(x_test)
        label_pred = pd.Series(index=sample_daily['stock'].values, data=y_pred.flatten())
        return label_pred