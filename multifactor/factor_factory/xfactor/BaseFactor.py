from abc import abstractmethod
import pandas as pd
from xfactor.Database import Database


class BaseFactor(object):
    depend_data = []
    depend_factors = []
    depend_nonfactors = []

    factor_type = "DAY"
    fix_times = ["1000", "1030", "1100", "1300", "1330", "1400", "1430"]
    lag = 0
    financial_lag = 0


    reform_window = 1

    def __init__(self, **args):
        for k, v in args.items():
            setattr(self, k, v)

    @classmethod
    def get_factor_class_name(cls):
        return cls.__name__

    def __update_single_database(self, database, single_database, data_info, start_datetime, end_datetime, depend_type,
                                 fix_time="1500"):
        depend_type_data_list = eval("self." + depend_type)
        for depend_type_data in depend_type_data_list:
            if data_info[depend_type][depend_type_data] == "DAY":
                if fix_time == "1500":
                    value = eval('database.{}'.format(depend_type))[depend_type_data].loc[start_datetime: end_datetime]
                else:
                    value = eval('database.{}'.format(depend_type))[depend_type_data].loc[
                            start_datetime: end_datetime].iloc[:-1, ]
            elif data_info[depend_type][depend_type_data] == "MINUTE":
                value = eval('database.{}'.format(depend_type))[depend_type_data].loc[
                        start_datetime + "0925": end_datetime + fix_time]
            else:
                # TODO 其他类型抛错
                raise Exception("data type only DAY or MINUTE!")
            single_database.update(depend_type, depend_type_data, value)

    def calc(self, database, data_info, calc_datetime_list, full_datetime_list):
        result = {}
        start_index = full_datetime_list.index(calc_datetime_list[0]) - max(self.reform_window - 1, 0)
        factor_name = self.get_factor_class_name()
        result_list = []

        if self.factor_type == "DAY":
            for index in range(start_index, start_index + len(calc_datetime_list) + max(self.reform_window - 1, 0)):
                single_database = Database()
                start_datetime = full_datetime_list[index - self.lag]
                end_datetime = full_datetime_list[index]

                if database.depend_data:
                    self.__update_single_database(database, single_database, data_info, start_datetime, end_datetime,
                                                  "depend_data", "1500")
                if database.depend_factors:
                    self.__update_single_database(database, single_database, data_info, start_datetime, end_datetime,
                                                  "depend_factors", "1500")
                if database.depend_nonfactors:
                    self.__update_single_database(database, single_database, data_info, start_datetime, end_datetime,
                                                  "depend_nonfactors", "1500")
                single_res = self.calc_single(single_database)
                single_res.name = end_datetime
                single_res = single_res.to_frame().T
                result_list.append(single_res)

            result_df = pd.concat(result_list, axis=0)
            result_df = self.reform(result_df).iloc[max(self.reform_window - 1, 0):]
            result.update({factor_name: result_df})
            return result

        elif self.factor_type == "FIX":
            for fix_time in self.fix_times:
                current_factor_name = "Fix" + fix_time + "_" + factor_name
                for index in range(start_index, start_index + len(calc_datetime_list) + max(self.reform_window - 1, 0)):
                    single_database = Database()
                    start_datetime = full_datetime_list[index - self.lag]
                    end_datetime = full_datetime_list[index]

                    if database.depend_data:
                        self.__update_single_database(database, single_database, data_info, start_datetime,
                                                      end_datetime, "depend_data", fix_time)
                    if database.depend_factors:
                        self.__update_single_database(database, single_database, data_info, start_datetime,
                                                      end_datetime, "depend_factors", fix_time)
                    if database.depend_nonfactors:
                        self.__update_single_database(database, single_database, data_info, start_datetime,
                                                      end_datetime, "depend_nonfactors", fix_time)

                    single_res = self.calc_single(single_database)
                    single_res.name = end_datetime
                    single_res = single_res.to_frame().T
                    result_list.append(single_res)
                result_df = pd.concat(result_list, axis=0)
                result_df = self.reform(result_df).iloc[max(self.reform_window - 1, 0):]
                result.update({current_factor_name: result_df})
            return result

    @abstractmethod
    def calc_single(self, single_database):
        return None

    def reform(self, temp_result):
        return temp_result
