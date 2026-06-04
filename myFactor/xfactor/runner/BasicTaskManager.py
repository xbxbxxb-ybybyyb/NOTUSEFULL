from xfactor.runner.BaseTaskManager import BaseTaskManager
from xfactor.Util import get_trading_day


# 一个因子一个任务，每个任务不超过100天
class BasicTaskManager(BaseTaskManager):
    max_factor_num_per_task = 1
    max_date_num_per_task = 100

    def split_calc_datetime_into_group(self):
        # 按照天数将需要计算的时间段进行分组，例如，每100个交易日分一组
        group = []
        calc_datetime_list = get_trading_day(self.start_date, self.end_date)
        size = len(calc_datetime_list)
        from_index = 0
        while from_index < size:
            group.append(calc_datetime_list[from_index: min(size, from_index + self.max_date_num_per_task)])
            from_index += self.max_date_num_per_task
        return group

    # 将因子进行分组
    def split_calc_factor_into_group(self):
        group = []
        size = len(self.factor_class_list)

        from_index = 0
        while from_index < size:
            group.append(self.factor_class_list[from_index: min(size, from_index + self.max_factor_num_per_task)])
            from_index += self.max_factor_num_per_task
        return group
