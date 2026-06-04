#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"

namespace huatai::atsquant::factor {

class FactorSellOfferQtyGap_Cgw : public Factor<> {
  static const int LAG = 21;

  SlidingWindow<double> bid_vol_qty_window{LAG};
  SlidingWindow<double> ask_vol_qty_window{LAG};

public:
  FactorSellOfferQtyGap_Cgw() { type_ = __func__; }

  Status caculate() override {
    auto table = get_market_data().get_prev_n_quote(1);

    const auto *bid_qty = table.list_item<QuoteSchema::Index::BID_QTY>();
    auto bid_qty_avg = compute::mean(bid_qty, 10);
    bid_vol_qty_window.push(bid_qty_avg);

    const auto *ask_qty = table.list_item<QuoteSchema::Index::ASK_QTY>();
    auto ask_qty_avg = compute::mean(ask_qty, 10);
    ask_vol_qty_window.push(ask_qty_avg);

    if (bid_vol_qty_window.size() < LAG) {
      value() = 0;
      return Status::OK();
    }

    auto bid_vol_qty = bid_vol_qty_window.back()-bid_vol_qty_window.front();
    auto ask_vol_qty = ask_vol_qty_window.back()-ask_vol_qty_window.front();

    auto sum_bid_ask = bid_vol_qty + ask_vol_qty;
    auto FactorAskOfferQtyGap = sum_bid_ask > 1e-6 ? (ask_vol_qty - bid_vol_qty) / sum_bid_ask : 0;
    value() = std::abs(FactorAskOfferQtyGap) < 10 ? FactorAskOfferQtyGap : 0;

    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor