from typing import List, Dict


class ParamManager:
    def __init__(self, open_triggers: List[float], close_triggers: List[float]):
        self.__open_triggers: List[float] = open_triggers
        self.__close_triggers: List[float] = close_triggers
        self.__params: List[Dict[str, float]] = []
        # self.__index = 0
        self.__prepare_params()
        # if default_key is None:
        #     self.__default_key = ['annualReturnMV', 'averageTradingReturnRate']
        # else:
        #     self.__default_key = default_key
        # self.__param_result_mat: Dict[str, np.ndarray] = {}

    def __prepare_params(self):
        for open_trigger in self.__open_triggers:
            for close_trigger in self.__close_triggers:
                trigger_dict = {}
                trigger_dict['longTriggerRatio'] = open_trigger
                trigger_dict['shortTriggerRatio'] = -open_trigger
                trigger_dict['longCloseRatio'] = close_trigger
                trigger_dict['shortCloseRatio'] = -close_trigger
                trigger_dict['longRiskRatio'] = close_trigger - 0.2
                trigger_dict['shortRiskRatio'] = -close_trigger + 0.2
                self.__params.append(trigger_dict)

    # def has_next(self) -> bool:
    #     if self.__index < len(self.__params):
    #         return True
    #     else:
    #         return False

    # def next(self) -> Dict[str, float]:
    #     trigger_dict = self.__params[self.__index]
    #     self.__index += 1
    #     return trigger_dict

    def get_all_param_dicts(self) -> List[Dict[str, float]]:
        return self.__params

    # def set_results(self, results, keys=None):
    #     self.analyze(results, keys)

    # def analyze(self, results, keys=None):
    #     if keys is None:
    #         keys = ['winRate', 'averagePositionTime', 'dayWinningRate', 'timesPerDay']
    #     for key in keys:
    #         self.set_mat_from_key(results, self.__param_result_mat, key)
    #     for key in self.__default_key:
    #         self.set_mat_from_key(results, self.__param_result_mat, key)

    # def set_mat_from_key(self, results, mat_dict, key: str):
    #     matrix = np.zeros((len(self.__open_triggers), len(self.__close_triggers)))
    #     for result in results:
    #         open_trigger = result['longTriggerRatio']
    #         close_trigger = result['longCloseRatio']
    #         open_index = self.__open_triggers.index(open_trigger)
    #         close_index = self.__close_triggers.index(close_trigger)
    #         value = result[key]
    #         matrix[open_index, close_index] = value
    #     mat_dict.update({key: matrix})

    # def find_best_param(self, mat_dict):
    #     pass
