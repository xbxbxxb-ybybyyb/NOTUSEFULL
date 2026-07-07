#pragma once
#include <bits/stdc++.h>
using namespace std;



/*
 * @brief DataRegister help to keep the data used by each graph nodes
 *
 */

class DataRegister
{
public:
  std::map<std::string, int> nioname;
  std::map<int, int> niomidmp;
  std::vector<struct NIO_BASE*> nioptr;
  void RegisterNiodata(int mid, const std::string &name, struct NIO_BASE *niodata);


/*
 * @brief GetData help to get the reference of data used by some graph node
 * @param dataname is key to the find data reference
 * @return data reference of some data of type NIO_BASE
 */

  template<template<typename T> class A, typename B>
  A<B>& GetData(const std::string &dataname)
  {
    if (nioname.count(dataname) == 0) {
      std::cerr<<"can not find:"<<dataname<<std::endl;
    }
    if (nioname.count(dataname) <= 0) throw "nioname.count(dataname) <= 0";
    int off = nioname[dataname];
    if (nioptr[off] == NULL) throw "nioptr[off] == NULL";
    return *(dynamic_cast<A<B>*>(nioptr[off]));
  }
};
