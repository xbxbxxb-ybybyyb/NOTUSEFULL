#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <algorithm>

namespace huatai::atsquant::factor {

class FactorBuyDetrend_Cgw : public Factor<> {
  static const int SECONDS = 5;
  SlidingWindow<double> SellTrend{SECONDS};

public:
  FactorBuyDetrend_Cgw() { type_ = __func__; }

  Status caculate() override {
    auto window = get_market_data().get_prev_n_quote(1);
    auto now_time = window.item<QuoteSchema::Index::TRIGGER_TIME>();
    const auto *buy_qty = window.list_item<QuoteSchema::Index::BID_QTY>();
    const auto *buy_price = window.list_item<QuoteSchema::Index::BID_PRICE>();
    auto buy1_price = buy_price[0];

    auto weight_buy_qty_sum = 0.0;
    auto weight_buy_value_sum = 0.0;
    for (int i = 0; i < 10; i++) {
      weight_buy_qty_sum += buy_qty[i] * (10 - i) / 55;
      weight_buy_value_sum += buy_price[i] * buy_qty[i] * (10 - i) / 55;
    }
    auto buy_vwap = weight_buy_qty_sum == 0 ? 0.0 : weight_buy_value_sum / weight_buy_qty_sum;
    auto buy_distance_ratio = buy1_price == 0.0 ? 0.0 : buy_vwap / buy1_price - 1;
    SellTrend.push(buy_distance_ratio);
    if(SellTrend.size()<5){
      value() = 0;
      return Status::OK();
    }
    auto SellTrend_copy = SellTrend;
    std::sort(SellTrend_copy.begin(), SellTrend_copy.end());
    value() = compute::sum(SellTrend) == 0 ? 0.0 : compute::corr(SellTrend, SellTrend_copy);

    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor