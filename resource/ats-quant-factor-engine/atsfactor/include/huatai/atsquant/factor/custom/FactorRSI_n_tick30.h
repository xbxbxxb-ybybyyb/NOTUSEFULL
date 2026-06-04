// ROC                  Rate of change : ((price/prevPrice)-1)*100
#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <arrow/status.h>

namespace huatai::atsquant::factor {

class FactorRSI_n_tick30 : public Factor<> {
  static const int LAG = 30;
  TimeSlidingWindow<double> up_window{LAG};
  TimeSlidingWindow<double> dw_window{LAG};

public:
  FactorRSI_n_tick30() { type_ = __func__; }
  Status caculate() override {
    auto row_tick = get_market_data().get_prev_n_quote(2);
    if (row_tick.len() < 2) {
      return Status::OK();
    }
    auto cur_time = row_tick[1];
    auto prev_time = row_tick[0];

    auto cur_last_px = cur_time.item<QuoteSchema::Index::LAST_PX>();
    auto prev_last_px = prev_time.item<QuoteSchema::Index::LAST_PX>();
    auto now_time = cur_time.item<QuoteSchema::Index::TRIGGER_TIME>();
    auto flag_up = cur_last_px > prev_last_px ? cur_last_px - prev_last_px : 0;
    auto flag_dw = cur_last_px < prev_last_px ? prev_last_px - cur_last_px : 0;

    up_window.push(now_time, flag_up);
    dw_window.push(now_time, flag_dw);
    if(up_window.size()<LAG){
      value() = 0.0;
      return Status::OK();
    }
    auto upavg = compute::ewa(up_window, 0.8);
    auto downavg = compute::ewa(dw_window, 0.8);
    auto rsi = 100 * (upavg / (upavg + downavg));
    value() = rsi;

    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor