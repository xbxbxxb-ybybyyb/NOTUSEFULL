from typing import List, Dict
from xquant.pyfile import Pyfile
import json


def get_symbols_quantities_from_json(json_path):
    symbols = []
    init_quantities = []
    py = Pyfile()
    with py.open(json_path, 'rb') as f:
        data = f.read()
        data = json.loads(data)
    for symbol in data['quantity'].keys():
        symbols.append(symbol)
        init_quantities.append(data['quantity'][symbol])
    return symbols, init_quantities


def split_params(original_params: List[Dict[str, float]], group_num: int) -> List[List[Dict[str, float]]]:
    splitted_params = []
    if len(original_params) <= group_num:
        for param in original_params:
            splitted_params.append([param])
    else:
        for index in range(group_num):
            splitted_params.append([])
        count = 0
        for param in original_params:
            splitted_params[count].append(param)
            count += 1
            if count >= group_num:
                count = 0
    return splitted_params


def split_assign_symbols(symbols: List[str], total_cpus: int=200) -> List[List[str]]:
    length = len(symbols)
    value = []
    if length >= total_cpus:
        splitted_symbols = np.array_split(symbols, total_cpus)
        for elem in splitted_symbols:
            value.append(elem.tolist())
    else:
        for symbol in symbols:
            value.append([symbol])
    return value
