import Utils_BT.HelperFunctions as HelperFunc
from Utils_BT.InputManager import InputManager
from Utils_BT.ResultManager import ResultManager
from Utils_BT.ThreadingManager import ThreadingManager
from Utils_BT.TotalSummary import summary


def bt_single(portfolio, bt_date, bt_dir, signal_csv_dir, param_dir, output_dir, trigger_path, executor_str,
              portfolio_suffix):
    symbols, target_quantities, target_values = HelperFunc.get_symbols_quantities_from_json(
        bt_dir[7:] + portfolio + "_quantity.json"
    )

    input_manager = InputManager(signal_csv_dir=signal_csv_dir, bt_dir=bt_dir, param_dir=param_dir,
                                 output_dir=output_dir, executor_str=executor_str, trigger_path=trigger_path)
    input_manager.set_symbols(symbols)
    input_manager.set_target_quantities(target_quantities)
    input_manager.set_target_values(target_values)
    input_manager.set_period(bt_date, bt_date)
    result_manager = ResultManager()
    threading_manager = ThreadingManager(input_manager, result_manager, max_tasks=len(symbols))

    threading_manager.start()
    summary(
        output_dir,
        "/data/user/666888/Apollo/bt_results/",
        "/{}/{}_{}/".format(bt_date, portfolio, portfolio_suffix),
        overwrite=True,
        name="result_all.xlsx"
    )
