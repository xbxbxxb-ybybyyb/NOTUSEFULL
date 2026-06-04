#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <cmath> // 或者 #include <math.h>

namespace huatai::atsquant::factor {

class FactorTechIndicatorForB3612 : public Factor<> {
  static const int lag1 = 30;
  static const int lag2 = 60;
  static const int lag3 = 90;
  static const int move_lag = 11;
  TimeSlidingWindow<double> lag1_list{lag1};
  TimeSlidingWindow<double> lag2_list{lag2};
  TimeSlidingWindow<double> lag3_list{lag3};
  SlidingWindow<double> midprice_list{move_lag};

public:
  FactorTechIndicatorForB3612() { type_ = __func__; }

  Status caculate() override {
    static int index = 0;
    index++;
    auto now_time = get_market_data().get_prev_n_quote(1);

    const auto *cur_bid_price = now_time.list_item<QuoteSchema::Index::BID_PRICE>();
    const auto *cur_ask_price = now_time.list_item<QuoteSchema::Index::ASK_PRICE>();
    auto cur_time = now_time.item<QuoteSchema::Index::TRIGGER_TIME>();
    auto mid_price = (cur_bid_price[0] + cur_ask_price[0]) / 2.0;
    lag1_list.push(cur_time, mid_price);
    lag2_list.push(cur_time, mid_price);
    lag3_list.push(cur_time, mid_price);
    midprice_list.push(mid_price);

    auto b36 = (compute::mean(lag1_list) - compute::mean(lag2_list)) / compute::mean(lag1_list);
    auto b612 = (compute::mean(lag2_list) - compute::mean(lag3_list)) / compute::mean(lag2_list);
    auto ret = (mid_price - midprice_list.front()+1e-10) / (mid_price);
    auto ret_up = ret > 0 ? 1 : 0;
    auto ret_dw = ret < 0 ? 1 : 0;

    auto temp = b36 * ret_up - b612 * ret_dw;
    value() = temp;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor