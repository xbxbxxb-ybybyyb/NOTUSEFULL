#include "util.h"

void TopoSort(std::vector<std::set<int>>&parent_raw,
    std::vector<int> &dmgr_order,
    std::vector<int> &dmgr_layer)
{
  int n = parent_raw.size();
  std::vector<std::set<int>> son(n);//make a copy
  for (int x = 0;x < n;++x) {
    for (auto v : parent_raw[x]) {
     son[v].insert(x);
    }
  }
  std::vector<int> indeg(n);
  for (int x = 0;x < n;++x) {
    indeg[x] = parent_raw[x].size();
  }
  std::queue<std::pair<int, int>> q;
  for (int x = 0;x < n;++x) {
    if (indeg[x] == 0) {
      q.push({x, 0});
    }
  }
  while (!q.empty()) {
    std::pair<int, int> y = q.front();
    q.pop();
    dmgr_order.push_back(y.first);
    dmgr_layer.push_back(y.second);

    for (int x :son[y.first]) {
      if (--indeg[x] == 0) {
        q.push({x, y.second + 1});
      }
    }
  }
  if (dmgr_order.size() != dmgr_layer.size()) throw "dmgr_order.size() != dmgr_layer.size()";
}


std::vector<std::string> split(const std::string& s, char delim) 
{
  std::vector<std::string> v;
  auto i = 0;
  auto pos = s.find(delim);
  while (pos != std::string::npos) {
    v.push_back(s.substr(i, pos-i));
    i = ++pos;
    pos = s.find(delim, pos);
  }
  if (pos == std::string::npos) v.push_back(s.substr(i, s.length()));
  return v;
}
