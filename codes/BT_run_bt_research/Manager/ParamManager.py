from typing import List, Dict


class ParamManager:
    def __init__(self, open_triggers: List[float], close_triggers: List[float]):
        self.__open_triggers: List[float] = open_triggers
        self.__close_triggers: List[float] = close_triggers
        self.__params: List[Dict[str, float]] = []
        self.__prepare_params()

    def __prepare_params(self):
        for open_trigger in self.__open_triggers:
            for close_trigger in self.__close_triggers:
                trigger_dict = dict()
                trigger_dict['longTriggerRatio'] = open_trigger
                trigger_dict['shortTriggerRatio'] = -open_trigger
                trigger_dict['longCloseRatio'] = close_trigger
                trigger_dict['shortCloseRatio'] = -close_trigger
                trigger_dict['longRiskRatio'] = close_trigger - 0.2
                trigger_dict['shortRiskRatio'] = -close_trigger + 0.2
                self.__params.append(trigger_dict)

    def get_all_param_dicts(self) -> List[Dict[str, float]]:
        return self.__params
