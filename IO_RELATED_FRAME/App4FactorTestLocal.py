import xfactor.runner.BasicRunner as Runner
import xfactor.test.TesterWithRay as Tester
import time

# 本地检测模式

# 计算因子值，TestDay
factor_name = "SampleDayFactor"
# 请研究员设置本地路径，用于存放日频因子本地检测报告
report_address = r"/data/user/000000/"
start = time.time()
# 计算时间开始时间前移一段时间
res = Runner.run([factor_name], 20140601, 20191231, options={"calc.num_cpus": 18})
test_result = Tester.test(20160101, 20191231, res, calc_num=18, local=True, pdf_address=report_address)
print(test_result)
print("total cost time:", time.time() - start)
