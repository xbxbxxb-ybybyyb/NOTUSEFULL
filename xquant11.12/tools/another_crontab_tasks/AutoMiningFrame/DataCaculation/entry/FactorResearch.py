import datetime as dt
import re, os, time, json, itertools
from AutoMiningFrame.DataCaculation.entry.FactorCalcBatch import calc_per_factor_by_file, \
    gen_factor_module, calc_factors_by_config
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
from AutoMiningFrame.FactorBacktest.TickFactorBacktest import FactorBacktest
import pandas as pd
from pandas.testing import assert_frame_equal
import numpy as np

# from FactorAutoMining.entry.factor_automining import AutoMining
# from FactorBacktest.entry.factor_backtest import FactorBacktest


def check_factor_data_nan_percent(factor_data, factor_names, nan_threshold=0.2):
    factor_data['Date1'] = factor_data['timestamp'].astype(str).apply(lambda x: x[:10])
    for factor_name in factor_names:
        check_nan_perct = factor_data.groupby('Date1')[factor_name].agg('count') / factor_data.groupby('Date1')['timestamp'].agg('count')
        #需要排除的天
        check_res = check_nan_perct[check_nan_perct<nan_threshold].index.to_list()
        # nan值超过阈值的天 全天置位nan
        factor_data.loc[factor_data['Date1'].isin(check_res), factor_name] = np.nan
    del factor_data['Date1']
    return factor_data


# 接口1 因子计算接口+存储+评价+上传到元数据表+上传到因子评价表
def sys_factor_calc_batch(factor_name, file_path, target_securities, user_id, label_name, table_type='personal',
                          automining_formula=None, save_factor=True, study_scenario='stock', data_type='enhanced_tick',
                          factor_descrip={}):
    """

    :param factor_descrip: dict 因子描述
    :param data_type: enhanced_tick or trade
    :param study_scenario: stock or fund
    :param save_factor: True or False
    :param automining_formula:
    :param factor_name: str类型，def后定义的因子名
    :param file_path: str类型，因子dos文件路径
    :param target_securities: list类型，单标的支持str
    :param user_id: str类型，用户id，从该id个人库取标签数据数
    :param label_name: str类型，标签名
    :param table_type: str类型，'personal'或'public'。元数据保存至个人元数据表或公共元数据表
    :return:
    """
    fp = FactorProvider(userID=user_id)
    fb = FactorBacktest()
    # 标的支持一个也支持多个，多个的话 开始时间就是最早上市的那个票的 不影响结果
    if not isinstance(target_securities, list):
        target_securities = [target_securities]
    # 因子描述参数的输入格式必须是字典
    if not isinstance(factor_descrip, dict):
        raise Exception("factor_desccrip参数类型必须是字典(dict)")

    # 起止时间不开发 可以是从配置文件读取 结束时间为20220630 开始时间为标的的上市日期
    end_date = "20220630"
    start_date = '20000101'
    # step 1: 计算
    print("[SysCalc] 开始计算")
    scriptFactor, funcFactor, resFactor, res = calc_per_factor_by_file(factor_name=factor_name, file_path=file_path,
                                                                       start_date=start_date, end_date=end_date,
                                                                       target_securities=target_securities,
                                                                       automining_formula=automining_formula,
                                                                       study_scenario=study_scenario, 
                                                                       data_type=data_type)
    print("[SysCalc] 计算完成")
    lack = set(resFactor) - set(factor_descrip.keys())
    if len(lack) > 0:
        raise Exception(f"factor_descrip 参数缺少以下因子描述，请添加：{list(lack)}")
    # 检查因子结果 如果 每天的因子的数据是nan的比例超过20% 则当天全置nan
    res = check_factor_data_nan_percent(factor_data=res, factor_names=resFactor, nan_threshold=0.1)
    # step 2: 存储
    if save_factor:
        print("[SysCalc] 开始存储")
        fp.save_personal_data_to_dfs(res, factor_type='factor', data_type=data_type)
        print("[SysCalc] 存储成功")

    # step 3: 上传信息到元数据表
    print("[SysCalc] 开始上传信息到元数据表")
    # TODO 部分指标写死 后续有系统功能了就开放
    print(resFactor)
    for rse in resFactor:
        upload_values_dict = {
            'FactorName': rse,
            'LabelName': label_name,
            'FactorFomula': scriptFactor,
            'FactorAttribute': re.findall(re.compile(r'[(](.*?)[)]', re.S), funcFactor)[0],
            'FactorDescription': factor_descrip[rse],
            "AuthorComment": "作者评价",
            "FactorPath": file_path,
            "FactorAuthor": user_id,
            "DemandCategory": "大类需求",
            "DemandInstance": "需求实例",
        }
        fp.upload_factor_meta(upload_values_dict, table_type=table_type, to_sql=True)
    print("[SysCalc] 上传信息到元数据表完成")
    #
    # # step4: 因子评价
    print("[SysCalc] 开始因子评价")
    label_df = fp.load_public_data_from_dfs(symbol=target_securities, factor_list=label_name,
                                            start_time=start_date, end_time=end_date, factor_type='label',
                                            data_type=data_type)
    factor_df = res.set_index(['timestamp'])
    label_df = label_df.set_index(['timestamp'])
    factor_label_list = fb.prepare_factor_label_by_dataframe(factor_df=factor_df, label_df=label_df,
                                                             factor_name_list=resFactor, tagger_name_list=[label_name])
    # 如果因子与标签 为空的天数超过总天数30& 则评价结束
    # valid_dates_num = 0.3
    # date_length = len(set([i[:10] for i in factor_df.index.astype(str).to_list()]))
    # if len(factor_label_list)/date_length < (1-valid_dates_num):
    #     raise Exception("[SysCalc异常]因子与标签融合数据为空的天数超过 {}， 评价终止".format(valid_dates_num))
    analysis_res = fb.test_all_factor(factor_label_list, label=label_name)
    print("[SysCalc] 因子评价完成")

    # # step 5: 因子评价指标入库
    print("[SysCalc] 因子评价指标开始入库")
    analysis_res = analysis_res[analysis_res['test_factor'].isin(resFactor)]
    analysis_res = analysis_res.groupby('test_factor').mean()
    analysis_res.insert(0, 'backtest_end_date', end_date)
    analysis_res.insert(0, 'backtest_start_date', start_date)
    analysis_res.insert(0, 'factor_fomula', scriptFactor)
    analysis_res.insert(0, 'user_id', user_id)
    analysis_res.reset_index(inplace=True)
    fp.upload_factor_analysis_res(user_id, analysis_res, table_type='personal', to_sql=True)
    print("[SysCalc] 因子评价指标已存储")
    return analysis_res


def check_analysis_res(analysis_res):
    """
    校验回测指标
    :param analysis_res: 单因子分析结果，DataFrame。回测函数test_all_factor算出的结果，按照因子分组对回测指标求均值。demo如下
    :return:
    """
    """
    analysis_res demo：
      test_factor user_id                                      factor_fomula backtest_start_date backtest_end_date  
      0      testF3  016869  @state\ndef testF3(){\ntestF3 = rand(10.0,1)[0...            20220701          20220930       
    """
    # 入库条件
    # 条件1：rank_ic>0.03 normal_ic>0.03
    if abs(analysis_res['normal_ic'].values[0]) >= 0.03 and abs(analysis_res['rank_ic'].values[0]) >= 0.03:
        single_factor_check_res = True
    else:
        single_factor_check_res = False
    return single_factor_check_res


# 接口2 提交因子到公共库： 拉取行情数据对样本外数据作为依赖数据计算因子
def _sys_factor_publish_serial(file_path, factor_list, auto_factor_dict, security_id, user_id, label_name, study_scenario='stock',
                               data_type='enhanced_tick', factor_descrip={}):
    """

    :param file_path: str类型，因子dos文件路径
    :param factor_list: 因子列表，file_path里需包含这些因子
    :param auto_factor_dict: 因子字典。key是因子名，value是因子表达式。
    :param security_id: 标的
    :param user_id: 用户ID
    :param label: 标签
    :return:
    """
    fp = FactorProvider(userID=user_id)
    fb = FactorBacktest()
    if isinstance(security_id, str):
        security_id = [security_id]
        # 因子描述参数的输入格式必须是字典
        if not isinstance(factor_descrip, dict):
            raise Exception("factor_desccrip参数类型必须是字典(dict)")

    # 自动挖掘的结果 ，入参是一个字典 key为因子名 value为因子表达式
    if auto_factor_dict:
        file_path = "./factor_tmp"
        os.mkdir(file_path)
        factor_list = []
        for k, v in auto_factor_dict:
            factor_list.append(k)
            gen_factor_module(path=file_path, factor_name=k, factor_expression=v)

    # 计算任务的开始时间为20220701 结束时间为20220930
    start_date = "20220701"
    end_date = '20220930'
    # 串行发布因子

    for factor_name in factor_list:
        print("[SysPublish] =============================={}==============================".format(factor_name))
        # step1: 计算样本外的因子数据
        # TODO 自动因子挖掘提交的时候 提交一个字典 key：因子名 value
        print("[SysPublish] 开始计算")
        scriptFactor, funcFactor, resFactor, res = calc_per_factor_by_file(factor_name=factor_name, file_path=file_path,
                                                                           start_date=start_date, end_date=end_date,
                                                                           target_securities=security_id,
                                                                           study_scenario=study_scenario,
                                                                           data_type=data_type)
        lack = set(resFactor) - set(factor_descrip.keys())
        if len(lack) > 0:
            raise Exception(f"factor_descrip 参数缺少以下因子描述，请添加：{list(lack)}")
        current_factor_list = fp.load_info_from_dfs(factor_type='factor', source_type='public', data_type=data_type)
        for f in resFactor:
            if f in current_factor_list:
                raise Exception(f"公共库已存在同名因子{f}，请更换因子名。")
        print("[SysPublish] 计算完成")

        # step2: 进行单因子评价，并根据阈值统计结果
        print("[SysPublish] 开始因子评价")
        label_df = fp.load_public_data_from_dfs(symbol=security_id, factor_list=label_name, start_time=start_date,
                                                end_time=end_date, factor_type='label', data_type=data_type)
        factor_df = res.set_index(['timestamp'])
        label_df = label_df.set_index(['timestamp'])
        factor_label_list = fb.prepare_factor_label_by_dataframe(factor_df=factor_df, label_df=label_df,
                                                                 factor_name_list=resFactor,
                                                                 tagger_name_list=[label_name])
        # 如果因子与标签 为空的天数超过总天数30& 则评价结束
        valid_dates_num = 0.3
        date_length = len(set([i[:10] for i in factor_df.index.astype(str).to_list()]))

        if len(factor_label_list) / date_length < (1 - valid_dates_num):
            raise Exception("[SysCalc异常]因子与标签融合数据为空的天数超过 {}， 评价终止".format(valid_dates_num))
        analysis_res = fb.test_all_factor(factor_label_list, label=label_name)
        analysis_res = analysis_res[analysis_res['test_factor'].isin(resFactor)]
        analysis_res = analysis_res.groupby('test_factor').mean()
        analysis_res.insert(0, 'backtest_end_date', end_date)
        analysis_res.insert(0, 'backtest_start_date', start_date)
        analysis_res.insert(0, 'factor_fomula', scriptFactor)
        analysis_res.insert(0, 'user_id', user_id)
        analysis_res.reset_index(inplace=True)
        print("[SysPublish] 因子评价完成")

        # step3: 进行多因子相关性评价,
        print("[SysPublish] 因子相关性计算开始")

        current_factor_data = fp.load_public_data_from_dfs(symbol=security_id, factor_list=current_factor_list,
                                                           start_time=start_date, end_time=end_date,
                                                           factor_type='factor', data_type=data_type)
        public_meta_tbl = fp.load_factor_meta(user_id, table_type='public', data_type=data_type)
        current_factor_list_by_label = public_meta_tbl[public_meta_tbl['LabelName'] == label_name]['FactorName'].to_list()
        current_factor_data = current_factor_data[current_factor_list_by_label]

        if current_factor_data.empty:
            print("[SysPublish] 该因子为因子库中第一个因子，跳过多因子评价环节")
            for factor in resFactor:
                analysis_res_per_return = analysis_res[analysis_res['test_factor'] == factor]
                single_factor_check_res = check_analysis_res(analysis_res_per_return)

                if single_factor_check_res:
                    print(f"[SysPublish] {factor} 因子符合入库标准，正在入库..")
                    scriptFactor, funcFactor, resFactor, res = calc_per_factor_by_file(factor_name=factor_name,
                                                                                       file_path=file_path,
                                                                                       start_date="20000101", end_date=end_date,
                                                                                       target_securities=security_id,
                                                                                       study_scenario=study_scenario,
                                                                                       data_type=data_type)
                    res = res[['timestamp', 'M_HTSCSecurityID', 'R_HTSCSecurityID', factor]]
                    fp.save_public_data_to_dfs(res, factor_type='factor')
                    print(f"[SysPublish] {factor} 因子符合入库标准，入库完成..")

                    print(f"[SysPublish] {factor} 开始上传元数据和评价结果")
                    # TODO 部分指标写死 后续有系统功能了就开放
                    upload_values_dict = {
                        'FactorName': factor,
                        'LabelName': label_name,
                        'FactorFomula': scriptFactor,
                        'FactorAttribute': re.findall(re.compile(r'[(](.*?)[)]', re.S), funcFactor)[0],
                        'FactorDescription': factor_descrip[factor],
                        "AuthorComment": "作者评价",
                        "FactorPath": file_path,
                        "FactorAuthor": user_id,
                        "DemandCategory": "大类需求",
                        "DemandInstance": "需求实例",
                    }
                    fp.upload_factor_meta(upload_values_dict, table_type='public', to_sql=True)
                    fp.upload_factor_analysis_res(user_id, analysis_res, table_type='public', to_sql=True)
                    print(f"[SysPublish] {factor} 上传元数据和评价结果完成")
                else:
                    print("[SysPublish]因子发布失败，原因是单因子评价指标不过关")
        else:
            corr_threshold = 0.8
            factor_df.reset_index(inplace=True)
            factor_df.replace([np.inf, -np.inf], np.NaN, inplace=True)
            current_factor_data.replace([np.inf, -np.inf], np.NaN, inplace=True)
            current_factor_data.dropna(axis=1, how='all', inplace=True)
            nan_row = current_factor_data.iloc[:, 3:].isna().all(1)
            current_factor_data = current_factor_data[~nan_row]
            for factor in resFactor:
                factor_df_uniquefactor = factor_df[['timestamp', 'M_HTSCSecurityID', 'R_HTSCSecurityID', factor]]
                factor_df_uniquefactor = factor_df_uniquefactor[factor_df_uniquefactor[factor].notna()]
                all_factors_data = pd.merge(current_factor_data, factor_df_uniquefactor, on=['timestamp', 'M_HTSCSecurityID', 'R_HTSCSecurityID'])
                # 按天求ic 然后求平均
                all_factors_data['Date1'] = all_factors_data['timestamp'].astype(str).apply(lambda x: x[:10])
                res = all_factors_data.groupby('Date1').corr().loc[:, factor].reset_index()
                #去掉待测因子本身
                res = res[res['level_1'].isin(current_factor_data.columns[3:])]
                res = res.groupby('level_1').mean()[factor]
                del all_factors_data['Date1']
                print(f"[SysPublish] {factor} 和库中因子相关性如下")
                print(res[res > corr_threshold])
                #res = all_factors_data[current_factor_data.columns[3:]].apply(lambda x: x.corr(all_factors_data[factor]), axis=0)
                nan_corr = res[res.isna()].values
                if len(nan_corr) > 0:
                    print(f"[SysPublish] 存在因子相关性为nan：{factor} --> {nan_corr}")
                res.fillna(1, inplace=True)
                non_conform_num = sum(abs(res) > corr_threshold)
                if non_conform_num>0:
                    muti_factor_corr_res = False
                else:
                    muti_factor_corr_res = True
                print(f"[SysPublish] {factor} 因子相关性计算完成")

                # step4: 根据评价结果，符合因子入库标准则计算全量因子数据并入到公共因子库中
                # step5: 符合入库流程则提交因子元数据到公共元数据表中，提交评价结果到公共评价表中
                analysis_res_per_return = analysis_res[analysis_res['test_factor'] == factor]
                print(f"[SysPublish]因子{factor}评价指标如下")
                print(analysis_res_per_return[['test_factor', 'normal_ic', 'rank_ic', 'backtest_start_date', 'backtest_end_date']])
                single_factor_check_res = check_analysis_res(analysis_res_per_return)
                if single_factor_check_res and muti_factor_corr_res:
                    print(f"[SysPublish] {factor} 因子符合入库标准，正在入库..")
                    scriptFactor, funcFactor, resFactor, res = calc_per_factor_by_file(factor_name=factor_name,
                                                                                       file_path=file_path,
                                                                                       start_date="20000101", end_date=end_date,
                                                                                       target_securities=security_id,
                                                                                       study_scenario=study_scenario,
                                                                                       data_type=data_type)
                    res = res[['timestamp', 'M_HTSCSecurityID', 'R_HTSCSecurityID', factor]]
                    # 首先判断下库中是否有同名因子，若没有则入库 若有 则提示用户有同名因子 和对应的标签信息，
                    # 并且和库中同名因子数据进行对比，  如果完全一致 则告知用户已经有了 如果不一致 提示用户改名
                    fac_public_list = fp.load_info_from_dfs('factor', source_type='public', data_type=data_type)
                    if factor in fac_public_list:
                        public_cur_factor_data = fp.load_public_data_from_dfs(symbol=security_id,
                                                                              factor_list=[factor],
                                                                              start_time=start_date, end_time=end_date,
                                                                              factor_type='factor', data_type=data_type)[['timestamp', "M_HTSCSecurityID", factor]]
                        wait_upload_res = res[['timestamp', "M_HTSCSecurityID", factor]]
                        try:
                            assert_frame_equal(public_cur_factor_data, wait_upload_res)
                        except Exception as e:
                            print(e)
                            raise Exception("警告！库中存在同名因子 并且因子值和正在提交的不一致，请确认因子逻辑是否有变动，如果有请改名")

                    else:
                        fp.save_public_data_to_dfs(res, factor_type='factor', data_type=data_type)
                    print(f"[SysPublish] {factor} 因子符合入库标准，入库完成..")

                    print(f"[SysPublish] {factor} 开始上传元数据和评价结果")
                    # TODO 部分指标写死 后续有系统功能了就开放
                    upload_values_dict = {
                        'FactorName': factor,
                        'LabelName': label_name,
                        'FactorFomula': scriptFactor,
                        'FactorAttribute': re.findall(re.compile(r'[(](.*?)[)]', re.S), funcFactor)[0],
                        'FactorDescription': factor_descrip[factor],
                        "AuthorComment": "作者评价",
                        "FactorPath": file_path,
                        "FactorAuthor": user_id,
                        "DemandCategory": "大类需求",
                        "DemandInstance": "需求实例",
                    }
                    fp.upload_factor_meta(upload_values_dict, table_type='public', to_sql=True)
                    fp.upload_factor_analysis_res(user_id, analysis_res_per_return, table_type='public', to_sql=True)
                    print(f"[SysPublish] {factor} 上传元数据和评价结果完成")
                # step6: 评级不通过，返回评价结果
                else:
                    if not single_factor_check_res:
                        print("[SysPublish]因子发布失败，原因是单因子评价指标不过关")
                    if not muti_factor_corr_res:
                        print("[SysPublish]因子发布失败，原因是与库中因子相关性不达标，阈值为{}，实际有{}个因子相关性高于阈值或因子相关性为nan".format(corr_threshold, non_conform_num))


def sys_factor_publish_serial(security_id, user_id, label_name, file_path=None, factor_list=None, auto_factor_dict=None,
                              study_scenario='stock', data_type='enhanced_tick', factor_descrip={}):
    """
    :param factor_descrip: dict 因子描述
    :param data_type: 增强tick（enhanced_tick） 逐笔数据（trade）
    :param study_scenario: 研究场景 stock(股票) or fund(基金)
    :param file_path: str 因子文件路径
    :param factor_list: list 因子列表
    :param auto_factor_dict:
    :param security_id: str 标的
    :param user_id: str, 用户工号
    :param label_name: str 标签名
    :return:
    """
    fp = FactorProvider(userID=user_id)
    if not((file_path and factor_list and not auto_factor_dict) or (auto_factor_dict and not file_path and not factor_list)):
        script = """
        file_path、factor_list、auto_factor_dict 三个参数组合需为：
        传入file_path、factor_list，不传auto_factor_dict；
        或传入auto_factor_dict，不传file_path、factor_list
        """
        raise Exception(script)
    if auto_factor_dict:
        factor_list = list(auto_factor_dict.keys())
    if not isinstance(factor_list, list):
        factor_list = [factor_list]

    # step1 ： 循环检查因子发布状态表 如果检测到有其他因子正在入库 则 等待 用户可终止
    while True:
        tag = fp.load_factor_upload_status(data_type=data_type)
        if tag:
            break
        else:
            print("[FactorResearch] " + str(dt.datetime.now()) + " 其他因子正在入库，30s 后重试...")
            time.sleep(30)

    # step2: 检查通过 未发现有其他用户正在提交 可以启动因子发布
    # step3: 首先向因子发布状态表中插入一条数据 状态码1 表示开始发布 会阻塞其他用户的提交任务
    for factor in factor_list:
        fp.insert_factor_upload_status(factor_name=factor, user_id=user_id, status=1, data_type=data_type)
    try:
        _sys_factor_publish_serial(file_path, factor_list, auto_factor_dict, security_id, user_id, label_name,
                                   study_scenario, data_type, factor_descrip)
    except Exception as e:
        # 如果发布异常 附状态码2 结束
        for factor in factor_list:
            fp.insert_factor_upload_status(factor_name=factor, user_id=user_id, status=2, data_type=data_type)
        raise Exception(e)
    # 发布成功则附状态码3
    for factor in factor_list:
        fp.insert_factor_upload_status(factor_name=factor, user_id=user_id, status=3, data_type=data_type)
    return


# 接口3：超参数调优接口
# 作用：用户传文件路径和因子名 配合多个自定义参数组合组成的字典 框架计算每一个组合对应的 因子值 以及评价结果
def factor_custom_param_tuning(factor_name, file_path, label_name, target_securities, user_id, custom_params_dict={},
                               study_scenario='stock', data_type='enhanced_tick'):
    fp = FactorProvider(userID=user_id)
    fb = FactorBacktest()
    # 标的支持一个也支持多个，多个的话 开始时间就是最早上市的那个票的 不影响结果
    if not isinstance(target_securities, list):
        target_securities = [target_securities]

    # 起止时间不开放 可以是从配置文件读取 结束时间为20220630 开始时间为标的的上市日期
    end_date = "20220630"
    start_date = '20000101'
    # step 0: 创建配置文件
    config_content = {factor_name: []}
    def params_product(args):
        return itertools.product(*args)
    params_name_list = list(custom_params_dict.keys())
    for i in params_product(tuple(custom_params_dict.values())):
        temp_dict = {}
        for index in range(len(params_name_list)):
            temp_dict[params_name_list[index]] = i[index]
        config_content[factor_name].append(temp_dict)

    config_path = os.path.join(file_path, "temp_config.json")
    with open(config_path, "w") as f:
        f.write(json.dumps(config_content))
    # step 1: 计算
    print("[ParamTuning] 开始计算")
    res, resFactor, = calc_factors_by_config(config_path, file_path, start_date, end_date, target_securities,
                                             return_mode='show', study_scenario=study_scenario, data_type=data_type)
    print("[ParamTuning] 计算完成")

    # step2: 回测
    res = check_factor_data_nan_percent(factor_data=res, factor_names=resFactor, nan_threshold=0.1)
    print("[ParamTuning] 开始因子评价")
    label_df = fp.load_public_data_from_dfs(symbol=target_securities, factor_list=label_name,
                                            start_time=start_date, end_time=end_date, factor_type='label',
                                            data_type=data_type)
    factor_df = res.set_index(['timestamp'])
    label_df = label_df.set_index(['timestamp'])
    factor_label_list = fb.prepare_factor_label_by_dataframe(factor_df=factor_df, label_df=label_df,
                                                             factor_name_list=resFactor, tagger_name_list=[label_name])

    analysis_res = fb.test_all_factor(factor_label_list, label=label_name)
    analysis_res = analysis_res[analysis_res['test_factor'].isin(resFactor)]
    analysis_res = analysis_res.groupby('test_factor').mean()
    analysis_res.insert(0, 'backtest_end_date', end_date)
    analysis_res.insert(0, 'backtest_start_date', start_date)
    analysis_res.insert(0, 'user_id', user_id)
    analysis_res.reset_index(inplace=True)
    print("[ParamTuning] 因子评价完成")
    return analysis_res

if __name__ == "__main__":
    factor_name = "testF4"
    file_path = "/tmp/pycharm_project_609/DolphinDB"
    target_securities = ['688599.SH']
    user_id = '016869'
    label_name = 'labelEQtriplebarriertaggertypeEQmidpricedsizeEQ300'
    # res = sys_factor_calc_batch(factor_name, file_path, target_securities, user_id, label_name, table_type='personal')
    # print(res)

    sys_factor_publish_serial(security_id=target_securities, user_id=user_id, label_name=label_name,
                              file_path=file_path, factor_list=factor_name, auto_factor_dict=None)

    factor_custom_param_tuning(factor_name, file_path, label_name, target_securities, user_id, custom_params_dict={})