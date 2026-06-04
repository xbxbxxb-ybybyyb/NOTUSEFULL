# _*_ coding:utf-8 _*_


index_list = ['000001.SH','000002.SH', '000016.SH','000300.SH','000905.SH','000906.SH',
                '399001.SZ','399005.SZ','399006.SZ', '000985.CSI']

def INDEX_retrieve(cdate_list, csv_path, index_list):
    factor_list = ['close', 'pre_close']
    table_dict = {'AIndexEODPrices': ['close', 'pre_close']}

    mapping_dict = {'close':'S_DQ_CLOSE', 'pre_close': 'S_DQ_PRECLOSE'}
    for table_name in table_dict:
        for dataset_name in table_dict[table_name]:
            factor_name = mapping_dict[dataset_name]
            retrieve_htsc(cdate_list, dataset_name, table_name, factor_name, csv_path, 'MD', use_stock_list = index_list)

