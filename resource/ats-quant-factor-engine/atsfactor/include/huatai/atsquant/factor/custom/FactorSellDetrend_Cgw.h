#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <algorithm>

namespace huatai::atsquant::factor {

class FactorSellDetrend_Cgw : public Factor<> {
  static const int SECONDS = 5;
  SlidingWindow<double> SellTrend{SECONDS};

public:
  FactorSellDetrend_Cgw() { type_ = __func__; }

  Status caculate() override {

    auto window = get_market_data().get_prev_n_quote(1);
    auto now_time = window.item<QuoteSchema::Index::TRIGGER_TIME>();
    const auto *Sell_qty = window.list_item<QuoteSchema::Index::ASK_QTY>();
    const auto *Sell_price = window.list_item<QuoteSchema::Index::ASK_PRICE>();
    auto Sell1_price = Sell_price[0];

    auto weight_Sell_qty_sum = 0.0;
    auto weight_Sell_value_sum = 0.0;
    for (int i = 0; i < 10; i++) {
      weight_Sell_qty_sum += Sell_qty[i] * (10 - i) / 55;
      weight_Sell_value_sum += Sell_price[i] * Sell_qty[i] * (10 - i) / 55;
    }
    auto Sell_vwap = weight_Sell_qty_sum == 0 ? 0.0 : weight_Sell_value_sum / weight_Sell_qty_sum;
    auto Sell_distance_ratio = Sell1_price == 0.0 ? 0.0 : Sell_vwap / Sell1_price - 1;
    SellTrend.push(Sell_distance_ratio);
    if (SellTrend.size() < SECONDS) {
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