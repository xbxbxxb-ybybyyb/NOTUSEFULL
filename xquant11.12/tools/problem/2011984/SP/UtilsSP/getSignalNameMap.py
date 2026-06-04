import json


def getSignalNameMap(modelPath, regressionName):
    with open("/data/user/666888/SignalLibraryMap/SignalNameMap.json", "r") as f:
        signalNameMapDict = json.load(f)

    modelPath = modelPath.strip("/")
    regressionName = regressionName.strip("/")

    if modelPath in signalNameMapDict and regressionName in signalNameMapDict[modelPath]:
        signalNameMap = signalNameMapDict[modelPath][regressionName]
    else:
        signalNameMap = {
            "0": "1min",
            "1": "2min",
            "2": "5min",
        }

    return signalNameMap
