"""不同标签投票的组合————update @ 2021.7.20"""

from itertools import combinations


all_tags = [0.25, 0.5, 1, 2, 5]


def get_voting_list(all_tags):
    sum_list = []
    for i in range(1, len(all_tags) + 1):
        sum_list += [sum(x) for x in list(combinations(all_tags, i))]

    sum_list = list(sorted(set(sum_list)))
    return sum_list


def get_voting_dict(all_tags):
    res_dict = {}
    for i in range(1, len(all_tags) + 1):
        c_ = list(combinations(all_tags, i))
        for c_sub in c_:
            res_dict.update({sum(c_sub): list(c_sub)})
    return res_dict


def get_voting_str_dict():
    all_tags = ['15sec', '30sec', '1min', '2min', '5min']
    tags_value = {'15sec': 0.25, '30sec': 0.5, '1min': 1, '2min': 2, '5min':5}
    res_dict = {}
    for i in range(1, len(all_tags) + 1):
        c_ = list(combinations(all_tags, i))
        for c_sub in c_:
            res_dict.update({sum([tags_value[x] for x in c_sub]): list(c_sub)})
    return res_dict


def resolve_voting_triggers(sum_num, all_tags):
    for i in range(1, len(all_tags) + 1):
        c_ = list(combinations(all_tags, i))
        for c_sub in c_:
            if sum(c_sub) == sum_num:
                return list(c_sub)


def split_col_names(vt_name='8min'):
    voting_dict = get_voting_dict([0.25, 0.5, 1, 2, 5])
    col_list = voting_dict[float(vt_name[:-3])]
    out_col_list = []
    for i in col_list:
        if i in [0.25, 0.5]:
            out_col_list.append(f'{int(i * 60)}sec')
        else:
            out_col_list.append(f'{i}min')
    return out_col_list


def get_voting_params(name='7v4'):
    vt_num1, vt_num2 = name.split('v')
    if vt_num1 == '7':
        vt_name_list = ['1min', '2min', '3min', '5min', '6min', '7min', '8min']
        vt_name = '8min'
    elif vt_num1 == '10':
        vt_name_list = ['1.75min', '2.75min', '3.25min', '3.5min', '5.75min', '6.25min', '6.5min', '7.25min', '7.5min', '8min']
        vt_name = '8.75min'
    elif vt_num1 == '16':
        vt_name_list = ['1.75min', '2.75min', '3.25min', '3.5min', '3.75min', '5.75min', '6.25min', '6.5min', '6.75min', '7.25min', '7.5min',
                        '7.75min', '8min', '8.25min', '8.5min', '8.75min']
        vt_name = '8.75min'
    else:
        raise ValueError

    vt_num2 = int(vt_num2)
    overwrite_params = {'vt_name': vt_name, 'vt_params': {'vt_name_list': vt_name_list, 'open_counter': vt_num2}}
    return overwrite_params
