import os 
import shutil

# os.remove("/app/data/013050/chensf/SingleModel125H5_324_500/ModelSignalDataSet/OrderCapacity.json")                   
# os.rename("/app/data/013050/chensf/AppleData/603517.SH/factorMAVolumeDistance40Short", "/app/data/013050/chensf/AppleData/603517.SH/factorMAVolumeDistance40")
# shutil.rmtree("/app/data/666888/Apple")
# shutil.copy(src_name + '/variables/variables.index', des_name + '/variables/variables.index')
# os.makedirs("/app/data/013050/chensf/ModelProduction/2018-09-01/20181203")
# shutil.move("/app/data/013050/chensf/ModelProduction/2018-09-01/ModelSignalDataSet/","/app/data/013050/chensf/ModelProduction/2018-09-01/20181201/") 
shutil.copytree("/app/data/013050/chensf/AppleData/000001.SZ",
                "/app/data/666888/Apple/AppleData/000001.SZ")
                
# shutil.rmtree("/app/data/013050/chensf/SingleModelGroup0_test/ModelSaved/AlgoShaolin-000333.SZ-20170124093015-20180824145659_model1minLong1minShort160200240Pred0.1SliceLag16_SavedModelBuilder")               
                