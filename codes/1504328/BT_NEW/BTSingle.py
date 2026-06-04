from Utils_BT.InputManager import InputManager
from Utils_BT.ResultManager import ResultManager
from Utils_BT.ThreadingManager import ThreadingManager, ThreadingManagerSpark
from CONFIG import get_hdfs_root_path


def bt_single(symbols, init_quantities, optimal_shift, start_date, end_date, signal_library, bt_dir, output_dir,
              executor_str, data_config, use_l2p, trigger_json_dir, mode="Local", max_tasks=400, **kwargs):

    bt_dir = get_hdfs_root_path(mode, bt_dir)
    output_dir = get_hdfs_root_path(mode, output_dir)
    trigger_json_dir = get_hdfs_root_path(mode, trigger_json_dir)

    input_manager = InputManager(
        start_date=start_date,
        end_date=end_date,
        signal_library=signal_library,
        bt_dir=bt_dir,
        output_dir=output_dir,
        executor_str=executor_str,
        data_config=data_config,
        use_l2p=use_l2p,
        trigger_json_dir=trigger_json_dir
    )

    overwrite_params = kwargs
    for key in overwrite_params.keys():
        input_manager.mock_trade_para.update({key: overwrite_params[key]})
    input_manager.set_symbols(symbols)
    input_manager.set_init_quantity(init_quantities)
    input_manager.set_optimal_shift(optimal_shift)
    result_manager = ResultManager()

    if mode == "Local":
        threading_manager = ThreadingManager(input_manager, result_manager)
    elif mode == "Spark":
        threading_manager = ThreadingManagerSpark(input_manager, result_manager, max_tasks)
    else:
        raise Exception("ONLY SUPPORT LOCAL OR SPARK MODE")

    print(" BT Start ")
    threading_manager.start()
    print(' BT Done ')

