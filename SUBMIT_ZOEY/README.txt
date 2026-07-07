#Project Overview
This is a C++ project that demonstrates the implementation 
of a graph-based computiional framework that calculates 
feature for financial instrumentss based on a stream of news updates. 



#File Structure

The project is organized into the following directories and files:

.
├── SRC/                                # Source code files
│   ├── main1.cpp                       # example usage1
│   ├── main2.cpp                       # example usage2
│   ├── main3.cpp                       # example usage3
│   ├── main4.cpp                       # example usage4
│   ├── main5.cpp                       # example usage5
│   ├── framwork/                       # framework related files
│   │   ├── graphnode.h                 # graph node definition header file
│   │   ├── graphnode.cc                # graph node implementation
│   │   ├── niobase.h                   # NIO data, a struct data that can be shared between different graph nodes
│   │   ├── register.h                  # register each graph node
│   │   ├── register.cc                 # register each graph node(implementation)
│   │   ├── registerdata.h              # register NIO data, header file
│   │   ├── registerdata.cc             # register NIO data, implementation
│   │   ├── util.h                      # some utility function, header file
│   │   └── util.cc                     # some utility function, implementation
│   └── DATA/                           # input and output data dir
│       ├── a.out                       # exe to generate input data
│       ├── data.csv                    # input data
│       ├── main.cpp                    # source code to generate input
│       ├── output1_from_EXE4.csv       # output1 from EXE4
│       ├── output_from_EXE4.csv        # output from EXE4 
│       ├── output_from_EXE5.csv        # output from EXE5 
│       ├── output_from_EXE2.csv        # output from EXE2 
│       ├── output_from_EXE3_AAPL.csv   # output from EXE3_AAPL
│       ├── output_from_EXE3_GOOG.csv   # output from EXE3_GOOG
│       └── output_from_EXE3_JPM.csv    # output from EXE3_JPM.
├── CMakeLists.txt                      # CMake configuration file
└── README.txt                          # readme file


#How to compile

To install and build the project, follow these steps:

1. Make sure your machine has cmake and g++


2. Navigate to the project directory:
cd [project-name]


3. Create a build directory:
mkdir build
cd build


4. Run CMake to configure the project:
cmake ..


5.Build the project:
make 
(or make -j20)



6. After building the project, you can run the executable from the build directory:

there are 4 different examples:
./build/EXE1 (define some graph nodes, calculating some PV features when good news or bad news happens, only for AAPL)
./build/EXE2 (define some graph nodes, calculating some PV features when good news or bad news happens, and save features for AAPL)
./build/EXE3 (define some graph nodes, calculating some PV features when good news or bad news happens, and save features for more than one instruments)
./build/EXE4 (this example is a more complex version, adding a graph node showing how to calculate a groupby algo in a stream way, and adding a node keep the feature when an hourly event happens)
./build/EXE5 (showing other usage of the framework)




#Notes

This project compiles the framework code into the libframework.so
and each example link to this libframework.so, so if you run it 
in other directories, need to set the environment variable LD_LIBRARY_PATH
correctly

#Contact

For questions or feedback, please contact zhanyixiaolu@gmail.com
