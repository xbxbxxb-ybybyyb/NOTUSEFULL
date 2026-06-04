#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <arrow/status.h>

namespace huatai::atsquant::factor {

class FactorNSWBuyToVWapCorr : public Factor<> {
  static const int LAG = 10;
  SlidingWindow<double> lag_window{LAG};
  SlidingWindow<double> mean_window{LAG};

public:
  FactorNSWBuyToVWapCorr() { type_ = __func__; }

  Status caculate() override {
    static int index = 0;
    index++;
    if (index < LAG) {
      value() = 0.0;
      return Status::OK();
    }
    auto row_tick = get_market_data().get_prev_n_quote(1);

    const auto *current_tick_ask_p = row_tick.list_item<QuoteSchema::Index::ASK_PRICE>();
    const auto *current_tick_bid_p = row_tick.list_item<QuoteSchema::Index::BID_PRICE>();
    const auto *current_tick_ask_v = row_tick.list_item<QuoteSchema::Index::ASK_QTY>();
    const auto *current_tick_bid_v = row_tick.list_item<QuoteSchema::Index::BID_QTY>();
    auto total_value = row_tick.item<QuoteSchema::Index::TOTAL_TURNOVER>();
    auto total_volume = row_tick.item<QuoteSchema::Index::TOTAL_VOLUME>();
    auto ave_price = total_value / total_volume;

    auto bid_vwap =
        compute::mul_sum(current_tick_bid_p, current_tick_bid_v, 10) / compute::sum(current_tick_bid_v, 10) / 100;
    auto ask_vwap =
        compute::mul_sum(current_tick_ask_p, current_tick_ask_v, 10) / compute::sum(current_tick_ask_v, 10) / 100;

    auto dis_to_vwap = bid_vwap > 0 ? 100 * (bid_vwap / ave_price - 1) / (ave_price / ask_vwap - 1) : 0.0;

    lag_window.push(dis_to_vwap);
    auto mean_dis = compute::mean(lag_window);
    mean_window.push(mean_dis);
    std::vector<double> const_array(mean_window.size(), 0);
    for (int i = 0; i < mean_window.size(); i++) {
      const_array[i] = i + 1;
    }

    auto corr_dis = compute::corr(mean_window, const_array);
    value() = corr_dis;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor