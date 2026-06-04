#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <cmath> // 或者 #include <math.h>

namespace huatai::atsquant::factor {

class FactorLuOrderBidOfferQtyRatioTrend : public Factor<> {
  static const int qty_list_lag = 11;
  SlidingWindow<double> qty_list{qty_list_lag};
  const std::array<double, 10> array = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9};

public:
  FactorLuOrderBidOfferQtyRatioTrend() { type_ = __func__; }
  Status caculate() override {
    static int index = 0;
    index++;
    auto window = get_market_data().get_prev_n_quote(1);
    auto *bid_qty = window.list_item<QuoteSchema::Index::BID_QTY>();
    auto *ask_qty = window.list_item<QuoteSchema::Index::ASK_QTY>();
    auto mean_buy_qty = compute::mean(bid_qty, 10);
    auto mean_sell_qty = compute::mean(ask_qty, 10);
    auto qty_ratio = mean_buy_qty / mean_sell_qty;
    qty_list.push(qty_ratio);

    if (qty_list.size() < qty_list_lag) {
      value() = 0;
      return Status::OK();
    }
    auto trend = compute::corr(qty_list.data(), array.data(), 10);
    value() = trend;

    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor