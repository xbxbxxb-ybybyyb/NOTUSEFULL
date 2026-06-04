# coding:utf-8
# import sys
# sys.path.append("D:\PycharmProjects\metadata\\")
from metadata import MetaData

md = MetaData()
# #1. 新增库
# md.add_factor_library("MetaTest")

# #2. 新建因子目录
# md.add_factor_catalog("MetaTest", "测试目录一")

# 3.新增因子查询配置 library_name, factor_dict, data_frequency, owner_table_name
# factor_dict = {'accrueddays': '已计息天数', 'accruedinterest': '应计利息', 'ptm': '剩余期限（年）', 'curyield': '当期收益率',
#                'ytm': '纯债到期收益率', 'strbvalue': '纯债价值', 'strbpremium': '纯债溢价', 'strbpremiumratio': '纯债溢价率',
#                'convprice': '转股价', 'convratio': '转股比例', 'convvalue': '转股价值', 'convpremium': '转股溢价',
#                'convpremiumratio': '转股溢价率'}
# factor_dict = {'accrueddays': '已计息天数',}
# md.add_factor_meta("MetaTest",factor_dict,6,"meta_test_table")

# # 4. 新增因子与目录关联 library_name, cata_name, factor_list
# factor_list = ['accrueddays', 'accruedinterest', 'ptm', 'curyield', 'ytm', 'strbvalue', 'strbpremium',
#                'strbpremiumratio', 'convprice', 'convratio', 'convvalue', 'convpremium', 'convpremiumratio']
#
# factor_list = ["accrueddays"]
# md.add_factor_catalog_rela("MetaTest","测试目录一", factor_list)


# # # 5. 批量删除因子
# factors = ["accrueddays"]
# md.del_factor_meta("MetaTest", "测试目录一", factors)
