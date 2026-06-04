from Utils_CV.InputManager import InputManager
from Utils_CV.ResultManager import ResultManager
from Utils_CV.ThreadingManager import ThreadingManager


def cv(symbols, init_quantities, bt_dir, signal_csv_dir, output_dir, executor_str='SignalExecutorTesting',
       max_tasks=400, **kwargs):
    open_triggers = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 2.0]
    close_triggers = [-1.0, -0.9, -0.8, -0.7, -0.6, -0.5, -0.4, -0.3, -0.2, -0.1,
                      0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    # open_triggers = [x / 10 for x in open_triggers]
    # close_triggers = [x / 10 for x in close_triggers]

    input_manager = InputManager(
        signal_csv_dir=signal_csv_dir,
        bt_dir=bt_dir,
        output_dir=output_dir,
        executor_str=executor_str,
        cross_valid=True
    )

    overwrite_params = kwargs
    for key in overwrite_params.keys():
        input_manager.mock_trade_para.update({key: overwrite_params[key]})

    input_manager.set_symbols(symbols)
    input_manager.set_init_quantity(init_quantities)
    input_manager.set_triggers(open_triggers, close_triggers, param_reduction=True)
    result_manager = ResultManager()
    threading_manager = ThreadingManager(input_manager, result_manager, max_tasks)

    print("Start")
    threading_manager.start()
    print('Done')
