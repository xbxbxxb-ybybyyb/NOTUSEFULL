#pragma once
#include<set>
#include<vector>
#include<queue>
#include<cmath>
#include<string>


/*
 * @brief toposort to sort graph node
 * @param parent_raw[i] = {set of node i's father, only when father finish calculation, we can start calculation for i}
 *
 * @param dmgr_order, after function finish, this varialbe keep the correct order calculation 
 * @param dmgr_layer, no use here
 */

void TopoSort(std::vector<std::set<int>>&parent_raw, std::vector<int> &dmgr_order, std::vector<int> &dmgr_layer);



/*
 * @brief split string by delimeter
 * @param parent_raw[i] = {set of node i's father, only when father finish calculation, we can start calculation for i}
 *
 * @param dmgr_order, after function finish, this varialbe keep the correct order calculation 
 * @param dmgr_layer, no use here
 * @return a list of string
 */

std::vector<std::string> split(const std::string& s, char delim);

/*@brief
 * @param
 * @param
 * @return 
 */
template <class InputIter>
int Count(InputIter first, InputIter last)
{
  int count = 0.0;
  for (; first != last; ++first) {
    if(!std::isnan(*first) && !std::isinf(*first)) {
      count += 1;
    }
  }
  return count;
}

template <class InputIter>
double Mean(InputIter first, InputIter last)
{
  double sum = 0;
  double count = 0.0;

  for (; first != last; ++first) {
    if(!std::isnan(*first) && !std::isinf(*first)) {
      sum += *first;
      count += 1.0;
    }
  }
  if (count > 0.0) sum /= count;
  return sum;
}

template <class InputIter>
double SquareMean(InputIter first, InputIter last)
{
  double sum = 0;
  double count = 0.0;

  for (; first != last; ++first) {
    if(!std::isnan(*first) && !std::isinf(*first)) {
      sum += (*first) * (*first);
      count += 1.0;
    }
  }
  if (count > 0.0) sum /= count;
  return sum;
}

template <class InputIter>
double Sigma(InputIter first, InputIter last)
{
  double ssize = Count(first, last);
  if(ssize <= 1) return 0.0;
  double sm = SquareMean(first, last);
  double m = Mean(first, last);
  double adj = (double) (ssize) / (double)(ssize - 1);
  return sqrt(sm - m * m) * sqrt(adj);
}

