#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <cmath> // 或者 #include <math.h>

namespace huatai::atsquant::factor {

class FactorTechIndicatorForWR_n_tick10 : public Factor<> {
  static const int lag1 = 30;
  TimeSlidingWindow<double> sell_price_list{lag1};
  TimeSlidingWindow<double> buy_price_list{lag1};

public:
  FactorTechIndicatorForWR_n_tick10() { type_ = __func__; }

  Status caculate() override {
    auto now_time = get_market_data().get_prev_n_quote(1);
    auto cur_time = now_time.item<QuoteSchema::Index::TRIGGER_TIME>();
    auto cur_last_px = now_time.item<QuoteSchema::Index::LAST_PX>();
    const auto *cur_sell_price = now_time.list_item<QuoteSchema::Index::ASK_PRICE>();
    const auto *cur_buy_price = now_time.list_item<QuoteSchema::Index::BID_PRICE>();
    auto buy1_price = cur_buy_price[0];
    auto sell1_price = cur_sell_price[0];
    sell_price_list.push(cur_time, sell1_price);
    buy_price_list.push(cur_time, buy1_price);

    auto max_sell_price = compute::max(sell_price_list);
    auto max_buy_price = compute::max(buy_price_list);

    auto temp = (max_sell_price - cur_last_px) / (max_sell_price - max_buy_price);
    value() = temp;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor