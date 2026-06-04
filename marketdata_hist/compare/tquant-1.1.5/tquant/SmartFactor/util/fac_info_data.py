"""
构建fac_info表数据
"""
import ray
import pandas as pd, numpy as np, cx_Oracle, os, sys, functools, time, datetime, re, importlib.util
from sqlalchemy import create_engine, MetaData, Table, inspect, update, Column
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker, mapper
basedir = os.path.abspath(os.path.join(os.path.abspath(__file__), '../../..'))
sys.path.append(basedir)
from tquant.SmartFactor.FactorFactory import Factor


if __name__ == '__main__':
    fc = Factor()
    Base = automap_base()
    Base.prepare(fc.insert_engine, reflect=True)
    tables = Base.classes.keys()
    tables_day = [i for i in tables if i.startswith('factor_day_')]
    no_fac = ['id', 'tradingcode', 'tdate', 'entrytime', 'updatetime', 'exchangecode', 'exchangename', 'divideseason',
              'statement_type', 'resourceid',]
    df = pd.DataFrame(columns=['fac_name', 'tb_name'])
    for tb_name in tables_day:
        # row_cls = getattr(Base.classes, tb)
        row_cls = Table(tb_name, fc.metadata, autoload=True)
        col = [str(i).split('.')[1] for i in row_cls.c]
        res = [i for i in col if i not in no_fac]
        df1 = pd.DataFrame()
        df1['fac_name'] = res
        df1['tb_name'] = tb_name
        df = pd.concat([df, df1])
    fc.to_sql(df, library_name='fac_info')
    print(df)
