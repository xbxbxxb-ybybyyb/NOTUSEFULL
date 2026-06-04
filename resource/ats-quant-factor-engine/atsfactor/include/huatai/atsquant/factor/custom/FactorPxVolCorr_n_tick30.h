#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"

namespace huatai::atsquant::factor {

class FactorPxVolCorr_n_tick30 : public Factor<> {
  static const int SECONDS = 90;
  TimeSlidingWindow<double> mid_price_window{SECONDS};
  TimeSlidingWindow<double> mid_price_gap_window{SECONDS};

  TimeSlidingWindow<double> mid_qty_window{SECONDS};
  TimeSlidingWindow<double> mid_qty_gap_window{SECONDS};

public:
  FactorPxVolCorr_n_tick30() { type_ = __func__; }

  Status caculate() override {
    auto table = get_market_data().get_prev_n_quote(1);
    auto mdtime = table.item<QuoteSchema::Index::TRIGGER_TIME>();

    auto bid1_price = table.list_item<QuoteSchema::Index::BID_PRICE>()[0];
    auto ask1_price = table.list_item<QuoteSchema::Index::ASK_PRICE>()[0];
    auto mid_price = (bid1_price + ask1_price) / 2;
    mid_price_window.push(mdtime, mid_price);
    auto mid_price_gap = mid_price - compute::mean(mid_price_window);
    mid_price_gap_window.push(mdtime, mid_price_gap);

    auto bid1_qty = table.list_item<QuoteSchema::Index::BID_ORDER_NUMS>()[0];
    auto ask1_qty = table.list_item<QuoteSchema::Index::ASK_ORDER_NUMS>()[0];
    auto mid_qty = (bid1_qty + ask1_qty) / 2.0;
    mid_qty_window.push(mdtime, mid_qty);
    auto mid_qty_gap = mid_qty - compute::mean(mid_qty_window);
    mid_qty_gap_window.push(mdtime, mid_qty_gap);

    value() = compute::corr(mid_price_gap_window, mid_qty_gap_window);
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor