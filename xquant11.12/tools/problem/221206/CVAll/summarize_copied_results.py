from Utils_CV.TotalSummary import summary

start_date = "20190701"
end_date = "20190831"

results_dir_buy = "666888/Apollo/cv_results/{}-{}_universal/buy/".format(start_date, end_date)
results_dir_sell = "666888/Apollo/cv_results/{}-{}_universal/sell/".format(start_date, end_date)

nas_path = "/data/user/666888/Apollo/cv_results/"

summary(
    results_dir_buy,
    nas_path,
    "/{}-{}_universal/buy/".format(start_date, end_date),
    overwrite=True,
    name="result_all.xlsx"
)

summary(
    results_dir_sell,
    nas_path,
    "/{}-{}_universal/sell/".format(start_date, end_date),
    overwrite=True,
    name="result_all.xlsx"
)
