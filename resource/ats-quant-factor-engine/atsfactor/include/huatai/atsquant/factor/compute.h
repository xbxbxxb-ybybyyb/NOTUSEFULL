#pragma once

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <functional>
#include <omp.h>
#include <type_traits>
#include <vector>

namespace huatai::atsquant::factor::compute {

template <typename T>
  requires std::is_arithmetic_v<T>
T sum(const T *vec, size_t size) {
  T t{};
#pragma omp simd reduction(+ : t)
  for (size_t i = 0; i < size; i++) {
    t += vec[i];
  }
  return t;
}

template <typename V>
  requires std::is_arithmetic_v<typename V::value_type>
V::value_type sum(const V &v) {
  return sum(v.data(), v.size());
}

template <typename T, typename F>
  requires std::is_arithmetic_v<T> && std::is_invocable_r_v<bool, F, size_t, const T &>
std::vector<T> filter(const T *vec, size_t size, F &&filter_fn) {
  std::vector<T> result;
  result.reserve(size);
  for (size_t i = 0; i < size; ++i) {
    if (std::invoke(std::forward<F>(filter_fn), i, vec[i])) {
      result.emplace_back(vec[i]);
    }
  }

  return result;
}

template <typename V, typename F>
  requires std::is_arithmetic_v<typename V::value_type> &&
           std::is_invocable_r_v<bool, F, size_t, const typename V::value_type &>
std::vector<typename V::value_type> filter(const V &v, F &&filter_fn) {
  return filter(v.data(), v.size(), std::forward<F>(filter_fn));
}

template <typename T>
  requires std::is_arithmetic_v<T>
double mean(const T *vec, size_t size) {
  return sum(vec, size) / (double)size;
}

template <typename V>
  requires std::is_arithmetic_v<typename V::value_type>
double mean(const V &v) {
  return mean(v.data(), v.size());
}

template <typename T>
  requires std::is_arithmetic_v<T>
T max(const T *vec, size_t size) {
  T t = -std::numeric_limits<T>::max();
#pragma omp simd reduction(max : t)
  for (size_t i = 0; i < size; i++) {
    t = t > vec[i] ? t : vec[i];
  }
  return t;
}

template <typename V>
  requires std::is_arithmetic_v<typename V::value_type>
V::value_type max(const V &v) {
  return max(v.data(), v.size());
}

template <typename T>
  requires std::is_arithmetic_v<T>
T min(const T *vec, size_t size) {
  T t = std::numeric_limits<T>::max();
#pragma omp simd reduction(min : t)
  for (size_t i = 0; i < size; i++) {
    t = t < vec[i] ? t : vec[i];
  }
  return t;
}

template <typename V>
  requires std::is_arithmetic_v<typename V::value_type>
V::value_type min(const V &v) {
  return min(v.data(), v.size());
}

template <typename T>
  requires std::is_arithmetic_v<T>
double std(const T *vec, size_t size) {
  if (size < 2) {
    return 0;
  }

  double u = mean(vec, size);
  double t{};
#pragma omp simd reduction(+ : t)
  for (size_t i = 0; i < size; i++) {
    double v = vec[i] - u;
    t += v * v;
  }
  return std::sqrt(t / (double)(size - 1));
}

template <typename V>
  requires std::is_arithmetic_v<typename V::value_type>
double std(const V &v) {
  return std(v.data(), v.size());
}

template <typename T>
  requires std::is_arithmetic_v<T>
int64_t imax(const T *vec, size_t size) {
  if (size == 0) {
    return -1;
  }

  // todo: simd
  // todo: UT
  int64_t index = 0;
  for (size_t i = 1; i < size; i++) {
    index = vec[i] > vec[index] ? i : index;
  }
  return index;
}

template <typename V>
  requires std::is_arithmetic_v<typename V::value_type>
int64_t imax(const V &v) {
  return imax(v.data(), v.size());
}

template <typename T>
  requires std::is_arithmetic_v<T>
int64_t imin(const T *vec, size_t size) {
  if (size == 0) {
    return -1;
  }

  // todo: simd
  // todo: UT
  int64_t index = 0;
  for (size_t i = 1; i < size; i++) {
    index = vec[i] < vec[index] ? i : index;
  }
  return index;
}

template <typename V>
  requires std::is_arithmetic_v<typename V::value_type>
int64_t imin(const V &v) {
  return imin(v.data(), v.size());
}

template <typename T>
  requires std::is_arithmetic_v<T>
void add(T *vec, size_t size, T scalar) {
#pragma omp simd
  for (size_t i = 0; i < size; i++) {
    vec[i] += scalar;
  }
}

template <typename V>
  requires std::is_arithmetic_v<typename V::value_type>
void add(V &v, typename V::value_type scalar) {
  add(v.data(), v.size(), scalar);
}

template <typename T>
  requires std::is_arithmetic_v<T>
T *add(T *v1, const T *v2, size_t size) {
#pragma omp simd
  for (size_t i = 0; i < size; i++) {
    v1[i] += v2[i];
  }
  return v1;
}

template <typename V1, typename V2>
  requires std::is_arithmetic_v<typename V1::value_type> &&
           std::is_same_v<typename V1::value_type, typename V2::value_type>
V1::value_type *add(V1 &v1, const V2 &v2) {
  if (v1.size() != v2.size()) {
    return nullptr;
  }

  return add(v1.data(), v2.data(), v1.size());
}

template <typename T>
  requires std::is_arithmetic_v<T>
void sub(T *vec, size_t size, T scalar) {
#pragma omp simd
  for (size_t i = 0; i < size; i++) {
    vec[i] -= scalar;
  }
}

template <typename V>
  requires std::is_arithmetic_v<typename V::value_type>
void sub(V &v, typename V::value_type scalar) {
  sub(v.data(), v.size(), scalar);
}

template <typename T>
  requires std::is_arithmetic_v<T>
T *sub(T *v1, const T *v2, size_t size) {
#pragma omp simd
  for (size_t i = 0; i < size; i++) {
    v1[i] -= v2[i];
  }
  return v1;
}

template <typename V1, typename V2>
  requires std::is_arithmetic_v<typename V1::value_type> &&
           std::is_same_v<typename V1::value_type, typename V2::value_type>
V1::value_type *sub(V1 &v1, const V2 &v2) {
  if (v1.size() != v2.size()) {
    return nullptr;
  }

  return sub(v1.data(), v2.data(), v1.size());
}

template <typename T>
  requires std::is_arithmetic_v<T>
void mul(T *vec, size_t size, T scalar) {
#pragma omp simd
  for (size_t i = 0; i < size; i++) {
    vec[i] *= scalar;
  }
}

template <typename V>
  requires std::is_arithmetic_v<typename V::value_type>
void mul(V &v, typename V::value_type scalar) {
  mul(v.data(), v.size(), scalar);
}

template <typename T>
  requires std::is_arithmetic_v<T>
T *mul(T *v1, const T *v2, size_t size) {
#pragma omp simd
  for (size_t i = 0; i < size; i++) {
    v1[i] *= v2[i];
  }
  return v1;
}

template <typename V1, typename V2>
  requires std::is_arithmetic_v<typename V1::value_type> &&
           std::is_same_v<typename V1::value_type, typename V2::value_type>
V1::value_type *mul(V1 &v1, const V2 &v2) {
  if (v1.size() != v2.size()) {
    return nullptr;
  }

  return mul(v1.data(), v2.data(), v1.size());
}

template <typename T>
  requires std::is_arithmetic_v<T>
void div(T *vec, size_t size, T scalar) {
#pragma omp simd
  for (size_t i = 0; i < size; i++) {
    vec[i] /= scalar;
  }
}

template <typename V>
  requires std::is_arithmetic_v<typename V::value_type>
void div(V &v, typename V::value_type scalar) {
  div(v.data(), v.size(), scalar);
}

template <typename T>
  requires std::is_arithmetic_v<T>
T *div(T *v1, const T *v2, size_t size) {
#pragma omp simd
  for (size_t i = 0; i < size; i++) {
    v1[i] /= v2[i];
  }
  return v1;
}

template <typename V1, typename V2>
  requires std::is_arithmetic_v<typename V1::value_type> &&
           std::is_same_v<typename V1::value_type, typename V2::value_type>
V1::value_type *div(V1 &v1, const V2 &v2) {
  if (v1.size() != v2.size()) {
    return nullptr;
  }

  return div(v1.data(), v2.data(), v1.size());
}

template <typename T>
  requires std::is_arithmetic_v<T>
T mul_sum(const T *v1, const T *v2, size_t size) {
  T s{};
#pragma omp simd reduction(+ : s)
  for (size_t i = 0; i < size; i++) {
    s += v1[i] * v2[i];
  }
  return s;
}

template <typename V1, typename V2>
  requires std::is_arithmetic_v<typename V1::value_type> &&
           std::is_same_v<typename V1::value_type, typename V2::value_type>
V1::value_type mul_sum(const V1 &v1, const V2 &v2) {
  return mul_sum(v1.data(), v2.data(), std::min(v1.size(), v2.size()));
}

template <typename T>
  requires std::is_arithmetic_v<T>
void diff(T *vec_dst, const T *vec_src, size_t size) {
#pragma omp simd
  for (size_t i = 1; i < size; i++) {
    vec_dst[i - 1] = vec_src[i] - vec_src[i - 1];
  }
}

template <typename T>
  requires std::is_arithmetic_v<T>
std::vector<T> diff(const T *vec_src, size_t size) {
  if (size < 2) {
    return {};
  }

  std::vector<T> vec_dst(size - 1);
  diff(vec_dst.data(), vec_src, size);
  return vec_dst;
}

template <std::size_t N, typename T>
  requires std::is_arithmetic_v<T>
std::array<T, N - 1> diff(const T *vec_src) {
  static_assert(N >= 2, "diff() can only be applied to an array size >= 2");
  std::array<T, N - 1> vec_dst;
  diff(vec_dst.data(), vec_src, N);
  return vec_dst;
}

template <typename T, std::size_t N>
  requires std::is_arithmetic_v<T>
std::array<T, N - 1> diff(const std::array<T, N> &vec_src) {
  return diff<N>(vec_src.data());
}

template <typename V>
  requires std::is_arithmetic_v<typename V::value_type>
std::vector<typename V::value_type> diff(const V &vec_src) {
  return diff(vec_src.data(), vec_src.size());
}

template <typename T>
  requires std::is_arithmetic_v<T>
T ewa(const T *vec, size_t size, double alpha) {
  double w = 1, s1 = 0, s2 = 0;
  for (size_t i = 0; i < size; i++) {
    s1 += w * vec[size - 1 - i];
    s2 += w;
    w *= 1 - alpha;
  }
  return s1 / s2;
}

template <typename V>
  requires std::is_arithmetic_v<typename V::value_type>
typename V::value_type ewa(const V &vec_src, double alpha) {
  return ewa(vec_src.data(), vec_src.size(), alpha);
}

template <typename T>
  requires std::is_arithmetic_v<T>
double cov(const T *x, const T *y, size_t size) {
  double mean_x = mean(x, size);
  double mean_y = mean(y, size);
  double cov_xy = 0;

#pragma omp simd reduction(+ : cov_xy)
  for (size_t i = 0; i < size; i++) {
    double x1 = x[i] - mean_x;
    double y1 = y[i] - mean_y;

    cov_xy += x1 * y1;
  }

  return cov_xy / size;
}

template <typename V1, typename V2>
  requires std::is_arithmetic_v<typename V1::value_type> &&
           std::is_same_v<typename V1::value_type, typename V2::value_type>
double cov(const V1 &v1, const V2 &v2) {
  if (v1.size() != v2.size()) {
    return NAN;
  }

  return cov(v1.data(), v2.data(), v1.size());
}

template <typename T>
  requires std::is_arithmetic_v<T>
double corr(const T *x, const T *y, size_t size) {
  double mean_x = mean(x, size);
  double mean_y = mean(y, size);
  double std_x = 0;
  double std_y = 0;
  double cov_xy = 0;

#pragma omp simd reduction(+ : std_x, std_y, cov_xy)
  for (size_t i = 0; i < size; i++) {
    double x1 = x[i] - mean_x;
    double y1 = y[i] - mean_y;

    std_x += x1 * x1;
    std_y += y1 * y1;
    cov_xy += x1 * y1;
  }

  return cov_xy / std::sqrt(std_x * std_y);
}

template <typename V1, typename V2>
  requires std::is_arithmetic_v<typename V1::value_type> &&
           std::is_same_v<typename V1::value_type, typename V2::value_type>
double corr(const V1 &v1, const V2 &v2) {
  if (v1.size() != v2.size()) {
    return NAN;
  }

  return corr(v1.data(), v2.data(), v1.size());
}

template <typename T>
  requires std::is_arithmetic_v<T>
double kurtosis(const T *vec, size_t size) {
  if (size < 4) {
    return NAN;
  }

  double u = mean(vec, size);
  double sigma = std(vec, size);
  double r = 0;
#pragma omp simd reduction(+ : r)
  for (size_t i = 0; i < size; i++) {
    double t = (vec[i] - u) / sigma;
    r += t * t * t * t;
  }

  r *= size * (size + 1) / (double)((size - 1) * (size - 2) * (size - 3));
  r -= 3 * (size - 1) * (size - 1) / (double)((size - 2) * (size - 3));

  return r;
}

template <typename V>
  requires std::is_arithmetic_v<typename V::value_type>
double kurtosis(const V &v) {
  return kurtosis(v.data(), v.size());
}

template <typename T>
  requires std::is_arithmetic_v<T>
double skewness(const T *vec, size_t size) {
  if (size < 3) {
    return NAN;
  }

  double u = mean(vec, size);
  double sigma = std(vec, size);
  double r = 0;

#pragma omp simd reduction(+ : r)
  for (size_t i = 0; i < size; i++) {
    double t = (vec[i] - u) / sigma;
    r += t * t * t;
  }

  r *= size / (double)((size - 1) * (size - 2));

  return r;
}

template <typename V>
  requires std::is_arithmetic_v<typename V::value_type>
double skewness(const V &v) {
  return skewness(v.data(), v.size());
}

} // namespace huatai::atsquant::factor::compute