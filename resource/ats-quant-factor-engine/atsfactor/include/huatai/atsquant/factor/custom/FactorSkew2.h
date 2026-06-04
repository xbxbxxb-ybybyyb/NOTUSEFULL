#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <cmath> // 或者 #include <math.h>

namespace huatai::atsquant::factor {

class FactorSkew2 : public Factor<> {
  static const int SECONDS = 30;
  TimeSlidingWindow<double> ret_list{SECONDS};

public:
  FactorSkew2() { type_ = __func__; }

  Status caculate() override {
    auto window = get_market_data().get_prev_n_quote(2);
    if (window.len() < 2) {
      return Status::OK();
    }

    auto now_time = window[1];
    auto prev_time = window[0];
    const auto *cur_bid_price = now_time.list_item<QuoteSchema::Index::BID_PRICE>();
    const auto *prev_bid_price = prev_time.list_item<QuoteSchema::Index::BID_PRICE>();
    const auto *cur_ask_price = now_time.list_item<QuoteSchema::Index::ASK_PRICE>();
    const auto *prev_ask_price = prev_time.list_item<QuoteSchema::Index::ASK_PRICE>();
    auto cur_time = now_time.item<QuoteSchema::Index::TRIGGER_TIME>();

    auto cur_mid_price = (cur_ask_price[0] + cur_bid_price[0]) / 2;
    auto prev_mid_price = (prev_bid_price[0] + prev_ask_price[0]) / 2;

    auto ret = cur_mid_price / prev_mid_price - 1;

    ret_list.push(cur_time, ret);

    auto skew = compute::skewness(ret_list);
    value() = skew;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor