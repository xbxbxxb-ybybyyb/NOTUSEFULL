# -*- coding: utf-8 -*-
"""
Created on 2019/6/17 11:02

@author: 006547
"""
import os
import platform


class AddressManagement:
    def __init__(self, x_cloud=True):
        self.__x_cloud = x_cloud
        self.__user_id = '054703'
        self.__root = None
        if platform.system() == "Windows":
            self.__platform = "Windows"
        elif os.system("nvidia-smi>/dev/null") == 0:
            self.__platform = "Linux-GPU"
        else:
            self.__platform = "Linux-CPU"

    def get_platform(self):
        return self.__platform

    def get_root(self, user_id='054703', windows_root=''):
        if not self.__x_cloud:
            if self.__platform == "Windows":  # 云桌面环境运行是Windows
                self.__root = windows_root
                return self.__root
            elif self.__platform == "Linux-GPU":
                if user_id == '666888':
                    self.__root = "/vipcsf"
                elif user_id == '666889':
                    self.__root = "/vipzrz"
                elif user_id == 'group':
                    self.__root = "/user/data"
                else:
                    self.__root = "/data/user"
                return self.__root
            elif self.__platform == "Linux-CPU":
                if user_id == 'auto':
                    self.__user_id = os.environ['USER_ID']
                elif user_id == 'group':
                    self.__root = "/user/data"
                    return self.__root
                else:
                    self.__user_id = user_id
                self.__root = "/user/data/" + self.__user_id
                return self.__root

        else:
            self.__user_id = user_id
            if user_id == 'group':
                self.__root = "/data/group"
            else:
                self.__root = "/data/user/" + self.__user_id
            return self.__root
