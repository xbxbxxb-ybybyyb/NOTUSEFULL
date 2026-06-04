#-*- coding:utf-8 -*-
# author: 015629
# datetime:2022/12/13 15:45


class SignalConfig(object):
    def __init__(self, library, tag_type):
        self.library = library
        self.tag_type = tag_type
        assert self.tag_type in ["Common", "Time", "NChange", "NChangeTime"]
        if self.tag_type == "Common":
            self.window_list = [1, 2, 5]
        else:
            self.window_list = [60, 120, 300]

        self.long_tag_columns = self.get_tag_name_list(self.tag_type, ["Long"], window_list=self.window_list)
        self.short_tag_columns = self.get_tag_name_list(self.tag_type, ["Short"], window_list=self.window_list)
        self.tag_columns = self.long_tag_columns + self.short_tag_columns
        self.long_signal_columns = [col.replace("tag", "prediction") for col in self.long_tag_columns]
        self.short_signal_columns = [col.replace("tag", "prediction") for col in self.short_tag_columns]
        self.signal_columns = self.long_signal_columns + self.short_signal_columns

    def get_tag_name_list(self, tag_type, direction_list=["Long", "Short"], window_list=[1, 2, 5]):
        tag_name_list = []
        for direction in direction_list:
            for window in window_list:
                tag_name_list.append(self.get_tag_name(tag_type, direction, window))
        return tag_name_list

    @staticmethod
    def get_tag_name(tag_type, direction, window):
        if tag_type in ["Time", "NChange", "NChangeTime"]:
            assert window in [30, 60, 90, 120, 300]
        else:
            assert window in [1, 2, 5]

        if tag_type == "Time":
            tag_name = "tag{}Sec{}".format(window, direction)
        elif tag_type == "NChange":
            tag_name = "tagN{}{}".format(window, direction)
        elif tag_type == "NChangeTime":
            tag_name = "tagN{}Sec{}".format(window, direction)
        else:
            tag_name = "tag{}min{}".format(window, direction)
        return tag_name

