import sys
try:
    import xquant.xqutils
    sys.modules["xquant.utils"] = sys.modules["xquant.xqutils"]
except:
    pass

try:
    import xquant.xqutils.xqfile
    sys.modules["xquant.pyfile"] = sys.modules["xquant.xqutils.xqfile"]
except:
    pass

try:
    import xquant.xqutils.xqlog
    sys.modules["xquant.log"] = sys.modules["xquant.xqutils.xqlog"]
except:
    pass

try:
    import xquant.strategy.backtest
    sys.modules["xquant.backtest"] = sys.modules["xquant.strategy.backtest"]
except:
    pass

try:
    import xquant.thirdpartydata.factor
    sys.modules["xquant.factor"] = sys.modules["xquant.thirdpartydata.factor"]
    sys.modules["xquant.factor.FactorEnum"] = sys.modules["xquant.thirdpartydata.factor.FactorEnum"]
except:
    pass

try:
    import xquant.xqutils.xqfile.ftpfile
    sys.modules["xquant.pyfile.ftp"] = sys.modules["xquant.xqutils.xqfile.ftpfile"]
except:
    pass

try:
    import xquant.xqutils.pyfilelib
    sys.modules["xquant.pyfilelib"] = sys.modules["xquant.xqutils.pyfilelib"]
except:
    pass

try:
    import xquant.thirdpartydata.multifactor
    sys.modules["xquant.multifactor"] = sys.modules["xquant.thirdpartydata.multifactor"]
except:
    pass

try:
    import xquant.compute.aimr
    sys.modules["xquant.tensorflow"] = sys.modules["xquant.compute.aimr"]
except:
    pass



