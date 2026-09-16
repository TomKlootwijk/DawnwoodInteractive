// Dawnwood Interactive | Tom Klootwijk | NL200678942 | 10-07-1990
// Native binding v0.3. All persistent code and routing words are data in the field.
#pragma once
#include <cstdint>
#include <cmath>
#include <cstddef>
#ifndef DW_REFERENCE_KERNEL
#define DW_REFERENCE_KERNEL 0
#endif
#ifdef __CUDACC__
#define DW_HD __host__ __device__
#else
#define DW_HD
#endif
namespace dw {
using u8=std::uint8_t; using u16=std::uint16_t; using u32=std::uint32_t;
using u64=std::uint64_t; using i32=std::int32_t; using i64=std::int64_t;
constexpr u32 OP_COUNT=31, BODY_WORDS=8, THREADS=128;
constexpr float TAU=6.2831853071795864769f, GOLD=0.3819660112501051518f;
constexpr float RHO_MIN=-4.f, RHO_SPAN=7.5f;
struct V2 { float x,y; };
struct alignas(16) V4 { float x,y,z,w; };
struct alignas(16) BC5 { u32 x,y,z,w; };
struct Aux { u32 history,inverse_t; };
struct alignas(16) Op {
    u32 location;      // low/high u16: quotient chart u,v
    u32 support;       // low u16: support radius; bits16..18: SDF primitive
    u32 links;         // two five-bit operator references
    u32 coeff;         // two u16 kinematic coefficients
    u32 code[BODY_WORDS]; // actual executable register-program words
    u32 last_rg,history,inverse_t,route;
};
static_assert(sizeof(Op)==64,"operator wire format");
struct alignas(16) Stage {
    BC5 bc5;
    u8 r[16],g[16];    // exact RG8 alternative; desired values for BC5 error audit
    Aux aux;
    u32 feedback,quant_error;
};
static_assert(sizeof(Stage)==64,"stage wire format");
struct Config { float dt=1.f/64.f, inverse_gain=0.25f; u32 jitter=1,mutate=1,hops=2; };
DW_HD inline u32 rotl(u32 x,u32 k) { k&=31; return (x<<k)|(x>>((32-k)&31)); }
DW_HD inline u32 mix(u32 x) { x^=x>>16; x*=0x7feb352du; x^=x>>15; x*=0x846ca68bu; return x^(x>>16); }
DW_HD inline u32 parity(u32 x) { x^=x>>16; x^=x>>8; x^=x>>4; return (0x6996u>>(x&15))&1; }
DW_HD inline i32 signed16(u32 x) { x&=65535; return x<32768?i32(x):i32(x)-65536; }
DW_HD inline float fract(float x) { return x-::floorf(x); }
DW_HD inline float delta(float x) { return x-::floorf(x+0.5f); }
DW_HD inline u32 pack16(u32 a,u32 b) { return (a&65535u)|((b&65535u)<<16); }
DW_HD inline u16 turn16(float x) { return u16(u32(::floorf(fract(x)*65536.f))); }
DW_HD inline u64 child(u64 i,u32 bit) { return 2*i+1+(bit&1); }
DW_HD inline u32 jit(u64 epoch,u64 index,u64 seed) {
    return parity(mix(u32(index)^u32(index>>32)^mix(u32(epoch))^u32(seed)^u32(seed>>32)));
}
struct Chart { float u,v; u32 flip; };
DW_HD inline Chart fold(float u,float v) {
    float n=::floorf(u); u32 odd=(::fmodf(::fabsf(n),2.f)>=1.f)?1u:0u;
    return {u-n,fract(odd?-v:v),odd};
}
DW_HD inline V4 klein(float u,float v) {
    float cv=::cosf(TAU*v),sv=::sinf(TAU*v),rad=2.f+0.5f*cv;
    return {rad*::cosf(TAU*u),rad*::sinf(TAU*u),0.5f*sv*::cosf(0.5f*TAU*u),0.5f*sv*::sinf(0.5f*TAU*u)};
}
// LP8: high nibble 1..15 selects log-radius cell; low nibble selects phase cell.
// High nibble zero is the zero-amplitude symbol. Cell-centre reconstruction.
DW_HD inline Chart token_chart(u8 q) {
    u32 hi=q>>4;
    return {hi?(float(hi)-0.5f)/15.f:0.f,(float(q&15)+0.5f)/16.f,0};
}
DW_HD inline u8 chart_token(float u,float v) {
    Chart a=fold(u,v);
    u32 h=u32(::floorf(a.u*15.f))+1, p=u32(::floorf(a.v*16.f));
    return u8((h<<4)|(p&15));
}
DW_HD inline V4 lut_entry(u32 q) {
    Chart c=token_chart(u8(q)); float r=(q>>4)?::exp2f(RHO_MIN+RHO_SPAN*c.u):0.f;
    return {r*::cosf(TAU*c.v),r*::sinf(TAU*c.v),c.u,c.v};
}
DW_HD inline u8 complex_token(float x,float y,float du=0,float dv=0) {
    float r2=x*x+y*y;
    if(r2==0.f) return 0; // exact zero is a representation symbol, not a cutoff
    return chart_token((0.5f*::log2f(r2)-RHO_MIN)/RHO_SPAN+du,::atan2f(y,x)/TAU+dv);
}
// BC4/BC5 UNORM block wire format: two 8-bit endpoints and sixteen 3-bit indices.
DW_HD inline void palette(u8 a,u8 b,u8* p) {
    p[0]=a;p[1]=b;
    if(a>b) for(u32 i=1;i<=6;++i) p[i+1]=u8(((7-i)*u32(a)+i*u32(b))/7);
    else { for(u32 i=1;i<=4;++i) p[i+1]=u8(((5-i)*u32(a)+i*u32(b))/5);p[6]=0;p[7]=255; }
}
// Retained literally for packed-output equivalence and the reference build.
DW_HD inline u64 encode_bc4_reference(const u8* q) {
    u8 lo=q[0],hi=q[0];for(u32 i=1;i<16;++i){lo=q[i]<lo?q[i]:lo;hi=q[i]>hi?q[i]:hi;}
    u8 p[8];palette(hi,lo,p);u64 out=u64(hi)|(u64(lo)<<8);
    for(u32 i=0;i<16;++i){u32 best=0,err=256;for(u32 j=0;j<8;++j){u32 e=q[i]>p[j]?q[i]-p[j]:p[j]-q[i];if(e<err){err=e;best=j;}}out|=u64(best)<<(16+3*i);}
    return out;
}
// Descending palette order is 0,2,3,4,5,6,7,1. Midpoint comparisons
// preserve the original lowest-index tie break, including repeated entries.
DW_HD inline u32 bc4_selector(u32 q,u32 hi,u32 lo,const u8* p) {
    u32 twice=2*q;
    u32 rank=u32(twice<hi+p[2])+u32(twice<u32(p[2])+p[3])+u32(twice<u32(p[3])+p[4])
            +u32(twice<u32(p[4])+p[5])+u32(twice<u32(p[5])+p[6])+u32(twice<u32(p[6])+p[7]);
    u32 best=rank?rank+1:0;
    return twice<=u32(p[7])+lo?1:best;
}
DW_HD inline u64 encode_bc4_optimized(const u8* q,u32& error) {
    u8 lo=q[0],hi=q[0];for(u32 i=1;i<16;++i){lo=q[i]<lo?q[i]:lo;hi=q[i]>hi?q[i]:hi;}
    u64 out=u64(hi)|(u64(lo)<<8);error=0;
    if(hi==lo)return out; // Every sample uses index zero, including 0 and 255.
    u8 p[8];palette(hi,lo,p);
    for(u32 i=0;i<16;++i){
        u32 best=bc4_selector(q[i],hi,lo,p);
        // Avoid a dynamically indexed local array on CUDA. The endpoint modes
        // here are known: extrema encoding always uses hi>lo or the constant case.
        u32 value=best==0?hi:(best==1?lo:((8-best)*u32(hi)+(best-1)*u32(lo))/7);
        error+=q[i]>value?q[i]-value:value-q[i];out|=u64(best)<<(16+3*i);
    }
    return out;
}
DW_HD inline u64 encode_bc4(const u8* q) {
#if DW_REFERENCE_KERNEL
    return encode_bc4_reference(q);
#else
    u32 error;return encode_bc4_optimized(q,error);
#endif
}
DW_HD inline u8 decode_bc4(u64 b,u32 pixel) {
    u8 p[8];palette(u8(b),u8(b>>8),p);return p[(b>>(16+3*(pixel&15)))&7];
}
DW_HD inline BC5 encode_bc5(const u8* r,const u8* g) {
    u64 a=encode_bc4(r),b=encode_bc4(g);return {u32(a),u32(a>>32),u32(b),u32(b>>32)};
}
DW_HD inline BC5 encode_bc5_with_error(const u8* r,const u8* g,u32& error) {
    u32 er,eg;u64 a=encode_bc4_optimized(r,er),b=encode_bc4_optimized(g,eg);
    error=er+eg;return {u32(a),u32(a>>32),u32(b),u32(b>>32)};
}
DW_HD inline void decode_bc5(BC5 b,u8* r,u8* g) {
    u64 a=u64(b.x)|(u64(b.y)<<32),c=u64(b.z)|(u64(b.w)<<32);
    for(u32 i=0;i<16;++i){r[i]=decode_bc4(a,i);g[i]=decode_bc4(c,i);}
}
DW_HD inline u32 quant_error(const BC5& b,const u8* r,const u8* g) {
    u8 a[16],c[16];decode_bc5(b,a,c);u32 e=0;
    for(u32 i=0;i<16;++i){e+=r[i]>a[i]?r[i]-a[i]:a[i]-r[i];e+=g[i]>c[i]?g[i]-c[i]:c[i]-g[i];}return e;
}
DW_HD inline u32 ins(u32 op,u32 dst,u32 a,u32 b,u32 imm=0) {
    return (op&15)|((dst&7)<<4)|((a&7)<<7)|((b&7)<<10)|((imm&65535)<<16);
}
// This VM has total arithmetic on 16-bit words; overflow is modular by definition.
DW_HD inline void execute(const Op& op,u16* r) {
    for(u32 i=0;i<BODY_WORDS;++i){
        u32 w=op.code[i],f=w&15,d=(w>>4)&7,a=r[(w>>7)&7],b=r[(w>>10)&7],k=w>>16,z=0;
        switch(f){
        case 0:z=a;break; case 1:z=a+b;break; case 2:z=a-b;break;
        case 3:z=(a*b)>>16;break;case 4:z=a^b;break;case 5:z=a&b;break;case 6:z=a|b;break;
        case 7:{u32 n=b&15;z=((a<<n)|(a>>((16-n)&15)));break;}
        // The largest product is 65536*23170 < INT32_MAX. These operations
        // therefore need no 64-bit arithmetic; signed division still truncates.
#if DW_REFERENCE_KERNEL
        case 8:z=u32((i64(signed16(a)+signed16(b))*23170)/32768);break;
        case 9:z=u32((i64(signed16(a)-signed16(b))*23170)/32768);break;
#else
        case 8:z=u32(((signed16(a)+signed16(b))*23170)/32768);break;
        case 9:z=u32(((signed16(a)-signed16(b))*23170)/32768);break;
#endif
        case 10:z=a<b?a:b;break;case 11:z=a>b?a:b;break;
#if DW_REFERENCE_KERNEL
        case 12:z=u32((u64(a)*(65535-k)+u64(b)*k)/65535);break;
#else
        // Convex integer weights sum to 65535, so the numerator is at most
        // 65535^2 = 4294836225 and fits uint32 without overflow.
        case 12:z=(a*(65535-k)+b*k)/65535;break;
#endif
        case 13:z=k;break;case 14:z=a+k;break;case 15:z=parity(a)?b:k;break;
        }r[d]=u16(z);
    }
}
DW_HD inline V2 chart_delta(Chart a,Chart b) {
    V2 best{0,0};float dd=1e30f;
    for(i32 k=-1;k<=1;++k){float x=a.u-(b.u+float(k));float y=delta(a.v-((k&1)?-b.v:b.v));float d=x*x+y*y;if(d<dd){dd=d;best={x,y};}}
    return best;
}
DW_HD inline float sd_box(float x,float y,float a,float b) {
    float qx=::fabsf(x)-a,qy=::fabsf(y)-b;
    float ox=qx>0?qx:0,oy=qy>0?qy:0;
    return ::sqrtf(ox*ox+oy*oy)+::fminf(::fmaxf(qx,qy),0.f);
}
DW_HD inline float sd_triangle(float x,float y,float r) {
    // Exact distance to an isosceles triangle; winding fixes the interior sign.
    const V2 p[3]={{-r,-r},{r,-r},{0,r}};float d2=1e30f;bool inside=true;
    for(u32 j=0;j<3;++j){V2 a=p[j],b=p[(j+1)%3];float ex=b.x-a.x,ey=b.y-a.y,px=x-a.x,py=y-a.y;
        float t=(px*ex+py*ey)/(ex*ex+ey*ey);t=::fmaxf(0.f,::fminf(1.f,t)); // segment projection
        float dx=px-t*ex,dy=py-t*ey;d2=::fminf(d2,dx*dx+dy*dy);inside=inside&&(ex*py-ey*px>=0.f);
    }return (inside?-1.f:1.f)*::sqrtf(d2);
}
DW_HD inline float support_sdf(const Op& o,Chart q) {
    Chart c{float(o.location&65535)/65536.f,float(o.location>>16)/65536.f,0};
    V2 p=chart_delta(q,c);float r=(float(o.support&65535)+1.f)/262144.f;
    switch((o.support>>16)%6){
    case 0:return ::sqrtf(p.x*p.x+p.y*p.y)-r; // circle
    case 1:return ::fminf(sd_box(p.x,p.y+r*0.3f,r*0.2f,r),sd_box(p.x,p.y-r*0.6f,r,r*0.2f)); // T union
    case 2:return sd_triangle(p.x,p.y,r); // pyramid side
    case 3:return sd_triangle(p.x,p.y,r*0.75f); // cone meridian
    case 4:{V4 a=klein(q.u,q.v),b=klein(c.u,c.v);float x=a.x-b.x,y=a.y-b.y,z=a.z-b.z,w=a.w-b.w;return ::sqrtf(x*x+y*y+z*z+w*w)-r;}
    default:return ::sqrtf(p.x*p.x+p.y*p.y); // apex point
    }
}
DW_HD inline u32 route(const Op* ops,Chart q,u32 j,u32 history) {
    u32 i=0;
    // Eytzinger implicit binary decision tree: all child addresses are inferred.
    while(child(i,1)<OP_COUNT){u32 b=(support_sdf(ops[i],q)>=0.f)^j^q.flip^(history&1)^(ops[i].route&1);i=u32(child(i,b));history=rotl(history,1);}
    return i;
}
DW_HD inline V2 deriv(V2 q,V2 drive,float coupling) {
    return {drive.x+coupling*::sinf(TAU*q.y),drive.y+coupling*::cosf(TAU*q.x)};
}
DW_HD inline V2 rk4(V2 q,V2 drive,float coupling,float dt,float y_unit=1.f/65536.f) {
    V2 a=deriv(q,drive,coupling);
    V2 b=deriv({q.x+dt*a.x*.5f,q.y+dt*a.y*.5f},drive,coupling);
    V2 c=deriv({q.x+dt*b.x*.5f,q.y+dt*b.y*.5f},drive,coupling);
    V2 d=deriv({q.x+dt*c.x,q.y+dt*c.y+2.f*y_unit},drive,coupling);
    return {q.x+dt*(a.x+2*b.x+2*c.x+d.x)/6.f,q.y+dt*(a.y+2*b.y+2*c.y+d.y)/6.f};
}
DW_HD inline Op seed_op(u32 i) {
    Op o{};
    float rho=0.5f*::log2f((float(i)+.5f)/float(OP_COUNT));
    o.location=pack16(turn16((rho-RHO_MIN)/RHO_SPAN),turn16(float(i)*GOLD));
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
DW_HD inline void seed_block(u64 index,u64 seed,u8* r,u8* g,Aux& a) {
    // Golden-step integer ordering; physical 4x4 blocks are storage, not a spatial grid.
    u32 h=mix(u32(index)^mix(u32(index>>32))^u32(seed));
    for(u32 k=0;k<16;++k){u32 v=h+(k+u32(index))*0x61c88647u;u32 radial=1+(v>>28)%15;
        r[k]=u8((radial<<4)|((v>>16)&15));g[k]=u8((radial<<4)|(((v>>16)+8)&15));}
    a={mix(h),0};
    // Source wavefront [0,2,0,1]: zero/2 amplitudes, B=0, inverse-T identity.
    if(index==0){for(u32 k=0;k<16;++k){r[k]=0;g[k]=complex_token(2.f,0.f);}a={0,0};}
}
constexpr float PAIR_ZERO=-1e30f;
// All 256^2 immutable LP8 pairs fit in a 1 MiB table. Store only the portion
// before the evolving chart offsets; dot coupling still uses the original LUT.
// Build this on the same device, from the same uploaded LUT, with --fmad=false.
DW_HD inline V2 pair_chart(float x,float y) {
    float r2=x*x+y*y;
    if(r2==0.f)return {PAIR_ZERO,0.f};
    return {(0.5f*::log2f(r2)-RHO_MIN)/RHO_SPAN,::atan2f(y,x)/TAU};
}
DW_HD inline V4 pair_entry(V4 x,V4 y) {
    float hx=(x.x+y.x)*0.7071067811865475f,hy=(x.y+y.y)*0.7071067811865475f;
    float gx=(x.x-y.x)*0.7071067811865475f,gy=(x.y-y.y)*0.7071067811865475f;
    V2 a=pair_chart(hx,hy),b=pair_chart(gx,gy);return {a.x,a.y,b.x,b.y};
}
DW_HD inline u8 pair_token(float u,float v,float du,float dv) {
    return u==PAIR_ZERO?u8(0):chart_token(u+du,v+dv);
}
DW_HD inline Stage evolve(const u8* r,const u8* g,Aux a,u8 nr,u8 ng,const Op* ops,const V4* lut,
                          u64 epoch,u64 index,u64 seed,const Config& cfg,const V4* pairs=nullptr) {
    Stage out{};u32 j=cfg.jitter?jit(epoch,index,seed):0;Chart q=token_chart(r[0]);
    u32 node=route(ops,q,j,a.history);const Op& o=ops[node];
    u16 regs[8]={turn16(q.u),turn16(q.v),turn16(token_chart(g[0]).u),turn16(token_chart(g[0]).v),
        u16(a.history),u16(a.inverse_t),u16(o.location),u16(1)};
    execute(ops[(o.links&31)%OP_COUNT],regs);execute(ops[((o.links>>5)&31)%OP_COUNT],regs);execute(o,regs);
    float dd=delta(token_chart(nr).v-2.f*q.v+token_chart(ng).v);
    V2 drive{float(signed16(regs[0]))/131072.f,float(signed16(regs[1]))/131072.f+GOLD};
    float coupling=(float(o.coeff&65535)+1.f)/1048576.f;
    V2 next=rk4({q.u,q.v},drive,coupling,cfg.dt);
    float du=next.x-q.u,dv=next.y-q.v+cfg.dt*dd;
    float inv_a=float(signed16(a.inverse_t))/65536.f,inv_b=float(signed16(a.inverse_t>>16))/65536.f;
    float da=dv+cfg.inverse_gain*inv_a,db=-dv+cfg.inverse_gain*inv_b;
    // T is the pair of applied phase rotations. A stores their exact quantized inverses.
    u16 pa=turn16(da),pb=turn16(db);out.aux.inverse_t=pack16(u16(0u-pa),u16(0u-pb));
    float qa=float(signed16(pa))/65536.f,qb=float(signed16(pb))/65536.f;
    for(u32 k=0;k<16;++k){V4 x=lut[r[k]],y=lut[g[k]];
#if !DW_REFERENCE_KERNEL
        if(pairs){
            V4 p=pairs[u32(r[k])|(u32(g[k])<<8)];
            float dot=x.x*y.x+x.y*y.y;float twist=cfg.dt*dot;
            out.r[k]=u8(pair_token(p.x,p.y,du,qa+twist)^j);
            out.g[k]=u8(pair_token(p.z,p.w,-du,qb-twist)^j);
        }else
#endif
        {
        float hx=(x.x+y.x)*0.7071067811865475f,hy=(x.y+y.y)*0.7071067811865475f;
        float gx=(x.x-y.x)*0.7071067811865475f,gy=(x.y-y.y)*0.7071067811865475f;
        // The double-dot coupling is the real two-vector dot product.
        float dot=x.x*y.x+x.y*y.y;float twist=cfg.dt*dot;
        out.r[k]=u8(complex_token(hx,hy,du,qa+twist)^j);
        out.g[k]=u8(complex_token(gx,gy,-du,qb-twist)^j);
        }
    }
    out.aux.history=rotl(a.history,1)^j^fold(q.u+du,q.v+da).flip^parity(u32(out.r[0])|(u32(out.g[0])<<8))^mix(u32(epoch));
#if DW_REFERENCE_KERNEL
    (void)pairs;
    out.bc5=encode_bc5(out.r,out.g);out.quant_error=quant_error(out.bc5,out.r,out.g);
#else
    out.bc5=encode_bc5_with_error(out.r,out.g,out.quant_error);
#endif
    out.feedback=u32(out.r[0])|(u32(out.g[0])<<8)|(node<<16)|(j<<24);return out;
}
DW_HD inline Op mutate_op(const Op* old,u32 i,const Stage& s,u64 epoch,u64 seed,const Config& cfg) {
    Op o=old[i];if(!cfg.mutate)return o;
    u32 ref=((o.links>>5)&31)%OP_COUNT;
    u32 h=mix(s.feedback^s.aux.history^old[ref].history^u32(epoch)^u32(seed));
    u32 j=cfg.jitter?jit(epoch,i,seed):0;
    // A one-bit code mutation may alter the primitive, operands, destination or immediate.
    o.code[(h>>5)%BODY_WORDS]^=j<<(h&31);
    o.links^=j<<((h>>11)%10);o.support^=j<<((h>>16)%19);o.coeff^=j<<((h>>21)&31);
    float u=float(o.location&65535)/65536.f+(float(signed16(s.feedback))/65536.f)*cfg.dt;
    float v=float(o.location>>16)/65536.f+cfg.dt*GOLD+float(j)/65536.f;
    Chart p=fold(u,v);o.location=pack16(turn16(p.u),turn16(p.v));o.route^=p.flip^j;
    o.last_rg=s.feedback;o.history=s.aux.history;o.inverse_t=s.aux.inverse_t;return o;
}
inline u64 page_bytes(u32 side,bool exact) {return u64(side)*side*(exact?2:1)+u64(side/4)*(side/4)*sizeof(Aux);}
inline u64 budget_bytes(u64 free,u64 reserve,double fill) {
    if(fill<=0||fill>1||free<=reserve)return 0;
    u64 a=free-reserve,b=u64(double(free)*fill);return a<b?a:b;
}
} // namespace dw
