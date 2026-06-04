# -*- coding: utf-8 -*-
"""
Created on Wed Aug 16 13:48:53 2017

@author: 006547
"""
from Tag.Tag import Tag
from System.SliceData import SliceData

class TagManagement:
    def __init__(self, para, factorManagement):
        self.__para = para      # 是计算这个Tag的参数
        self.__factorManagement = factorManagement
        self.__tag = []         # 它的内容是Tag的实例
        self.__indexTagUnfinished = []   # 还未完成(finish)的Tag的位置索引
        self.__timeStamp = []
        sliceData = SliceData()  # 初始化一个没用的切片用于实例化标签要用的因子和非因子
        Tag(self.__para, self.__factorManagement, sliceData)  # 实例化标签要用的因子和非因子

    def calculate(self, sliceData):  # 根据slice行情驱动，每个切片都会驱动一次
        self.__timeStamp.append(sliceData.timeStamp)
        indexTagUnfinished = []      # 临时存储是否完成的标记
        if len(self.__indexTagUnfinished) > 0:   # 查看哪些Tag还未完成(finish)，计算这些未完成的Tag的相应数据，如完成则做相应标记
            for i in range(len(self.__indexTagUnfinished)):
                if not self.__tag[self.__indexTagUnfinished[i]].finished:
                    self.__tag[self.__indexTagUnfinished[i]].calculate(sliceData)
                if not self.__tag[self.__indexTagUnfinished[i]].finished:   # 注意，前两行执行后、未必这个Tag就一定完成了（大概率还是未完成的），如未完成，再记录下来、记录到临时的indexTagUnfinished （注意没有self.）
                    indexTagUnfinished.append(self.__indexTagUnfinished[i])
        self.__indexTagUnfinished = indexTagUnfinished    # 上述循环结束后，以临时的indexTagUnfinished更新到self.__indexTagUnfinished中去

        self.__tag.append(Tag(self.__para, self.__factorManagement, sliceData))   # 根据最新的sliceData数据再实例化一组新的Tag, 并添加进TagManagement中
        self.__indexTagUnfinished.append(len(self.__tag) - 1)   # 刚生成的Tag显然是未完成的，所以要把其索引号（就是len-1）添加进self.__indexTagUnfinished

    def getLastTag(self):
        lastTag = self.__tag[-1]
        return lastTag

    def getLastTimeStamp(self):
        return self.__timeStamp[-1]
