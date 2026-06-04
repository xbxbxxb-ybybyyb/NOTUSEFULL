

import pandas as pd

import pymysql

sql_config = {
            'host': '168.63.1.131',
            'user': 'xquant_cusdata',
            'passwd': 'XU_viah_8826',
            'db': 'xquant_cusdata',
            'port': 3307,
            'charset': 'utf8'
        }


def get_conforecastindex_factor_info():
    data = pd.read_excel("conforecastindex_factor.xlsx", sheet_name=None, header=0, usecols=["因子名称", "来源表"])
    df = data['一致预期']
    df['来源表'] = df['来源表'].apply(lambda x: x.strip().lower())
    df['因子名称'] = df['因子名称'].apply(lambda x: x.strip().lower())
    df.rename(columns={'因子名称':'factor','来源表':'source_table',},inplace=True)
    df['is_calc'] = 0
    values = [tuple(xi) for xi in df.values]
    return values


def insert_sql():
    conn_t = pymysql.connect(**sql_config)
    cur_t = conn_t.cursor()
    values = get_conforecastindex_factor_info()
    print(values)
    sql_use = "insert into fac_info (fac_name,tb_name,is_calc) values (%s,%s,%s) "
    # try:
    #     cur_t.executemany(sql_use,values)
    #     conn_t.commit()
    # except pymysql.err as e:
    #     conn_t.rollback()
    #     print("插入数据失败：{}".format(e))
    cur_t.close()
    conn_t.close()



insert_sql()
