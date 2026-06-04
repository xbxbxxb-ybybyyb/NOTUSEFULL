import pandas as pd

pd.set_option('display.max_columns', None)
import pymysql
import pymysql.cursors

connection1 = pymysql.connect(host='168.63.1.130', port=3309, user='xquant', password='QQ_jfdf_2289',
                              db='xquant', charset='utf8', cursorclass=pymysql.cursors.DictCursor)

cursor1 = connection1.cursor()

# %%
"""
#步骤1，创库
insert into tbl_factor_library(id, library_type, library_name, remark) values(5, 1, "Industry_factor", null);

#步骤2，创建目录（需要手动输入父目录），一级目录的父目录为0
insert into tbl_factor_catalog(catalog_id, parent_id, library_id, cata_name,creator_account,status,create_time) 
values(null, {}, 5, "行业数据库因子", "010793", 1, now());

insert into tbl_factor_catalog(catalog_id, parent_id, library_id, cata_name,creator_account,status,create_time) 
values(null, {}, 5, "房地产行业", "010793", 1, now());

"""
path = "D:/013150/Downloads/name.csv"
df = pd.read_csv(path)
# 步骤3，创建因子元数据(需要手动梳理因子中，英文名)
# day_type，0交易日，1自然日
# data_frequency:0每日
#
"""
             converttable(暂时不用)  factorcode            factorename   factorname         id
0  factor_d_financialreportindex    20502103     unearned_prem_rsrv   未到期责任准备金       1
1  factor_d_financialreportindex    20502104          out_loss_rsrv   未决赔款准备金         2 
2  factor_d_financialreportindex    20502105        life_insur_rsrv   寿险责任准备金         3
3  factor_d_financialreportindex    20502106      lt_health_insur_v   长期健康险责任准备金    4
4  factor_d_financialreportindex    20502107  independent_acct_liab   独立账户负债           5
"""
sql_sample = """INSERT INTO `tbl_factor_meta`
(`id`, `factor_symbol`, `factor_name`, `day_type`, `estimate_ground_time`, `estimate_symbol_count`, `estimate_symbol_percent`, `data_frequency`, `create_time`, `modify_time`, `factor_desc`, `library_id`, `owner_table_name`, `owner_col_name`, `creator_account`, `status`, `high_frequency`, `remark`) VALUES 
(null, '{}', '{}', 1, null, 0, 0, 0, sysdate(), sysdate(), NULL, {}, '{}', '{}', '010793', 1, NULL, NULL);
"""

error_count = 0
sql_list = []
for row_id, row in df.iterrows():
    factorename = str(row.loc["INDEXID"])
    factorname = row.loc["INDEXNAME"]
    #    converttable = row.loc["converttable"]
    library_id = 5
    sql = sql_sample.format(factorename, factorname, library_id, "", factorename)
    sql = sql.replace("\n", "")
    try:
        sql_list.append(sql)
    #        cursor1.execute(sql)
    #        connection1.commit()
    except Exception as e:
        print(e)
        print(sql)
        error_count = error_count + 1

# 步骤4，创建因子目录关联(需要手动添加catalog_id)

sql_sample = """INSERT INTO `tbl_factor_catalog_rela`
(`id`, `catalog_id`, `factor_id`, `remark`) VALUES 
(NULL, {}, {}, NULL);
"""

sql = "select * from tbl_factor_meta a where a.library_id = '5';"

result = cursor1.execute(sql)
result = cursor1.fetchall()
df = pd.DataFrame(result)

error_count = 0
sql_list = []
for row_id, row in df.iterrows():
    factor_id = row.loc["id"]
    #    catalog_id = 1515
    raise Exception("请确认catalog_id目录")

    sql = sql_sample.format(catalog_id, factor_id)
    sql = sql.replace("\n", "")
    try:
        sql_list.append(sql)
        cursor1.execute(sql)
        connection1.commit()
    except Exception as e:
        print(e)
        print(sql)
        error_count = error_count + 1


