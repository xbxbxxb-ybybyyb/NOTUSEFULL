import subprocess
import os
from time import sleep

class TestManageLabelData(object):
	def setLogs(self, logFile, testFile):
		Stdout = subprocess.PIPE
		Stderr = subprocess.PIPE
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

	def getIformation(self, logFile, subStr1):
		ErrorLine = ""
		dataList = []
		checkResult= False
		Logs = open(logFile)
		LogContent = Logs.readlines()
		for line in LogContent:
			if (subStr1 in line):
				index = line.find(subStr1)
				checkResult= True
			if(checkResult == True):
				break
		Logs.close()
		return checkResult

	def test_manage_label_data(self):
		operateResult = self.setLogs("nohup.out", "test_manage_label_data.py")
		#operateResult = self.setLogs()
		if(operateResult==True):
			CheckResult = self.getIformation("nohup.out", "Label data has been stored successfully! HTSCSecurityID")
			os.system("rm -rf nohup.out")
			assert CheckResult
		else:
			assert False
			
			
class TestWebCalculationDevelopHigh(object):
	def setLogs(self, logFile, testFile):
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

	def test_web_calculation_develop_high(self):
		operateResult = self.setLogs("nohup.out", "test_web_calculation_develop_high.py")
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
			

class TestWebHfrefactorBacktest(object):
	def setLogs(self, logFile, testFile):
		#logFile = "nohup.out"
		Stdout = subprocess.PIPE
		Stderr = subprocess.PIPE
		#testFile = "test_web_backtest_develop_sys.py"
		operateResult = False
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

	def getIformation(self, logFile, subStr1):
		ErrorLine = ""
		dataList = []
		checkResult= False
		Logs = open(logFile)
		LogContent = Logs.readlines()
		for line in LogContent:
			if (subStr1 in line):
				index = line.find(subStr1)
				checkResult= True
			if(checkResult == True):
				break
		Logs.close()
		return checkResult

	def test_web_hfrefactor_backtest(self):
		operateResult = self.setLogs("nohup.out", "test_web_hfrefactor_backtest.py")
		if(operateResult == True):
			checkResult = self.getIformation("nohup.out", "=====发送kafka消息=======")
			os.system("rm -rf nohup.out")
			if(checkResult== True):
				assert True
			else:
				print("test_web_hfrefactor_backtest.py run fail")
				assert False
		else:
			assert False