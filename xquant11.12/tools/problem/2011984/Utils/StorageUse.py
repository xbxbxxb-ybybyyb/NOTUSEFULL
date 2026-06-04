import os
import pandas as pd


def main():
    # print_memory()
    print_file_nums()


def check_memory(path, style='M'):
    i = 0
    for dir_path, dirname, filename in os.walk(path):
        for ii in filename:
            i += os.path.getsize(os.path.join(dir_path, ii))
    if style == 'M':
        memory = i / 1024. / 1024.
    else:
        memory = i / 1024. / 1024./ 1024.
    return memory


def print_memory():
    father_dir = '/data/user/011668/'
    dirs = os.listdir(father_dir)
    dir_save_dict = {}
    for single_dir in dirs:
        abs_path = father_dir + single_dir
        mem = check_memory(abs_path, 'G')
        dir_save_dict.update({single_dir: mem})
        print(f'{single_dir}: {round(mem, 4)} GB')
    dir_save_series = pd.Series(dir_save_dict)
    print(f'Total: {dir_save_series.sum()} GB')


def check_file_nums(path):
    count_dir, count_file = 0, 0
    root_res = {}
    for root, dirs, files in os.walk(path):
        count_dir += len(dirs)
        count_file += len(files)
        root_res.update({root: [len(dirs), len(files)]})
    return count_dir, count_file, root_res


def resolve_root_res(abs_path, root_res, n=1):
    # 分解几级目录
    root_list = []
    for path, res_r in root_res.items():
        path1 = path.replace(abs_path, '').lstrip('/')
        if path1 == '':
            continue
        path_n = path1.split('/')
        res_r += path_n
        root_list.append(res_r)
    root_df = pd.DataFrame(root_list)
    root_df1 = root_df.groupby(list(range(2, 2 + n))).sum().sort_values(by=1, ascending=False)
    if n > 1:
        root_df1.index = [os.path.join(*x) for x in root_df1.index]
    return root_df1


def print_file_nums():
    father_dir = '/data/user/011668'
    dirs = os.listdir(father_dir)
    count_dir_sum, count_file_sum = len(dirs), 0
    for single_dir in dirs:
        abs_path = os.path.join(father_dir, single_dir)
        count_dir, count_file, root_res = check_file_nums(abs_path)
        count_dir_sum += count_dir
        count_file_sum += count_file
        print('=' * 150)
        print_format(abs_path, count_dir, count_file)
        if count_dir + count_file > 10000:
            sub_res = resolve_root_res(abs_path, root_res, n=1)
            for i in sub_res.index:
                if sub_res.loc[i, 0] + sub_res.loc[i, 1] > 10000:
                    print('   ' + '-' * 120)
                    print_format(f'   .../{i}', sub_res.loc[i, 0], sub_res.loc[i, 1])
                    sub_res2 = resolve_root_res(abs_path, root_res, n=2)
                    sub_res2 = sub_res2.loc[[x for x in sub_res2.index if x.startswith(i)]]
                    for j in sub_res2.index:
                        if sub_res2.loc[j, 0] + sub_res2.loc[j, 1] > 10000:
                            print_format(f'      .../{i}/{j}', sub_res2.loc[j, 0], sub_res2.loc[j, 1])
    print('=' * 150)
    print(f'汇总 {father_dir}   文件夹个数为：{count_dir_sum}，文件个数为：{count_file_sum}')


def print_format(str1, num1, num2, total_len=100):
    str2 = f'文件夹个数为：{num1}'
    str3 = f'文件个数为：{num2}'
    str2 = str2 + ' ' * (14 - len(str2))
    str1 = str1 + ' ' * (total_len - len(str1) - len(str2))
    print(f'{str1}{str2}{str3}')


if __name__ == '__main__':
    main()
