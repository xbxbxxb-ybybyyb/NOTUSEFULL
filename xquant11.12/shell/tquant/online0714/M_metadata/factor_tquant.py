# 录入除8大类外的其他因子
import pandas as pd
from metadata import MetaData

md = MetaData()

# # 2. 新建因子目录
catalog_dict = {"行情指标": 2, "估值指标": 3, "财务报表": 4, "分红指标": 5,
                "最新信息": 6, "一致预期": 7, "财务分析": 8, "风险分析": 9,
                "Alpha指标": 10, "Barra指标": 11, "技术面指标": 12,
                "动量指标": 13, "情绪指标": 14,"评价指标":15, "Barra6指标":16}

# # for cata_name in catalog_dict:
# md.add_factor_catalog("Basic_factordata", "Barra6指标", catalog_dict["Barra6指标"])

# # 3.新增因子查询配置 library_name, factor_dict, data_frequency, owner_table_name
factor_dict = {'barra_cne6_beta': '贝塔',
               'barra_cne6_booktoprice': '账面市值比',
                'barra_cne6_dividendyield': '股息率',
                'barra_cne6_earningsquality': '收益质量',
                'barra_cne6_earningsvariability': '收益变动性',
                'barra_cne6_earningsyield': '收益率',
                'barra_cne6_growth': '成长',
                'barra_cne6_inverstmentquality': '投资质量',
                'barra_cne6_leverage': '杠杆因子',
                'barra_cne6_liquidity': '流动性因子',
                'barra_cne6_longtermreversal': '长期反转因子',
                'barra_cne6_midcap': '中市值',
                'barra_cne6_momentum': '动量因子',
                'barra_cne6_profitability': '盈利能力',
                'barra_cne6_residualvolatility': '市场杠杆',
                'barra_cne6_size': '规模',
               }
#
# try:
#     md.add_factor_meta("Basic_factordata", factor_dict, 6, 'factor_day_barrarisk6')
# except Exception as e:
#     print("table:{0} insert error,the reason:{1}".format('factor_day_barrarisk6', e))



# # 4. 新增因子与目录关联 library_name, cata_name, factor_list
catalog_list = ["行情指标", "估值指标", "财务报表", "财务分析", "风险分析", "最新信息",
                "Alpha指标", "Barra指标", "技术面指标", "动量指标", "情绪指标","Barra6指标"]#, "分红指标"
try:
    md.add_factor_catalog_rela("Basic_factordata", "Barra6指标", list(factor_dict.keys()))
except Exception as e:
    print("<ERROR> : table:{0} insert error,the reason:{1}".format("行情指标", e))

