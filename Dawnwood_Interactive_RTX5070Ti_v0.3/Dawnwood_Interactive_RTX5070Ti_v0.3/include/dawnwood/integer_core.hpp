// Integer edition 1: explicit finite numerical law for the source architecture.
#pragma once
#include "dawnwood/integer_math.hpp"
#include "dawnwood/integer_pair_cache.hpp"
#include <type_traits>
namespace dwi {
using dw::Op; using dw::Aux; using dw::Stage; using dw::BC5;
using dw::OP_COUNT; using dw::BODY_WORDS; using dw::THREADS;
using dw::mix; using dw::parity; using dw::jit; using dw::rotl; using dw::pack16;
using dw::signed16; using dw::ins; using dw::execute;
using dw::encode_bc5; using dw::decode_bc5; using dw::encode_bc5_with_error;
using dw::page_bytes; using dw::budget_bytes;
constexpr i32 GOLD_Q16=25032;
constexpr u32 MASK_WORDS=15*8;
// Exact sign specialization of support_sdf. Magnitudes remain available in
// integer_math.hpp; routing needs only >=0, so avoid square roots/projections.
template<class LUT> DW_HD inline bool support_nonnegative_fast(const LUT& lut,const Op& o,Chart q){
    Chart center{i32(o.location&65535),i32(o.location>>16),0};V2 p=chart_delta(q,center);
    i32 x=4*p.x,y=4*p.y,r=i32(o.support&65535)+1;u32 shape=(o.support>>16)%6;
    if(shape==0)return i64(x)*x+i64(y)*y>=i64(r)*r;
    if(shape==1){
        i32 a=i32(round_div_const<5>(r));
        bool stem=abs_i32_geometry(x)<a&&abs_i32_geometry(y+i32(round_div_const<10>(i64(r)*3)))<r;
        bool bar=abs_i32_geometry(x)<r&&abs_i32_geometry(y-i32(round_div_const<5>(i64(r)*3)))<a;
        return !(stem||bar);
    }
    if(shape==2||shape==3){
        if(shape==3)r=i32(round_div_const<4>(i64(r)*3));
        // Strict interior of triangle (-r,-r),(r,-r),(0,r).
        bool inside=y>-r&&i64(r)*x*2+i64(r)*(r-y)>0&&-i64(r)*x*2+i64(r)*(r-y)>0;
        return !inside;
    }
    if(shape==4){V4 a=klein(lut,q.u,q.v),b=klein(lut,center.u,center.v);
        i64 dx=i64(a.x)-b.x,dy=i64(a.y)-b.y,dz=i64(a.z)-b.z,dw_=i64(a.w)-b.w;
        return dx*dx+dy*dy+dz*dz+dw_*dw_>=i64(r)*r;
    }
    return true;
}
struct Config {u32 dt_q16=1024,inverse_gain_q16=16384,jitter=1,mutate=1,hops=2;};
DW_HD inline bool valid_config(const Config& c){return c.dt_q16>=1&&c.dt_q16<=65536&&c.inverse_gain_q16<=65536&&c.jitter<=1&&c.mutate<=1;}
struct MemoryOps {
    const Op* records;const u32* masks;
    DW_HD Op op(u32 i)const{return records[i];}
    DW_HD u32 predicate(u32 i,u8 token)const{return (masks[i*8+(token>>5)]>>(token&31))&1;}
};
template<bool MASKED,class OPS,class LUT> DW_HD inline u32 route(const OPS& ops,const LUT& lut,u8 token,u32 j,u32 history){
    Chart q=token_chart(token);u32 i=0;
    for(u32 depth=0;depth<4;++depth){Op o=ops.op(i);
        u32 predicate=MASKED?ops.predicate(i,token):u32(support_sdf(lut,o,q)>=0);
        u32 b=predicate^j^q.flip^(history&1)^(o.route&1);i=2*i+1+b;history=rotl(history,1);}
    return i;
}
template<class LUT> DW_HD inline V2 deriv(const LUT& lut,V2 q,V2 drive,i32 coupling){
    return {drive.x+mul_q15(coupling,sin_q15(lut,q.y)),drive.y+mul_q15(coupling,cos_q15(lut,q.x))};
}
template<class LUT> DW_HD inline V2 rk4(const LUT& lut,V2 q,V2 drive,i32 coupling,i32 dt){
    V2 a=deriv(lut,q,drive,coupling);
    V2 b=deriv(lut,{q.x+i32(round_div_const<131072>(i64(dt)*a.x)),q.y+i32(round_div_const<131072>(i64(dt)*a.y))},drive,coupling);
    V2 c=deriv(lut,{q.x+i32(round_div_const<131072>(i64(dt)*b.x)),q.y+i32(round_div_const<131072>(i64(dt)*b.y))},drive,coupling);
    // Two one-unit Y events are applied to the fourth derivative input only.
    V2 d=deriv(lut,{q.x+mul_q16(dt,c.x),q.y+mul_q16(dt,c.y)+2},drive,coupling);
    return {q.x+i32(round_div_const<393216>(i64(dt)*(i64(a.x)+2*b.x+2*c.x+d.x))),
            q.y+i32(round_div_const<393216>(i64(dt)*(i64(a.y)+2*b.y+2*c.y+d.y)))};
}
struct NoPairCache {};
template<bool MASKED,class OPS,class LUT,class PAIRS=NoPairCache> DW_HD inline Stage evolve(const u8* r,const u8* g,Aux a,u8 nr,u8 ng,const OPS& ops,const LUT& lut,
    u64 epoch,u64 index,u64 seed,const Config& cfg,const PAIRS& pairs={}){
    Stage out{};u32 j=cfg.jitter?jit(epoch,index,seed):0;Chart q=token_chart(r[0]);
    u32 node=route<MASKED>(ops,lut,r[0],j,a.history);Op o=ops.op(node);Chart cg=token_chart(g[0]);
    u16 regs[8]={u16(q.u),u16(q.v),u16(cg.u),u16(cg.v),u16(a.history),u16(a.inverse_t),u16(o.location),1};
    execute(ops.op((o.links&31)%OP_COUNT),regs);execute(ops.op(((o.links>>5)&31)%OP_COUNT),regs);execute(o,regs);
    i32 dd=delta_turn(i64(token_chart(nr).v)-2*q.v+token_chart(ng).v);
    V2 drive{i32(round_div_const<2>(signed16(regs[0]))),i32(round_div_const<2>(signed16(regs[1])))+GOLD_Q16};
    i32 coupling=i32(round_div_const<16>(i64(o.coeff&65535)+1));
    V2 next=rk4(lut,{q.u,q.v},drive,coupling,i32(cfg.dt_q16));
    i32 du=next.x-q.u,dv=next.y-q.v+mul_q16(i32(cfg.dt_q16),dd);
    i32 da=dv+mul_q16(i32(cfg.inverse_gain_q16),signed16(a.inverse_t));
    i32 db=-dv+mul_q16(i32(cfg.inverse_gain_q16),signed16(a.inverse_t>>16));
    u16 pa=u16(floor_mod_turn(da)),pb=u16(floor_mod_turn(db));
    out.aux.inverse_t=pack16(u16(0u-pa),u16(0u-pb));
    i32 qa=signed16(pa),qb=signed16(pb);
    for(u32 k=0;k<16;++k){Complex x=decode(lut,r[k]),y=decode(lut,g[k]);
        i64 dot=i64(x.x)*y.x+i64(x.y)*y.y; // Q22 amplitude squared
        i32 twist=i32(round_div_const<4194304>(i64(cfg.dt_q16)*dot));
        if constexpr(std::is_same<PAIRS,NoPairCache>::value){
            Hadamard h=hadamard(x,y);
            out.r[k]=u8(complex_token(lut,h.plus,du,qa+twist)^j);
            out.g[k]=u8(complex_token(lut,h.minus,-du,qb-twist)^j);
        }else{
            out.r[k]=u8(pair_plus_token(pairs,r[k],g[k],du,qa+twist)^j);
            out.g[k]=u8(pair_minus_token(pairs,r[k],g[k],-du,qb-twist)^j);
        }
    }
    out.aux.history=rotl(a.history,1)^j^fold(i64(q.u)+du,i64(q.v)+da).flip^parity(u32(out.r[0])|(u32(out.g[0])<<8))^mix(u32(epoch));
    out.bc5=encode_bc5_with_error(out.r,out.g,out.quant_error);
    out.feedback=u32(out.r[0])|(u32(out.g[0])<<8)|(node<<16)|(j<<24);return out;
}
DW_HD inline Op mutate_op(const Op* old,u32 i,const Stage& s,u64 epoch,u64 seed,const Config& cfg){
    Op o=old[i];if(!cfg.mutate)return o;u32 ref=((o.links>>5)&31)%OP_COUNT;
    u32 h=mix(s.feedback^s.aux.history^old[ref].history^u32(epoch)^u32(seed));u32 j=cfg.jitter?jit(epoch,i,seed):0;
    o.code[(h>>5)%BODY_WORDS]^=j<<(h&31);o.links^=j<<((h>>11)%10);o.support^=j<<((h>>16)%19);o.coeff^=j<<((h>>21)&31);
    Chart p=fold(i64(o.location&65535)+mul_q16(signed16(s.feedback),i32(cfg.dt_q16)),
                 i64(o.location>>16)+mul_q16(i32(cfg.dt_q16),GOLD_Q16)+j);
    o.location=pack16(u32(p.u),u32(p.v));o.route^=p.flip^j;o.last_rg=s.feedback;o.history=s.aux.history;o.inverse_t=s.aux.inverse_t;return o;
}
DW_HD inline void seed_block(u64 index,u64 seed,u8* r,u8* g,Aux& a){
    u32 h=mix(u32(index)^mix(u32(index>>32))^u32(seed));
    for(u32 k=0;k<16;++k){u32 v=h+(k+u32(index))*0x61c88647u;u32 radial=1+(v>>28)%15;
        r[k]=u8((radial<<4)|((v>>16)&15));g[k]=u8((radial<<4)|(((v>>16)+8)&15));}
    a={mix(h),0};
    // [0,2,0,1]: amplitude 2 maps to LP8 0xb0, history zero, identity inverse.
    if(index==0){for(u32 k=0;k<16;++k){r[k]=0;g[k]=176;}a={0,0};}
}
// Seed body is shared as integer data with the historical edition; locations are
// initialized by the integer logarithm and the Q16 golden step.
DW_HD inline Op seed_op(u32 i) {
    Op o{};
    i64 log_ratio=i64(log2_q16(2*i+1))-log2_q16(2*OP_COUNT);
    i32 u=i32(round_div_const<15>(log_ratio+8*65536));
    o.location=pack16(u32(floor_mod_turn(u)),u32(floor_mod_turn(i64(i)*GOLD_Q16)));
    u32 shape=(i==7?1:(i==8?2:(i==10?3:(i==11?4:(i==12?5:0)))));
    o.support=24000u|(shape<<16);o.links=((i+1)%OP_COUNT)|(((i+OP_COUNT-1)%OP_COUNT)<<5);
    o.coeff=pack16(4096+i*71,6144+i*31);
    o.code[0]=ins(8,0,0,2);o.code[1]=ins(9,2,0,2);o.code[2]=ins(4,1,1,4);
    o.code[3]=ins(12,3,3,1,25032);o.code[4]=ins(14,0,0,0,211+i*37);
    o.code[5]=ins(1,2,2,6);o.code[6]=ins(14,1,1,0,137+i);o.code[7]=ins(4,3,3,5);
    // Named seed bodies. Kinematics, SDFs and packing also have their native
    // evaluation stages; these words are their editable contributions to the field.
    switch(i){
    case 0:o.code[0]=ins(15,1,4,1,0);o.code[1]=ins(2,3,7,3);break; // Klein return
    case 1:break; // Hadamard seed above
    case 2:o.code[0]=ins(14,0,0,0,4096);o.code[1]=ins(14,1,1,0,4096);break;
    case 3:o.code[0]=ins(12,0,0,2,21845);o.code[1]=ins(12,1,1,3,43690);break;
    case 4:o.code[0]=ins(14,1,1,0,25032);o.code[1]=ins(14,3,3,0,25032);break;
    case 5:o.code[0]=ins(14,1,1,0,1024);o.code[1]=ins(14,3,3,0,64512);break;
    case 6:o.code[0]=ins(3,0,0,2);o.code[1]=ins(3,1,1,3);o.code[2]=ins(1,0,0,1);break;
    case 7:o.code[0]=ins(10,0,0,6);o.code[1]=ins(11,1,1,6);break;
    case 8:o.code[0]=ins(2,0,0,1);o.code[1]=ins(10,0,0,6);break;
    case 9:o.code[0]=ins(3,0,0,0);o.code[1]=ins(3,1,1,1);break;
    case 10:o.code[0]=ins(2,0,0,1);o.code[1]=ins(11,0,0,6);break;
    case 11:o.code[0]=ins(3,0,0,0);o.code[1]=ins(3,1,1,1);o.code[2]=ins(1,0,0,1);break;
    case 12:o.code[0]=ins(10,0,0,2);o.code[1]=ins(10,1,1,3);break;
    case 13:o.code[0]=ins(2,1,3,1);o.code[1]=ins(2,1,1,3);break;
    case 14:o.code[0]=ins(12,0,0,2,25032);o.code[1]=ins(12,1,1,3,25032);break;
    case 15:o.code[0]=ins(13,0,0,0,0);o.code[1]=ins(13,1,0,0,2);o.code[2]=ins(13,2,0,0,0);o.code[3]=ins(13,3,0,0,1);break;
    case 16:o.code[0]=ins(14,1,1,0,2);o.code[1]=ins(14,3,3,0,2);break;
    case 17:o.code[0]=ins(15,0,4,0,0);o.code[1]=ins(4,2,0,2);break;
    case 18:o.code[0]=ins(13,7,0,0,0);o.code[1]=ins(2,1,7,5);break;
    case 19:o.code[0]=ins(1,1,1,5);o.code[1]=ins(1,3,3,5);break;
    case 20:o.code[0]=ins(4,0,0,4);o.code[1]=ins(4,1,1,4);break;
    case 21:o.code[0]=ins(1,0,0,0);o.code[1]=ins(14,0,0,0,1);break;
    case 22:o.code[0]=ins(13,7,0,0,0);o.code[1]=ins(2,1,7,1);break;
    case 23:o.code[0]=ins(13,7,0,0,1);o.code[1]=ins(7,4,4,7);break;
    case 24:o.code[0]=ins(0,0,0,0);o.code[1]=ins(0,2,2,2);break;
    case 25:o.code[0]=ins(15,0,4,0,0);o.code[1]=ins(15,2,4,2,0);break;
    case 26:o.code[0]=ins(10,0,0,2);o.code[1]=ins(11,2,0,2);break;
    case 27:o.code[0]=ins(13,7,0,0,1);o.code[1]=ins(7,0,0,7);break;
    case 28:o.code[0]=ins(15,0,4,7,0);o.code[1]=ins(4,1,1,0);break;
    case 29:o.code[0]=ins(14,4,4,0,1);o.code[1]=ins(14,1,1,0,1);break;
    case 30:o.code[0]=ins(4,0,0,4);o.code[1]=ins(4,1,1,6);break;
    }
    o.last_rg=0x00000200u;o.history=mix(i);o.inverse_t=0;o.route=0;return o;
}
} // namespace dwi
