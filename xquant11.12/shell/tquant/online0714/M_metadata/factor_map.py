import pandas as pd
import pymysql1
import os
import json

encrypt_path = os.path.join('/'.join(os.path.abspath(__file__).split('/')[:-1]), "encrypted_database.json")
with open(encrypt_path, 'rb') as f:
    ENCRYPTED_HOSTS = json.load(f)



switch = 1

if switch == 0:
    xquant_config = {
        'host': '168.63.1.130',
        'user': 'xquant',
        'passwd': ENCRYPTED_HOSTS['xquant']['test']['xquant']['ciphertext'],
        'db': 'xquant',
        'port': 3309,
        'charset': 'utf8'
    }
    xquant_data_config = {
        'host': '168.63.1.130',
        'user': 'xquant_data',
        'passwd': ENCRYPTED_HOSTS['xquant']['test']['xquant_data']['ciphertext'],
        'db': 'xquant_data',
        'port': 3309,
        'charset': 'utf8'
    }

else:
    xquant_config = {
        'host': '168.6.68.72',
        'user': 'xquant',
        'passwd': ENCRYPTED_HOSTS['xquant']['prd']["xquant"]['ciphertext'],
        'db': 'xquant',
        'port': 3306,
        'charset': 'utf8'
    }
    xquant_data_config = {
                    'host': '168.6.68.72',
                    'user': 'xquant',
                    'passwd': ENCRYPTED_HOSTS['xquant']['prd']['xquant']['ciphertext'],
                    'db': 'xquant_data',
                    'port': 3306,
                    'charset': 'utf8'
                }


def get_meta_factors():
    conn_xquant = pymysql1.connect(**xquant_config)
    sql_use = "select factor_symbol,factor_name,owner_table_name from tbl_factor_meta where owner_table_name like 'factor_d_%' or owner_table_name like 'bond_d_%' and library_id=1"
    df = pd.read_sql(sql_use, conn_xquant)
    conn_xquant.close()
    return df


def get_factor_map_factors():
    conn_xquant_data = pymysql1.connect(**xquant_data_config)
    sql_use = "select factorename,factorname from factor_map"
    df = pd.read_sql(sql_use, conn_xquant_data)
    conn_xquant_data.close()
    df.rename(columns={'factorname': 'factor_name', 'factorename': 'factor_symbol'}, inplace=True)
    return df


def get_unconfig_factor():
    df_meta = get_meta_factors()
    df_map = get_factor_map_factors()
    factor_map_factors = df_map["factor_symbol"].tolist()
    df_unconfig = df_meta[~df_meta["factor_symbol"].isin(factor_map_factors)]
    unconfig_data = [tuple(i) for i in df_unconfig.values]
    return unconfig_data


def insert_factor_map():
    conn_xquant_data = pymysql1.connect(**xquant_data_config)
    cur = conn_xquant_data.cursor()
    sql_use = """insert into factor_map (factorename,factorname,converttable) 
                 values 
                 (%s, %s, %s)
                    """
    values = get_unconfig_factor()
    print(values)
    try:
        if len(values) == 1:
            cur.execute(sql_use, values[0])
        else:
            cur.executemany(sql_use, values)
        conn_xquant_data.commit()
    except pymysql1.err.OperationalError as e:
        conn_xquant_data.rollback()
        raise Exception("因子配置插入失败：{0}".format(e))
    cur.close()
    conn_xquant_data.close()


if __name__ == "__main__":
    insert_factor_map()
