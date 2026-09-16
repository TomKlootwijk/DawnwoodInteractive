// Exact acceleration of the integer numerical law by D4 pair symmetry.
// This cache changes implementation cost, not the chart/Hadamard quantizers.
#pragma once
#include "dawnwood/integer_math.hpp"
namespace dwi {
constexpr u32 PAIR_CACHE_ENTRIES=8192;
constexpr i32 PAIR_ZERO=(-2147483647-1);
struct PairEntry {
    i32 u;
    u16 phase;
    // Eight signed 2-bit corrections, orientation=(swap?4:0)|rotation.
    // Zero in the absence of CORDIC roundoff asymmetry; never changes radius.
    u16 corrections;
};
static_assert(sizeof(PairEntry)==8,"pair cache entry wire format");
struct PairChart {i32 u;u16 phase;};
struct PairAddress {u32 index,rotation,swap;};
struct PairCache {
    PairEntry entries[PAIR_CACHE_ENTRIES];
    DW_HD PairEntry pair(u32 i)const{return entries[i];}
};
static_assert(sizeof(PairCache)==65536,"D4 pair cache is exactly 64 KiB");
struct PairCacheAudit {
    u32 corrected_entries=0,corrections=0,max_abs_correction=0;
    u32 invariant_failures=0,correction_overflows=0;
};
DW_HD inline PairAddress pair_address(u8 r,u8 g){
    u32 rotation=(r&15)>>2,rphase=r&3;
    u32 gphase=((g&15)+16-4*rotation)&15,swap=rphase>=2;
    if(swap){rphase=3-rphase;gphase=(19-gphase)&15;}
    return {(((r>>4)*2+rphase)<<8)|(g&240)|gphase,rotation,swap};
}
DW_HD inline PairChart direct_pair_chart(Complex z){
    u64 r2=squared_norm(z);if(!r2)return {PAIR_ZERO,0};
    return {i32(round_div_const<15>(i64(log2_q16(r2))-14*65536)),atan2_turn16(z.y,z.x)};
}
DW_HD inline i32 unpack_phase_correction(u16 packed,u32 orientation){
    u32 value=(u32(packed)>>(2*orientation))&3;
    return value>=2?i32(value)-4:i32(value);
}
template<class CACHE> DW_HD inline PairChart pair_plus_chart(const CACHE& cache,u8 r,u8 g){
    PairAddress address=pair_address(r,g);PairEntry value=cache.pair(address.index);
    if(value.u==PAIR_ZERO)return {PAIR_ZERO,0};
    i32 phi=address.swap?16384-i32(value.phase):i32(value.phase);
    phi+=i32(address.rotation*16384)+unpack_phase_correction(value.corrections,address.rotation|(address.swap<<2));
    return {value.u,u16(u32(phi)&65535)};
}
template<class CACHE> DW_HD inline PairChart pair_minus_chart(const CACHE& cache,u8 r,u8 g){
    return pair_plus_chart(cache,r,u8(g^8));
}
DW_HD inline u8 pair_chart_token(PairChart p,i32 du=0,i32 dv=0){
    return p.u==PAIR_ZERO?0:chart_token(i64(p.u)+du,i64(p.phase)+dv);
}
template<class CACHE> DW_HD inline u8 pair_plus_token(const CACHE& cache,u8 r,u8 g,i32 du=0,i32 dv=0){
    return pair_chart_token(pair_plus_chart(cache,r,g),du,dv);
}
template<class CACHE> DW_HD inline u8 pair_minus_token(const CACHE& cache,u8 r,u8 g,i32 du=0,i32 dv=0){
    return pair_chart_token(pair_minus_chart(cache,r,g),du,dv);
}
template<class CACHE> DW_HD inline u8 cached_token(const CACHE& cache,u8 r,u8 g,i32 du=0,i32 dv=0){
    return pair_plus_token(cache,r,g,du,dv);
}
// Host initialization is integer-only as well. Every possible orientation is
// compared with the base numerical law before this cache is accepted.
// Return false if D4 breaks radius invariance or requires a correction outside
// the representable signed2-bit range; callers must then keep the direct path.
template<class LUT> inline bool init_pair_cache(PairCache& cache,const LUT& lut,PairCacheAudit* audit=nullptr){
    PairCacheAudit stats{};
    for(u32 index=0;index<PAIR_CACHE_ENTRIES;++index){
        u8 r=u8(((index>>9)<<4)|((index>>8)&1)),g=u8(index);
        PairChart canonical=direct_pair_chart(hadamard(decode(lut,r),decode(lut,g)).plus);
        PairEntry entry{canonical.u,canonical.phase,0};bool changed=false;
        for(u32 swap=0;swap<2;++swap)for(u32 rotation=0;rotation<4;++rotation){
            u32 rp=swap?3-(r&15):r&15,gp=swap?(19-(g&15))&15:g&15;
            u8 transformed_r=u8((r&240)|((rp+4*rotation)&15));
            u8 transformed_g=u8((g&240)|((gp+4*rotation)&15));
            PairChart actual=direct_pair_chart(hadamard(decode(lut,transformed_r),decode(lut,transformed_g)).plus);
            if(actual.u!=canonical.u){++stats.invariant_failures;continue;}
            if(actual.u==PAIR_ZERO)continue;
            i32 predicted=(swap?16384-i32(canonical.phase):i32(canonical.phase))+i32(rotation*16384);
            i32 correction=delta_turn(i32(actual.phase)-predicted);
            u32 absolute=u32(correction<0?-correction:correction);
            if(absolute>stats.max_abs_correction)stats.max_abs_correction=absolute;
            if(correction<-2||correction>1){++stats.correction_overflows;continue;}
            entry.corrections|=u16((u32(correction)&3)<<(2*(rotation|(swap<<2))));
            if(correction){++stats.corrections;changed=true;}
        }
        if(changed)++stats.corrected_entries;
        cache.entries[index]=entry;
    }
    if(audit)*audit=stats;
    return stats.invariant_failures==0&&stats.correction_overflows==0;
}
} // namespace dwi
