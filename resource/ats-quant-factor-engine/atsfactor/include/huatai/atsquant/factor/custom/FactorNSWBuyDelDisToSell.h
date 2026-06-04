#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"

namespace huatai::atsquant::factor {

class FactorNSWBuyDelDisToSell : public Factor<> {
public:
  FactorNSWBuyDelDisToSell() { type_ = __func__; }

  Status caculate() override {
    value() = 0;
    auto row_tick = get_market_data().get_prev_n_quote(2);

    auto current_row_tick = row_tick[1];
    auto last_row_tick = row_tick[0];

    const auto *current_tick_ask_p = current_row_tick.list_item<QuoteSchema::Index::ASK_PRICE>();
    const auto *last_tick_ask_p = last_row_tick.list_item<QuoteSchema::Index::ASK_PRICE>();
    const auto *current_tick_bid_p = current_row_tick.list_item<QuoteSchema::Index::BID_PRICE>();
    const auto *current_tick_bid_v = current_row_tick.list_item<QuoteSchema::Index::BID_QTY>();

    if (current_tick_ask_p[0] <= 0.01 || last_tick_ask_p[0] <= 0.01 || row_tick.len() < 2) {
      value() = 1;
      return Status::OK();
    }

    auto buy_amt_sum = compute::mul_sum(current_tick_bid_p, current_tick_bid_v, 10);
    auto buy_vol_sum = compute::sum(current_tick_bid_v, 10);
    auto buy_vwap = buy_amt_sum / buy_vol_sum;
    auto dis1 = buy_vwap / current_tick_ask_p[0] - 1;
    auto dis2 = current_tick_ask_p[0] / last_tick_ask_p[0] - 1;

    if (buy_vol_sum == 0) {
      value() = -1;
    } else {
      value() = (dis1 + dis2) * 100;
    }
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor