#pragma once

#include "arrow/status.h"
#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"

namespace huatai::atsquant::factor {

class FactorGuangFaTechIndicatorWAD_n_tick20 : public Factor<> {
  static const int LAG1 = 21;
  static const int LAG2 = 20;

  SlidingWindow<double> lag_list{LAG1};
  SlidingWindow<double> wad_list{LAG2};

public:
  FactorGuangFaTechIndicatorWAD_n_tick20() { type_ = __func__; }

  Status caculate() override {
    auto window = get_market_data().get_prev_n_quote(1);

    auto now_time = window.item<QuoteSchema::Index::TRIGGER_TIME>();
    auto lastpx_now = window.item<QuoteSchema::Index::LAST_PX>();
    auto buy1_price = window.list_item<QuoteSchema::Index::BID_PRICE>()[0];
    auto sell1_price = window.list_item<QuoteSchema::Index::ASK_PRICE>()[0];

    lag_list.push(lastpx_now);
    if (lag_list.size() < LAG1) {
      // auto trl = buy1_price;
      // wad_list.push(trl);
      return Status::OK();
    }
    auto trh = std::max(sell1_price, lag_list.front());
    auto trl = std::min(buy1_price, lag_list.front());
    auto ret = (lastpx_now - lag_list.front()) / lastpx_now;
    double wad = ret > 0 ? trh : ret == 0 ? 0.0 : trl;
    wad_list.push(wad);

    auto temp = compute::mean(wad_list) - lastpx_now;
    value() = temp;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor