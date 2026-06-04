"""并行化计算函数（包括multiprocessing，ray，spark）"""

import os
import time


def get_split_params(all_params, process_nums):
    split_params = list()
    for i in range(process_nums):
        split_params.append([])
    for j in range(len(all_params)):
        split_params[j % process_nums].append(all_params[j])
    return split_params


def main_multiprocess(task_single, para_list, multiprocess_nums=1, is_sum_result=True):
    multiprocess_nums = min(len(para_list), multiprocess_nums)
    if multiprocess_nums > 1:  # 并行化运算
        import multiprocessing as mp
        print('MultiProcess Starts: {} Multi Tasks'.format(multiprocess_nums))
        split_params_all = get_split_params(para_list, multiprocess_nums)
        pool = mp.Pool(processes=multiprocess_nums)
        multi_process_result = []
        for split_params in split_params_all:
            result = pool.apply_async(task_single, [split_params], )
            multi_process_result.append(result)
        pool.close()
        pool.join()
        if is_sum_result:
            summary_result = []
            for kk in multi_process_result:
                summary_result_single = kk.get()
                summary_result.append(summary_result_single)
            return summary_result
    else:  # 非并行化运算
        summary_result = task_single(para_list)
        if is_sum_result:
            return summary_result


def list_transfer(input_list):
    output_list = []
    for x in input_list:
        output_list.extend(x)
    return output_list


def main_ray(task_single, para_list, multiprocess_nums=1, is_sum_result=True):
    multiprocess_nums = min(len(para_list), multiprocess_nums)
    if multiprocess_nums > 1:  # 并行化运算
        import ray
        ray.init(num_cpus=multiprocess_nums)
        execute_task = ray.remote(task_single)
        summary_result = ray.get([execute_task.remote(para) for para in para_list])
        ray.shutdown()
        if is_sum_result:
            return summary_result
    else:  # 非并行化运算
        summary_result = task_single(para_list)
        if is_sum_result:
            return summary_result


def main_spark(task_single, para_list, multiprocess_nums=600):
    multiprocess_nums = min(len(para_list), multiprocess_nums, 600)
    if multiprocess_nums > 1:
        from xquant.compute.sparkmr import Configuration
        from xquant.compute.sparkmr import Job
        config = Configuration()
        config.set_app_name(f'sparkMain_{int(time.time())}')
        config.set_dst_dir(f'011668/sparkMain/{int(time.time())}')
        config.set_env_dir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config.set_executor_instances(str(multiprocess_nums))
        config.set_executor_memory('4G')
        job = Job(config, 'Overwrite')
        job.add_tasks(para_list)
        job.set_func(task_single)
        job.start()
    else:
        for para in para_list:
            task_single('', para)
