from sqlalchemy import create_engine
from xquant1.factordata.storageConfig import get_sql_config

def get_engine(user):
    engine = create_engine('mysql+pymysql://%s:%s@%s:%d/%s?charset=utf8' % (
        get_sql_config(user)['user'], get_sql_config(user)['passwd'],
        get_sql_config(user)['host'], get_sql_config(user)['port'], get_sql_config(user)['db']))
    return engine