class TaskMeta:
    def __init__(self,
                 codeList,
                 startDate,
                 endDate,
                 modelName,
                 modelPath,
                 factorLibraryList,
                 factorNamesDict,
                 windowSizeDict,
                 save,
                 saveLibraryList,
                 concat1sSignal,
                 save1sLibrary
                 ):

        self.codeList = codeList
        self.startDate = startDate
        self.endDate = endDate
        self.modelName = modelName
        self.modelPath = modelPath
        self.factorLibraryList = factorLibraryList
        self.factorNamesDict = factorNamesDict
        self.windowSizeDict = windowSizeDict
        self.save = save
        self.saveLibraryList = saveLibraryList
        self.concat1sSignal = concat1sSignal
        self.save1sLibrary = save1sLibrary



