#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <cmath>
#include <queue>

namespace huatai::atsquant::factor {
class FactorAsk1StdLS : public Factor<> {
  static const int SHORT = 60;
  static const int LONG = 180;
  TimeSlidingWindow<double> short_window{SHORT};
  TimeSlidingWindow<double> long_window{LONG};


public:
  FactorAsk1StdLS() { type_ = __func__; }

  Status caculate() override {
    // auto market_prev60 = get_market_data().get_prev_n_sec_quote(60);
    // auto market_prev180 = get_market_data().get_prev_n_sec_quote(180);
    // auto market_prev60 = get_market_data().get_prev_n_sec_quote(60);
    // auto ask1_price_60 = market_prev60.level<QuoteSchema::Index::ASK_PRICE>(0);

    // auto market_prev180 = get_market_data().get_prev_n_sec_quote(180);
    // auto ask1_price_180 = market_prev180.level<QuoteSchema::Index::ASK_PRICE>(0);
    auto now_tick = get_market_data().get_prev_n_quote(1);
    auto const *ask_price = now_tick.list_item<QuoteSchema::Index::ASK_PRICE>();
    auto ask1_price = ask_price[0];
    auto now_time = now_tick.item<QuoteSchema::Index::TRIGGER_TIME>();
    short_window.push(now_time, ask1_price);
    long_window.push(now_time, ask1_price);

    auto short_std = compute::std(short_window);
    auto long_std = compute::std(long_window);
    if (long_std == 0 or short_std == 0) {
      value() = 0;
      return Status::OK();
    }
    value() = short_std / long_std;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor