import pytest
import os


def create_file(filename):
    """
    创建文件夹
    :param filename:文件名称后带上/
    :return:
    """
    path = filename[0:filename.rfind('/')]
    print(path)
    if not os.path.isdir(path):
        os.makedirs(path)
    else:
        pass


class RunTestSuit(object):

    def run_testcase(self, t_type='-v', test_path='test_case'):
        curPath = os.path.abspath(os.path.join(os.path.dirname(__file__), test_path))
        args = [t_type, curPath]
        pytest.main(args)

    def run_coverage(self, cov_path):
        # 覆盖率
        args = ['--cov=%s', '--cov-report=html' % cov_path]
        pytest.main(args)

    def get_report(self, test_path, html_report_file):
        # 生成测试报告
        reportPath = os.path.abspath(os.path.join(os.path.dirname(__file__), 'test_report', html_report_file))
        curPath = os.path.abspath(os.path.join(os.path.dirname(__file__), test_path))
        args = ['-s', curPath, '--html=%s' % reportPath]
        pytest.main(args)

    def upload_report(self, report_path):
        """
        上传测试报告
        :param report_path:报告路径
        :return:
        """
        tar_cmd = r'tar -cvf tquant-report.tar {}'.format(report_path)
        curl_cmd = r'curl ftp://168.8.2.60/013150/ -u "htzq:htzq" -T tquant-report.tar'
        os.system(tar_cmd)
        os.system(curl_cmd)

    def run_func(self):
        # 运行.py模块里面的某个函数
        os.system("pytest test_mod.py:: test_func")
        # 运行.py模块里面，测试类里面的某个方法
        os.system("pytest test_mod.py::TestClass::test_method")

    def run_version_case(self, test_path, tag):
        # 运行某一个版本的测试用例
        args = ['-s', test_path, '-m=%s' % tag]
        pytest.main(args)


if __name__ == "__main__":
    rs = RunTestSuit()
    path_dir = str(os.path.abspath(os.path.join(os.path.dirname(__file__))))
    test_file = path_dir + '/test_report/'
    create_file(test_file)
    rs.get_report('tquant_testcase', 'report.html')
    rs.upload_report(test_file)




