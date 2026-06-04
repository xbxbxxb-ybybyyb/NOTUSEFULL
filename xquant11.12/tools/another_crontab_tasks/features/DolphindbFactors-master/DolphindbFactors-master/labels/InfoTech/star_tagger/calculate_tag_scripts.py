import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
# import matplotlib.pyplot as plt

# from scipy import stats
# from DolphindbUtils.DOIApi import *
# from DolphindbUtils.FactorManager import *
from src.tagger_data import TaggerData
# from src.VolatilityTaggerData import VolatilityTaggerData
from src.tagger_calculator import TagCalculator
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider


user_id='016884'
fd = FactorProvider(user_id)

endtag_config = [
    {
    "class_name": "EndTagger",
    "param": {
        "base_name": "endtagger",
        "label_coeff": 1000,
        "d_size": 300,
        "step_increment": 1,
        "type_method": "midprice",
    }
}
]

endtagabs_config = [
    {
    "class_name": "EndTaggerAbs",
    "param": {
        "base_name": "endtaggerabs",
        "label_coeff": 1000,
        "d_size": 30,
        "step_increment": 1,
        "type_method": "midprice",
    }
}
]

triple_barrier_config = [
    {
        "class_name": "TripleBarrierTagger",
        "param": {
            "base_name": "triplebarriertagger",
            "label_coeff": 1000,
            "d_size": 300,
            "step_increment": 1,
            "type_method": "midprice",
            "volatility_px": "midprice",
            "num_diff_tick": 1,
            "label_triple_barrier_span": 20,
            "label_triple_barrier_alpha": 6
        }
    }
]

new_triple_barrier_config = [
    {
        "class_name": "TripleBarrierTaggerNew",
        "param": {
            "base_name": "triplebarriertaggernew",
            "label_coeff": 1000,
            "d_size": 300,
            "step_increment": 1,
            "type_method": "midprice",
            "volatility_px": "midprice",
            "num_diff_tick": 1,
            "label_triple_barrier_span": 50,
            "label_triple_barrier_alpha": 4
        }
    }
]

first_reach_config = [
    {
        "class_name": "FirstReachTagger",
        "param": {
            "base_name": "firstreachtagger",
            "label_coeff": 1000,
            "d_size": 300,
            "step_increment": 1,
            "type_method": "midprice",
            "volatility_px": "midprice",
            "num_diff_tick": 1,
            "threshold": 1.2,
            "ignore": True
        }
    }
]

vol_tag_config = [
    {
    "class_name": "VolatilityTagger",
    "param": {
        "base_name": "volatilitytagger",
        "label_coeff": 1000,
        "d_size": 300,
        "step_increment": 1,
        "type_method": "vwap"
    }
}
]

vol_tag_by_trade_config = [
    {
    "class_name": "VolatilityByTradeTagger",
    "param": {
        "base_name": "volatilitybytradetagger",
        "label_coeff": 1e3,
        "d_size": 100,
        "step_increment": 1,
        "price_method": "max",
        "type_method": "midprice",
        "std_object": "return"
    }
}
]

endprice_tag_config = [
    {
    "class_name": "EndPriceTagger",
    "param": {
        "base_name": "endpricetagger",
        "label_coeff": 1000,
        "d_size": 300,
        "step_increment": 1,
        "type_method": "midprice",
    }
}
]

data_config_dict_year = {
    "symbol": ["688126.SH"],
    "symboltype": "stock",
    "start_time": "20200101",
    "end_time": "20230201",
    "source": "xquant",
    "raw_name_list": [
        "Sell1Price","Buy1Price"
    ],
    "n_job":8
}

multi_triple_barrier_config = [
    {
        "class_name": "MultiTagger",
        "param": {
            "base_name": "multitagger",
            "label_coeff": 1000,
            "d_size": 300,
            "step_increment": 1,
            "type_method": "midprice",
            "volatility_px": "midprice",
            "num_diff_tick": 1,
        }
    }
]

mean_config = [
    {
        "class_name": "MeanTagger",
        "param": {
            "base_name": "meantagger",
            "label_coeff": 1000,
            "d_size": 300,
            "step_increment": 1,
            "type_method": "midprice",
            "volatility_px": "midprice",
            "num_diff_tick": 1,
        }
    }
]

endmean_config = [
    {
        "class_name": "EndMeanTagger",
        "param": {
            "base_name": "endmeantagger",
            "label_coeff": 1000,
            "d_size": 300,
            "step_increment": 1,
            "type_method": "lastpx",
            "num_diff_tick": 1,
        }
    }
]

triple_barrier_config_v2 = [
    {
        "class_name": "TripleBarrierTaggerV2",
        "param": {
            "base_name": "triplebarriertaggerv2",
            "label_coeff": 1000,
            "d_size": 120,
            "step_increment": 1,
            "price_type": "midprice",
            "volatility_px": "midprice",
            "num_diff_tick": 1,
            "barrier": 1,
        }
    }
]

new_triple_barrier_v2_config = [
    {
        "class_name": "TripleBarrierTaggerNewV2",
        "param": {
            "base_name": "triplebarriertaggernewv2",
            "label_coeff": 1000,
            "d_size": 300,
            "step_increment": 1,
            "price_type": "midprice",
            "volatility_px": "midprice",
            "barrier": 5,
            "min_count": 10,
            "num_diff_tick": 1,
            "label_triple_barrier_span": 50,
            "label_triple_barrier_alpha": 3
        }
    }
]

def tag_util(code, tag_config):
    symboltype = "stock" if code.startswith("6") else "fund"
    data_config_dict_year = {
    "symbol": [code],
    "symboltype": symboltype,
    "start_time": "20230529",
    "end_time": "20230613",
    "source": "xquant",
    "raw_name_list": [
        "Sell1Price", "Buy1Price"
    ],
    "n_job":32
    }
    # tagger_data = VolatilityTaggerData(data_config_dict_week, save_label=False)
    tagger_data = TaggerData(data_config_dict_year, save_label=True)
    print("tagger_data Finish")
    # tagger_data = TaggerData(data_config_dict_week, save_label=False)
    tag_calculator = TagCalculator(tag_config)
    print("tag_calculator Finish")
    label_df = tagger_data.get_labels_ready(tag_calculator)
    print("label_df Finish")



for d_size in [120]:
    for tag_config in [triple_barrier_config_v2]:
        for code in [
                "688599.SH",
                #"688012.SH",
                #"688599.SH"
                # # "601012.SH", "688223.SH",
                # "603806.SH",
                # # '600151.SH',
                # # '600207.SH',
                # '600438.SH',
                # '600537.SH',
                # '600732.SH',
                # '601222.SH',
                # '601865.SH',
                # '601908.SH',
                # '603105.SH',
                # '603185.SH',
                # '603396.SH',
                # '603628.SH',
                # '605117.SH',
                # '688303.SH'
            # "510300.SH",
            # "510330.SH",
            # "516780.SH",
            # "516150.SH",
            #"688363.SH",
            # "688029.SH",
            # "512360.SH","588360.SH","588400.SH","515750.SH","560010.SH"
            ]:
            print(code)
            tag_config[0]["param"]["d_size"] = d_size
            print(d_size, tag_config[0]["class_name"], code)
            tag_util(code, tag_config)

