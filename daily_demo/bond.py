from xquant.bonddata import BondData
bd = BondData()

#set1 =  bd.get_bond_set('20210813', bond_type='kzz')
#set2 =  bd.get_bond_set('20210813', bond_type='kzz')

#result = bd.get_bond_data_day("SH", "20211214", "Tick")
#result.to_csv("a.csv")
#raise Exception()

result_1 = bd.get_bond_data("123038.SZ", "20220818 090000000", "20220818 200000000", 'K_1MIN')
print(result_1)
raise Exception()

#result_2 = bd.get_bond_data("123021.SZ", "20200202 090000000", "20200302 200000000", 'K_1MIN')
#print(result_2.head())

#result_3 = bd.get_bond_data("123021.SZ", "20200202 090000000", "20200302 200000000", 'TICK')
#print(result_3.head())


result_4 = bd.get_bond_data("113610.SH", "20210222 090000000", "20210222 200000000", 'TICK')
print(result_4)
#raise Exception()

#result_5 = bd.get_bond_data("123015.SZ", "20201029 090000000", "20201029 200000000", 'ORDER')
#print(result_5)

