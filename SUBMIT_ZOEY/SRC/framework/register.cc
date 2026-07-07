#include "register.h"

/*
 * @brief each node of graph is derived from GraphNodeBase, for example class Node1:public GraphNodeBase or class Node2:public GraphNodeBase. graph_node_class_map["Node1"] will return a function pointer, so return graph_node_class_map["Node1"]() will be same as return new Node1();
 */
std::map<std::string, std::function<std::shared_ptr<void>()>> graph_node_class_map;



/*
 * @brief if Node1 is derives from GraphNodeBase, GetClassFromName("Node1") will return a pointer of type (Node1*)
 *
 * @param str class name
 * @return pointer to some object(its type is same as parameter str)
 */
std::shared_ptr<void> GetClassFromName(std::string &str)
{
  if (graph_node_class_map.find(str) == graph_node_class_map.end()) {
    std::cout<<"graph_node_class_map.size() == "<<graph_node_class_map.size()<<std::endl;
    std::cout<<"factor:"<<str<<" miss"<<std::endl;
    assert(false);
    return nullptr;
  }
  return graph_node_class_map[str]();
}


Register:: Register(std::string str, std::function<std::shared_ptr<void>()> func) {
  graph_node_class_map.insert(std::make_pair(str, func));
}
