from xquant.factordata import FactorData

fd = FactorData()

try:
    fd.create_factor_library("ApolloBTSignals", 'T+0')
except:
    pass

try:
    for fn in ["timestamp", "ticktime", "prediction1minLong", "prediction1minShort", "prediction2minLong",
               "prediction2minShort", "prediction5minLong", "prediction5minShort"]:
        try:
            fd.add_factor("ApolloBTSignals", [fn])
        except Exception as e:
            print(e)
            pass
except:
    pass
