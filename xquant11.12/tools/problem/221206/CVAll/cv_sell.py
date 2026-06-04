import Utils_CV.HelperFunctions as HelperFunc
from Utils_CV.InputManager import InputManager
from Utils_CV.ResultManager import ResultManager
from Utils_CV.ThreadingManager import ThreadingManager


def main():
    start_date = 20190701
    end_date = 20190831
    cv_suffix = 1

    bt_dir = "666888/Apollo/cv_info/{}-{}_universal/".format(start_date, end_date)
    signal_csv_dir = "Model20190101_48"
    param_dir = "666888/Apollo/cv_params/{}-{}_universal/Apollo/".format(start_date, end_date)
    output_dir = "666888/Apollo/cv_results/sell{}/{}-{}_universal/".format(cv_suffix, start_date, end_date)
    executor_str = "SignalExecutorAlphaVWAPEZ"

    symbols, target_quantities, target_values = HelperFunc.get_symbols_quantities_from_json(
        param_dir[7:] + "/../" + "Apollo_quantity_negative" + str(cv_suffix) + ".json"
    )

    open_long_aggr_qs = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.99]
    open_long_pass_qs = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.99]

    input_manager = InputManager(signal_csv_dir=signal_csv_dir, bt_dir=bt_dir, param_dir=param_dir,
                                 output_dir=output_dir, executor_str=executor_str)
    input_manager.set_symbols(symbols)
    input_manager.set_target_quantities(target_quantities)
    input_manager.set_target_values(target_values)
    input_manager.set_period(start_date, end_date)
    input_manager.set_quantiles(open_long_aggr_qs, open_long_pass_qs, param_reduction=True)
    result_manager = ResultManager()
    threading_manager = ThreadingManager(input_manager, result_manager, max_tasks=len(symbols))

    threading_manager.start()
    print("Done")


if __name__ == "__main__":
    main()
