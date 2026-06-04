import os
import path
from pickle import load, dump
# 记录实验次数
exp_num_path = "../expNum.pickle"
# 记录map
name_dict_path = "../nameDict.pickle"

def get_history_exp():
    if os.path.exists(exp_num_path):
        with open(exp_num_path,'rb') as f:
            exp_num = load(f)
    else:
        exp_num = 0

    if os.path.exists(name_dict_path):
        with open(name_dict_path,'rb') as f:
            name_map = load(f)
    else:
        name_map ={}

    return exp_num, name_map


def save_current_exp(exp_num, name_map):
    with open(exp_num_path,'wb') as f:
        dump(exp_num, f)

    with open(name_dict_path,'wb') as f:
        dump(name_map, f)

if __name__ == "__main__":
    exp_num = 0
    # print(get_history_exp())
    # exp_num = 1
    # name_map = {}
    # name_map['test'] = 0
    # save_current_exp(exp_num, name_map)