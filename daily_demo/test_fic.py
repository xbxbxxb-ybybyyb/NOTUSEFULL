from xquant.thirdpartydata.fic_api_data import FicApiData
fad = FicApiData()

resource = 'ZX_CONCEPTION'#'ZX_CIQKEYDEVABSTRACT'#'ZX_CIQKEYDEV'#"ZX_STK_ACHIEVEMENTFORECAST"
paramMaps = {'CONCEPTTYPECODE':'00030024'}#{'KEYDEVID':'703166782'}#{"LISTDATE": "20190103"}
#orderBy = "EXCHANGECODE"
rownum = 100
startrow = 0
#分页查询第0条到第100条
result_dict = fad.get_fic_api_data(resource, paramMaps, startrow=startrow, rownum=rownum)
import pickle
pickle.dump(result_dict, open("result_dict.pkl", "wb"))
print(result_dict)
