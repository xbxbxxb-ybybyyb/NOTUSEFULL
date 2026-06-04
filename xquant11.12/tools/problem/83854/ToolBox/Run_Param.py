import os, shutil
import json


next_trading_day = '20190517'
cv_path = '/app/data/666888/BT_Results/sources/20190301-20190508_20190516/cv-20190301-20190508_20190516-800-300-1200/'
portfolio = '800'
has_base_cv = True
base_cv_paths = [
'/app/data/666888/BT_Results/sources/20190301-20190508_20190511/cv-20190301-20190508_20190511-800-300-1200/',
'/app/data/666888/BT_Results/sources/20190301-20190508_20190513/cv-20190301-20190508_20190513-800-300-1200/',
'/app/data/666888/BT_Results/sources/20190301-20190508_20190514/cv-20190301-20190508_20190514-800-300-1200/',
'/app/data/666888/BT_Results/sources/20190301-20190508_20190515/cv-20190301-20190508_20190515-800-300-1200'
]


output_path = '/app/data/666888/ProductionParams/{}/'.format(str(next_trading_day))
capacity_path = '/app/data/666888/OrderCapacity/'

if os.path.exists(os.path.join(output_path, portfolio + '.json')):
    raise Exception('path exists: {}'.format(os.path.join(output_path, portfolio + '.json')))


def gene_param(cv_path):
    output_dict = {}
    symbols = os.listdir(cv_path)
    for symbol in symbols:
        # capacity
        with open(os.path.join(capacity_path, symbol, 'OrderCapacity.json'), 'r') as f:
            capacities = json.load(f)
            try:
                capacity = capacities['OrderCapacity'][str(next_trading_day)]
            except Exception as e:
                print('capacity not found for ' + symbol)
                continue
        # holo
        if 300000 <= int(symbol[0: 6]) < 399999:
            holo = 'true'
        else:
            holo = 'false'
        # trigger
        with open(os.path.join(cv_path, symbol, 'triggerRatio.json'), 'r') as f:
            trigger = json.load(f)
        # adjust
        if int(trigger['longTriggerRatio']) == 999999:
            capacity = 1.0
        # push
        output_dict.update({symbol: {'Datetime': str(next_trading_day), 'OrderCapacity': capacity, 'TriggerRatio': trigger, 'Holo': holo}})
    return output_dict
            

results = []
if has_base_cv:
    for base_cv_path in base_cv_paths:
        results.append(gene_param(base_cv_path))
results.append(gene_param(cv_path))
result = {}
for result_dict in results:
    result.update(result_dict)

os.makedirs(output_path, exist_ok=True)

with open(os.path.join(output_path, portfolio + '.json'), 'w') as f:
    json.dump(result, f)

print('done')

