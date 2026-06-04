#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include "huatai/atsquant/factor/nonfactor/FactorSecTradeAgg.h"

namespace huatai::atsquant::factor {

class FactorBuyWillingByPrice : public Factor<> {
public:
  FactorBuyWillingByPrice() { type_ = __func__; }
  std::shared_ptr<FactorSecTradeAgg> nonfac;

  void on_init() override {
    nonfac = get_factor<FactorSecTradeAgg>();
    if (nonfac == nullptr) {
      throw std::runtime_error("get nonfactor FactorSecBuySellNum error!");
    }
  }

  Status caculate() override {
    auto current_quote = get_market_data().get_prev_n_quote(1);
    auto sample_1s_flag = current_quote.item<QuoteSchema::Index::SAMPLE_1S_FLAG>();
    // todo: 1s采样计算计算太多，可能导致耗时太集中？
    if (sample_1s_flag) {
      if (nonfac->trade_buy_money_list.size() > 0) {
        auto buy_money = nonfac->trade_buy_money_list.back();
        auto sell_money = nonfac->trade_sell_money_list.back();
        auto buy_num = nonfac->trade_buy_num_list.back();
        auto sell_num = nonfac->trade_sell_num_list.back();

        auto diff_v = (buy_money / (buy_num + 1) - sell_money / (sell_num + 1));
        auto sum_v = (buy_money / (buy_num + 1) + sell_money / (sell_num + 1));
        if (sum_v == 0) {
          value() = 0;
        } else {
          value() = diff_v / sum_v;
        }
      } else {
        value() = 0;
      }
    }
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor