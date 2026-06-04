#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include "huatai/atsquant/factor/nonfactor/FactorSecBuySellNum.h"
#include "huatai/atsquant/factor/simple_regression.h"
#include <stdexcept>

namespace huatai::atsquant::factor {

class FactorBuyNumCorr3 : public Factor<> {
  static const int lag1 = 30;
  TimeSlidingWindow<double> ret_list{lag1};
  std::shared_ptr<FactorSecBuySellNum> nonfac;

public:
  FactorBuyNumCorr3() { type_ = __func__; }

  void on_init() override {
    nonfac = get_factor<FactorSecBuySellNum>();
    if (nonfac == nullptr) {
      throw std::runtime_error("get nonfactor FactorSecBuySellNum error!");
    }
  }

  Status caculate() override {
    if (nonfac->num_bids_sec_list.size() < 5) {
      value() = 0;
    } else {
      // simple regression
      SimpleRegression regression;
      auto bid_num_list = nonfac->num_bids_sec_list.prev_n(lag1);
      for (int i = 1; i <= std::min(nonfac->num_bids_sec_list.size(), (size_t)lag1); ++i) {
        regression.addData(i, bid_num_list[i - 1]);
      }
      value() = regression.getSlope(); // 计算斜率
    }
    return Status::OK();
  }
};
} // namespace huatai::atsquant::factor