# -*- coding: utf-8 -*-
"""
Created on Wed Dec  5 09:34:16 2018

@author: zsj
"""
import os

def generate_path(base_path,sub_folder_list):
    path_dict = {sub:os.path.join(base_path,str(sub)) for sub in sub_folder_list}
    [os.makedirs(path) if not os.path.exists(path) else None for path in list(path_dict.values())+[base_path]]
    return path_dict
