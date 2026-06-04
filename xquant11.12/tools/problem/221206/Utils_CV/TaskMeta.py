from Utils_CV.InputManager import InputManager
from Utils_CV.ResultManager import ResultManager
from typing import List


class TaskMeta:
    def __init__(self, symbols: List[str], input_manager: 'InputManager', result_manager: 'ResultManager', params=None,
                 symbol_suffix_id: int = None):
        self.__symbols = symbols
        self.__input_manager = input_manager
        self.__result_manager = result_manager
        self.__params = params
        self.__symbol_suffix_id = symbol_suffix_id

    def get_symbols(self):
        return self.__symbols

    def get_input_manager(self):
        return self.__input_manager

    def get_result_manager(self):
        return self.__result_manager

    def get_params(self):
        return self.__params

    def get_symbol_id(self):
        return self.__symbol_suffix_id
