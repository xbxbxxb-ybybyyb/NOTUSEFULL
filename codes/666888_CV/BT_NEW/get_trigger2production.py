from xquant.pyfile import Pyfile
import json


replace_all = True
# replace_all = False
input_dir = 'AlgoModelCmp/bt_results/cv-20200301-20200430-hs300-500000000-180-800_SeparateModelSignals/'
# input_dir = 'AlgoGenzong2/bt_results/cv-20191101-20191231-zz500-300000000-180-800_Model20191101_2/'
# input_dir = "AlgoGenzong2/bt_results/cv-20191101-20191231-zz500-500000000-180-800_Model20191101_93_4/"
py = Pyfile()
index = input_dir.index('/cv')
sub_str = input_dir[index + 1: ]
name = sub_str.split('/')[0]
output_dir = 'AlgoModelCmpTriggers/SeparateModelSignals/hs300/500000000/'
# output_dir = 'AlgoGenzong2Triggers/zz500/300000000/'
# output_dir = 'ModelTestTriggers/zz500/500000000/'
if replace_all:
    if py.exists(output_dir):
        py.delete(output_dir, recursive=True)
    py.mkdir(output_dir)
files = py.listdir(input_dir)
for file in files:
    if file == 'TEMP' or file == '.tmp':
        continue
    trigger_ratio_dir = input_dir + file + '/triggerRatio.json'
    with py.open(trigger_ratio_dir, 'rb') as f:
        data = f.read()
        data = json.loads(data)
    with py.open(output_dir + file + '.json', 'wb') as f:
        json.dump(data, f)
with py.open(output_dir + 'come_from.json', 'wb') as f:
    json.dump(name, f)
# print(len(py.listdir(output_dir)))
