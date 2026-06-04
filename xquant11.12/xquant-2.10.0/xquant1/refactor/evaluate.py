# -*- coding: utf-8 -*-
"""
Created on Wed Aug 15 10:28:15 2018

@author: 013150
"""


#%%(6)模型评价
def plot_curve(dat, basePath):
    from matplotlib import pyplot as plt
    x = list(range(dat.shape[0]))
    y = dat[:]
#    y_smoonth = spline(T,power,xnew)  
    plt.figure()
    plt.plot(x,y)
    plt.savefig(basePath+str(1))