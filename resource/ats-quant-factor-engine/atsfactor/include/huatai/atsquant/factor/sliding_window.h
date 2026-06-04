#pragma once

#include <algorithm>
#include <cstdint>
#include <span>
#include <vector>

namespace huatai::atsquant::factor {
template <typename T, typename SlidingPolicy> class BaseSlidingWindow {
public:
  using value_type = T;
  using __value_data_type = std::vector<value_type>;
  using reference = value_type &;
  using const_reference = const value_type &;
  using size_type = __value_data_type::size_type;
  using allocator_type = __value_data_type::allocator_type;
  using __alloc_traits = std::allocator_traits<allocator_type>;
  using difference_type = __value_data_type::difference_type;
  using pointer = value_type *;
  using const_pointer = const value_type *;
  using iterator = __value_data_type::iterator;
  using const_iterator = __value_data_type::const_iterator;
  using reverse_iterator = std::reverse_iterator<iterator>;
  using const_reverse_iterator = std::reverse_iterator<const_iterator>;

  template <typename... Args> BaseSlidingWindow(Args &&...args) : value_data_{std::forward<Args>(args)...} {}

  template <typename... Args> void push(Args &&...args) { push_(std::forward<Args>(args)...); }

  constexpr pointer data() noexcept { return value_data_.data() + offset_(); }
  constexpr const_pointer data() const noexcept { return value_data_.data() + offset_(); }

  constexpr reference operator[](size_type n) noexcept { return value_data_[n + offset_()]; }
  constexpr const_reference operator[](size_type n) const noexcept { return value_data_[n + offset_()]; }

  constexpr reference at(size_type n) noexcept { return value_data_.at(n + offset_()); }
  constexpr const_reference at(size_type n) const noexcept { return value_data_.at(n + offset_()); }

  constexpr reference front() noexcept { return *begin(); };
  constexpr const_reference front() const noexcept { return *begin(); };

  constexpr reference back() noexcept { return value_data_.back(); };
  constexpr const_reference back() const noexcept { return value_data_.back(); };

  constexpr iterator begin() noexcept { return value_data_.begin() + offset_(); }
  constexpr const_iterator begin() const noexcept { return value_data_.begin() + offset_(); }
  constexpr iterator end() noexcept { return value_data_.end(); };
  constexpr const_iterator end() const noexcept { return value_data_.end(); }

  constexpr reverse_iterator rbegin() noexcept { return reverse_iterator(end()); }
  constexpr const_reverse_iterator rbegin() const noexcept { return const_reverse_iterator(end()); }
  constexpr reverse_iterator rend() noexcept { return reverse_iterator(begin()); }
  constexpr const_reverse_iterator rend() const noexcept { return const_reverse_iterator(begin()); }

  constexpr const_iterator cbegin() const noexcept { return begin(); }
  constexpr const_iterator cend() const noexcept { return end(); }
  constexpr const_iterator crbegin() const noexcept { return rbegin(); }
  constexpr const_iterator crend() const noexcept { return rend(); }

  constexpr size_type size() const noexcept { return end() - begin(); }

  constexpr bool empty() const noexcept { return value_data_.empty(); }

  constexpr const __value_data_type &value_data() const noexcept { return value_data_; }

  constexpr const_iterator prev_n_begin(size_type n) const noexcept {
    if (value_data_.size() < n) {
      return value_data_.begin();
    }
    return value_data_.end() - n;
  }

  constexpr std::span<const value_type> prev_n(size_type n) const noexcept { return {prev_n_begin(n), end()}; }

private:
  constexpr SlidingPolicy &sliding_policy_() noexcept { return *static_cast<SlidingPolicy *>(this); }

  constexpr const SlidingPolicy &sliding_policy_() const noexcept { return *static_cast<const SlidingPolicy *>(this); }

  constexpr size_type offset_() const noexcept { return sliding_policy_().offset(); };

  template <typename... Args> void push_(Args &&...args) { sliding_policy_().push(std::forward<Args>(args)...); }

protected:
  __value_data_type value_data_;
};

template <typename T> class SlidingWindow : public BaseSlidingWindow<T, SlidingWindow<T>> {
public:
  using size_type = BaseSlidingWindow<T, SlidingWindow<T>>::size_type;

  template <typename... Args>
  SlidingWindow(size_type window_size, Args &&...args)
      : BaseSlidingWindow<T, SlidingWindow<T>>(std::forward<Args>(args)...), window_size_(window_size) {}

  constexpr size_type offset() const noexcept {
    return this->value_data_.size() > window_size_ ? this->value_data_.size() - window_size_ : 0;
  }

  template <typename... Args> void push(Args &&...args) { this->value_data_.emplace_back(std::forward<Args>(args)...); }

  constexpr size_type window_size() const noexcept { return window_size_; }

private:
  const size_type window_size_;
};

template <typename T> class TimeSlidingWindow : public BaseSlidingWindow<T, TimeSlidingWindow<T>> {
public:
  using size_type = BaseSlidingWindow<T, SlidingWindow<T>>::size_type;
  using value_type = BaseSlidingWindow<T, SlidingWindow<T>>::value_type;

  template <typename... Args>
  TimeSlidingWindow(int64_t seconds, Args &&...args)
      : BaseSlidingWindow<T, TimeSlidingWindow<T>>(std::forward<Args>(args)...), sample_index_(seconds + 1) {
    sample_index_.push(0);
  }

  constexpr size_type offset() const noexcept { return prev_n_sec_offset(seconds()); }

  template <typename... Args> void push(int64_t timestamp, Args &&...args) {
    this->value_data_.emplace_back(std::forward<Args>(args)...);
    timestamp_.emplace_back(timestamp);

    auto sample_point = timestamp_.front() + sample_index_.value_data().size() * 1000;
    if (sample_point <= timestamp) {
      auto index_back = this->value_data_.size() - 1;
      auto diff = (timestamp - sample_point) / 1000;
      for (uint32_t i = 0; i <= diff; i++) {
        sample_index_.push(index_back);
      }
    }
  }

  constexpr size_type prev_n_sec_offset(size_type n) const noexcept {
    if (sample_index_.size() == 1) {
      return 0;
    }

    auto search_begin = timestamp_.cbegin() + *sample_index_.prev_n_begin(n + 1);
    auto search_end = timestamp_.cbegin() + *sample_index_.prev_n_begin(n);
    int64_t accurate_begin_time = timestamp_.back() - 1000 * n;
    auto accurate_it = std::upper_bound(search_begin, search_end, accurate_begin_time);
    return accurate_it - timestamp_.cbegin();
  }

  constexpr std::span<const value_type> prev_n_sec(size_type n) const noexcept {
    return {this->value_data_.cbegin() + prev_n_sec_offset(n), this->value_data_.cend()};
  }

  constexpr size_type seconds() const noexcept { return sample_index_.window_size() - 1; }

private:
  std::vector<int64_t> timestamp_;
  SlidingWindow<size_type> sample_index_;
};

} // namespace huatai::atsquant::factor