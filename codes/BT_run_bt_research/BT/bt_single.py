from Manager.InputManager import InputManager
from Manager.ResultManager import ResultManager
from Manager.ThreadingManager import ThreadingManager


def bt_single(symbols, init_quantities, bt_dir, signal_csv_dir, output_dir, executor_str, trigger_json_dir,
              mode="spark", max_tasks=600, **kwargs):
    if mode == "spark":
        bt_dir = '011668/' + bt_dir
        trigger_json_dir = '011668/' + trigger_json_dir
        output_dir = '011668/' + output_dir
    input_manager = InputManager(signal_csv_dir, bt_dir, output_dir, executor_str, trigger_json_dir)
    overwrite_params = kwargs
    for key in overwrite_params.keys():
        input_manager.mock_trade_para.update({key: overwrite_params[key]})
    input_manager.set_symbols(symbols)
    input_manager.set_init_quantity(init_quantities)
    result_manager = ResultManager()

    threading_manager = ThreadingManager(input_manager, result_manager, max_tasks)
    threading_manager.start(mode)
    print('Backtest finished.')
