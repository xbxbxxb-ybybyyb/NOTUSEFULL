#-*- coding:utf-8 -*-
# author: 015629
# datetime:2021/11/16 15:22

class DataConfig(object):
    def __init__(self):
        self.tick_data_source = "hbase"
        self.tick_hbase_library = "Stock036SL2PDataLib"
        self.tran_data_source = "hbase"
        self.tran_hbase_library = "ZeusDataLib"
        self.order_data_source = None
        self.order_hbase_library = None

    def set_tick_data_source(self, tick_data_source):
        self.tick_data_source = tick_data_source

    def set_tick_hbase_library(self, tick_hbase_library):
        self.tick_hbase_library = tick_hbase_library

    def set_tran_data_source(self, tran_data_source):
        self.tran_data_source = tran_data_source

    def set_tran_hbase_library(self, tran_hbase_library):
        self.tran_hbase_library = tran_hbase_library

    def set_order_data_source(self, order_data_source):
        self.order_data_source = order_data_source

    def set_order_hbase_library(self, order_hbase_library):
        self.order_hbase_library = order_hbase_library



