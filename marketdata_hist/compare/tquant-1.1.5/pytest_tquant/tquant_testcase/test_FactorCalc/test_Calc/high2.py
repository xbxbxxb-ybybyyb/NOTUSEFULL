from tquant.SmartFactor.HFBaseFactor import HFBaseFactor


class high2(HFBaseFactor):
    factor_type = "TICK"
    factor_name = 'high2'
    security_type = 'stock'
    security_pool = ['688001.SH']
    custom_params = {"interval_seconds": 50, "tick_interval_seconds": 3}

    def calc(self, price_data, factor_data, custom_params):
        interval_seconds = custom_params["interval_seconds"]
        tick_interval_seconds = custom_params["tick_interval_seconds"]
        n_tick = interval_seconds // tick_interval_seconds

        res = price_data['LastPx'].diff(n_tick) / price_data['LastPx'].shift(n_tick) * 1000
        res.index = price_data['MDTime']

        return res
