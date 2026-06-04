from xquant.factordata import FactorData

fd = FactorData()

y = fd.get_factor_value("ApolloBTSignals", "300212.SZ", "20191216", ["timestamp"])
print(y)