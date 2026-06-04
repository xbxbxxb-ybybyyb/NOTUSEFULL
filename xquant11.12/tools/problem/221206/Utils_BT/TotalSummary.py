import os, shutil
import zipfile
import pandas as pd
from xquant.pyfile import Pyfile
from functools import reduce


def zip_file(source_path, save_path, file_name):
    """
    将文件夹下的文件保存到zip文件中。
    :param source_path: 待存文件夹
    :param save_path: 存储路径
    :return:
    """
    save_path = os.path.realpath(save_path)
    print(save_path)
    if not os.path.exists(save_path):
        os.mkdir(save_path)
    file_list = []
    new_zip = zipfile.ZipFile(save_path + "/" + file_name + '.zip', 'w')
    for dir_path, dir_names, file_names in os.walk(source_path):
        for filename in file_names:
            file_list.append(os.path.join(dir_path, filename))
    count = 0
    for tar in file_list:
        # tar为写入的文件，tar[len(filePath)]为保存的文件名        
        # for pattern in alpha_code:
            # if re.search(pattern, tar):
        # print(tar)
        new_zip.write(tar, tar[len(source_path):])
        count = count + 1
    print ("num:", count)
    new_zip.close()
    print('save to :', save_path)


def remove_relative(path):
    if 'SHARE_21' in path:
        path = path.replace('SHARE_21', '$21')
    elif '$21' in path:
        pass
    else:
        while path[0] == '/':
            path = path[1:]
        index = path.index('/')
        path = path[index + 1:]
    return path


def summary(root, dst, suffix, overwrite=False, name='result_all.xlsx'):
    # CHECK
    source_path = '{}/sources/{}'.format(dst, suffix)
    result_path = '{}/results/{}'.format(dst, suffix)
    zipped_path = '{}/zipped/{}'.format(dst, suffix)

    if overwrite:
        shutil.rmtree(source_path, ignore_errors=True)
        shutil.rmtree(result_path, ignore_errors=True)
        shutil.rmtree(zipped_path, ignore_errors=True)

    if not os.path.exists(source_path):
        os.makedirs(source_path)
    else:
        raise Exception('Path already exists: {}'.format(source_path))

    if not os.path.exists(result_path):
        os.makedirs(result_path)
    else:
        raise Exception('Path already exists: {}'.format(result_path))

    # TRANSFER
    py = Pyfile()
    root = remove_relative(root)
    py.download(source_path, root)
    
    # SUMMARIZE
    output_name = 'TotalSummary.xlsx'
    output_filepath = os.path.join(result_path, output_name)
    summary_list = []
    saved_dict = {}
    wratio_dict = {}
    daily_results = []

    symbols = os.listdir(source_path)
    for symbol in symbols:
        file = os.path.join(source_path, symbol, name)
        if not os.path.exists(file):
            continue
        shutil.copyfile(file, os.path.join(result_path, symbol + '.xlsx'))
        summary_df = pd.read_excel(file, 'summary')
        summary_list.append(summary_df)
        daily_df = pd.read_excel(file, 'daily')
        daily_df['Date'] = daily_df['Date']
        daily_df.set_index('Date', inplace=True)

        saved_single = daily_df['Saved']
        saved_dict.update({symbol: saved_single})

        wratio_single = daily_df["WRatio"]
        wratio_dict.update({symbol: wratio_single})

        result = pd.DataFrame(daily_df, columns=['Saved'])
        result['AbsAccQty'] = abs(daily_df['Quantity'])
        result['AbsTargetQty'] = abs(summary_df.loc[0, 'TargetQty'])
        result['AbsTargetMV'] = abs(summary_df.loc[0, 'TargetMV'])
        result['AbsExecutedMV'] = abs(daily_df['Quantity'] * daily_df['VWAP'])
        daily_results.append(result)
    # Sheet Summary
    summary = pd.concat(summary_list)
    # Sheet Saved
    saved = pd.concat(saved_dict, axis=1)
    saved.fillna(0, inplace=True)
    saved['Total'] = saved.sum(axis=1)
    # Sheet WRatio
    wratio = pd.concat(wratio_dict, axis=1)
    wratio.fillna(0, inplace=True)
    # Sheet Result
    result = reduce(lambda x, y: x.add(y, fill_value=0), daily_results)
    result = result[['AbsTargetQty', 'AbsAccQty', 'AbsTargetMV', 'AbsExecutedMV', 'Saved']]
    result['FinishRate'] = result['AbsAccQty'] / result['AbsTargetQty']
    result['SavedRate'] = result['Saved'] / result['AbsExecutedMV']

    # save
    writer = pd.ExcelWriter(output_filepath, engine='xlsxwriter')
    summary.to_excel(writer, sheet_name='Summary', index=False)
    saved.to_excel(writer, sheet_name='Saved', index=True)
    wratio.to_excel(writer, sheet_name='WRatio', index=True)
    result.to_excel(writer, sheet_name='Result', index=True)
    writer.save()
    
    # TO GPU WEB
    if not os.path.exists(zipped_path):
        os.makedirs(zipped_path)
    zip_file(source_path, zipped_path, 'source')
    zip_file(result_path, zipped_path, 'result')
