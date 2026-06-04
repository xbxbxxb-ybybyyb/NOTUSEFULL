#-*- coding:utf-8 -*-
# author: 015629
# datetime:2022/12/13 15:53
from SignalEns.SignalConfig import SignalConfig


class SignalConfigManager(object):
    def __init__(self, library_list, tag_type_list, save_library, save_tag_type):
        self.library_list = library_list
        self.tag_type_list = tag_type_list
        self.save_library = save_library
        self.save_tag_type = save_tag_type
        self.scm_dict = {library: SignalConfig(library, tag_type) for library, tag_type in zip(self.library_list, self.tag_type_list)}
        self.scm_dict.update({save_library: SignalConfig(self.save_library, self.save_tag_type)})

    def get_signal_columns(self, library):
        return self.scm_dict.get(library).signal_columns

    def get_long_signal_columns(self, library):
        return self.scm_dict.get(library).signal_long_columns

    def get_short_signal_columns(self, library):
        return self.scm_dict.get(library).signal_short_columns

    def get_tag_columns(self, library):
        return self.scm_dict.get(library).tag_columns

    def get_long_tag_columns(self, library):
        return self.scm_dict.get(library).long_tag_columns

    def get_short_tag_columns(self, library):
        return self.scm_dict.get(library).short_tag_columns

    def get_columns_dict(self, src_library, dst_library, column_type_list=["Signal"]):
        columns_dict = dict()
        if "Signal" in column_type_list:
            columns_dict.update({src_col: dst_col for src_col, dst_col in zip(self.get_signal_columns(src_library), self.get_signal_columns(dst_library))})
        if "Tag" in column_type_list:
            columns_dict.update({src_col: dst_col for src_col, dst_col in zip(self.get_tag_columns(src_library), self.get_tag_columns(dst_library))})
        return columns_dict

    @staticmethod
    def add_timestamp_columns(columns):
        return ["timestamp"] + columns


if __name__ == "__main__":
    library_list = ["Albest20220201Order036Signals", "LightGBMRegr_DataSZ_Ev20220201Sample_036"]
    tag_type_list = ["Common", "NChangeTime"]
    save_library = "Albest20220201_LightGBMRegr_EvSample_036"
    save_tag_type = "Common"
    scm = SignalConfigManager(library_list, tag_type_list, save_library, save_tag_type)
    print(scm.get_signal_columns(save_library))