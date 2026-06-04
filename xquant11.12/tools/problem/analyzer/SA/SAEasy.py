#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/2/25 20:26

import numpy as np


class SAEasy:
    """
    Simulated Annealing of Easy Strategy
    """
    def __init__(self, func, max_open_amount, per_open_amount, shift,
                 init_iter_num=30, step_size=5, T=10000, max_iter_num=500, max_stay_num=150):

        self.func = func
        self.max_open_amount = max_open_amount
        self.per_open_amount = per_open_amount
        self.shift = shift
        self.init_iter_num = init_iter_num  # 搜索初始解尝试次数
        self.step_size = step_size
        self.T = T                          # 温度
        self.max_iter_num = max_iter_num    # 最大迭代次数
        self.max_stay_num = max_stay_num    # stop if best_y stay unchanged over max_stay_counter times
        self.re_init = True                 # 是否重新初始化

        ### Parameters
        self.x = {}   ### 保存{"i1": i1, "i2": i2, "i3": i3, "i4": i4, "i5": i5, "i6": i6}
        self.x1 = {}

        self.parameters_history = {}
        self.objective_history = []
        self.solution_dict = {}

    @staticmethod
    def is_valid_backtest_result(result):
        """
        Check 回测结果是否合法
        """
        # return (result['Average Return Rate'] > 0.7) and (result['Average Holding Time'] < 300) and (result['Win Rate (per day)'] > 0.5) and (result['Win Rate (per trade)'] > 0.4)
        # return (result['Average Holding Time'] < 300) and (result['Usage'] > 0) and (result['Days Open Rate'] > 0.5)
        # return (result['Average Holding Time (Long)'] < 300) and (result['Average Holding Time (Short)'] < 600)
        return (result['Average Holding Time'] < 300) and (result['Usage'] > 0)

    @staticmethod
    def get_objective_value(result):
        """ 输入回测结果，返回模拟退火优化的目标函数值
        """
        # return result['Average Profit (Long)'] + 2* result['Average Profit (Short)']
        # return result['Average Profit'] * max(0, result['Average Return Rate']) ** 0.3
        # return (result['Average Profit'] * 600) / (result['Average Holding Time'] + 600)
        # return result['Average Profit'] * abs(result['Average Return Rate']) ** 0.5 * result['Average Turnover'] ** 0.1
        # return result['Average Profit'] * abs(result['Market Value Return Rate']) ** 0.5
        return result['Average Profit'], - result['Std Return (per trade)']

    def generate_init_parameters(self):
        """
        生成初始参数, 存储在 self.x 字典里
        """
        print("Try to Generate Initial Parameters")
        is_found = False
        parameter_dict = {}
        for step in range(self.init_iter_num):
            i1 = np.random.choice(range(int(5 * self.shift + 2), 21))
            i4 = int(i1 - self.shift * 10)
            i2 = np.random.choice(range(-i4, i1 - 1))
            i3 = i2 - 2
            i6 = np.random.choice(range(-i1 + (i4 + i3), i4 - 3))
            i5 = i6 + 2

            self.x.update({"i1": i1, "i2": i2, "i3": i3, "i4": i4, "i5": i5, "i6": i6})

            ### 计算回测结果
            parameter_dict["long_trigger_ratio"] = i1 / 10
            parameter_dict["short_trigger_ratio"] = - i4 / 10
            parameter_dict["short_close_ratio"] = i3 / 10
            parameter_dict["short_risk_ratio"] = i2 / 10
            parameter_dict["long_close_ratio"] = -i6 / 10
            parameter_dict["long_risk_ratio"] = - i5/ 10

            bt_result = self.func.evaluate(parameter_dict)

            if self.is_valid_backtest_result(bt_result):
                print("Initial Parameters Found at Step: {}".format(step))
                is_found = True
                break

            print('Warming step: {}'.format(step))

        return is_found, bt_result

    def generate_new_parameters(self):
        """
        生成new参数: 基于已有参数self.x，产生新参数self.x1
        """
        s1 = np.round(np.random.standard_cauchy() * self.step_size)
        i11 = self.x["i1"] + s1
        while i11 > 20 or i11 < 5 * self.shift + 3 / 2:
            s1 = np.round(np.random.standard_cauchy() * self.step_size)
            i11 = self.x["i1"] + s1
        i41 = i11 - self.shift * 10

        i31 = self.x["i3"] + np.round(np.random.standard_cauchy() * self.step_size)
        while i31 < -i41 or i31 + 3 > i11:
            i31 = self.x["i3"]+ np.round(np.random.standard_cauchy() * self.step_size)
        i21 = min(i31 + 2, i11)

        i61 = self.x["i6"] + np.round(np.random.standard_cauchy() * self.step_size)
        while i11 + i61 < i31 + i41 or i61 + 3 > i41:
            i61 = self.x["i6"] + np.round(np.random.standard_cauchy() * self.step_size)
        i51 = min(i61 + 2, i41)

        self.x1.update({"i1": i11, "i2": i21, "i3": i31, "i4": i41, "i5": i51, "i6": i61})

    def cool_down(self):
        """
         实现温度冷却函数
        """
        self.T = self.T * 0.95
        self.step_size = max(1, self.step_size * 0.99)

    def update_solution(self, i_max, objective_value_list):
        """ 注意：目标值分别为平均盈利和每笔交易盈利波动率负值，值均是越大越好
        """
        obj_one, obj_two = objective_value_list
        remove_list = []
        dominated_by_others = False
        for obj1, obj2 in self.solution_dict:
            if (obj_one >= obj1 and obj_two > obj2) or (obj_one > obj1 and obj_two >= obj2) or (
                    obj_one > obj1 and obj_two > obj2):
                remove_list.append((obj1, obj2))
            elif obj_one <= obj1 and obj_two <= obj2:
                dominated_by_others = True
        for e in remove_list:
            self.solution_dict.pop(e)
        if not dominated_by_others:
            self.solution_dict[(obj_one, obj_two)] = i_max

    def run(self):
        """
        执行模拟退火算法
        """
        ### Step 1, 生成初始参数
        is_init_found, init_bt_result = self.generate_init_parameters()
        if not is_init_found:
            return self.solution_dict

        ### Step 2, 执行模拟退火迭代
        i_max = [self.x["i1"], self.x["i2"], self.x["i3"], self.x["i4"], self.x["i5"], self.x["i6"], init_bt_result['Total Profit']]
        obj_one, obj_two = self.get_objective_value(init_bt_result)
        self.solution_dict[(obj_one, obj_two)] = i_max

        opt_obj = obj_one
        current_obj = obj_one
        bt_result = init_bt_result
        opt_bt_result = init_bt_result
        k, k1, k_opt = 0, 0, 0
        last_update_k = None
        # re_anneal_interval = 0
        while k <= self.max_iter_num:
            if k1 >= self.max_stay_num:
                break

            self.generate_new_parameters()

            i11, i21, i31, i41, i51, i61 = self.x1['i1'], self.x1['i2'], self.x1['i3'], self.x1['i4'], self.x1['i5'], self.x1['i5']

            if any([abs(i21) > 30, abs(i31) > 30, abs(i51) > 30, abs(i61) > 30]):
                continue

            if (i11, i21, i31, i41, i51, i61) in self.parameters_history:
                 bt_result_new = self.parameters_history[i11, i21, i31, i41, i51, i61]
            else:
                parameter_dict = {}
                parameter_dict["long_trigger_ratio"] = i11 / 10
                parameter_dict["short_trigger_ratio"] = - i41 / 10
                parameter_dict["short_close_ratio"] = i31 / 10
                parameter_dict["short_risk_ratio"] = i21 / 10
                parameter_dict["long_close_ratio"] = -i61 / 10
                parameter_dict["long_risk_ratio"] = - i51 / 10
                bt_result_new = self.func.evaluate(parameter_dict)
                self.parameters_history[i11, i21, i31, i41, i51, i61] = bt_result_new

            obj_one, obj_two = self.get_objective_value(bt_result)
            obj_one_new, obj_two_new = self.get_objective_value(bt_result_new)
            delta_obj = (obj_one - obj_one_new + obj_two - obj_two_new) / 2.
            prob = np.exp( - delta_obj / self.T)   # delta_obj < 0: 更优解；delta_obj > 0: 以一定概率成为容忍解
            t1 = np.random.sample()

            if t1 <= prob and self.is_valid_backtest_result(bt_result_new):
                # re_anneal_interval += 1
                last_update_k = k
                i1, i2, i3, i4, i5, i6 = i11, i21, i31, i41, i51, i61
                self.x.update({"i1": i1, "i2": i2, "i3": i3, "i4": i4, "i5": i5, "i6": i6})

                bt_result = bt_result_new
                current_obj = obj_one_new

                self.objective_history.append([current_obj, i1, i2, i3, i4, i5, i6])
                self.update_solution([i1, i2, i3, i4, i5, i6, bt_result['Total Profit']], [obj_one_new, obj_two_new])

                if self.objective_history[-1][0] >= opt_obj:
                    k_opt = k
                    opt_obj = self.objective_history[-1][0]
                    opt_bt_result = bt_result
                    i_max = [i1, i2, i3, i4, i5, i6, bt_result['Total Profit']]

            # if re_anneal_interval > 20:
            #     self.T = 5000
            #     self.step_size = 3
            #     re_anneal_interval = 0

            if last_update_k is not None and k - last_update_k > 50:
                break

            if current_obj < opt_obj and k - k_opt > 20:
                i1, i2, i3, i4, i5, i6, _ = i_max
                self.x.update({"i1": i1, "i2": i2, "i3": i3, "i4": i4, "i5": i5, "i6": i6})
                k_opt = k
                bt_result = opt_bt_result

                if opt_obj > 10000 and self.re_init == True:
                    self.T = self.T * 10 * (0.95 ** k1)
                    self.re_init = False
                    print('Re-Initialization, Temperature Cooling Down to {}'.format(self.T))

            if self.is_valid_backtest_result(bt_result_new):
                self.cool_down()
                k1 += 1

            k += 1

        if len(self.objective_history) == 0:
            return {}
        else:
            return self.solution_dict






