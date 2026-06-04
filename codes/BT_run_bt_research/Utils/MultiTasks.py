def get_split_params(all_params, process_nums):
    split_params = list()
    for i in range(process_nums):
        split_params.append([])
    for j in range(len(all_params)):
        split_params[j % process_nums].append(all_params[j])
    print('MultiProcess Starts: {} Multi Tasks'.format(process_nums))
    return split_params


def main_multiprocess(task_single, para_list, multiprocess_nums=1, is_sum_result=True):
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
        #if is_sum_result:
        #    summary_result = []
        #    for kk in multi_process_result:
        #        summary_result_single = kk.get()
        #        summary_result += summary_result_single
        #    return summary_result
    else:  # 非并行化运算
        summary_result = task_single(para_list)
        if is_sum_result:
            return summary_result
