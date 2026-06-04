import math
import json
from xquant.pyfile import Pyfile

s_date = "20190701"
e_date = "20190831"

path = "Apollo/cv_info/{}-{}_universal/".format(s_date, e_date)
output_path = "Apollo/cv_params/{}-{}_universal/".format(s_date, e_date)
stock_num_per_cv = 600

py = Pyfile()
with py.open(path + "Apollo_quantity.json", "rb") as f:
    total_quantity = json.load(f)

codes = list(total_quantity["quantity"].keys())

for i in range(math.ceil(len(codes) / stock_num_per_cv)):
    new_quantity = {
        "Combine": total_quantity["Combine"],
        "quantity": {},
        "value": {}
    }
    new_quantity_negative = {
        "Combine": total_quantity["Combine"],
        "quantity": {},
        "value": {}
    }

    for code in codes[stock_num_per_cv * i:stock_num_per_cv * (i + 1)]:
        new_quantity["quantity"][code] = total_quantity["quantity"][code]
        new_quantity["value"][code] = total_quantity["value"][code]
        new_quantity_negative["quantity"][code] = -total_quantity["quantity"][code]
        new_quantity_negative["value"][code] = -total_quantity["value"][code]

    with py.open(output_path + "Apollo_quantity" + str(i + 1) + ".json", "wb") as f:
        json.dump(new_quantity, f)

    with py.open(output_path + "Apollo_quantity_negative" + str(i + 1) + ".json", "wb") as f:
        json.dump(new_quantity_negative, f)
