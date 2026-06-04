
def parse_target_type(label_name):
    target_type = None
    if label_name.startswith("LabelFirstPeak"):
        target_type = "mid"
    elif label_name.startswith("LabelLong") or  label_name.startswith("LabelShort"):
        target_type = "longshort"
    elif "short_ret" in  label_name or "long_ret" in label_name:
        target_type = "longshort"
    elif "ask2ask" in  label_name:
        target_type = "ask1"
    elif "bid2bid" in  label_name:
        target_type = "bid1"
    else:
        raise Exception("无法识别target_type!", label_name)
    return target_type


def parse_winloss_columns(label_name):
    if "Long" in label_name:
        plot_columns = ['涨日均个数', '涨总体止盈率', '涨总体平率', '涨总体止损率', "信号质量加权"]
    elif "Short" in label_name:
        plot_columns = ['跌日均个数', '跌总体止盈率', '跌总体平率', '跌总体止损率', "信号质量加权"]
    elif "short_ret" in  label_name:
        plot_columns = ['跌日均个数', '跌总体止盈率', '跌总体平率', '跌总体止损率', "信号质量加权"]
    elif "long_ret" in label_name:
        plot_columns = ['涨日均个数', '涨总体止盈率', '涨总体平率', '涨总体止损率', "信号质量加权"]
    elif "ask2ask" in  label_name:
        plot_columns = ['涨跌日均个数', '涨跌总体止盈率', '涨跌总体平率', '涨跌总体止损率', "信号质量加权"]
    elif "bid2bid" in  label_name:
        plot_columns = ['涨跌日均个数', '涨跌总体止盈率', '涨跌总体平率', '涨跌总体止损率', "信号质量加权"]
    else:
        plot_columns = ['涨跌日均个数', '涨跌总体止盈率', '涨跌总体平率', '涨跌总体止损率', "信号质量加权"]
    return plot_columns