from xquant.pyfile import Pyfile
import json


replace_all = False
portfolio = '5161101+800'
input_dir = 'production/cv-20181222-20190222_20190225-5161101+800-200-800/'

py = Pyfile()
index = input_dir.index('/cv')
sub_str = input_dir[index + 1: ]
name = sub_str.split('/')[0]
output_dir = 'production_triggers_month/{}/'.format(portfolio)
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
