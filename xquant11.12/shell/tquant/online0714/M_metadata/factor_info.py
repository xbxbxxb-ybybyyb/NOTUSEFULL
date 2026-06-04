import json
import os
encrypt_path = os.path.join('/'.join(os.path.abspath(__file__).split('/')[:-1]), "encrypted_database.json")

with open(encrypt_path, 'rb') as f:
    ENCRYPTED_HOSTS = json.load(f)
import pandas as pd

import pymysql1
switch = 1
if switch ==0:
    sql_config = {
                'host': '168.63.1.131',
                'user': 'xquant_cusdata',
                'passwd': ENCRYPTED_HOSTS['tquant']['test']['xquant_cusdata']['ciphertext'],
                'db': 'xquant_cusdata',
                'port': 3307,
                'charset': 'utf8'
                }
else:
    sql_config = {
                'host': '168.11.241.39',
                'user': 'htsc_dwa_quant',
                'passwd': ENCRYPTED_HOSTS['tquant']['prd']['htsc_dwa_quant']['ciphertext'],
                'db': 'htsc_dwa_quant',
                'port': 3306,
                'charset': 'utf8'
                }


def insert_sql():
    conn_t = pymysql1.connect(**sql_config)
    cur_t = conn_t.cursor()
    values = [('barra_cne6_beta', 'factor_day_barrarisk6', 0),
              ('barra_cne6_booktoprice', 'factor_day_barrarisk6', 0),
              ('barra_cne6_dividendyield', 'factor_day_barrarisk6', 0),
              ('barra_cne6_earningsquality', 'factor_day_barrarisk6', 0),
              ('barra_cne6_earningsvariability', 'factor_day_barrarisk6', 0),
              ('barra_cne6_earningsyield', 'factor_day_barrarisk6', 0),
              ('barra_cne6_growth', 'factor_day_barrarisk6', 0),
              ('barra_cne6_inverstmentquality', 'factor_day_barrarisk6', 0),
              ('barra_cne6_leverage', 'factor_day_barrarisk6', 0),
              ('barra_cne6_liquidity', 'factor_day_barrarisk6', 0),
              ('barra_cne6_longtermreversal', 'factor_day_barrarisk6', 0),
              ('barra_cne6_midcap', 'factor_day_barrarisk6', 0),
              ('barra_cne6_momentum', 'factor_day_barrarisk6', 0),
              ('barra_cne6_profitability', 'factor_day_barrarisk6', 0),
              ('barra_cne6_residualvolatility', 'factor_day_barrarisk6', 0),
              ('barra_cne6_size', 'factor_day_barrarisk6', 0)
              ]
    sql_use = "insert into fac_info (fac_name,tb_name,is_calc) values (%s,%s,%s) "
    try:
        cur_t.executemany(sql_use, values)
        conn_t.commit()
    except pymysql1.err as e:
        conn_t.rollback()
        print("插入数据失败：{}".format(e))

    cur_t.close()
    conn_t.close()


insert_sql()
