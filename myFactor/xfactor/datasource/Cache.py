import os
import shutil

import pandas as pd
from loguru import logger

import settings
import xfactor.Util as Util

column_list = ["close", "limit_status", "amt", "volume"]


def __generate_local_file_list(p_date, local_cache_path):
    result = {}
    months = get_last_3_month(p_date)
    for month in months:
        for column in column_list:
            source_file = os.path.join(settings.MINUTE_DATA_PATH, 'stock', column, month + "_" + column + ".pkl")
            if os.path.join(source_file):
                target_file = local_cache_path + source_file
                result.update({
                    source_file: target_file
                })
    return result


# 实盘环境下，在onStrategyStateUpdated时调用
def cache_file_to_local(p_date, local_cache_path):
    file_mapping = __generate_local_file_list(p_date, local_cache_path)
    if os.path.exists(local_cache_path):
        logger.info("本地缓存路径存在，需要删除: {}".format(local_cache_path))
        shutil.rmtree(local_cache_path)
        logger.info("删除本地缓存路径成功: {}".format(local_cache_path))
    os.mkdir(local_cache_path)
    logger.info("创建本地缓存目录成功: {}".format(local_cache_path))
    total_size = 0
    for source_file in file_mapping:
        target_file = file_mapping[source_file]
        try:
            if os.path.exists(source_file):
                dir_name = os.path.dirname(target_file)
                if not os.path.exists(dir_name):
                    os.makedirs(dir_name)
                shutil.copy2(source_file, target_file)
                size = os.path.getsize(target_file) / 1024 / 1024
                total_size += size
                logger.info(
                    "缓存文件成功： source_file={}, target_file={}, size={}MB".format(source_file, target_file,
                                                                               float('%.2f' % size)))
        except:
            logger.error(
                "缓存文件失败： source_file={}, target_file={}".format(source_file, target_file))
    logger.info("完成本地缓存构建, total_size={}GB".format(float('%.2f' % (total_size / 1024))))

    logger.info("开始缓存文件校验, file_count={}".format(len(file_mapping)))
    new_mapping = __check_cache(file_mapping)
    logger.info("完成缓存文件校验, passed_count={}/{}".format(len(new_mapping), len(file_mapping)))
    return new_mapping


def __check_cache(file_mapping):
    new_mapping = {}
    for source_file in file_mapping:
        target_file = file_mapping[source_file]
        source_exist = os.path.exists(source_file)
        target_exist = os.path.exists(target_file)
        if source_exist and target_exist:
            try:
                df = pd.read_pickle(target_file)
                new_mapping.update({
                    source_file: target_file
                })
                logger.info("成功校验缓存文件： target_file={}, record_count={}".format(target_file, len(df)))
            except:
                logger.error("缓存文件校验异常: target_file={}".format(target_file))
        else:
            logger.error("缓存文件异常： source_file={}, source_exist={}, target_file={}, target_exist={}".format(source_file,
                                                                                                           source_exist,
                                                                                                           target_file,
                                                                                                           target_exist))
    return new_mapping


def get_last_3_month(curr_date):
    trading_days = Util.get_trading_day(None, curr_date)
    pre_trading_days = trading_days[:-1]
    trading_month = list(set([day[:6] for day in pre_trading_days]))
    trading_month.sort()
    return trading_month[-3:]


if __name__ == '__main__':
    file_mapping = cache_file_to_local(20210805, '/home/appadmin/temp')
    print(file_mapping)
