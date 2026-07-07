#pragma once


/*
 * @brief NIO_BASE is an abstract class
 */

struct NIO_BASE
{
  virtual void Clear() = 0;
};


/*
 * @brief NIO_MATRIX<T> can be used to define some data which can be used in each graph node
 */
template<class T>
struct NIO_MATRIX:public NIO_BASE
{
  T ptr_;
  NIO_MATRIX() {}
  T* GetBasePtr() { return &ptr_; }
  const T* GetBasePtr() const { return &ptr_; }
  void Clear() { }
};
