from xquant.factordata import FactorData


def createLibrary(libraryName, factorList):
    fd = FactorData()

    try:
        fd.create_factor_library(libraryName, "T+0")
    except Exception as e:
        print(e)

    for factor in factorList:
        try:
            fd.add_factor(libraryName, [factor])
        except Exception as e:
            print(e)

if __name__ == "__main__":

    signalLibraryList = ["Albest20221001SHOrder1Signals"]
    freq_list = ["036", "147", "258"]
        
    signalLibraryList += ["Albest20221001SHOrder{}Signals".format(freq) for freq in freq_list]
    signalColumns =  ["timestamp", "ticktime", "prediction1minLong", "prediction1minShort", "prediction2minLong", "prediction2minShort", "prediction5minLong", "prediction5minShort",
                      "tag1minLong", "tag1minShort", "tag2minLong", "tag2minShort", "tag5minLong", "tag5minShort"
                      ]

    factorNames = signalColumns
    for signalLibrary in signalLibraryList:
        createLibrary(signalLibrary, factorNames)