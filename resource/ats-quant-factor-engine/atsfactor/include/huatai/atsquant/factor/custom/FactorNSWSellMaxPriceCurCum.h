#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include "huatai/atsquant/factor/nonfactor/FactorSecOrderBook.h"

namespace huatai::atsquant::factor {

class FactorNSWSellMaxPriceCurCum : public Factor<> {
  static const int LAG1 = 10;
  static const int LAG2 = 5;
  SlidingWindow<double> sell_price_window{LAG1 + 1};
  std::shared_ptr<FactorSecOrderBook> nonfac;

public:
  FactorNSWSellMaxPriceCurCum() { type_ = __func__; }

  void on_init() override {
    nonfac = get_factor<FactorSecOrderBook>();
    if (nonfac == nullptr) {
      throw std::runtime_error("get nonfactor FactorSecOrderBook error!");
    }
  }

  Status caculate() override {
    auto current_quote = get_market_data().get_prev_n_quote(1);
    auto sample_1s_flag = current_quote.item<QuoteSchema::Index::SAMPLE_1S_FLAG>();
    if (sample_1s_flag) {
      const auto ask_price = nonfac->ask_price_list.back();
      auto ask_price_avg = compute::mean(ask_price, 10);
      sell_price_window.push(ask_price_avg);
      if (sell_price_window.size() < LAG1 + 1) {
        value() = 0;
      }

      auto oqty = compute::diff(sell_price_window);
      std::for_each(oqty.begin(), oqty.end(), [](auto &e) { e = e < 0 ? 0 : e; });
      value() = 0;
      // todo: M_WeightedAvgOfferPx
    } else {
      value() = 0;
    }

    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor