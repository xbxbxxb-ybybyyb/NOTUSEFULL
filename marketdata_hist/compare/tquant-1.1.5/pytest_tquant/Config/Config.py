import os
import base64


class Config:
    def __init__(self):
        """
        初始化
        """
        self.sso_host = 'http://168.63.66.97:8080'
        self.username = '013320'
        # self.password = base64.b64decode('工号密码的base64编码')
        path_dir = str(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
        self.xml_report_path = path_dir + '/pytestReport/xml'
        self.html_report_path = path_dir + '/pytestReport/html'
        self.html_report_file = path_dir + '/pytestReport/report.html'


