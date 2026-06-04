#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"

#include <array>

namespace huatai::atsquant::factor {

class FactorNSWTickPress : public Factor<> {
  static constexpr std::array<double, 10> WEIGHT = []() {
    std::array<double, 10> arr;
    for (int i = 0; i < 10; i++) {
      arr[i] = (i + 1) / 10.0;
    }
    return arr;
  }();

  static constexpr std::array<double, 10> WEIGHT_RATIO = []() {
    std::array<double, 10> arr;
    for (int i = 0; i < 10; i++) {
      arr[i] = (2 * (10 - i) - 1) / 100.0;
    }
    return arr;
  }();

  static double calpress(const double *price_list, const double *order_qty, int maxvol, double lastpx) {
    std::array<double, 11> res_price_list;
    std::fill(res_price_list.begin(),res_price_list.end(), std::log(price_list[9]));
    res_price_list[0] = std::log(lastpx);

    std::array<double, 10> weight_qty_list(WEIGHT);
    compute::mul(weight_qty_list, maxvol);

    for (int i = 0; i < 10; ++i) {
      double cumvol = 0;
      int j = 0;
      for (; j < 10; ++j) {
        cumvol += order_qty[j];
        if (cumvol > weight_qty_list[i]) {
          res_price_list[i + 1] = std::log(price_list[j]);
          break;
        }
        
      }
    }

    auto _diff = compute::diff(res_price_list);
    compute::mul(_diff, WEIGHT_RATIO);

    return compute::sum(_diff);
  }

public:
  FactorNSWTickPress() { type_ = __func__; }

  Status caculate() override {
    value() = 0;

    auto last_row_tick = get_market_data().get_prev_n_quote(1);

    const auto *current_tick_ask_p = last_row_tick.list_item<QuoteSchema::Index::ASK_PRICE>();
    const auto *current_tick_ask_v = last_row_tick.list_item<QuoteSchema::Index::ASK_QTY>();
    const auto *current_tick_bid_p = last_row_tick.list_item<QuoteSchema::Index::BID_PRICE>();
    const auto *current_tick_bid_v = last_row_tick.list_item<QuoteSchema::Index::BID_QTY>();
    auto last_px = last_row_tick.item<QuoteSchema::Index::LAST_PX>();
    auto sell_vol_sum = compute::sum(current_tick_ask_v, 10);
    auto buy_vol_sum = compute::sum(current_tick_bid_v, 10);
    auto maxvol = std::max(sell_vol_sum, buy_vol_sum);

    auto buy_pressure = calpress(current_tick_bid_p, current_tick_bid_v, maxvol, last_px);
    auto sell_pressure = calpress(current_tick_ask_p, current_tick_ask_v, maxvol, last_px);

    value() = buy_pressure + sell_pressure;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor