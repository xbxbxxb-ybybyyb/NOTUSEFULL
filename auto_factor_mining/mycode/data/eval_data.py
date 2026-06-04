import sys
import os
from joblib import Parallel, delayed
from os import path
sys.path.append(path.join(path.dirname(__file__), '..'))

import numpy as np
import pandas as pd
from gplearn_my.genetic import SymbolicTransformer
from gplearn_my.customized_utils import gplearn_offical_alpha
from gplearn_my.fitness import _fitness_map, _Fitness


def filter_redundancy(est_gp):
    expression_set = set()
    program_list = list()
    for i in range(len(est_gp._best_programs)):
        program = est_gp._best_programs[i]
        if str(program) in expression_set:
            continue
        expression_set.add(str(program))
        program_list.append(program)
    return program_list

def parallel_evaluate_data(est_gp, decap_df, X, y, index, save_path, 
                           save=False, n_jobs=8, save_columns=["y_pred_raw"]):
    #decap_df = est_gp.decap_file
    exp_num = 1
    program_list = filter_redundancy(est_gp)
    program_list = program_list[:100]

    def parallel_evaluate(program, exp_num, X, y, index, save_path, save_columns=["y_pred_raw"]):
        factor_result = {}
        factor_col = "FactorAlpha{}".format(exp_num) # 存储的factor_name
        fitness = program.raw_fitness_
        factor_name  = "{}".format(program) # 存储的factor_expression

        factor_all = program.execute_norm(X, y, decap_df, index)

       
        if save_columns == ["y_pred_raw"]:
            factor_all = factor_all["y_pred_raw"]
            factor_all = factor_all.unstack()
            factor_all.to_pickle(os.path.join(save_path, factor_col+".pkl"))
        else:        
            factor_all[save_columns].parquet(os.path.join(save_path, factor_col+".parquet"))

        factor_result[factor_col] = [factor_name]
        return factor_result

    
    result = Parallel(n_jobs=n_jobs)(
        delayed(parallel_evaluate)(program, exp_num+i, X, y, index, save_path) for i, program in enumerate(program_list))


    print("Program Length: {}, result: {}".format(len(program_list),len(result)))
    #print(result)
    result = pd.concat([pd.DataFrame.from_dict(tmp, orient="index") for tmp in result])
    result = result.reset_index()
    result.columns = ["Factor","Formula"]

    file_name = str(save_path) + "/factor_resut_" + str(save_path).split('/')[-1] + ".csv"
    print(file_name)
    result.to_csv(file_name, index=True, )
    return result