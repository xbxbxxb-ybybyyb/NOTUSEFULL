import pandas as pd
import os
from pandas.testing import assert_frame_equal
from loguru import logger

logger.add("/data/user/013565/log/CompareH5Data-{time}.log")

h5_datas = os.listdir('/data/group/800120/basic_data/full/financial_data/DATABASE/WIND')
try:
    for single_data in h5_datas:
        logger.info("compare talbe:{}".format(single_data))
        data1 = pd.read_hdf("/data/group/800120/basic_data/full/financial_data/DATABASE/WIND/{}/{}.h5".format(single_data,single_data))
        data2 = pd.read_hdf("/data/group/800080/warehouse/prod/DATABASE/WIND/{}/{}.h5".format(single_data,single_data))
        try:
            assert_frame_equal(data1,data2,check_dtype=False)
            logger.info("wind_data={},Matched!".format(single_data))

        except Exception as e:
            logger.error("wind_data={},MisMatched,error={}".format(single_data,e))

except Exception as e:

    logger.error(e)