# _*_ coding:utf-8 _*_

from enum import IntEnum,unique


@unique
class STYPE(IntEnum):
    COMBINED     =  408001000     # 合并报表
    COMBINED_SS  =  408002000     # 合并报表(单季度
    COMBINED_SSA =  408003000     # 合并报表(单季度调整
    COMBINED_A   =  408004000     # 合并报表(调整
    COMBINED_NM  =  408005000     # 合并报表(更正前
    PARENT       =  408006000     # 母公司报表
    PARENT_SS    =  408007000     # 母公司报表(单季度
    PARENT_SSA   =  408008000     # 母公司报表(单季度调整
    PARENT_A     =  408009000     # 母公司报表(调整
    PARENT_NM    =  408010000     # 母公司报表(更正前


@unique
class IndustryType(IntEnum):
    CSRC    = 1     #证监会分类
    CITICS  = 2     #中信证券分类
    SW      = 3     #申万证券分类