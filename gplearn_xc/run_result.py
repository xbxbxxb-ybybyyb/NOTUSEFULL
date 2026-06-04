import pandas as pd
import numpy as np

from tqdm import tqdm
from joblib import Parallel, delayed

import os
import time as mytime
import pickle
import shutil
import random
from my_gplearn.genetic import SymbolicRegressor

import sys
# print(os.path.abspath('../my_functions'))
sys.path.append(os.path.abspath('../my_functions'))
import my_fun as mf

# BASE_DIR = r'D:/Work/遗传算法测试'

BASE_DIR = r'/data/user/017839/my_python/gplearn_xc'


def get_fitness_list(gp_gen,gen = 0):
    # gp_gen = est_gp._programs[gen]
    fit_list = []
    for i in range(len(gp_gen)):
        if gp_gen[i] is None:
            fitness = np.nan
            oob_fitness = np.nan
        else:
            fitness = gp_gen[i].raw_fitness_
            oob_fitness = gp_gen[i].oob_fitness_
        fit_list.append([gen,i,fitness,oob_fitness])
    return fit_list

def get_fitness_parallel(est_gp,n_jobs = -1):
    n_gen = len(est_gp._programs)
    # gp_gen = est_gp._programs[gen]
    result = Parallel(n_jobs=n_jobs,verbose = 0)(delayed(get_fitness_list)(est_gp._programs[i],i) for i in tqdm(range(n_gen),position = 0))
    
    rlist = []
    for i in result:
        rlist = rlist + i
        
    result = pd.DataFrame(rlist,columns = ['gen','idx','fitness','out_fitness'])
    result = result.sort_values(by = 'out_fitness',ascending = False)
    return result
        
def load_result(fn):
    with open(BASE_DIR + r'/result/%s' % fn,'rb') as file:
        result = pickle.load(file)
    est_gp = result[1]
    result = get_fitness_parallel(est_gp)

    return result


print(1111)