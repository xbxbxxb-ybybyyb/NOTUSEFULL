import pandas as pd
import pandas as pd
import pymysql

# sql 命令
sql_cmd = "  select b.id,a.signal_subtype from signal_subtype_encode a join signal_subtype_encode_map b on a.signal_subtype = b.signal_subtype where a.signal_type_code = 8 order by id;"

#sql)cmd = "select * from signal_subtype_encode"

# 用DBAPI构建数据库链接engine
#con = pymysql.connect(host="168.64.33.17", user="xtraderops", password="YV_turi_86", database="ats_quant", charset='utf8', use_unicode=True)
con = pymysql.connect(host="168.9.65.8", port = 3317, user="marketmake_grey_dml", password="GXNA_idnd_0807", database="ats_quant_star_gray", charset='utf8', use_unicode=True)
df = pd.read_sql(sql_cmd, con)

result = []
for rid,row in df.iterrows():
    result.append({row["signal_subtype"]:row['id']})

import json
res = json.dumps(result)
res = res.replace(",", ",\n")

res = res.replace(":", ",")
print(res)
