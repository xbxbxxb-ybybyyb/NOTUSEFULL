import json
from xquant.xqutils.xqfile import HDFSFile


def func_run_single(context, task_meta):
    hdfsfile = HDFSFile()
    symbol = task_meta.get_symbols()[0]
    try:
        with hdfsfile.open("{}/{}/triggerRatio.json".format(trigger_json_dir, symbol), 'rb') as f:
            trigger_dict = f.read()
            trigger_dict = json.loads(trigger_dict)
            print(symbol)
    except Exception as e:
        print(str(e) + '; return safely')
        return


class TaskMeta:
    def __init__(self, symbols):
        self.__symbols = symbols

    def get_symbols(self):
        return self.__symbols


class ThreadingManager:
    def __init__(self, max_tasks: int = 200):
        self.__symbols = symbols

    def start(self, mode):
        task_metas = []
        for symbol in self.__symbols:
            task_metas.append(TaskMeta([symbol]))

        if mode == "local":
            self.task_single(task_metas)

        elif mode == "multiprocessing":
            main_multiprocess(task_single=self.task_single, para_list=task_metas, multiprocess_nums=2)

    @staticmethod
    def task_single(task_metas_list):
        for i in task_metas_list:
            func_run_single("", i)


def get_split_params(all_params, process_nums):
    split_params = list()
    for i in range(process_nums):
        split_params.append([])
    for j in range(len(all_params)):
        split_params[j % process_nums].append(all_params[j])
    print('MultiProcess Starts: {} Multi Tasks'.format(process_nums))
    return split_params


def main_multiprocess(task_single, para_list, multiprocess_nums=1):
    if multiprocess_nums > 1:  # 并行化运算
        import multiprocessing as mp
        split_params_all = get_split_params(para_list, multiprocess_nums)
        pool = mp.Pool(processes=multiprocess_nums)
        multi_process_result = []
        for split_params in split_params_all:
            result = pool.apply_async(task_single, [split_params], )
            multi_process_result.append(result)
        pool.close()
        pool.join()
        summary_result = []
        for kk in multi_process_result:
            summary_result_single = kk.get()
            summary_result += summary_result_single
    else:  # 非并行化运算
        summary_result = task_single(para_list)
    return summary_result


if __name__ == "__main__":
    mode = "multiprocessing"  # local 或 multiprocessing
    symbols = ['110031.SH', '110048.SH', '110062.SH', '113009.SH', '113020.SH']
    trigger_json_dir = 'cv/CB/cv-20200315-20200529_20200601-WuKong-50-100_big_cb_stock_20200301_20200413_2'
    threading_manager = ThreadingManager()
    threading_manager.start(mode)
    print("End")
