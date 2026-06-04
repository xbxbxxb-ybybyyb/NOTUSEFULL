import json
import numpy as np
from typing import List, Dict
from xquant.pyfile import Pyfile


def get_symbols_quantities_from_json(json_path):
    if 'SHARE_21' in json_path:
        json_path = json_path.replace('SHARE_21', '$21')
    elif '$21' in json_path:
        pass
    else:
        while json_path[0] == '/':
            json_path = json_path[1:]
        index = json_path.index('/')
        json_path = json_path[index + 1:]

    py = Pyfile()
    with py.open(json_path, 'rb') as f:
        data = f.read()
        data = json.loads(data)

    symbols_to_remove = []
    symbols_to_append = []

    symbols = []
    init_quantities = []
    for symbol in data['quantity'].keys():
        if symbol in symbols_to_remove:
            continue
        symbols.append(symbol)
        init_quantities.append(data['quantity'][symbol])

    for symbol in symbols_to_append:
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