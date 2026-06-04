#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <arrow/status.h>

namespace huatai::atsquant::factor {

class FactorNSWSellToVWapCorr : public Factor<> {
  static const int LAG = 10;
  SlidingWindow<double> lag_window{LAG};

public:
  FactorNSWSellToVWapCorr() { type_ = __func__; }

  Status caculate() override {

    auto row_tick = get_market_data().get_prev_n_quote(1);

    const auto *current_tick_ask_p = row_tick.list_item<QuoteSchema::Index::ASK_PRICE>();
    const auto *current_tick_ask_v = row_tick.list_item<QuoteSchema::Index::ASK_QTY>();
    auto total_value = row_tick.item<QuoteSchema::Index::TOTAL_TURNOVER>();
    auto total_volume = row_tick.item<QuoteSchema::Index::TOTAL_VOLUME>();
    auto ave_price = total_value / total_volume;

    auto ask_vwap =
        compute::mul_sum(current_tick_ask_p, current_tick_ask_v, 10) / compute::sum(current_tick_ask_v, 10) / 100;

    auto dis_to_vwap = ask_vwap > 0 ? ave_price / ask_vwap - 1 : 0.0;

    lag_window.push(dis_to_vwap);
    if (lag_window.size() < LAG) {
      value() = 0.0;
      return Status::OK();
    }
    auto max_dis = compute::max(lag_window);
    auto min_dis = compute::min(lag_window);
    value() = max_dis - min_dis;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor