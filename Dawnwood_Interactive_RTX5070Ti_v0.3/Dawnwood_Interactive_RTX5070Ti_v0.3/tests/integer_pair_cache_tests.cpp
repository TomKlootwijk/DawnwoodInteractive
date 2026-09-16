#include "dawnwood/integer_pair_cache.hpp"
#include <array>
#include <chrono>
#include <iostream>
#include <stdexcept>
using namespace dwi;
static u64 checks=0;
void require(bool p,const char* message){++checks;if(!p)throw std::runtime_error(message);}
int main(){try{
    MathLut lut{};init_math_lut(lut);PairCache cache{};PairCacheAudit audit{};
    require(init_pair_cache(cache,lut,&audit),"symmetry cache accepted by initializer");
    require(sizeof(cache)==65536&&sizeof(PairEntry)==8,"exact cache size");
    std::cout<<"METRIC cache_bytes="<<sizeof(cache)<<"\nMETRIC corrected_entries="<<audit.corrected_entries
             <<"\nMETRIC orientation_corrections="<<audit.corrections<<"\nMETRIC max_phase_correction="<<audit.max_abs_correction
             <<"\nMETRIC radial_invariance_failures="<<audit.invariant_failures<<"\n";
    const std::array<V2,8> offsets{{{0,0},{1,-1},{-65536,32768},{12345,-23456},
                                  {2147483647,2147483647},{(-2147483647-1),(-2147483647-1)},
                                  {-1000000,1000000},{65536,-65536}}};
    std::array<u32,PAIR_CACHE_ENTRIES> coverage{};
    for(u32 r=0;r<256;++r)for(u32 g=0;g<256;++g){
        PairAddress address=pair_address(u8(r),u8(g));require(address.index<PAIR_CACHE_ENTRIES,"canonical cache address bound");++coverage[address.index];
        Hadamard h=hadamard(decode(lut,u8(r)),decode(lut,u8(g)));
        PairChart actual_plus=direct_pair_chart(h.plus),actual_minus=direct_pair_chart(h.minus);
        PairChart cached_plus=pair_plus_chart(cache,u8(r),u8(g)),cached_minus=pair_minus_chart(cache,u8(r),u8(g));
        require(actual_plus.u==cached_plus.u&&actual_plus.phase==cached_plus.phase,"plus pre-offset chart exact");
        require(actual_minus.u==cached_minus.u&&actual_minus.phase==cached_minus.phase,"minus pre-offset chart exact");
        for(V2 d:offsets){
            require(complex_token(lut,h.plus,d.x,d.y)==pair_plus_token(cache,u8(r),u8(g),d.x,d.y),"plus offset encode exact");
            require(complex_token(lut,h.minus,d.x,d.y)==pair_minus_token(cache,u8(r),u8(g),d.x,d.y),"minus offset encode exact");
        }
        if((r>>4)==(g>>4)&&((r^g)&15)==8)require(cached_plus.u==PAIR_ZERO,"antipodal sum exact zero sentinel");
        if(r==g)require(cached_minus.u==PAIR_ZERO,"equal difference exact zero sentinel");
    }
    for(u32 count:coverage)require(count==8,"every canonical cache entry has eight orientations");
    // Independent timing is CPU-only and not a claim of GPU acceleration.
    volatile u64 checksum=0;constexpr u32 repeats=4;
    auto begin=std::chrono::steady_clock::now();
    for(u32 repeat=0;repeat<repeats;++repeat)for(u32 r=0;r<256;++r)for(u32 g=0;g<256;++g){
        Hadamard h=hadamard(decode(lut,u8(r)),decode(lut,u8(g)));
        checksum+=complex_token(lut,h.plus,repeat,0);checksum+=complex_token(lut,h.minus,-i32(repeat),1);
    }
    auto middle=std::chrono::steady_clock::now();
    for(u32 repeat=0;repeat<repeats;++repeat)for(u32 r=0;r<256;++r)for(u32 g=0;g<256;++g){
        checksum+=pair_plus_token(cache,u8(r),u8(g),repeat,0);checksum+=pair_minus_token(cache,u8(r),u8(g),-i32(repeat),1);
    }
    auto end=std::chrono::steady_clock::now();
    double direct_ms=std::chrono::duration<double,std::milli>(middle-begin).count();
    double cached_ms=std::chrono::duration<double,std::milli>(end-middle).count();
    std::cout<<"METRIC cpu_direct_ms="<<direct_ms<<"\nMETRIC cpu_cached_ms="<<cached_ms
             <<"\nMETRIC cpu_speed_ratio="<<direct_ms/cached_ms<<"\nMETRIC checksum="<<checksum<<"\n";
    std::cout<<"SUMMARY "<<checks<<" assertions, 0 failures\n";return 0;
}catch(const std::exception& e){std::cerr<<"FAIL "<<e.what()<<" after "<<checks<<" assertions\n";return 1;}}

