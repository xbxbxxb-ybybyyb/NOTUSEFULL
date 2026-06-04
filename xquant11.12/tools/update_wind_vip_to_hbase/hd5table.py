from tables import *
from pandas import DataFrame
import datetime
import time
import os
from xquant.factor import FactorData
import multiprocessing
import traceback
import sys

# BATCH_COUNT = 100
# rootPath = 'D:\\projects\\x-quant\\data\\Xquant'

BATCH_COUNT = 100000
rootPath = '/app/data/010739/'

def decode_string_date8(x):
    """
    b'yyyy-MM-dd' to yyyyMMdd
    b'1899-12-30' to NaN
    :param x:
    :return:
    """
    if x == b'1899-12-30':
        return float('nan')
    else:
        return int(x.decode('utf-8').replace('-',''))


def import_h5_table(factorid, table, fields, tpname):
    total_rows = table.nrows
    task_name = table._v_pathname[:table._v_pathname.index('/', 1)]
    print('[' + task_name + ',' + str(factorid) + '] ' + 'start import, total rows ' + str(total_rows) + '...')
    count = 0
    start_tm = time.time()
    os.environ["factor_id"] = str(factorid)
    fa = FactorData(timeout=60 * 30)

    while count < total_rows:
        symbol_array = table.read(count, count + BATCH_COUNT, field=fields[0])
        symbol_array = [x.decode('utf-8') for x in symbol_array]

        date_array = table.read(count, count + BATCH_COUNT, field=fields[1])
        date_array = [datetime.date.fromtimestamp(x / 1000000000.0).strftime('%Y%m%d') for x in date_array]

        value_array = table.read(count, count + BATCH_COUNT, field=fields[2])
        if tpname == 'float64' or tpname == 'int32' or tpname == 'int64':
            pass
        elif tpname == 'bool':
            value_array = [1 if x else 0 for x in value_array]
        elif tpname == 'string(yyyy-MM-dd)':
            value_array = [decode_string_date8(x) for x in value_array]
            pass
        else:
            print('error: unknown data type: ' + tpname)
            print(value_array)
            return

        df = DataFrame({'symbol':symbol_array, 'time':date_array, 'value':value_array})
        # print(df)

        # df = DataFrame(arr, columns=['index', 'symbol', 'time', 'value'], out=a)
        # print(df)
        fa.putBatch(df)

        count += len(symbol_array)
        print('[' + task_name + '] ' + 'imported ' + str(count) + ' rows(' + str(int(count * 1000 / total_rows) / 10) + '%)...')

    end_tm = time.time()
    print('[' + task_name + ',' + str(factorid) + '] ' + 'import end, cost: ' + str(int((end_tm - start_tm) * 1000) / 1000) + "s")


def import_h5_file2(file, factorid, name, fields, tpname):
    if not os.path.exists(file):
        return

    try:
        with open_file(file, mode='r') as f:
            import_h5_table(factorid, f.get_node('/' + name + '/table'), fields, tpname)
    except:
        print('[' + name + ',' + str(factorid) + '] error: ')
        traceback.print_exc()


tasks = []


def import_h5_file(file, factorid, name, fields, tpname):
    task = [file, factorid, name, fields, tpname]
    tasks.append(task)


def error_callback(e):
    print(e)
    traceback.print_stack()


def run():
    results=[]
    pool = multiprocessing.Pool(processes=10)
    for task in tasks:
        results.append(pool.apply_async(func=import_h5_file2, error_callback=error_callback, args=(task[0], task[1], task[2], task[3], task[4])))
        # results.append(pool.apply(func=import_h5_file2, args=(task[0], task[1], task[2], task[3], task[4])))
    pool.close()
    while True:
        count = 0
        succ = 0
        work = 0
        for result in results:
            if result.ready():
                count += 1
                if result.successful():
                    succ += 1
            else:
                work += 1
        print("progress:", count, succ, work, len(results))
        if count == len(results):
            break
        time.sleep(1)
    pool.join()
    print('over.')


def main():
    # 【基本面数据(日频率)】
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1300, 'apturn', ['Ticker', 'dt', 'apturn'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1301, 'arturn', ['Ticker', 'dt', 'arturn'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1302, 'assetstoequity', ['Ticker', 'dt', 'assetstoequity'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1303, 'assetsturn1', ['Ticker', 'dt', 'assetsturn1'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1304, 'cashflow_ttm2', ['Ticker', 'dt', 'cashflow_ttm2'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1306, 'catoassets', ['Ticker', 'dt', 'catoassets'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1307, 'caturn', ['Ticker', 'dt', 'caturn'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1308, 'current', ['Ticker', 'dt', 'current'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1309, 'currentdebttodebt', ['Ticker', 'dt', 'currentdebttodebt'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1310, 'currentdebttoequity', ['Ticker', 'dt', 'currentdebttoequity'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1311, 'debttoassets', ['Ticker', 'dt', 'debttoassets'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1312, 'dividendyield2', ['Ticker', 'dt', 'dividendyield2'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1313, 'dupont_assetstoequity', ['Ticker', 'dt', 'dupont_assetstoequity'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1314, 'ebit2_ttm', ['Ticker', 'dt', 'ebit2_ttm'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1315, 'ebitda2_ttm', ['Ticker', 'dt', 'ebitda2_ttm'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1316, 'ebitdatosales', ['Ticker', 'dt', 'ebitdatosales'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1317, 'ebittoassets2', ['Ticker', 'dt', 'ebittoassets2'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1318, 'ebttoor_ttm', ['Ticker', 'dt', 'ebttoor_ttm'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1319, 'eps_basic', ['Ticker', 'dt', 'eps_basic'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1320, 'faturn', ['Ticker', 'dt', 'faturn'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1321, 'fcfe', ['Ticker', 'dt', 'fcfe'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1322, 'fcff', ['Ticker', 'dt', 'fcff'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1323, 'fcftocf', ['Ticker', 'dt', 'fcftocf'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1324, 'gc_ttm2', ['Ticker', 'dt', 'gc_ttm2'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1325, 'gctogr_ttm2', ['Ticker', 'dt', 'gctogr_ttm2'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1326, 'gr_ttm2', ['Ticker', 'dt', 'gr_ttm2'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1327, 'grossmargin_ttm2', ['Ticker', 'dt', 'grossmargin_ttm2'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1328, 'grossprofitmargin', ['Ticker', 'dt', 'grossprofitmargin'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1329, 'grossprofitmargin_ttm2', ['Ticker', 'dt', 'grossprofitmargin_ttm2'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1330, 'intdebttototalcap', ['Ticker', 'dt', 'intdebttototalcap'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1331, 'interestexpense_ttm', ['Ticker', 'dt', 'interestexpense_ttm'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1332, 'investcapital', ['Ticker', 'dt', 'investcapital'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1333, 'investincometoebt', ['Ticker', 'dt', 'investincometoebt'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1334, 'invturn', ['Ticker', 'dt', 'invturn'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1335, 'longcapitaltoinvestment', ['Ticker', 'dt', 'longcapitaltoinvestment'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1336, 'longdebttodebt', ['Ticker', 'dt', 'longdebttodebt'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1337, 'longdebttolongcaptial', ['Ticker', 'dt', 'longdebttolongcaptial'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1338, 'maintenance', ['Ticker', 'dt', 'maintenance'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1339, 'ncatoequity', ['Ticker', 'dt', 'ncatoequity'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1340, 'netprofitmargin_ttm2', ['Ticker', 'dt', 'netprofitmargin_ttm2'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1341, 'netprofittoassets', ['Ticker', 'dt', 'netprofittoassets'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1342, 'netprofittoor_ttm', ['Ticker', 'dt', 'netprofittoor_ttm'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1343, 'nonoperateprofittoebt', ['Ticker', 'dt', 'nonoperateprofittoebt'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1344, 'ocftoassets', ['Ticker', 'dt', 'ocftoassets'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1345, 'ocftocf', ['Ticker', 'dt', 'ocftocf'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1346, 'ocftodebt', ['Ticker', 'dt', 'ocftodebt'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1347, 'ocftodividend', ['Ticker', 'dt', 'ocftodividend'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1348, 'ocftointerest', ['Ticker', 'dt', 'ocftointerest'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1349, 'ocftoop', ['Ticker', 'dt', 'ocftoop'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1350, 'ocftoor_ttm2', ['Ticker', 'dt', 'ocftoor_ttm2'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1351, 'ocftosales', ['Ticker', 'dt', 'ocftosales'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1352, 'operatecaptialturn', ['Ticker', 'dt', 'operatecaptialturn'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1353, 'operatecashflow_ttm2', ['Ticker', 'dt', 'operatecashflow_ttm2'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1354, 'operateexpensetogr', ['Ticker', 'dt', 'operateexpensetogr'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1355, 'operateincometoebt', ['Ticker', 'dt', 'operateincometoebt'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1356, 'operateincometoebt_ttm2', ['Ticker', 'dt', 'operateincometoebt_ttm2'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1357, 'optoebt', ['Ticker', 'dt', 'optoebt'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1358, 'optoebt_qfa', ['Ticker', 'dt', 'optoebt_qfa'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1359, 'optogr', ['Ticker', 'dt', 'optogr'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1360, 'optogr_ttm2', ['Ticker', 'dt', 'optogr_ttm2'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1361, 'pb_lf', ['Ticker', 'dt', 'pb_lf'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1362, 'pcf_ocf_ttm', ['Ticker', 'dt', 'pcf_ocf_ttm'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1363, 'pe_ttm', ['Ticker', 'dt', 'pe_ttm'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1364, 'profit_ttm2', ['Ticker', 'dt', 'profit_ttm2'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1365, 'profittogr', ['Ticker', 'dt', 'profittogr'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1366, 'profittogr_ttm2', ['Ticker', 'dt', 'profittogr_ttm2'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1367, 'ps_ttm', ['Ticker', 'dt', 'ps_ttm'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1368, 'qfa_grossmargin', ['Ticker', 'dt', 'qfa_grossmargin'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1369, 'qfa_grossprofitmargin', ['Ticker', 'dt', 'qfa_grossprofitmargin'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1370, 'qfa_netprofitmargin', ['Ticker', 'dt', 'qfa_netprofitmargin'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1371, 'qfa_ocftoor', ['Ticker', 'dt', 'qfa_ocftoor'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1372, 'qfa_ocftosales', ['Ticker', 'dt', 'qfa_ocftosales'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1373, 'qfa_operateincome', ['Ticker', 'dt', 'qfa_operateincome'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1374, 'qfa_operateincometoebt', ['Ticker', 'dt', 'qfa_operateincometoebt'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1375, 'qfa_profittogr', ['Ticker', 'dt', 'qfa_profittogr'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1376, 'qfa_roa', ['Ticker', 'dt', 'qfa_roa'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1377, 'qfa_roe', ['Ticker', 'dt', 'qfa_roe'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1378, 'qfa_yoycf', ['Ticker', 'dt', 'qfa_yoycf'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1379, 'qfa_yoyeps', ['Ticker', 'dt', 'qfa_yoyeps'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1380, 'qfa_yoygr', ['Ticker', 'dt', 'qfa_yoygr'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1381, 'qfa_yoyocf', ['Ticker', 'dt', 'qfa_yoyocf'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1382, 'qfa_yoyop', ['Ticker', 'dt', 'qfa_yoyop'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1383, 'qfa_yoyprofit', ['Ticker', 'dt', 'qfa_yoyprofit'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1384, 'qfa_yoysales', ['Ticker', 'dt', 'qfa_yoysales'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1385, 'quick', ['Ticker', 'dt', 'quick'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1386, 'roa', ['Ticker', 'dt', 'roa'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1387, 'roa2', ['Ticker', 'dt', 'roa2'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1388, 'roa2_ttm2', ['Ticker', 'dt', 'roa2_ttm2'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1389, 'roe_basic', ['Ticker', 'dt', 'roe_basic'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1390, 'roe_ttm2', ['Ticker', 'dt', 'roe_ttm2'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1391, 'roic', ['Ticker', 'dt', 'roic'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1392, 'roic_ttm2', ['Ticker', 'dt', 'roic_ttm2'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1394, 'tot_assets', ['Ticker', 'dt', 'tot_assets'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1395, 'tot_equity', ['Ticker', 'dt', 'tot_equity'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1396, 'tot_liab', ['Ticker', 'dt', 'tot_liab'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1397, 'tot_non_cur_liab', ['Ticker', 'dt', 'tot_non_cur_liab'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1398, 'yoy_assets', ['Ticker', 'dt', 'yoy_assets'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1399, 'yoy_cash', ['Ticker', 'dt', 'yoy_cash'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1400, 'yoy_equity', ['Ticker', 'dt', 'yoy_equity'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1401, 'yoy_fixedassets', ['Ticker', 'dt', 'yoy_fixedassets'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1402, 'yoy_tr', ['Ticker', 'dt', 'yoy_tr'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1403, 'yoycf', ['Ticker', 'dt', 'yoycf'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1404, 'yoydebt', ['Ticker', 'dt', 'yoydebt'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1405, 'yoyeps_basic', ['Ticker', 'dt', 'yoyeps_basic'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1406, 'yoynetprofit', ['Ticker', 'dt', 'yoynetprofit'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1407, 'yoyocf', ['Ticker', 'dt', 'yoyocf'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1408, 'yoyocfps', ['Ticker', 'dt', 'yoyocfps'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1409, 'yoyop', ['Ticker', 'dt', 'yoyop'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1410, 'yoyprofit', ['Ticker', 'dt', 'yoyprofit'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_DAILY_WIND.h5', 1411, 'yoyroe', ['Ticker', 'dt', 'yoyroe'], 'float64')


    # 【基本面数据(季度频率)】
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014300, 'apturn', ['Ticker', 'dt', 'apturn'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014301, 'arturn', ['Ticker', 'dt', 'arturn'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014302, 'assetstoequity',
                   ['Ticker', 'dt', 'assetstoequity'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014303, 'assetsturn1',
                   ['Ticker', 'dt', 'assetsturn1'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014304, 'cashflow_ttm2',
                   ['Ticker', 'dt', 'cashflow_ttm2'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014305, 'cashtostdebt',
                   ['Ticker', 'dt', 'cashtostdebt'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014306, 'catoassets',
                   ['Ticker', 'dt', 'catoassets'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014307, 'caturn', ['Ticker', 'dt', 'caturn'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014308, 'current', ['Ticker', 'dt', 'current'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014309, 'currentdebttodebt',
                   ['Ticker', 'dt', 'currentdebttodebt'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014310, 'currentdebttoequity',
                   ['Ticker', 'dt', 'currentdebttoequity'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014311, 'debttoassets',
                   ['Ticker', 'dt', 'debttoassets'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014313, 'dupont_assetstoequity',
                   ['Ticker', 'dt', 'dupont_assetstoequity'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014314, 'ebit2_ttm', ['Ticker', 'dt', 'ebit2_ttm'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014315, 'ebitda2_ttm',
                   ['Ticker', 'dt', 'ebitda2_ttm'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014316, 'ebitdatosales',
                   ['Ticker', 'dt', 'ebitdatosales'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014317, 'ebittoassets2',
                   ['Ticker', 'dt', 'ebittoassets2'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014318, 'ebttoor_ttm',
                   ['Ticker', 'dt', 'ebttoor_ttm'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014319, 'eps_basic', ['Ticker', 'dt', 'eps_basic'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014320, 'faturn', ['Ticker', 'dt', 'faturn'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014321, 'fcfe', ['Ticker', 'dt', 'fcfe'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014322, 'fcff', ['Ticker', 'dt', 'fcff'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014323, 'fcftocf', ['Ticker', 'dt', 'fcftocf'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014324, 'gc_ttm2', ['Ticker', 'dt', 'gc_ttm2'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014325, 'gctogr_ttm2',
                   ['Ticker', 'dt', 'gctogr_ttm2'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014326, 'gr_ttm2', ['Ticker', 'dt', 'gr_ttm2'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014327, 'grossmargin_ttm2',
                   ['Ticker', 'dt', 'grossmargin_ttm2'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014328, 'grossprofitmargin',
                   ['Ticker', 'dt', 'grossprofitmargin'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014329, 'grossprofitmargin_ttm2',
                   ['Ticker', 'dt', 'grossprofitmargin_ttm2'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014330, 'intdebttototalcap',
                   ['Ticker', 'dt', 'intdebttototalcap'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014331, 'interestexpense_ttm',
                   ['Ticker', 'dt', 'interestexpense_ttm'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014332, 'investcapital',
                   ['Ticker', 'dt', 'investcapital'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014333, 'investincometoebt',
                   ['Ticker', 'dt', 'investincometoebt'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014334, 'invturn', ['Ticker', 'dt', 'invturn'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014335, 'longcapitaltoinvestment',
                   ['Ticker', 'dt', 'longcapitaltoinvestment'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014336, 'longdebttodebt',
                   ['Ticker', 'dt', 'longdebttodebt'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014337, 'longdebttolongcaptial',
                   ['Ticker', 'dt', 'longdebttolongcaptial'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014338, 'maintenance',
                   ['Ticker', 'dt', 'maintenance'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014339, 'ncatoequity',
                   ['Ticker', 'dt', 'ncatoequity'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014340, 'netprofitmargin_ttm2',
                   ['Ticker', 'dt', 'netprofitmargin_ttm2'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014341, 'netprofittoassets',
                   ['Ticker', 'dt', 'netprofittoassets'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014342, 'netprofittoor_ttm',
                   ['Ticker', 'dt', 'netprofittoor_ttm'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014343, 'nonoperateprofittoebt',
                   ['Ticker', 'dt', 'nonoperateprofittoebt'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014344, 'ocftoassets',
                   ['Ticker', 'dt', 'ocftoassets'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014345, 'ocftocf', ['Ticker', 'dt', 'ocftocf'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014346, 'ocftodebt', ['Ticker', 'dt', 'ocftodebt'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014347, 'ocftodividend',
                   ['Ticker', 'dt', 'ocftodividend'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014348, 'ocftointerest',
                   ['Ticker', 'dt', 'ocftointerest'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014349, 'ocftoop', ['Ticker', 'dt', 'ocftoop'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014350, 'ocftoor_ttm2',
                   ['Ticker', 'dt', 'ocftoor_ttm2'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014351, 'ocftosales',
                   ['Ticker', 'dt', 'ocftosales'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014352, 'operatecaptialturn',
                   ['Ticker', 'dt', 'operatecaptialturn'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014353, 'operatecashflow_ttm2',
                   ['Ticker', 'dt', 'operatecashflow_ttm2'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014354, 'operateexpensetogr',
                   ['Ticker', 'dt', 'operateexpensetogr'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014355, 'operateincometoebt',
                   ['Ticker', 'dt', 'operateincometoebt'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014356, 'operateincometoebt_ttm2',
                   ['Ticker', 'dt', 'operateincometoebt_ttm2'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014357, 'optoebt', ['Ticker', 'dt', 'optoebt'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014358, 'optoebt_qfa',
                   ['Ticker', 'dt', 'optoebt_qfa'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014359, 'optogr', ['Ticker', 'dt', 'optogr'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014360, 'optogr_ttm2',
                   ['Ticker', 'dt', 'optogr_ttm2'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014364, 'profit_ttm2',
                   ['Ticker', 'dt', 'profit_ttm2'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014365, 'profittogr',
                   ['Ticker', 'dt', 'profittogr'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014366, 'profittogr_ttm2',
                   ['Ticker', 'dt', 'profittogr_ttm2'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014368, 'qfa_grossmargin',
                   ['Ticker', 'dt', 'qfa_grossmargin'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014369, 'qfa_grossprofitmargin',
                   ['Ticker', 'dt', 'qfa_grossprofitmargin'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014370, 'qfa_netprofitmargin',
                   ['Ticker', 'dt', 'qfa_netprofitmargin'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014371, 'qfa_ocftoor',
                   ['Ticker', 'dt', 'qfa_ocftoor'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014372, 'qfa_ocftosales',
                   ['Ticker', 'dt', 'qfa_ocftosales'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014373, 'qfa_operateincome',
                   ['Ticker', 'dt', 'qfa_operateincome'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014374, 'qfa_operateincometoebt',
                   ['Ticker', 'dt', 'qfa_operateincometoebt'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014375, 'qfa_profittogr',
                   ['Ticker', 'dt', 'qfa_profittogr'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014376, 'qfa_roa', ['Ticker', 'dt', 'qfa_roa'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014377, 'qfa_roe', ['Ticker', 'dt', 'qfa_roe'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014378, 'qfa_yoycf', ['Ticker', 'dt', 'qfa_yoycf'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014379, 'qfa_yoyeps',
                   ['Ticker', 'dt', 'qfa_yoyeps'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014380, 'qfa_yoygr', ['Ticker', 'dt', 'qfa_yoygr'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014381, 'qfa_yoyocf',
                   ['Ticker', 'dt', 'qfa_yoyocf'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014382, 'qfa_yoyop', ['Ticker', 'dt', 'qfa_yoyop'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014383, 'qfa_yoyprofit',
                   ['Ticker', 'dt', 'qfa_yoyprofit'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014384, 'qfa_yoysales',
                   ['Ticker', 'dt', 'qfa_yoysales'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014385, 'quick', ['Ticker', 'dt', 'quick'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014386, 'roa', ['Ticker', 'dt', 'roa'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014387, 'roa2', ['Ticker', 'dt', 'roa2'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014388, 'roa2_ttm2', ['Ticker', 'dt', 'roa2_ttm2'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014389, 'roe_basic', ['Ticker', 'dt', 'roe_basic'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014390, 'roe_ttm2', ['Ticker', 'dt', 'roe_ttm2'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014391, 'roic', ['Ticker', 'dt', 'roic'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014392, 'roic_ttm2', ['Ticker', 'dt', 'roic_ttm2'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014393, 'stm_issuingdate',
                   ['Ticker', 'dt', 'stm_issuingdate'], 'string(yyyy-MM-dd)')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014394, 'tot_assets',
                   ['Ticker', 'dt', 'tot_assets'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014395, 'tot_equity',
                   ['Ticker', 'dt', 'tot_equity'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014396, 'tot_liab', ['Ticker', 'dt', 'tot_liab'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014397, 'tot_non_cur_liab', ['Ticker', 'dt', 'tot_non_cur_liab'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014398, 'yoy_assets',
                   ['Ticker', 'dt', 'yoy_assets'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014399, 'yoy_cash', ['Ticker', 'dt', 'yoy_cash'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014400, 'yoy_equity',
                   ['Ticker', 'dt', 'yoy_equity'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014401, 'yoy_fixedassets',
                   ['Ticker', 'dt', 'yoy_fixedassets'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014402, 'yoy_tr', ['Ticker', 'dt', 'yoy_tr'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014403, 'yoycf', ['Ticker', 'dt', 'yoycf'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014404, 'yoydebt', ['Ticker', 'dt', 'yoydebt'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014405, 'yoyeps_basic',
                   ['Ticker', 'dt', 'yoyeps_basic'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014406, 'yoynetprofit',
                   ['Ticker', 'dt', 'yoynetprofit'], 'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014407, 'yoyocf', ['Ticker', 'dt', 'yoyocf'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014408, 'yoyocfps', ['Ticker', 'dt', 'yoyocfps'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014409, 'yoyop', ['Ticker', 'dt', 'yoyop'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014410, 'yoyprofit', ['Ticker', 'dt', 'yoyprofit'],
                   'float64')
    import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', 1014411, 'yoyroe', ['Ticker', 'dt', 'yoyroe'],
                   'float64')

    # error: invalid stmnote_audit_category type: string
    # import_h5_file(rootPath + '/FDD_CHINA_STOCK_QUARTERLY_WIND.h5', ?, 'stmnote_audit_category', ['Ticker', 'dt', 'stmnote_audit_category'], 'string')


    # 【BARRA风格因子】
    import_h5_file(rootPath + '/risk_CHINA_STOCK_DAILY_STYLEFACTOR.h5', 1150, 'Beta', ['Ticker', 'dt', 'Beta'], 'float64')
    import_h5_file(rootPath + '/risk_CHINA_STOCK_DAILY_STYLEFACTOR.h5', 1151, 'EarningsYield', ['Ticker', 'dt', 'EarningsYield'], 'float64')
    import_h5_file(rootPath + '/risk_CHINA_STOCK_DAILY_STYLEFACTOR.h5', 1152, 'Growth', ['Ticker', 'dt', 'Growth'], 'float64')
    import_h5_file(rootPath + '/risk_CHINA_STOCK_DAILY_STYLEFACTOR.h5', 1153, 'Industry', ['Ticker', 'dt', 'Industry'], 'int64')
    import_h5_file(rootPath + '/risk_CHINA_STOCK_DAILY_STYLEFACTOR.h5', 1154, 'Leverage', ['Ticker', 'dt', 'Leverage'], 'float64')
    import_h5_file(rootPath + '/risk_CHINA_STOCK_DAILY_STYLEFACTOR.h5', 1155, 'Liquidity', ['Ticker', 'dt', 'Liquidity'], 'float64')
    import_h5_file(rootPath + '/risk_CHINA_STOCK_DAILY_STYLEFACTOR.h5', 1156, 'Momentum', ['Ticker', 'dt', 'Momentum'], 'float64')
    import_h5_file(rootPath + '/risk_CHINA_STOCK_DAILY_STYLEFACTOR.h5', 1157, 'NonLinearSize', ['Ticker', 'dt', 'NonLinearSize'], 'float64')
    import_h5_file(rootPath + '/risk_CHINA_STOCK_DAILY_STYLEFACTOR.h5', 1158, 'ResidualVolatility', ['Ticker', 'dt', 'ResidualVolatility'], 'float64')
    import_h5_file(rootPath + '/risk_CHINA_STOCK_DAILY_STYLEFACTOR.h5', 1159, 'Size', ['Ticker', 'dt', 'Size'], 'float64')
    import_h5_file(rootPath + '/risk_CHINA_STOCK_DAILY_STYLEFACTOR.h5', 1160, 'Value', ['Ticker', 'dt', 'Value'], 'float64')


    # 【风险池与alpha池-Risk Universe & Alpha Universe】
    # import_h5_file(rootPath + '/UNIV_CHINA_STOCK_DAILY_OPTM.h5', 1110, 'stock_universe', ['Ticker', 'dt', 'risk_universe'], 'bool')
    # import_h5_file(rootPath + '/UNIV_CHINA_STOCK_DAILY_OPTM.h5', 1111, 'stock_universe', ['Ticker', 'dt', 'alpha_universe'], 'bool')
    # import_h5_file(rootPath + '/UNIV_CHINA_STOCK_DAILY_OPTM.h5', 1112, 'stock_universe', ['Ticker', 'dt', 'index_50'], 'bool')
    # import_h5_file(rootPath + '/UNIV_CHINA_STOCK_DAILY_OPTM.h5', 1113, 'stock_universe', ['Ticker', 'dt', 'index_300'], 'bool')
    # import_h5_file(rootPath + '/UNIV_CHINA_STOCK_DAILY_OPTM.h5', 1114, 'stock_universe', ['Ticker', 'dt', 'index_500'], 'bool')
    # import_h5_file(rootPath + '/UNIV_CHINA_STOCK_DAILY_OPTM.h5', 1115, 'stock_universe', ['Ticker', 'dt', 'index_weight_sh50'], 'float64')
    # import_h5_file(rootPath + '/UNIV_CHINA_STOCK_DAILY_OPTM.h5', 1116, 'stock_universe', ['Ticker', 'dt', 'index_weight_hs300'], 'float64')
    # import_h5_file(rootPath + '/UNIV_CHINA_STOCK_DAILY_OPTM.h5', 1117, 'stock_universe', ['Ticker', 'dt', 'index_weight_zz500'], 'float64')
    # import_h5_file(rootPath + '/UNIV_CHINA_STOCK_DAILY_OPTM.h5', 1118, 'stock_universe', ['Ticker', 'dt', 'filter_opendownlimit'], 'bool')
    # import_h5_file(rootPath + '/UNIV_CHINA_STOCK_DAILY_OPTM.h5', 1119, 'stock_universe', ['Ticker', 'dt', 'filter_openuplimit'], 'bool')
    # import_h5_file(rootPath + '/UNIV_CHINA_STOCK_DAILY_OPTM.h5', 1120, 'stock_universe', ['Ticker', 'dt', 'filter_sso'], 'bool')
    # import_h5_file(rootPath + '/UNIV_CHINA_STOCK_DAILY_OPTM.h5', 1121, 'stock_universe', ['Ticker', 'dt', 'filter_stpt'], 'bool')
    # import_h5_file(rootPath + '/UNIV_CHINA_STOCK_DAILY_OPTM.h5', 1122, 'stock_universe', ['Ticker', 'dt', 'filter_suspend'], 'bool')
    # import_h5_file(rootPath + '/UNIV_CHINA_STOCK_DAILY_OPTM.h5', 1123, 'stock_universe', ['Ticker', 'dt', 'Listing_date'], 'int32')
    # import_h5_file(rootPath + '/UNIV_CHINA_STOCK_DAILY_OPTM.h5', 1124, 'stock_universe', ['Ticker', 'dt', 'listing_1yr'], 'bool')
    # import_h5_file(rootPath + '/UNIV_CHINA_STOCK_DAILY_OPTM.h5', 1125, 'stock_universe', ['Ticker', 'dt', 'listing_3yr'], 'bool')
    # import_h5_file(rootPath + '/UNIV_CHINA_STOCK_DAILY_OPTM.h5', 1126, 'stock_universe', ['Ticker', 'dt', 'over_half_for_half_year'], 'bool')


    # 【风险池与alpha池-Risk Universe & Alpha Universe】
    import_h5_file(rootPath + '/UNIV_CHINA_STOCK_DAILY_OPTM.h5', 1110, 'risk_universe', ['Ticker', 'dt', 'risk_universe'], 'bool')
    import_h5_file(rootPath + '/UNIV_CHINA_STOCK_DAILY_OPTM.h5', 1111, 'alpha_universe', ['Ticker', 'dt', 'alpha_universe'], 'bool')
    import_h5_file(rootPath + '/UNIV_CHINA_STOCK_DAILY_OPTM.h5', 1112, 'index_50', ['Ticker', 'dt', 'index_50'], 'bool')
    import_h5_file(rootPath + '/UNIV_CHINA_STOCK_DAILY_OPTM.h5', 1113, 'index_300', ['Ticker', 'dt', 'index_300'], 'bool')
    import_h5_file(rootPath + '/UNIV_CHINA_STOCK_DAILY_OPTM.h5', 1114, 'index_500', ['Ticker', 'dt', 'index_500'], 'bool')
    import_h5_file(rootPath + '/UNIV_CHINA_STOCK_DAILY_OPTM.h5', 1115, 'index_weight_sh50', ['Ticker', 'dt', 'index_weight_sh50'], 'float64')
    import_h5_file(rootPath + '/UNIV_CHINA_STOCK_DAILY_OPTM.h5', 1116, 'index_weight_hs300', ['Ticker', 'dt', 'index_weight_hs300'], 'float64')
    import_h5_file(rootPath + '/UNIV_CHINA_STOCK_DAILY_OPTM.h5', 1117, 'index_weight_zz500', ['Ticker', 'dt', 'index_weight_zz500'], 'float64')
    import_h5_file(rootPath + '/UNIV_CHINA_STOCK_DAILY_OPTM.h5', 1118, 'filter_opendownlimit', ['Ticker', 'dt', 'filter_opendownlimit'], 'bool')
    import_h5_file(rootPath + '/UNIV_CHINA_STOCK_DAILY_OPTM.h5', 1119, 'filter_openuplimit', ['Ticker', 'dt', 'filter_openuplimit'], 'bool')
    import_h5_file(rootPath + '/UNIV_CHINA_STOCK_DAILY_OPTM.h5', 1120, 'filter_sso', ['Ticker', 'dt', 'filter_sso'], 'bool')
    import_h5_file(rootPath + '/UNIV_CHINA_STOCK_DAILY_OPTM.h5', 1121, 'filter_stpt', ['Ticker', 'dt', 'filter_stpt'], 'bool')
    import_h5_file(rootPath + '/UNIV_CHINA_STOCK_DAILY_OPTM.h5', 1122, 'filter_suspend', ['Ticker', 'dt', 'filter_suspend'], 'bool')
    import_h5_file(rootPath + '/UNIV_CHINA_STOCK_DAILY_OPTM.h5', 1123, 'Listing_date', ['Ticker', 'dt', 'Listing_date'], 'int32')
    import_h5_file(rootPath + '/UNIV_CHINA_STOCK_DAILY_OPTM.h5', 1124, 'listing_1yr', ['Ticker', 'dt', 'listing_1yr'], 'bool')
    import_h5_file(rootPath + '/UNIV_CHINA_STOCK_DAILY_OPTM.h5', 1125, 'listing_3yr', ['Ticker', 'dt', 'listing_3yr'], 'bool')
    import_h5_file(rootPath + '/UNIV_CHINA_STOCK_DAILY_OPTM.h5', 1126, 'over_half_for_half_year', ['Ticker', 'dt', 'over_half_for_half_year'], 'bool')


    # 【Universe_complete 包含开盘涨跌停，停盘，STPT，指数成分等数据】
    import_h5_file(rootPath + '/universe_complete.h5', 1101, 'HS300', ['Ticker', 'dt', 'HS300'], 'float64')
    import_h5_file(rootPath + '/universe_complete.h5', 1102, 'Listing_date', ['Ticker', 'dt', 'Listing_date'], 'float64')
    import_h5_file(rootPath + '/universe_complete.h5', 1103, 'OPENDOWNLIMIT', ['Ticker', 'dt', 'OPENDOWNLIMIT'], 'float64')
    import_h5_file(rootPath + '/universe_complete.h5', 1104, 'OPENUPLIMIT', ['Ticker', 'dt', 'OPENUPLIMIT'], 'float64')
    import_h5_file(rootPath + '/universe_complete.h5', 1105, 'SH50', ['Ticker', 'dt', 'SH50'], 'float64')
    import_h5_file(rootPath + '/universe_complete.h5', 1106, 'SSO', ['Ticker', 'dt', 'SSO'], 'float64')
    import_h5_file(rootPath + '/universe_complete.h5', 1107, 'STPT', ['Ticker', 'dt', 'STPT'], 'float64')
    import_h5_file(rootPath + '/universe_complete.h5', 1108, 'SUSPEND', ['Ticker', 'dt', 'SUSPEND'], 'float64')
    import_h5_file(rootPath + '/universe_complete.h5', 1109, 'ZZ500', ['Ticker', 'dt', 'ZZ500'], 'float64')


    # 【量价(Market Data)】
    import_h5_file(rootPath + '/MD_CHINA_STOCK_DAILY_WIND.h5', 8, 'adjfactor', ['Ticker', 'dt', 'adjfactor'], 'float64')
    import_h5_file(rootPath + '/MD_CHINA_STOCK_DAILY_WIND.h5', 7, 'amt', ['Ticker', 'dt', 'amt'], 'float64')
    import_h5_file(rootPath + '/MD_CHINA_STOCK_DAILY_WIND.h5', 5, 'close', ['Ticker', 'dt', 'close'], 'float64')
    import_h5_file(rootPath + '/MD_CHINA_STOCK_DAILY_WIND.h5', 9, 'free_float_shares', ['Ticker', 'dt', 'free_float_shares'], 'float64')
    import_h5_file(rootPath + '/MD_CHINA_STOCK_DAILY_WIND.h5', 3, 'high', ['Ticker', 'dt', 'high'], 'float64')
    import_h5_file(rootPath + '/MD_CHINA_STOCK_DAILY_WIND.h5', 4, 'low', ['Ticker', 'dt', 'low'], 'float64')
    import_h5_file(rootPath + '/MD_CHINA_STOCK_DAILY_WIND.h5', 10, 'mkt_cap_ard', ['Ticker', 'dt', 'mkt_cap_ard'], 'float64')
    import_h5_file(rootPath + '/MD_CHINA_STOCK_DAILY_WIND.h5', 2, 'open', ['Ticker', 'dt', 'open'], 'float64')
    import_h5_file(rootPath + '/MD_CHINA_STOCK_DAILY_WIND.h5', 11, 'pct_chg', ['Ticker', 'dt', 'pct_chg'], 'float64')
    import_h5_file(rootPath + '/MD_CHINA_STOCK_DAILY_WIND.h5', 1, 'pre_close', ['Ticker', 'dt', 'pre_close'], 'float64')
    import_h5_file(rootPath + '/MD_CHINA_STOCK_DAILY_WIND.h5', 12, 'total_shares', ['Ticker', 'dt', 'total_shares'], 'float64')
    import_h5_file(rootPath + '/MD_CHINA_STOCK_DAILY_WIND.h5', 13, 'turn', ['Ticker', 'dt', 'turn'], 'float64')
    import_h5_file(rootPath + '/MD_CHINA_STOCK_DAILY_WIND.h5', 6, 'volume', ['Ticker', 'dt', 'volume'], 'float64')
    import_h5_file(rootPath + '/MD_CHINA_STOCK_DAILY_WIND.h5', 14, 'vwap', ['Ticker', 'dt', 'vwap'], 'float64')


    # 【股指基准-Benchmark】
    import_h5_file(rootPath + '/MD_CHINA_INDEX_DAILY_WIND.h5', 5, 'close', ['Ticker', 'dt', 'close'], 'float64')
    import_h5_file(rootPath + '/MD_CHINA_INDEX_DAILY_WIND.h5', 1, 'pre_close', ['Ticker', 'dt', 'pre_close'], 'float64')


    # 【行业数据(中信一级)-Industry】
    import_h5_file(rootPath + '/INDUSTRY_CHINA_STOCK_DAILY_WIND.h5', 2001, 'industry3', ['Ticker', 'dt', 'industry3'], 'int64')


    # import_h5_file(rootPath + '/tot_non_cur_liab_daily.h5', 1397, 'tot_non_cur_liab', ['Ticker', 'dt', 'tot_non_cur_liab'], 'float64')
    # import_h5_file(rootPath + '/tot_non_cur_liab_qtr.h5', 1014397, 'tot_non_cur_liab', ['Ticker', 'dt', 'tot_non_cur_liab'], 'float64')

    run()

if __name__ == '__main__':
    rootPath += sys.argv[1]
    print(rootPath)
    main()

