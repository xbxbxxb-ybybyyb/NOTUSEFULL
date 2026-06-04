# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
import os
import shutil
from functools import reduce


def distribute_factor(src_path, dst_path, class_list):
    os.makedirs(dst_path, exist_ok=True)
    for each in class_list:
        src_file = os.path.join(src_path, "{}.py".format(each))
        dst_file = os.path.join(dst_path, "{}.py".format(each))
        shutil.copy(src_file, dst_file)
        print(each, "is copied to", dst_path)


if __name__== "__main__":
    src_path = "/tmp/pycharm_project_897/MMFactor"
    dst_path = "/data/user/015619/factor"

    # from StockFactor3S_2021.FACTOR_CONFIG import FACTOR_CONFIG_EASY, FACTOR_CONFIG_ALGO, FACTOR_CONFIG_ZEUS, FACTOR_CONFIG_MDF
    # from StockFactor3S_2021.NONFACTOR_CONFIG import NONFACTOR_CONFIG_MDF, NONFACTOR_CONFIG
    # FACTOR_CONFIG = FACTOR_CONFIG_MDF + FACTOR_CONFIG_ALGO + FACTOR_CONFIG_ZEUS + FACTOR_CONFIG_EASY + \
    #                 NONFACTOR_CONFIG + NONFACTOR_CONFIG_MDF

    from MMFactor.FACTOR_CONFIG import FACTOR_CONFIG
    from MMFactor.NONFACTOR_CONFIG import NONFACTOR_CONFIG

    from Production.Utils.get_nonfactors import get_nonfactors

    CONFIG = {each["FactorName"] if "FactorName" in each else each["ClassName"]: each for each in FACTOR_CONFIG + NONFACTOR_CONFIG}

    from collections import defaultdict
    owner_dict = defaultdict(list)

    for each in FACTOR_CONFIG:
        if "Successor" in each:
            owner = each["Successor"]
        else:
            owner = each["Owner"]

        # if each["FactorType"] == "TS":
        owner_dict[owner].append(each["FactorName"])

    class_dict = dict()

    for owner, factor_list in owner_dict.items():

        nonfactor_map = get_nonfactors(factor_list, CONFIG)
        nonfactor_list = sorted(reduce(lambda x, y: set(x).union(set(y)), nonfactor_map.values()))

        factor_class_list = sorted(set([CONFIG[each]["ClassName"] for each in factor_list]))
        nonfactor_class_list = sorted(set([CONFIG[each]["ClassName"] for each in nonfactor_list]))

        path = os.path.join(dst_path, owner)
        os.makedirs(path, exist_ok=True)

        distribute_factor(os.path.join(src_path, "Factor"), path, factor_class_list)
        distribute_factor(os.path.join(src_path, "NonFactor"), path, nonfactor_class_list)

        print(owner, len(factor_class_list))



