# -*- coding: utf-8 -*-
"""
Created on 2018/8/9 15:51

@author: 006547
"""
from DataAPI.DataToolkit import *
import pickle


class ModelManagement:
    def __init__(self, start_date=None, end_date=None, position_window=None, update_model_period=None, mode='research', model_file=None, data_buffer=None, train_fri=True):
        self.model = None
        self.start_date = start_date
        self.end_date = end_date
        self.trading_day = get_trading_day(self.start_date, self.end_date)
        self.trading_day_fri = get_friday_trading_days(self.start_date, self.end_date)
        self.train_fri = train_fri
        self.position_window = position_window
        self.update_model_period = update_model_period
        self.infer_result = {}
        if mode == 'research':
            self.model_saved = {}
        else:
            self.model_saved = {self.trading_day[-1]: model_file}
            self.data_buffer = data_buffer
        self.mode = mode

    def register(self, model):
        self.model = model

    def train(self):
        model = self.model
        if self.mode == 'research':
            i_1 = 0
            for i in range(self.trading_day.__len__()):
                if self.train_fri:
                    if i == 0 or (self.trading_day[i] in self.trading_day_fri and i-i_1 >= self.position_window*self.update_model_period):
                        print('training ' + str(self.trading_day[i]))
                        i_1 = i
                        self.model_saved.update({self.trading_day[i]: model.train(self.trading_day[i])})
                else:
                    if i % (self.position_window*self.update_model_period) == 0:
                        print('training ' + str(self.trading_day[i]))
                        self.model_saved.update({self.trading_day[i]: model.train(self.trading_day[i])})
                if i % self.position_window == 0:
                    print('inferring ' + str(self.trading_day[i]))
                    absolutePath = self.model.para_model['absolutePath']
                    # if not os.path.exists(absolutePath + 'SignalFile/' + 'signal_' + str(self.trading_day[i]) + '.pickle'):
                    signal = model.infer(self.trading_day[i])
                    # else:
                    #     with open(absolutePath + 'SignalFile/' + 'signal_' + str(self.trading_day[i]) + '.pickle', 'rb') as f:
                    #         signal = pickle.load(f)
                    if signal is not None:
                        self.infer_result.update({self.trading_day[i]: signal})
                        if not os.path.exists(absolutePath + 'SignalFile/'):
                            os.makedirs(absolutePath + 'SignalFile/')
                        with open(absolutePath + 'SignalFile/' + 'signal_' + str(self.trading_day[i]) + '.pickle', 'wb') as f:
                            pickle.dump(signal, f)
                else:
                    print('copy ' + str(self.trading_day[i]))
                    absolutePath = self.model.para_model['absolutePath']
                    # if not os.path.exists(absolutePath + 'SignalFile/' + 'signal_' + str(self.trading_day[i]) + '.pickle'):
                    signal = self.infer_result[self.trading_day[i-1]]
                    # else:
                    #     with open(absolutePath + 'SignalFile/' + 'signal_' + str(self.trading_day[i]) + '.pickle', 'rb') as f:
                    #         signal = pickle.load(f)
                    if signal is not None:
                        self.infer_result.update({self.trading_day[i]: signal})
                        if not os.path.exists(absolutePath + 'SignalFile/'):
                            os.makedirs(absolutePath + 'SignalFile/')
                        with open(absolutePath + 'SignalFile/' + 'signal_' + str(self.trading_day[i]) + '.pickle', 'wb') as f:
                            pickle.dump(signal, f)
        elif self.mode == 'production':
            for i in range(self.trading_day.__len__()):
                signal = model.infer(self.trading_day[i])
                self.infer_result.update({self.trading_day[i]: signal})

