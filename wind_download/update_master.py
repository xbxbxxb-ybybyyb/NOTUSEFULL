from multifactor.data.utils import *
from update_wind import update_wind
from updater_universe import updater_universe
from update_wind_htsc import first_job
from update_barra_risk import update_barra_risk
import settings
import os
import utils
from loguru import logger
from multiprocessing import Process


multiprocss_flag = True
# run_mode : run     并行运行  生产状态
# run_mode : debug   串行运行  调试状态

logger.add(os.path.join(settings.RUN_LOG_DIR, "wind_downloader-{time}.log"), enqueue=True)

# 返回交易日的，缺省值nan，返回当天
sdate, edate, _ = check_update_date()
# sdate, edate =20201217,20201217
logger.info("开始日期：{}, 结束日期：{}".format(sdate, edate))


def __first_job():
    utils.create_flag(str(edate) + '_' + 'RDF.start', edate)
    first_job(sdate, edate)  # 云上原表 to rdf_csv to rdf_h5
    utils.create_flag(str(edate) + '_' + 'RDF.success', edate)


def __wind_job():
    # 价量数据和提取出来的财务数据
    utils.create_flag(str(edate) + '_' + 'MD.start', edate)
    update_wind(sdate, edate)  # rdf_h5 to FDD_csv MD_csv to FDD_h5 MD_h5
    utils.create_flag(str(edate) + '_' + 'MD.success', edate)

    utils.create_flag(str(edate) + '_' + 'UNIV.start', edate)
    updater_universe(sdate, edate)  # rdf_h5 to universe to universe_csv to universe_h5
    utils.create_flag(str(edate) + '_' + 'UNIV.success', edate)

    utils.create_flag(str(edate) + '_' + 'RISK.start', edate)
    update_barra_risk(sdate, edate)
    utils.create_flag(str(edate) + '_' + 'RISK.success', edate)

if multiprocss_flag==True:

    p0 = Process(target=__first_job, args=())
    p0.start()
    p0.join()

    p1 = Process(target=__wind_job, args=())
    p1.start()
    p1.join()
else:
    __first_job()
    __wind_job()