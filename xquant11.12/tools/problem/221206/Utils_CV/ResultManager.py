import numpy as np
import pandas as pd
from typing import List, Dict, Union
from xquant.pyfile import Pyfile


class ResultManager:
    def __init__(self, method='default', default_keys=None, is_output_all=False):
        self.__method = method
        if default_keys is None:
            self.__keys = ['annualReturnMV', 'averageTradingReturnRate', 'winRate', 'averagePositionTime',
                           'dayWinningRate', 'timesPerDay']
        else:
            self.__keys = default_keys
        self.__param_result_mat: Dict[str, Dict[str, np.ndarray]] = {}
        self.__open_triggers: Dict[str, List[float]] = {}
        self.__close_triggers: Dict[str, List[float]] = {}
        self.__results_df: Dict[str, pd.DataFrame] = {}
        self.__index_names = ['longAggressiveRatio', 'longPassiveRatio', 'shortAggressiveRatio', 'shortPassiveRatio']

    def get_keys(self):
        return self.__keys

    def set_results_for_symbol(self, symbol: str, results: List[Dict[str, Union[pd.DataFrame, Dict[str, float]]]]):
        self.__results_to_df(symbol, results)

    def __results_to_df(self, symbol, results: List[Dict[str, Union[pd.DataFrame, Dict[str, float]]]]):
        container = {}
        for name in self.__index_names:
            container.update({name: []})
        container.update({'Saved': []})
        for result in results:
            total = result['total']
            trigger = result['trigger']
            total_saved = total['Saved'].sum()
            for name in self.__index_names:
                th = trigger[name]
                container[name].append(th)
            container['Saved'].append(total_saved)
        index = []
        for name in self.__index_names:
            index.append(container[name])
        data = pd.DataFrame(data=container['Saved'], index=index, columns=['TotalSaved'])
        data.index.names = self.__index_names
        self.__results_df.update({symbol: data})

    def find_best_param(self, symbol: str, output_dir=None, suffix=None) -> Dict[str, float]:  # return the quantile
        best = self.__best_param(symbol)
        if output_dir is not None and suffix is not None:
            self.__output(symbol, best, output_dir, suffix)
        return best

    def __best_param(self, symbol: str) -> Dict[str, float]:
        df = self.__results_df[symbol]
        irow = df['TotalSaved'].values.argmax()
        row = df.index[irow]
        best = {}
        for name in self.__index_names:
            value = row[self.__index_names.index(name)]
            best.update({name: value})
        best.update({'irow': irow, 'row': row})
        return best

    def __output(self, symbol: str, q_dict, output_dir, suffix):
        py = Pyfile()
        xls_dir = output_dir + symbol + '/selection_from_' + suffix + '.xlsx'
        with py.open(xls_dir, 'wb') as f:
            writer = pd.ExcelWriter(f, engine='xlsxwriter')
            self.__results_df[symbol].to_excel(writer)
            writer.save()

    def get_results_full(self):
        return self.__param_result_mat
