from xquant.characteristic import CharacteristicData
ct_data = CharacteristicData()
df = ct_data.get_shhktinfo('20190715','20190722')
print(df.head())
