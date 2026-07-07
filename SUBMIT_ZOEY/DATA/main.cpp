#include <bits/stdc++.h>
#include <fstream>
using namespace std;



int main(void)
{
  
  int N = 100000;
  ofstream out("data.csv");
  vector<string> IIs = {"AAPL", "GOOG", "JPM"};
  vector<string> header = {"GOOD header", "BAD header", "NEUTRAL header"};
  vector<string> body = {"GOOD body", "BAD body", "NEUTRAL body"};
  
  int64_t start_unix_timestamp = 1744246595;
  
  for (int i = 0;i < N;++i) {
    string ii = IIs[rand() % IIs.size()];
    
    int prc = 100 + rand() % 10;//price is in range [100, 109] for each stock
    int qty = 1 + rand() % 1000;//qty is in range [1, 1000] for each stock
                              
    string &local_header = header[rand() % header.size()];
    string &local_body = body[rand() % body.size()];
    start_unix_timestamp = start_unix_timestamp + 1 + rand() % 10;
    out<<start_unix_timestamp<<","<<ii<<","<<prc<<","<<qty<<","<<local_header<<","<<local_body<<endl;
  }
 
 return 0;
}
