#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <numeric> // 包含 std::accumulate

namespace huatai::atsquant::factor {

class FactorAvgOutRatio_n_tick20 : public Factor<> {
  static const int TIME_PERIOD = 20;

public:
  FactorAvgOutRatio_n_tick20() { type_ = __func__; }

  Status caculate() override {
    auto table = get_market_data().get_prev_n_sec_quote(TIME_PERIOD);
    if (table.len() < 2) {
      return Status::OK();
    }

    // const auto *lastpx = table.item_address<QuoteSchema::Index::LAST_PX>();
    // auto delta_lastpx = compute::diff<TIME_PERIOD>(lastpx);
    // std::array<int, delta_lastpx.size()> ret_down;
    // for (size_t i = 0; i < delta_lastpx.size(); ++i) {
    //   if (delta_lastpx[i] < 0) {
    //     ret_down[i] = 1; // 如果元素小于0，则置位1
    //   } else {
    //     ret_down[i] = 0; // 不满足条件则置位0
    //   }
    // }

    // auto *volume_trade = table.item_address<QuoteSchema::Index::TOTAL_VOLUME>();
    // auto *num_trades = table.item_address<QuoteSchema::Index::TRADES>();
    // auto delta_volume_trade = compute::diff<TIME_PERIOD>(volume_trade);
    // auto delta_num_trades = compute::diff<TIME_PERIOD>(num_trades);

    // auto temp1_sum = 0.0;
    // for (size_t i = 0; i < ret_down.size(); ++i) {
    //   temp1_sum += ret_down[i] * delta_num_trades[i];
    // }

    // auto temp2_sum = 0.0;
    // for (size_t i = 0; i < ret_down.size(); ++i) {
    //   temp2_sum += ret_down[i] * delta_volume_trade[i];
    // }

    // auto down_avg = 0.0;
    // down_avg = temp1_sum > 0.0 ? temp2_sum / temp1_sum : 0.0;
    auto first_volume_trade = table.item<QuoteSchema::Index::TOTAL_VOLUME>();
    auto first_num_trades = table.item<QuoteSchema::Index::TRADES>();

    auto last = table[-1];
    auto last_volume_trade = last.item<QuoteSchema::Index::TOTAL_VOLUME>();
    auto last_num_trades = last.item<QuoteSchema::Index::TRADES>();
    auto volume_per_trade = (last_num_trades - first_num_trades) == 0.0
                                ? 0.0
                                : (last_volume_trade - first_volume_trade) / (last_num_trades - first_num_trades);

    value() = volume_per_trade;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor