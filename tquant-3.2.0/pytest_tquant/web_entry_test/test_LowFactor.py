import subprocess
import os
from time import sleep
import pytest

@pytest.mark.skip
class TestWebCalculationDevelopLow(object):
    def setLogs(self, logFile, testFile):
        print("aaaaa")
        Stdout = subprocess.PIPE
        Stderr = subprocess.PIPE
        testFile = "/opt/anaconda3/lib/python3.6/site-packages/pytest_tquant/web_entry_test/" + testFile
        command1 = "nohup python3 " + testFile + " &"
        operateResult = False

        val = os.system(command1)
        popen = subprocess.Popen(["tail", "-f", logFile], stdout=Stdout, stderr=Stderr)
        while True:
            Line = str(popen.stdout.readline().strip())
            # print(line)
            if Line:
                if ("produceTime" in Line):
                    print(Line)
                    operateResult = True
                    break
        popen.terminate()
        return operateResult

    def getIformation(self, logFile, subStr1, subStr2):
        ErrorLine = ""
        dataList = []
        Logs = open(logFile)
        LogContent = Logs.readlines()
        for line in LogContent:
            if (subStr1 in line):
                index = line.find(subStr1)
                start = index + len(subStr1)
                end = start + 8
                data = line[start:end]
                dataList.append(data)
            if (subStr2 in line):
                ErrorLine = line
        Logs.close()
        return ErrorLine, dataList

    def test_web_calculation_develop_low(self):
        operateResult = self.setLogs("nohup.out", "test_web_calculation_develop_low.py")
        #operateResult = self.setLogs()
        if(operateResult==True):
            ErrorLine, dataList = self.getIformation("nohup.out", "The calc function has error !!: date:", "{'testnsw': [")
            os.system("rm -rf nohup.out")
            if(ErrorLine != ""):
                missDataList = []
                for data in dataList:
                    if (data not in ErrorLine):
                        missDataList.append(data)
                assert len(missDataList) == 0
            else:
                assert True
        else:
            assert False


@pytest.mark.skip
class TestWebBacktestDevelopUser(object):
    def setLogs(self, logFile, testFile):
        Stdout = subprocess.PIPE
        Stderr = subprocess.PIPE
        operateResult = False
        testFile = "/opt/anaconda3/lib/python3.6/site-packages/pytest_tquant/web_entry_test/" + testFile
        command1 = "nohup python3 " + testFile + " &"

        val = os.system(command1)
        sleep(5)
        command2 = "grep -i 'produceTime' " + logFile
        while True:
            line = subprocess.getoutput(command2)
            # print(line)
            if line:
                if ("produceTime" in line):
                    operateResult = True
                    break
        return operateResult

    def getIformation(self, logFile, subStr):
        LogContent = open(logFile).readlines()
        checkResult = False
        for line in LogContent:
            #subStr = "* Finished - testnsw *"
            if (subStr in line):
                checkResult = True
                break
        return checkResult

    def test_web_backtest_develop_user(self):
        operateResult = self.setLogs("nohup.out", "test_web_backtest_develop_user.py")
        if(operateResult == True):
            checkResult = self.getIformation("nohup.out", "* Finished - testnsw *")
            os.system("rm -rf nohup.out")
            if(checkResult== True):
                Pdfcheck = os.system("ls -al /home/appadmin/testnsw/*.pdf")
                os.system("rm -rf /home/appadmin/testnsw/*.pdf")
                if (Pdfcheck == 0):
                    assert True
                else:
                    print("File not exists!")
                    assert False
            else:
                print("test_web_backtest_develop_user.py run fail")
                assert False
        else:
            assert False


@pytest.mark.skip
class TestWebBacktestDevelopSys(object):
    def setLogs(self, logFile, testFile):
        #logFile = "nohup.out"
        Stdout = subprocess.PIPE
        Stderr = subprocess.PIPE
        #testFile = "test_web_backtest_develop_sys.py"
        operateResult = False
        testFile = "/opt/anaconda3/lib/python3.6/site-packages/pytest_tquant/web_entry_test/" + testFile
        command1 = "nohup python3 " + testFile + " &"

        val = os.system(command1)
        sleep(5)
        command2 = "grep -i 'produceTime' " + logFile
        while True:
            line = subprocess.getoutput(command2)
            # print(line)
            if line:
                if ("produceTime" in line):
                    operateResult = True
                    break
        return operateResult

    def getIformation(self, logFile, subStr):
        LogContent = open(logFile).readlines()
        checkResult = False
        for line in LogContent:
            #subStr = "* Finished - testnsw *"
            if (subStr in line):
                checkResult = True
                break
        return checkResult

    def test_web_backtest_develop_user(self):
        operateResult = self.setLogs("nohup.out", "test_web_backtest_develop_sys.py")
        if(operateResult == True):
            checkResult = self.getIformation("nohup.out", "* Finished - testnsw *")
            os.system("rm -rf nohup.out")
            if(checkResult== True):
                Pdfcheck = os.system("ls -al /home/appadmin/testnsw/*.pdf")
                os.system("rm -rf /home/appadmin/testnsw/*.pdf")
                if (Pdfcheck == 0):
                    assert True
                else:
                    print("File not exists!")
                    assert False
            else:
                print("test_web_backtest_develop_user.py run fail")
                assert False
        else:
            assert False