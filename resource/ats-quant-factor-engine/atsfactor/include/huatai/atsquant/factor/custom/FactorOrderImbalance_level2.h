#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <arrow/status.h>

namespace huatai::atsquant::factor {

class FactorOrderImbalance_level2 : public Factor<> {

public:
  FactorOrderImbalance_level2() { type_ = __func__; }

  Status caculate() override {
    auto row_tick = get_market_data().get_prev_n_quote(1);
    const auto *current_tick_ask_p = row_tick.list_item<QuoteSchema::Index::ASK_PRICE>();
    const auto *current_tick_ask_v = row_tick.list_item<QuoteSchema::Index::ASK_QTY>();
    const auto *current_tick_bid_p = row_tick.list_item<QuoteSchema::Index::BID_PRICE>();
    const auto *current_tick_bid_v = row_tick.list_item<QuoteSchema::Index::BID_QTY>();
    auto buy1_qty = current_tick_bid_v[2];
    auto buy1_price = current_tick_bid_p[2];
    auto ask1_qty = current_tick_ask_v[2];
    auto ask1_price = current_tick_ask_p[2];
    auto tmpa = (buy1_qty - ask1_qty) * buy1_price;
    auto tmpb = (buy1_qty + ask1_qty) * ask1_price;

    value() = tmpa / tmpb;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor