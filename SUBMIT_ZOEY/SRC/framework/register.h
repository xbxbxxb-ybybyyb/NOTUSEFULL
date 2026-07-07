#pragma once
#include <bits/stdc++.h>

/*
 * @brief each node of graph is derived from GraphNodeBase, for example class Node1:public GraphNodeBase or class Node2:public GraphNodeBase. graph_node_class_map["Node1"] will return a function pointer, so return graph_node_class_map["Node1"]() will be same as return new Node1();
 */
extern std::map<std::string, std::function<std::shared_ptr<void>()>> graph_node_class_map;



/*
 * @brief if Node1 is derives from GraphNodeBase, GetClassFromName("Node1") will return a pointer of type (Node1*)
 *
 * @param str class name
 * @return pointer to some object(its type is same as parameter str)
 */

std::shared_ptr<void> GetClassFromName(std::string &str);



/*
 * @brief this class help to insert elements to graph_node_class_map
 *
 */
class Register {
public:
  Register(std::string str, std::function<std::shared_ptr<void>()> func);
};



/*
 * @brief this is a macro, whenever we define a derived class from GraphNodeBase, class Node1:public GraphNodeBase, we need to call this macro like this REGISTER(Node1), it will help as to add it to graph_node_class_map
 *
 */

#define REGISTER(classname) \
  class Register##classname {\
    public:                  \
    static std::shared_ptr<classname> instance(){\
      return std::make_shared<classname>();\
    }\
  };\
  auto temp##classname = Register(std::string(#classname), Register##classname::instance);

