import Utils_CV.HelperFunctions as HelperFunc
from Utils_CV.InputManager import InputManager
from Utils_CV.ResultManager import ResultManager
from Utils_CV.ThreadingManager import ThreadingManager
from Utils_CV.TotalSummary import summary


def main():
    portfolio = "5161101"
    next_trading_day = "20191223"

    start_date = 20191007
    end_date = 20191220

    cv_dir = "666888/Apollo/cv_info/{}-{}_{}/{}/".format(start_date, end_date, next_trading_day, portfolio)
    signal_csv_dir = "Model20190101_48"
    param_dir = "666888/Apollo/cv_params/{}-{}_{}/{}/".format(start_date, end_date, next_trading_day, portfolio)
    output_dir = "666888/Apollo/cv_results/{}-{}_{}/{}/".format(start_date, end_date, next_trading_day, portfolio)
    # executor_str = "SignalExecutorAlphaVWAPEZNew"
    executor_str = "SignalExecutorCsfNew"

    symbols, target_quantities, target_values = HelperFunc.get_symbols_quantities_from_json(
        cv_dir[7:] + portfolio + "_quantity.json"
    )

    # open_long_aggr_qs = [0.7, 0.73, 0.76, 0.79, 0.82, 0.85, 0.88, 0.91, 0.94, 0.97, 0.99]
    # open_long_pass_qs = [0.7, 0.73, 0.76, 0.79, 0.82, 0.85, 0.88, 0.91, 0.94, 0.97, 0.99]
    
    open_long_aggr_qs = [0.88, 0.91, 0.94, 0.97]
    open_long_pass_qs = [0.88, 0.91, 0.94, 0.97]
    open_short_aggr_qs = [0.03, 0.06, 0.09, 0.12]
    open_short_pass_qs = [0.03, 0.06, 0.09, 0.12]

    input_manager = InputManager(signal_csv_dir=signal_csv_dir, bt_dir=cv_dir, param_dir=param_dir,
                                 output_dir=output_dir, executor_str=executor_str)
    input_manager.set_symbols(symbols)
    input_manager.set_target_quantities(target_quantities)
    input_manager.set_target_values(target_values)
    input_manager.set_period(start_date, end_date)
    input_manager.set_quantiles(open_long_aggr_qs, open_long_pass_qs, open_short_aggr_qs, open_short_pass_qs, param_reduction=True)
    # input_manager.set_quantiles(open_long_aggr_qs, open_long_pass_qs, param_reduction=True)
    result_manager = ResultManager()
    threading_manager = ThreadingManager(input_manager, result_manager, max_tasks=len(symbols))

    threading_manager.start()
    summary(
        output_dir,
        "/data/user/666888/Apollo/cv_results/",
        "/{}-{}_{}/{}/".format(start_date, end_date, next_trading_day, portfolio),
        overwrite=True,
        name="result_all.xlsx"
    )
    print("Done")


if __name__ == "__main__":
    main()
