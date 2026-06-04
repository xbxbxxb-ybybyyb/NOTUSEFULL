#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <cmath> // 或者 #include <math.h>

namespace huatai::atsquant::factor {

class FactorVixDown_n_tick40 : public Factor<> {
  static const int lag1 = 120;
  TimeSlidingWindow<double> ret_list{lag1};

public:
  FactorVixDown_n_tick40() { type_ = __func__; }

  Status caculate() override {
    auto quote = get_market_data().get_prev_n_quote(2);
    if (quote.len() < 2) {
      return Status::OK();
    }
    auto now_time = quote[-1];
    auto last_time = quote[0];

    auto cur_time = now_time.item<QuoteSchema::Index::TRIGGER_TIME>();
    auto cur_last_px = now_time.item<QuoteSchema::Index::LAST_PX>();

    const auto *cur_sell_price = now_time.list_item<QuoteSchema::Index::ASK_PRICE>();
    const auto *cur_buy_price = now_time.list_item<QuoteSchema::Index::BID_PRICE>();
    const auto *prev_sell_price = last_time.list_item<QuoteSchema::Index::ASK_PRICE>();
    const auto *prev_buy_price = last_time.list_item<QuoteSchema::Index::BID_PRICE>();

    auto cur_buy1_price = cur_buy_price[0];
    auto cur_sell1_price = cur_sell_price[0];
    auto cur_mid_price = (cur_buy1_price + cur_sell1_price) / 2;

    auto prev_buy1_price = prev_buy_price[0];
    auto prev_sell1_price = prev_sell_price[0];
    auto prev_mid_price = (prev_buy1_price + prev_sell1_price) / 2;

    auto ret = cur_mid_price / prev_mid_price - 1;
    auto pow_ret = std::pow(ret * (ret < 1), 2);
    ret_list.push(cur_time, pow_ret);
    auto temp = std::sqrt(compute::sum(ret_list));
    value() = temp;

    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor