#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include "huatai/atsquant/factor/schema.h"
#include <cmath> // 或者 #include <math.h>

namespace huatai::atsquant::factor {

class FactorSeqNo : public Factor<> {

public:
  FactorSeqNo() { type_ = __func__; }

  Status caculate() override {
    auto window = get_market_data().get_prev_n_quote(1);
    value() = window.item<QuoteSchema::Index::TRIGGER_APPL_SEQ_NUM>();
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor