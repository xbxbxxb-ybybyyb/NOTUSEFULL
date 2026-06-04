from xquant.factordata import FactorData


def create_library(lib_name, factor_name_list=[]):
    fd = FactorData()

    try:
        fd.create_factor_library(lib_name, "T+0")
    except Exception as e:
        print(e)

    for fn in factor_name_list:
        try:
            fd.add_factor(lib_name, [fn])
        except Exception as e:
            print(e)


def factor_value_reverse_T0(factor_name):
    lib_name = 'FactorJS'
    fd = FactorData()

    code_list = list(GetCodeVol(bt_date, bt_date).get_sp_code(f'Everest1S_sp').keys())
    for code in code_list:
        data_code = load_lib_data(code, [bt_date], old_lib, col_names)
        data_code = data_code.set_index('timestamp')
        sel_index = [x for x in data_code.index if x % 3 == 0]
        data_code036 = data_code.loc[sel_index].reset_index()
        fd.update_factor_value(new_lib, data_code036, code, bt_date)


