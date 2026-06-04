from enum import Enum, unique


@unique
class SignalType(Enum):
    price_limit = 0
    price_limit_open = 1
    invalid_signal = 2
    aggressive = 3
    passive = 4
    supplement = 5
    interval_end = 6
    market_close = 7
    price_deviation = 8
    low_volatility = 9
    market_close_morning = 10
    vwap_bias = 11
    low_swing = 12
    up = 13
    down = 14
