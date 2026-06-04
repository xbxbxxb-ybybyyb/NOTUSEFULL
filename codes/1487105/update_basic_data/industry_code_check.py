import sys
import os
import pandas as pd
import numpy as np
import datetime
from xquant.xqutils.helper import link
from config_path import * 
industries = ['sw1_industry_code','sw2_industry_code','industry_code_all','swX_industry_code',
                'citics1_industry_code','citics2_industry_code','citicsX_industry_code']

cnum = {}                
for ind in industries:
    cc=pd.read_pickle(basic_data_path+'daily/'+ind+'.pkl')
    cnum[ind] = (cc.iloc[-1].fillna(100.) != cc.iloc[-2].fillna(100.)).sum()

lm = link.LinkMessage()
lm.sendMessage("Miss Dict: {0}".format(cnum))