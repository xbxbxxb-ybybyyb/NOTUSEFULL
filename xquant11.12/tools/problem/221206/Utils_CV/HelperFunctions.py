import json
from xquant.pyfile import Pyfile
from xquant.factordata import FactorData


def get_symbols_quantities_from_json(json_path):
    symbols = []
    init_quantities = []
    init_values = []
    py = Pyfile()
    with py.open(json_path, 'rb') as f:
        data = f.read()
        data = json.loads(data)
    for symbol in data['quantity'].keys():
        symbols.append(symbol)
        init_quantities.append(data['quantity'][symbol])
        init_values.append(data['value'][symbol])
    return symbols, init_quantities, init_values


def load_signals(bt_dir, symbols, library_name):
    signals_dict = {}

    prediction_names = ["timestamp", "ticktime", "prediction1minLong", "prediction2minLong",
                        "prediction5minLong", "prediction1minShort", "prediction2minShort",
                        "prediction5minShort"]
    rename_dict = {
        "timestamp": "Timestamp",
        "ticktime": "Ticktime",
        "prediction1minLong": "1minLong",
        "prediction1minShort": "1minShort",
        "prediction2minLong": "2minLong",
        "prediction2minShort": "2minShort",
        "prediction5minLong": "5minLong",
        "prediction5minShort": "5minShort"
    }
    py = Pyfile()
    factor_data = FactorData()

    k = 1
    total_num = len(symbols)
    print("Total number of stocks: {}".format(total_num))
    for symbol in symbols:
        signals_dict[symbol] = {}

        try:
            with py.open(bt_dir[7:] + symbol + '/Dates.json', 'rb') as f:
                data = f.read()
                dates = json.loads(data)['Dates']
                dates.sort()
        except:
            print("{} failed, {}/{}".format(symbol, k, total_num))
            k += 1
            continue

        for date in dates:
            try:
                signal_df = factor_data.get_factor_value(library_name, symbol, date, prediction_names)
                signal_df = signal_df.rename(columns=rename_dict)
            except AttributeError:
                signal_df = None
            except Exception as e:
                print(symbol, date)
                print(e)
                signal_df = None

            signals_dict[symbol][date] = signal_df
        print("{} succeeded, {}/{}".format(symbol, k, total_num))
        k += 1

    return signals_dict
