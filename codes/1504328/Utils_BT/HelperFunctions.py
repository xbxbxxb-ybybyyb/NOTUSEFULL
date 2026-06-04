from typing import List, Dict
import numpy as np
from xquant.xqutils.xqfile import HDFSFile
import json


def get_symbols_quantities_from_json(json_path):
    # if 'SHARE_21' in json_path:
    #     json_path = json_path.replace('SHARE_21', '$21')
    # elif '$21' in json_path:
    #     pass
    # else:
    #     while json_path[0] == '/':
    #         json_path = json_path[1:]
    #     index = json_path.index('/')
    #     json_path = json_path[index + 1: ]

    symbols = []
    init_quantities = []
    hf = HDFSFile()
    with hf.open(json_path, 'rb') as f:
        data = f.read()
        data = json.loads(data)
    for symbol in data['Quantity'].keys():
        symbols.append(symbol)
        init_quantities.append(data['Quantity'][symbol])
    return symbols, init_quantities


def get_optimal_shift_from_json(json_path):
    hf = HDFSFile()
    with hf.open(json_path, 'rb') as f:
        data = f.read()
        data = json.loads(data)

    symbols_to_remove = []
    symbols_to_append = []

    symbols = []
    optimal_shift = []
    for symbol in data['OptShift'].keys():
        if symbol in symbols_to_remove:
            continue
        symbols.append(symbol)
        optimal_shift.append(data['OptShift'][symbol])

    for symbol in symbols_to_append:
        symbols.append(symbol)
        optimal_shift.append(data['OptShift'][symbol])

    return symbols, optimal_shift


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