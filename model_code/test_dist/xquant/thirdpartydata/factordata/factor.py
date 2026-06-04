from FactorProvider.factordata import xqfactor
from FactorProvider.factordata.psfactor import FactorData as PFactorData
from xquant.xqutils.utils import statisticLog


class FactorData():
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance:
            return cls.__instance
        else:
            obj = object.__new__(cls)
            cls.__instance = obj
            cls.__instance.__initialized = False
            return cls.__instance

    @statisticLog('thirdpartydata', 'FactorData')
    def __init__(self):
        if self.__initialized:
            return
        self.__initialized = True
        self.ps_factor = PFactorData()

    @statisticLog('thirdpartydata', 'FactorData')
    def get_factor_value(self, library_name, stock=None, mddate=None, factor_names=None, statement_type=None,
                         stock_type=1, block_type=4, fill_na=False, use_mysql=False, return_single_factor=False,
                         daily_bar_num=242, sort_option=True, category='stock', **kwargs):
        scheme_source = library_name.split("_")[0].upper()
        table_name = library_name[len(scheme_source) + 1:]
        if scheme_source in ["WIND", "GOGOAL"]:
            if return_single_factor:
                raise Exception("查询 {} 因子不支持该参数设为True!".format(scheme_source))
            if use_mysql and xqfactor.judge_table_in_mysql(table_name):
                result = xqfactor.get_mysql_source(library_name, **kwargs)
            else:
                result = self.ps_factor.__get_wind_source(library_name, **kwargs)
            return result
        else:
            if return_single_factor:
                raise Exception("查询 {} 因子不支持该参数设为True!".format(scheme_source))
            result = self.ps_factor.__get_wind_source(library_name, scheme_source, **kwargs)
            return result
