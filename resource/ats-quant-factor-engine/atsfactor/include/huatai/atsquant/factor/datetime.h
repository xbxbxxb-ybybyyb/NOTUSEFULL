#pragma once

#include <cstdint>
#include <cstdlib>

namespace huatai::atsquant::factor {

inline uint32_t mdtime_millis_since_today(uint32_t time) {
  // time = 150002123
  auto d = std::div(time, 1000);

  // millis = 123
  uint32_t millis = d.rem;

  d = std::div(d.quot, 100);

  // s = 2
  uint32_t s = d.rem;

  d = std::div(d.quot, 100);

  // m = 0
  uint32_t m = d.rem;

  // h = 15
  uint32_t h = d.quot;

  return (h * 3600 + m * 60 + s) * 1000 + millis;
}

} // namespace huatai::atsquant::factor