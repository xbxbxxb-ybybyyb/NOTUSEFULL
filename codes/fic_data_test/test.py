from xquant.thirdpartydata.fic_api_data import FicApiData
fad = FicApiData()

resource = "ZX_STKSHAREINDUSTRYST"
paramMaps = {"STATISTICSDATE": "20201230"}

#paramMaps={"TIMEINTERVAL": ["[2019-08-14, 2019-12-14]"]}
#resource = "ZX_STKLISTSHARENEWEST"

orderBy = "STATISTICSDATE"
rownum = 100
startrow = 0
#分页查询第0条到第100条
result_dict = fad.get_fic_api_data(resource, paramMaps={}, startrow=startrow, rownum=rownum,
                               orderBy=orderBy)
print(result_dict)

