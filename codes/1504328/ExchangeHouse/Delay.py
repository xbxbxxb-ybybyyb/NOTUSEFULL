#-*- coding:utf-8 -*-
# author: 015629
# datetime:2021/11/11 14:25
# -*- coding:utf-8 -*-
# author: 015629
# datetime:2021/8/31 13:54

def get_order_send_delay(code):
    if code.endswith(".SH"):
        delay = 1.0
    else:
        if code.startswith("0"):
            delay = 0.05
        else:  # code.startswith("3")
            delay = 0.05
    return delay


def get_order_back_delay(code):
    if code.endswith(".SH"):
        delay = 0.4
    else:
        if code.startswith("0"):
            delay = 0.05
        else:  # code.startswith("3")
            delay = 0.05
    return delay


def get_order_delay(code, direction="sendDelay"):
    return get_order_send_delay(code) if direction == "sendDelay" else get_order_back_delay(code)

