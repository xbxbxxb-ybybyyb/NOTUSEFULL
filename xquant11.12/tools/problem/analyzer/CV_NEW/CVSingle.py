from Utils_CV.InputManager import InputManager
from Utils_CV.ResultManager import ResultManager
from Utils_CV.ThreadingManager import ThreadingManager, ThreadingManagerSpark
from CONFIG import get_hdfs_root_path


def cv(symbols, init_quantities, optimal_shift, bt_dir, signal_csv_dir, output_dir, executor_str='SignalExecutorTesting', mode="Local",
       max_tasks=400, **kwargs):

    open_triggers = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0]
    close_triggers = [-1.0, -0.9, -0.8, -0.7, -0.6, -0.5, -0.4, -0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

    # signal_csv_dir = get_hdfs_root_path(mode, signal_csv_dir), 信号数据保存在HBASE中，不需要加前缀
    bt_dir = get_hdfs_root_path(mode, bt_dir)
    output_dir = get_hdfs_root_path(mode, output_dir)

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
    input_manager.set_optimal_shift(optimal_shift)
    input_manager.set_triggers(open_triggers, close_triggers, param_reduction=True)
    result_manager = ResultManager()
    if mode == "Local":
        threading_manager = ThreadingManager(input_manager, result_manager)
    elif mode == "Spark":
        threading_manager = ThreadingManagerSpark(input_manager, result_manager, max_tasks)

    print("CV Start")
    threading_manager.start()
    print('CV Done')
