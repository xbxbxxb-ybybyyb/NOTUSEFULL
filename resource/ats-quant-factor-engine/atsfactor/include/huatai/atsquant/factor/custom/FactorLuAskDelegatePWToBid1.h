#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <cmath> // 或者 #include <math.h>

namespace huatai::atsquant::factor {

class FactorLuAskDelegatePWToBid1 : public Factor<> {
  static const int lag = 2;
  SlidingWindow<double> lag_list{lag};

public:
  FactorLuAskDelegatePWToBid1() { type_ = __func__; }

  Status caculate() override {
    auto window = get_market_data().get_prev_n_quote(1);
    if (window.len() < 1) {
      return Status::OK();
    }

    auto now_time = window.item<QuoteSchema::Index::TRIGGER_TIME>();
    auto *bid_price = window.list_item<QuoteSchema::Index::BID_PRICE>();
    auto *bid_qty = window.list_item<QuoteSchema::Index::BID_QTY>();
    auto *sell_price = window.list_item<QuoteSchema::Index::ASK_PRICE>();
    auto *sell_qty = window.list_item<QuoteSchema::Index::ASK_QTY>();
    auto bid1_price = bid_price[0];
    lag_list.push(bid1_price);
    auto sell_money = 0.0;
    for (int i; i < 10; i++) {
      sell_money += sell_price[i] * sell_qty[i];
    }
    auto askpw = sell_money / compute::sum(sell_qty, 10);
    auto dist1 = askpw / lag_list.front() - 1;
    auto dist2 = lag_list.front() / bid1_price - 1;
    value() = (dist1 + dist2) * 1e2;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor