import xfactor.runner.BasicRunner as Runner

'''
    不限制因子个数，不限制时间跨度

示例场景：
    1、业务人员本地研究时，计算某个因子一段时间的因子值
    2、因子入库或者批量计算
'''

'''
    $$$$$日频因子示例$$$

    factor_name_list: 因子名称列表
    start_date、end_date： 计算起止日期，可以为非交易日
    output_factor_lib： 输出因子库路径。若该路径下已经有指定因子的数据文件，则会追加
    save: 是否保存。为True时才会将结果保存为因子库(可以保存至自己的目录，个人不要保存到正式因子库)。
          不论save的取值，run()方法都会返回计算结果
    options: 相关额外设置，
            calc.num_cpus： 因子计算的并行度，若不设置或者设置为1，则将串行计算，可用来调试
'''
res = Runner.run(factor_name_list=["SampleDayFactor"], start_date=20200801, end_date=20200805,
                 output_factor_lib="/data/user/012872/x_day_lib/", save=False, options={"calc.num_cpus": 16})

'''
    最精简的使用方法，未设置calc.num_cpus，为串行计算
'''
# res = Runner.run(factor_name_list=["SampleDayFactor"], start_date=20140601, end_date=20200801)


'''
    $$$$fix因子计算示例$$$$
    其中，fix_times可以不传，或者传[], 表示计算所有7个时间点，同日频因子调用方式
    或者诸如：fix_times=["1000", "1030", "1100", "1300", "1330", "1400", "1430"]
'''
# res = Runner.run(factor_name_list=["SampleFixFactor"], start_date=20140601, end_date=20200801,
#                  output_factor_lib="/data/user/012872/x_day_lib/", save=False,
#                  options={"calc.num_cpus": 16})
# print(res)
