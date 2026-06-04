#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <cmath> // 或者 #include <math.h>

namespace huatai::atsquant::factor {

class FactorLu200Reverse : public Factor<> {
  static const int PREV_LAG = 2;
  static const int half_life = 2;
  static const int lag = 5;
  SlidingWindow<double> lastpx_list{PREV_LAG};
  SlidingWindow<double> lag_list{lag};
  template <typename V> static double getWeight(const V &X) {
    if (X.size() < 5) {
      return 0;
    }
    auto lenth = X.size();
    std::vector<double> weight_vec(lenth, 0);
    auto t = std::pow(0.5, 1.0 / half_life);
    for (int i = 0; i < lenth; i++) {
      weight_vec[i] = std::pow(t, (lenth - 1 - i));
    }
    auto res = 0.0;
    auto sum_weight_vec = compute::sum(weight_vec);
    for (int i = 0; i < lenth; i++) {
      res += X[i] * weight_vec[i] / sum_weight_vec;
    }
    return res;
  }

public:
  FactorLu200Reverse() { type_ = __func__; }

  Status caculate() override {

    auto window = get_market_data().get_prev_n_quote(1);

    auto now_time = window.item<QuoteSchema::Index::TRIGGER_TIME>();
    auto lastpx_now = window.item<QuoteSchema::Index::LAST_PX>();

    lastpx_list.push(lastpx_now);
    auto pct = 100 * (lastpx_list.front() / lastpx_now - 1);
    lag_list.push(pct);
    value() = getWeight(lag_list);
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor