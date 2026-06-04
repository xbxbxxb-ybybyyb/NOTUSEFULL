from Utils_BT.InputManager import InputManager
from Utils_BT.ResultManager import ResultManager
from Utils_BT.ThreadingManager import ThreadingManager


def bt_single(symbols,
              init_quantities,
              bt_dir,
              signal_csv_dir,
              output_dir,
              executor_str,
              trigger_json_dir,
              max_tasks=400,
              **kwargs):
    input_manager = InputManager(
        signal_csv_dir=signal_csv_dir,
        bt_dir=bt_dir,
        output_dir=output_dir,
        executor_str=executor_str,
        trigger_json_dir=trigger_json_dir
    )

    overwrite_params = kwargs
    for key in overwrite_params.keys():
        input_manager.mock_trade_para.update({key: overwrite_params[key]})
    input_manager.set_symbols(symbols)
    input_manager.set_init_quantity(init_quantities)
    result_manager = ResultManager()
    threading_manager = ThreadingManager(input_manager, result_manager, max_tasks)

    threading_manager.start()

    print('Backtest finished.')
