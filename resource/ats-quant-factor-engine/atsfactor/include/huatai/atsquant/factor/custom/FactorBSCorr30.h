#pragma once
#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"

namespace huatai::atsquant::factor {
struct FactorBSCorr30Param {
  int lag = 30;
};
NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE_WITH_DEFAULT(FactorBSCorr30Param, lag)

class FactorBSCorr30 : public Factor<FactorBSCorr30Param> {
public:
  FactorBSCorr30() { type_ = __func__; }

  Status caculate() override {
    auto quotes = get_market_data().get_prev_n_quote(param().lag);
    std::vector<double> ratio(quotes.len(), 0);
    std::vector<double> range(quotes.len(), 0);
    if (quotes.len() >= 5) {

      for (int i = 0; i < quotes.len(); i++) {
        auto quote = quotes[i];
        auto a = quote.item<QuoteSchema::Index::TOTAL_BID_QTY>();
        auto b = quote.item<QuoteSchema::Index::TOTAL_ASK_QTY>();
        ratio[i] = quote.item<QuoteSchema::Index::TOTAL_BID_QTY>() /
                   (quote.item<QuoteSchema::Index::TOTAL_ASK_QTY>() + quote.item<QuoteSchema::Index::TOTAL_BID_QTY>());
        range[i] = i;
      }
      value() = compute::corr(ratio, range);
    } else {
      value() = 0;
    }
    return Status::OK();
  }
};
} // namespace huatai::atsquant::factor