from LongShortAnalyzer import analyzeLongShortProfits
import os

sdate = 20200101
edate = 20200131

path = "/data/user/666888/AlgoModelCmp/results/{}-{}/".format(sdate, edate)
outputPath = "/data/user/666888/AlgoModelCmp/Cmp/"

# path1 = "/cv-20191101-20191231-zz500-500000000-180-800_Model20191101_universe_133_20200325_simple_tmp/"
# path2 = "/cv-20191101-20191231-zz500-500000000-180-800_Model20191101_universe_48_simple/"
# path3 = "/cv-20191101-20191231-zz500-500000000-180-800_Model20191101_48/"

# path1 = "/bt-20200201-20200228-zz500-cv-20191101-20191231-zz500-500000000-180-800_Model20191101_universe_133_20200325_simple_tmp/"
# path2 = "/bt-20200201-20200228-zz500-cv-20191101-20191231-zz500-500000000-180-800_Model20191101_universe_48_simple/"
path3 = "/bt-20200101-20200131-zz500-cv-20191101-20191231-zz500-500000000-180-800_Model20191101_48/"
# path4 = "/bt-20200201-20200228-zz500-cv-20191101-20191231-zz500-500000000-180-800_Model20190301/"

if not os.path.exists("{}/{}/{}-{}/".format(outputPath, "zz500", sdate, edate)):
    os.makedirs("{}/{}/{}-{}/".format(outputPath, "zz500", sdate, edate))

# analyzeLongShortProfits([path + path1]).to_excel("{}/{}/{}-{}/{}_{}-{}_{}.xlsx".format(outputPath, "zz500", sdate, edate, "zz500", sdate, edate, "Model20191101_universe_133_20200325_simple_tmp"))
# analyzeLongShortProfits([path + path2]).to_excel("{}/{}/{}-{}/{}_{}-{}_{}.xlsx".format(outputPath, "zz500", sdate, edate, "zz500", sdate, edate, "Model20191101_universe_48_simple"))
analyzeLongShortProfits([path + path3]).to_excel("{}/{}/{}-{}/{}_{}-{}_{}.xlsx".format(outputPath, "zz500", sdate, edate, "zz500", sdate, edate, "Model20191101_48"))
# analyzeLongShortProfits([path + path4]).to_excel("{}/{}/{}-{}/{}_{}-{}_{}.xlsx".format(outputPath, "zz500", sdate, edate, "zz500", sdate, edate, "Model20190301"))


# path1 = "/cv-20191101-20191231-hs300-500000000-180-800_Model20191101_universe_133_20200325_simple_tmp/"
# path2 = "/cv-20191101-20191231-hs300-500000000-180-800_Model20191101_universe_48_simple/"
# path3 = "/cv-20191101-20191231-hs300-500000000-180-800_Model20191101_48/"

# path1 = "/bt-20200201-20200228-hs300-cv-20191101-20191231-hs300-500000000-180-800_Model20191101_universe_133_20200325_simple_tmp/"
# path2 = "/bt-20200201-20200228-hs300-cv-20191101-20191231-hs300-500000000-180-800_Model20191101_universe_48_simple/"
path3 = "/bt-20200101-20200131-hs300-cv-20191101-20191231-hs300-500000000-180-800_Model20191101_48/"
# path4 = "/bt-20200201-20200228-hs300-cv-20191101-20191231-hs300-500000000-180-800_Model20190301/"

if not os.path.exists("{}/{}/{}-{}/".format(outputPath, "hs300", sdate, edate)):
    os.makedirs("{}/{}/{}-{}/".format(outputPath, "hs300", sdate, edate))

# analyzeLongShortProfits([path + path1]).to_excel("{}/{}/{}-{}/{}_{}-{}_{}.xlsx".format(outputPath, "hs300", sdate, edate, "hs300", sdate, edate, "Model20191101_universe_133_20200325_simple_tmp"))
# analyzeLongShortProfits([path + path2]).to_excel("{}/{}/{}-{}/{}_{}-{}_{}.xlsx".format(outputPath, "hs300", sdate, edate, "hs300", sdate, edate, "Model20191101_universe_48_simple"))
analyzeLongShortProfits([path + path3]).to_excel("{}/{}/{}-{}/{}_{}-{}_{}.xlsx".format(outputPath, "hs300", sdate, edate, "hs300", sdate, edate, "Model20191101_48"))
# analyzeLongShortProfits([path + path4]).to_excel("{}/{}/{}-{}/{}_{}-{}_{}.xlsx".format(outputPath, "hs300", sdate, edate, "hs300", sdate, edate, "Model20190301"))
