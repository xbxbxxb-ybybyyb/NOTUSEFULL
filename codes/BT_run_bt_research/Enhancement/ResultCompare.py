import pandas as pd


def main():
    abs_path_list = [
        "/data/user/011668/bt_test/results/20200601-20200831/bt-20200601-20200831-WuKong-ProductionExecutor2/",
        "/data/user/011668/bt_test/results/20200601-20200831/bt-20200601-20200831-WuKong-ProductionExecutor-3/",
    ]

    tags = ["origin", "v3"]
    result = ResultCompare(abs_path_list, tags)
    daily_earn_df, acc_earn_df = result.compare_daily_earn()
    stock_earn_df = result.compare_stock_earn(is_output_gap=True)
    stock_gap_detail = result.stock_gap_df()
    print("")


class ResultCompare:
    def __init__(self, abs_path_list, tags):
        self.abs_path_list = abs_path_list
        self.tags = tags

    def compare_daily_earn(self, st_date=None, ed_date=None):
        daily_earn_list = []
        acc_earn_list = []
        for path in self.abs_path_list:
            combine_data = pd.read_excel(path + "/result_daily.xls", sheet_name="dailyInfo", index_col=0)
            daily_earn_list.append(combine_data["总盈利"])
            acc_earn_list.append(combine_data["总盈利"].cumsum())  # 累计总盈利

        daily_earn_df = pd.concat(daily_earn_list, axis=1)
        acc_earn_df = pd.concat(acc_earn_list, axis=1)
        daily_earn_df.columns = self.tags
        acc_earn_df.columns = self.tags
        if st_date is not None and ed_date is not None:
            daily_earn_df = daily_earn_df.loc[st_date:ed_date]
            acc_earn_df = acc_earn_df.loc[st_date:ed_date]
        return daily_earn_df, acc_earn_df

    def compare_stock_earn(self, is_output_gap=False):
        stock_earn_list = []
        for path in self.abs_path_list:
            combine_data = pd.read_excel(path + "/TotalSummary.xls", sheet_name="TotalSummary", index_col=0)
            stock_earn_list.append(combine_data["afterCostProfit"])
        stock_earn_df = pd.concat(stock_earn_list, axis=1)
        stock_earn_df.columns = self.tags

        if is_output_gap and len(self.tags) == 2:
            stock_earn_df["gap"] = stock_earn_df[self.tags[0]] - stock_earn_df[self.tags[1]]
            stock_earn_df = stock_earn_df.sort_values(by="gap")
            stock_earn_df = stock_earn_df[stock_earn_df["gap"] != 0]
        return stock_earn_df

    def stock_gap_df(self):
        if len(self.tags) != 2:
            raise ValueError("只适用于对比2个结果的情况（abs_path_list长度应该为2）")
        daily_split_1 = pd.read_excel("{}/daily_split.xlsx".format(self.abs_path_list[0]), index_col=0).set_index("Date")
        daily_split_2 = pd.read_excel("{}/daily_split.xlsx".format(self.abs_path_list[1]), index_col=0).set_index("Date")
        earn_gap = daily_split_1 - daily_split_2
        earn_gap_by_date = earn_gap.sum(axis=0).sort_values()
        sel_code = list(earn_gap_by_date[earn_gap_by_date != 0].index)
        sel_earn_gap = earn_gap[sel_code]
        return sel_earn_gap


if __name__ == '__main__':
    main()
