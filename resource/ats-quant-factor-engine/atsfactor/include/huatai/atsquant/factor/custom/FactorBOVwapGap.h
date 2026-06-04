#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"

namespace huatai::atsquant::factor {

class FactorBOVwapGap : public Factor<> {
  static constexpr std::array<double, 10> WEIGHT = []() {
    std::array<double, 10> arr;
    for (int i = 0; i < 10; i++) {
      arr[i] = (i + 1) / 10.0;
    }
    return arr;
  }();

public:
  FactorBOVwapGap() { type_ = __func__; }

  Status caculate() override {
    auto now = get_market_data().get_prev_n_quote(1);
    value() = 0;

    const auto *current_tick_ask_p = now.list_item<QuoteSchema::Index::ASK_PRICE>();
    const auto *current_tick_ask_v = now.list_item<QuoteSchema::Index::ASK_QTY>();
    const auto *current_tick_bid_p = now.list_item<QuoteSchema::Index::BID_PRICE>();
    const auto *current_tick_bid_v = now.list_item<QuoteSchema::Index::BID_QTY>();

    std::array<double, 10> weight_v;

    std::copy(current_tick_ask_v, current_tick_ask_v + 10, weight_v.begin());
    compute::mul(weight_v, WEIGHT);
    auto sell_vol_sum = compute::sum(weight_v);

    std::copy(current_tick_bid_v, current_tick_bid_v + 10, weight_v.begin());
    compute::mul(weight_v, WEIGHT);
    auto buy_vol_sum = compute::sum(weight_v);

    std::array<double, 10> prices;
    std::copy(current_tick_bid_p, current_tick_bid_p + 10, prices.begin());
    compute::mul(prices, weight_v);
    auto buy_amt_sum = compute::sum(prices);

    std::copy(current_tick_ask_p, current_tick_ask_p + 10, prices.begin());
    compute::mul(prices, weight_v);
    auto sell_amt_sum = compute::sum(prices);

    auto buy_vwap = buy_amt_sum / buy_vol_sum;
    auto sell_vwap = sell_amt_sum / sell_vol_sum;

    if (buy_vwap - sell_vwap < 1e-4) {
      value() = 0.0;
    } else {
      value() = (buy_vwap - sell_vwap) / (buy_vwap + sell_vwap) * 100;
    }

    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor