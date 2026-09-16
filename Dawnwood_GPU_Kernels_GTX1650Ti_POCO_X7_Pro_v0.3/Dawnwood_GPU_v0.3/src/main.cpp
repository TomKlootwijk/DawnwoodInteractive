#include "runtime.hpp"
#include <iostream>
int main(int argc,char** argv){try{std::vector<std::string> args;for(int i=1;i<argc;++i)args.emplace_back(argv[i]);auto report=execute(args);std::cout<<report<<'\n';return report.find("\"passed\":false")!=std::string::npos?2:0;}catch(const std::exception& e){std::cerr<<"{\"error\":"<<json_escape(e.what())<<"}\n";return 1;}}
