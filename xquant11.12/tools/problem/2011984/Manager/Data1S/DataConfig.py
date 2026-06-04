class DataConfig(object):
    def __init__(self):
        self.tick_hbase_library = "Channel1STickDataLib"
        self.tran_hbase_library = "ZeusDataLib"

    def set_tick_hbase_library(self, tick_hbase_library):
        self.tick_hbase_library = tick_hbase_library

    def set_tran_hbase_library(self, tran_hbase_library):
        self.tran_hbase_library = tran_hbase_library


