#include "dawnwood/cpu.hpp"
#include <iostream>
#include <fstream>
#include <iomanip>
#include <string>
using namespace dw;
int main(int argc,char** argv){try{
    bool exact=false;u32 steps=64;std::string output;
    for(int i=1;i<argc;++i){std::string a=argv[i];if(a=="--exact")exact=true;else if(a=="--steps"&&i+1<argc){unsigned long v=std::stoul(argv[++i]);if(v>UINT32_MAX)throw std::runtime_error("steps exceed uint32");steps=u32(v);}else if(a=="--out"&&i+1<argc)output=argv[++i];else throw std::runtime_error("Usage: dawnwood_cpu [--exact] [--steps N] [--out trace.jsonl]");}
    CPUField field(3,16,7,exact);std::ofstream file;if(!output.empty()){file.open(output);if(!file)throw std::runtime_error("Cannot open trace");}
    for(u32 i=0;i<steps;++i){field.step();if(file)file<<"{\"epoch\":"<<field.epoch<<",\"cursor\":"<<field.cursor<<",\"digest_fnv1a64\":\""<<std::hex<<field.digest()<<std::dec<<"\",\"cumulative_token_error\":"<<field.error<<"}\n";}
    std::cout<<"{\"backend\":\"CPU reference\",\"codec\":\""<<(exact?"rg8":"bc5-software")<<"\",\"pages\":3,\"side\":16,\"epochs\":"<<field.epoch<<",\"visited_blocks\":"<<field.visited
        <<",\"digest_fnv1a64\":\""<<std::hex<<field.digest()<<std::dec<<"\",\"software_codec_mean_absolute_token_error\":"<<std::setprecision(12)<<(field.visited?double(field.error)/(field.visited*32):0)<<"}\n";
    if(file){file.flush();if(!file)throw std::runtime_error("Trace write failed");}return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}}
