import traceback
from loguru import logger
from xfactor.test.test_data_loader import *
from xfactor.test.algorithm_team.factor_test_algorithm import FactorTestAlgorithm
from xfactor.test.symbol_team.FactorTest.SingleIntraFactorTest import SingleFactorTest as FixFactorTestSymbol
import numpy as np
import shutil

try:
    from xfactor.test.symbol_team.FactorTest.SingleIntraFactorTestOOS import SingleFactorTest as FixFactorTestSymbolOOS
except:
    pass
try:
    from xfactor.test.algorithm_team.factor_test_algorithm_oos import FactorTestAlgorithm as FactorTestAlgorithmOOS
except:
    pass

default_check_date_list = [20160630, 20161231, 20170630, 20171231, 20180630, 20181231, 20190630]
default_fix_time_intervals = ['1000', '1030', '1100', '1300', '1330', '1400', '1430']


def factor_test_algorithm(factor_name, factor_value, start_date, end_date, local, pdf_address):
    factor_value, start_date, end_date = adapt_for_algorithm(factor_value, start_date, end_date)
    if local:
        factor_test_class = FactorTestAlgorithm(factor_name, factor_value, start_date, end_date, pdf_address)
    else:
        factor_test_class = FactorTestAlgorithmOOS(factor_name, factor_value, start_date, end_date)

    test_result = factor_test_class.launch_test()

    print("factor_test_algorithm: ", factor_name, " finished")
    return test_result


def factor_test_symbol_forfix(start_date, end_date, factor_name, factor_result, execute_cpu_num=1, local=True):
    print("factor_test_symbol: ", factor_name)
    if local:
        factor_test_class = FixFactorTestSymbol(factor_name, factor_result, start_date, end_date, execute_cpu_num)
    else:
        factor_test_class = FixFactorTestSymbolOOS(factor_name, factor_result, start_date, end_date, execute_cpu_num)
    test_result = factor_test_class.launch_test()
    print("factor_test_symbol: ", factor_name, " finished")
    return test_result


def day_factor_test(start_date, end_date, factor_result, local=True, report=None):
    factor_name, factor_value = factor_result.popitem()
    factor_result[factor_name] = factor_value
    print("Start Factor Test:", factor_name)
    t1 = dt.datetime.now()
    try:
        test_results = []
        test_results.append(
            factor_test_algorithm(factor_name, factor_value, start_date, end_date, local, pdf_address=report))
        ret = test_results[0][0]
        logger.info("raw_test_result: {}".format(ret))

        if ret and local == False:
            adjrecord(test_results[0][1])
            save_data(test_results[0][1])
        t2 = dt.datetime.now()
        print("Finish Factor Test:", factor_name, "costs", t2 - t1)
        return ret
    except Exception:
        traceback.print_exc()
        return False


def save_data(inlib_details, isfix=False):
    if isfix == True:
        pass
    else:
        factorname = list(inlib_details.keys())[0]
        inlib_details_singlefactor = inlib_details[factorname]
        old_ic = pd.read_pickle(factors_spe_IC_path)
        toconcat = inlib_details_singlefactor['res_ic'].reindex(old_ic.index)
        new_ic = old_ic.copy()
        new_ic.loc[:, factorname] = np.nan
        new_ic.loc[:, factorname] = toconcat
        new_ic.to_pickle(factors_spe_IC_path)
        old_ic.to_pickle(factors_spe_IC_path.replace('.pkl', '_bk.pkl'))
    pass


def adjrecord(inlib_details, isfix=False):
    if isfix == True:
        factors_inlib_dict = pd.read_pickle(fix_inlib_factors_path)
        for singlefactor in inlib_details:
            inlib_details_singlefactor = inlib_details[singlefactor]
            corrfactorspk_singlefactor = inlib_details_singlefactor['corrfactorspk_result']
            factors_out_singlefactor = inlib_details_singlefactor['factors_out']
            for thetime in default_fix_time_intervals:
                singlefactor_thetime = 'Fix{}_{}'.format(thetime, singlefactor)
                factors_inlib_dict[thetime] = factors_inlib_dict[thetime][
                    ~factors_inlib_dict[thetime].index.duplicated()]
                if corrfactorspk_singlefactor == 0:
                    toconcat = pd.DataFrame({
                        'isInLib': [1],
                        'LoseinBattleamongtheCorr': [0],
                        'beatby': [None]
                    }, index=[singlefactor_thetime])
                    if singlefactor_thetime in factors_inlib_dict[thetime].index:
                        factors_inlib_dict[thetime] = factors_inlib_dict[thetime].drop(singlefactor_thetime)
                    factors_inlib_dict[thetime] = pd.concat([factors_inlib_dict[thetime], toconcat], axis=0)
                elif corrfactorspk_singlefactor == 1:
                    for singlefactortodelete in factors_out_singlefactor:
                        singlefactortodelete_thetime = 'Fix{}_{}'.format(thetime, singlefactortodelete)
                        if singlefactortodelete_thetime in factors_inlib_dict[thetime].index:
                            factors_inlib_dict[thetime] = factors_inlib_dict[thetime].drop(singlefactortodelete_thetime)
                        factors_inlib_dict[thetime].loc[singlefactortodelete_thetime, :] = pd.Series({
                            'isInLib': 0,
                            'LoseinBattleamongtheCorr': 1,
                            'beatby': singlefactor_thetime
                        })
                    toconcat = pd.DataFrame({
                        'isInLib': [1],
                        'LoseinBattleamongtheCorr': [0],
                        'beatby': [None]
                    }, index=[singlefactor_thetime])
                    if singlefactor_thetime in factors_inlib_dict[thetime].index:
                        factors_inlib_dict[thetime] = factors_inlib_dict[thetime].drop(singlefactor_thetime)
                    factors_inlib_dict[thetime] = pd.concat([factors_inlib_dict[thetime], toconcat], axis=0)
        if os.path.exists(fix_inlib_factors_path):
            shutil.copyfile(fix_inlib_factors_path, fix_inlib_factors_path_bk)
        with open(fix_inlib_factors_path, 'wb') as f:
            pickle.dump(factors_inlib_dict, f)
            f.close()
    else:
        # 修改入库文件
        factorname = list(inlib_details.keys())[0]
        inlib_details_singlefactor = inlib_details[factorname]
        factors_inlib = pd.read_pickle(day_inlib_factors_path)
        ltr = inlib_details_singlefactor['ltr_flag']
        nltr = inlib_details_singlefactor['ntr_flag']
        factors_inlib = factors_inlib[~factors_inlib.index.duplicated()]
        if (ltr == True) & (nltr == True):
            toconcat = pd.DataFrame({
                'isInLib': [1],
                'InLibReason': 'both',
            }, index=[factorname])
        elif (ltr == True) & (nltr == False):
            toconcat = pd.DataFrame({
                'isInLib': [1],
                'InLibReason': 'linear',
            }, index=[factorname])
        elif (ltr == False) & (nltr == True):
            toconcat = pd.DataFrame({
                'isInLib': [1],
                'InLibReason': 'nonlinear',
            }, index=[factorname])

        factors_inlib = pd.concat([factors_inlib, toconcat], axis=0)
        if os.path.exists(day_inlib_factors_path):
            shutil.copyfile(day_inlib_factors_path, day_inlib_factors_path_bk)
        with open(day_inlib_factors_path, 'wb') as f:
            pickle.dump(factors_inlib, f)
            f.close()
        pass

    pass


def fix_factor_test(start_date, end_date, factor_result, local, calc_num=8):
    print("Start Fix Factor Test:")
    t1 = dt.datetime.now()
    try:
        factor_name = list(factor_result.keys())[0].replace(list(factor_result.keys())[0].split('_')[0] + '_', '')
        test_results = []
        test_results.append(
            factor_test_symbol_forfix(start_date, end_date, factor_name, factor_result, calc_num, local))
        logger.info("raw_test_result: {}".format(test_results))
        passed_count = 0
        inlib_details = {}
        for test_result in test_results:
            factor = test_result["factor"]
            ret = process_test_result(factor, None, test_result)
            passed_count = passed_count + 1 if ret else passed_count
            if ret and local == False:
                inlib_details.update({factor: test_result['inlib']})
        pass_result_of_logic = passed_count >= 1
        if pass_result_of_logic and local == False:
            adjrecord(inlib_details, True)
        t2 = dt.datetime.now()
        print("Finish Fix Factor Test: costs ", t2 - t1)
        if pass_result_of_logic:
            return pass_result_of_logic, {'1000': True, '1030': True, '1100': True, '1300': True, '1330': True,
                                          '1400': True, '1430': True}
        else:
            return pass_result_of_logic, {'1000': False, '1030': False, '1100': False, '1300': False, '1330': False,
                                          '1400': False, '1430': False}
    except Exception:
        traceback.print_exc()
        return False


def process_test_result(factor_name, algorithm_result, symbol_result):
    flag_algorithm, detail, reason_algorithm = True, None, None
    flag_symbol, reason_symbol = True, None

    if algorithm_result is not None:
        flag_algorithm = algorithm_result["flag"]
        detail = algorithm_result["stat_result"]
        reason_algorithm = algorithm_result["reason"]

    if symbol_result is not None:
        flag_symbol = symbol_result["flag"]
        reason_symbol = symbol_result["reason"]

    if flag_algorithm and flag_symbol:
        print("Factor Test Result:", factor_name, "True")
        return True

    print("Factor Test Result:", factor_name, "False")
    if algorithm_result is not None:
        print("Algorithm Team Factor Test Result is: {}, Reason: \n{}\n{}\n".format(flag_algorithm, reason_algorithm,
                                                                                    detail))
    if symbol_result is not None:
        print("Stock-Trade Team Factor Test Result is: {}, Reason:".format(flag_symbol))
        for time_range, test_result in reason_symbol.items():
            print(time_range, test_result)
    return False


def test(start_date, end_date, factor_result, calc_num=1, local=True, pdf_address=None):
    check_factor_result(factor_result)
    if len(factor_result) > 1:
        return fix_factor_test(start_date, end_date, factor_result, local, calc_num=calc_num)
    else:
        return day_factor_test(start_date, end_date, factor_result, local=local, report=pdf_address)
