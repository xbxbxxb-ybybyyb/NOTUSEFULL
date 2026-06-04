#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/7/14 16:03
### 主力合约
ZL = "ZL"
ZL00 = "ZL00"
ZL01 = "ZL01"

### 中国金融期货交易所
CF = "CF"
CF_FUTURE_LIST = ['IF', 'IC', 'IH', 'TS', 'TF', 'T']

### 上海期货交易所
SHF = "SHF"
SHF_FUTURE_LIST = ['CU', 'AL', 'ZN', 'PB', 'NI', 'SN', 'AU', 'AG', 'RB', 'WR', 'HC', 'SC', 'FU', 'BU','RU', 'SP']

### 郑州商品交易所
ZCE = "ZCE"
ZCE_FUTURE_LIST = ['WH', 'SR', 'RS', 'LR', 'CJ', 'PM', 'OI', 'RM', 'CY', 'CF', 'RI', 'JR', 'AP','TA', 'FG', 'SF', 'MA', 'ZC', 'SM']

### 大连商品交易所
DCE = "DCE"
DCE_FUTURE_LIST = ['C', 'CS', 'A', 'B', 'M', 'Y', 'P', 'FB', 'BB', 'JD', 'L', 'V', 'PP', 'J', 'JM', 'I', 'EG']

def starts_within_list(start_str, str_list):
    assert len(str_list) > 0, " InValid Empty List "
    for str_item in str_list:
        if start_str.startswith(str_item):
            return True
    return False

def starts_within_zl00(code, str_list):
    assert len(str_list) > 0, " InValid Empty List "
    for str_item in str_list:
        if code.startswith(str_item + ZL00):
            return True
    return False

def starts_within_zl01(code, str_list):
    assert len(str_list) > 0, " InValid Empty List "
    for str_item in str_list:
        if code.startswith(str_item + ZL01):
            return True
    return False

def is_cf_future_code(code):
    if (code.endswith(CF) and starts_within_list(code, CF_FUTURE_LIST) ) \
            or starts_within_zl00(code, CF_FUTURE_LIST) or starts_within_zl01(code, CF_FUTURE_LIST):
        return True
    return False

def is_shf_future_code(code):
    if (code.endswith(SHF) and starts_within_list(code, SHF_FUTURE_LIST) ) \
            or starts_within_zl00(code, SHF_FUTURE_LIST) or starts_within_zl01(code, SHF_FUTURE_LIST):
        return True
    return False

def is_zce_future_code(code):
    if (code.endswith(ZCE) and starts_within_list(code, ZCE_FUTURE_LIST) ) \
            or starts_within_zl00(code, ZCE_FUTURE_LIST) or starts_within_zl01(code, ZCE_FUTURE_LIST):
        return True
    return False

def is_dce_future_code(code):
    if (code.endswith(DCE) and starts_within_list(code, DCE_FUTURE_LIST) ) \
            or starts_within_zl00(code, DCE_FUTURE_LIST) or starts_within_zl01(code, DCE_FUTURE_LIST):
        return True
    return False

def is_future_code(code):
    if is_cf_future_code(code) or is_shf_future_code(code) or is_zce_future_code(code) or is_dce_future_code(code):
        return True
    return False

def is_future_zl00_code(code):
    if is_future_code(code):
        if starts_within_zl00(code, CF_FUTURE_LIST) or starts_within_zl00(code, SHF_FUTURE_LIST) \
            or starts_within_zl00(code, ZCE_FUTURE_LIST) or starts_within_zl00(code, DCE_FUTURE_LIST):
            return True
    return False

def is_future_zl01_code(code):
    if is_future_code(code):
        if starts_within_zl01(code, CF_FUTURE_LIST) or starts_within_zl01(code, SHF_FUTURE_LIST) \
            or starts_within_zl01(code, ZCE_FUTURE_LIST) or starts_within_zl01(code, DCE_FUTURE_LIST):
            return True
    return False

def is_future_zl_code(code):
    if is_future_zl00_code(code) or is_future_zl01_code(code):
        return True
    return False

def get_future_contract_type(code):
    if is_future_zl00_code(code):
        return "ZL00"
    elif is_future_zl01_code(code):
        return "ZL01"
    else:
        return None

def get_future_maket_type(code):
    assert is_future_code(code), " Not Supported Future: {}".format(code)
    if is_cf_future_code(code):
        return "CF"
    elif is_shf_future_code(code):
        return "SHF"
    elif is_zce_future_code(code):
        return "ZCE"
    elif is_dce_future_code(code):
        return "DCE"

INDEX_FUTURE_INDEX_MAP = {
    "IHZL": "000016.SH",
    "IFZL": "000300.SH",
    "ICZL": "000905.SH"
}


