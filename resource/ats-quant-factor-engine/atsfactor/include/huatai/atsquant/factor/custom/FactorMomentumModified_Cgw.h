#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include "huatai/atsquant/factor/schema.h"
#include "huatai/atsquant/factor/sliding_window.h"
#include <arrow/status.h>
#include <cmath>

namespace huatai::atsquant::factor {
class FactorMomentumModified_Cgw : public Factor<> {
  static const int LAG = 5;
  SlidingWindow<double> midprice_window{LAG};
  SlidingWindow<double> delta_ttlvalue_window1{LAG};
  static const int MAAmountLag = 80;
  SlidingWindow<double> delta_ttlvalue_window2{MAAmountLag};
  static const int LAG1 = 2;
  SlidingWindow<double> ttlvalue_window{LAG};
  static const int LAG2 = 6;
  SlidingWindow<double> ema_window{LAG2};

public:
  FactorMomentumModified_Cgw() { type_ = __func__; }
  Status caculate() override {
    auto quote = get_market_data().get_prev_n_quote(1);
    const auto *sellprice = quote.list_item<QuoteSchema::Index::ASK_PRICE>();
    const auto *buyprice = quote.list_item<QuoteSchema::Index::BID_PRICE>();
    auto ttl_value = quote.item<QuoteSchema::Index::TOTAL_TURNOVER>();
    ttlvalue_window.push(ttl_value);
    auto delta_ttlvalue = ttlvalue_window[1] - ttlvalue_window[0];
    delta_ttlvalue_window1.push(delta_ttlvalue);
    delta_ttlvalue_window2.push(delta_ttlvalue);

    auto midprice = (sellprice[0] + buyprice[0]) / 2;
    midprice_window.push(midprice);

    auto emaprice = compute::ewa(midprice_window, 0.5);
    ema_window.push(emaprice);
    auto lastfactorspeed = emaprice / ema_window[0] - 1;
    auto amount =
        std::log((compute::sum(delta_ttlvalue_window1) + 1e-5) / (compute::sum(delta_ttlvalue_window2) + 1e-5));
    value() = 100 * lastfactorspeed * amount;
    return Status::OK();
  }
};
} // namespace huatai::atsquant::factor