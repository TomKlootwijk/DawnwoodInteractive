// Dawnwood Interactive: explicit integer numerical binding, edition 1.
// Not a claim that these quantizers or finite-precision rules occur in the source PDF.
// Runtime primitives below contain integer arithmetic only.
#pragma once
#include "dawnwood/core.hpp"
#include <limits>
namespace dwi {
using dw::u8; using dw::u16; using dw::u32; using dw::u64; using dw::i32; using dw::i64;
constexpr i32 CHART_ONE=65536, COMPLEX_ONE=2048, GEOMETRY_ONE=262144;
constexpr i32 RHO_MIN_Q16=-262144, RHO_SPAN_Q16=491520;
struct Chart { i32 u,v; u32 flip; }; // u: normalized log radius; v: linear phase turns, Q16
struct Complex { i32 x,y; }; // Cartesian amplitudes, Q11
struct V2 { i32 x,y; };
struct V4 { i32 x,y,z,w; }; // geometric embedding, Q18
struct Hadamard { Complex plus,minus; };

// Integer divisions in this file explicitly use either C++ truncation toward zero
// or round-nearest/ties-away-from-zero. No signed shifts implement a rounding rule.
// saturate_i32 is used at public arithmetic boundaries; recurrence callers should
// retain the documented Q scales. Phase and chart quotients wrap, never saturate.
DW_HD inline i32 saturate_i32(i64 x) {
    return x>2147483647LL?2147483647:(x<(-2147483647LL-1)?(-2147483647-1):i32(x));
}
DW_HD inline u64 magnitude(i64 x) { return x<0?u64(-(x+1))+1:u64(x); }
struct UDivMod { u64 quotient,remainder; };
DW_HD inline UDivMod divmod_u64(u64 n,u64 d) {
    // Restoring long division: integer instructions only, including on CUDA
    // where a native C++ variable divide can lower to a floating reciprocal.
    // d must be positive. Carry handling also covers divisors above 2^63.
    u64 q=0,r=0;
    for(i32 i=63;i>=0;--i){
        u64 carry=r>>63;r=(r<<1)|((n>>i)&1);
        if(carry||r>=d){r-=d;q|=u64(1)<<i;}
    }
    return {q,r};
}
DW_HD inline i64 signed_magnitude(u64 q,bool negative) {
    if(!negative)return i64(q);
    return q==(u64(1)<<63)?(-9223372036854775807LL-1):-i64(q);
}
DW_HD inline i64 round_div(i64 n,i64 d) {
    // d is positive. The unsigned magnitude also supports INT64_MIN.
    u64 b=u64(d);UDivMod result=divmod_u64(magnitude(n),b);
    u64 q=result.quotient+u64(result.remainder>=(b/2+b%2));
    return signed_magnitude(q,n<0);
}
template<i64 D> DW_HD inline i64 round_div_const(i64 n) {
    static_assert(D>0,"positive fixed divisor");
    constexpr u64 b=u64(D);u64 a=magnitude(n),q=a/b,r=a%b;
    q+=r>=(b/2+b%2);return signed_magnitude(q,n<0);
}
DW_HD inline i64 trunc_pow2(i64 n,u32 shift) {
    return signed_magnitude(shift<64?magnitude(n)>>shift:0,n<0);
}
DW_HD inline i32 mul_q16(i32 a,i32 b) { return saturate_i32(round_div_const<65536>(i64(a)*b)); }
DW_HD inline i32 mul_q15(i32 a,i32 b) { return saturate_i32(round_div_const<32768>(i64(a)*b)); }
DW_HD inline i32 floor_mod_turn(i64 x) { i64 r=x%65536;return i32(r<0?r+65536:r); }
DW_HD inline Chart fold(i64 u,i64 v) {
    i32 fu=floor_mod_turn(u);
    // Compute floor(u/65536) without subtracting fu from INT64_MIN.
    i64 wind=u/65536-(u%65536<0?1:0);u32 flip=u32(u64(wind)&1);
    i32 fv=floor_mod_turn(v);
    return {fu,flip?(fv?65536-fv:0):fv,flip};
}
DW_HD inline Chart token_chart(u8 q) {
    u32 h=q>>4;
    return {h?i32(round_div_const<30>(i64(2*h-1)*65536)):0,i32((q&15)*4096+2048),0};
}
DW_HD inline u8 chart_token(i64 u,i64 v) {
    Chart c=fold(u,v);
    return u8(((u32(c.u)*15/65536+1)<<4)|(u32(c.v)>>12));
}

// Offline constants: nearest integer Q11 samples at rho=-4+(h-1/2)/2,
// phi=(p+1/2)/16. Entries p+8 are NEGATIONS of p, not separately rounded
// trigonometric evaluations. Thus antipodes cancel exactly, including zero.
inline constexpr u32 LP_WORDS[256]={
    0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u,
    0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u,
    0x001e0095u, 0x0055007fu, 0x007f0055u, 0x0095001eu, 0x0095ffe2u, 0x007fffabu, 0x0055ff81u, 0x001eff6bu,
    0xffe2ff6bu, 0xffabff81u, 0xff81ffabu, 0xff6bffe2u, 0xff6b001eu, 0xff810055u, 0xffab007fu, 0xffe20095u,
    0x002a00d3u, 0x007800b3u, 0x00b30078u, 0x00d3002au, 0x00d3ffd6u, 0x00b3ff88u, 0x0078ff4du, 0x002aff2du,
    0xffd6ff2du, 0xff88ff4du, 0xff4dff88u, 0xff2dffd6u, 0xff2d002au, 0xff4d0078u, 0xff8800b3u, 0xffd600d3u,
    0x003b012bu, 0x00a900fdu, 0x00fd00a9u, 0x012b003bu, 0x012bffc5u, 0x00fdff57u, 0x00a9ff03u, 0x003bfed5u,
    0xffc5fed5u, 0xff57ff03u, 0xff03ff57u, 0xfed5ffc5u, 0xfed5003bu, 0xff0300a9u, 0xff5700fdu, 0xffc5012bu,
    0x005401a6u, 0x00ef0166u, 0x016600efu, 0x01a60054u, 0x01a6ffacu, 0x0166ff11u, 0x00effe9au, 0x0054fe5au,
    0xffacfe5au, 0xff11fe9au, 0xfe9aff11u, 0xfe5affacu, 0xfe5a0054u, 0xfe9a00efu, 0xff110166u, 0xffac01a6u,
    0x00770255u, 0x015201fau, 0x01fa0152u, 0x02550077u, 0x0255ff89u, 0x01fafeaeu, 0x0152fe06u, 0x0077fdabu,
    0xff89fdabu, 0xfeaefe06u, 0xfe06feaeu, 0xfdabff89u, 0xfdab0077u, 0xfe060152u, 0xfeae01fau, 0xff890255u,
    0x00a8034du, 0x01de02ccu, 0x02cc01deu, 0x034d00a8u, 0x034dff58u, 0x02ccfe22u, 0x01defd34u, 0x00a8fcb3u,
    0xff58fcb3u, 0xfe22fd34u, 0xfd34fe22u, 0xfcb3ff58u, 0xfcb300a8u, 0xfd3401deu, 0xfe2202ccu, 0xff58034du,
    0x00ee04aau, 0x02a503f5u, 0x03f502a5u, 0x04aa00eeu, 0x04aaff12u, 0x03f5fd5bu, 0x02a5fc0bu, 0x00eefb56u,
    0xff12fb56u, 0xfd5bfc0bu, 0xfc0bfd5bu, 0xfb56ff12u, 0xfb5600eeu, 0xfc0b02a5u, 0xfd5b03f5u, 0xff1204aau,
    0x01500699u, 0x03bd0598u, 0x059803bdu, 0x06990150u, 0x0699feb0u, 0x0598fc43u, 0x03bdfa68u, 0x0150f967u,
    0xfeb0f967u, 0xfc43fa68u, 0xfa68fc43u, 0xf967feb0u, 0xf9670150u, 0xfa6803bdu, 0xfc430598u, 0xfeb00699u,
    0x01db0955u, 0x054907e9u, 0x07e90549u, 0x095501dbu, 0x0955fe25u, 0x07e9fab7u, 0x0549f817u, 0x01dbf6abu,
    0xfe25f6abu, 0xfab7f817u, 0xf817fab7u, 0xf6abfe25u, 0xf6ab01dbu, 0xf8170549u, 0xfab707e9u, 0xfe250955u,
    0x02a00d32u, 0x077a0b30u, 0x0b30077au, 0x0d3202a0u, 0x0d32fd60u, 0x0b30f886u, 0x077af4d0u, 0x02a0f2ceu,
    0xfd60f2ceu, 0xf886f4d0u, 0xf4d0f886u, 0xf2cefd60u, 0xf2ce02a0u, 0xf4d0077au, 0xf8860b30u, 0xfd600d32u,
    0x03b612a9u, 0x0a920fd2u, 0x0fd20a92u, 0x12a903b6u, 0x12a9fc4au, 0x0fd2f56eu, 0x0a92f02eu, 0x03b6ed57u,
    0xfc4aed57u, 0xf56ef02eu, 0xf02ef56eu, 0xed57fc4au, 0xed5703b6u, 0xf02e0a92u, 0xf56e0fd2u, 0xfc4a12a9u,
    0x05401a64u, 0x0ef31660u, 0x16600ef3u, 0x1a640540u, 0x1a64fac0u, 0x1660f10du, 0x0ef3e9a0u, 0x0540e59cu,
    0xfac0e59cu, 0xf10de9a0u, 0xe9a0f10du, 0xe59cfac0u, 0xe59c0540u, 0xe9a00ef3u, 0xf10d1660u, 0xfac01a64u,
    0x076d2553u, 0x15241fa4u, 0x1fa41524u, 0x2553076du, 0x2553f893u, 0x1fa4eadcu, 0x1524e05cu, 0x076ddaadu,
    0xf893daadu, 0xeadce05cu, 0xe05ceadcu, 0xdaadf893u, 0xdaad076du, 0xe05c1524u, 0xeadc1fa4u, 0xf8932553u,
    0x0a8034c9u, 0x1de62cbfu, 0x2cbf1de6u, 0x34c90a80u, 0x34c9f580u, 0x2cbfe21au, 0x1de6d341u, 0x0a80cb37u,
    0xf580cb37u, 0xe21ad341u, 0xd341e21au, 0xcb37f580u, 0xcb370a80u, 0xd3411de6u, 0xe21a2cbfu, 0xf58034c9u,
    0x0ed94aa6u, 0x2a493f48u, 0x3f482a49u, 0x4aa60ed9u, 0x4aa6f127u, 0x3f48d5b7u, 0x2a49c0b8u, 0x0ed9b55au,
    0xf127b55au, 0xd5b7c0b8u, 0xc0b8d5b7u, 0xb55af127u, 0xb55a0ed9u, 0xc0b82a49u, 0xd5b73f48u, 0xf1274aa6u
};
// Quarter-wave samples sin(pi*i/512), i=0..256, rounded to Q15.
// 32768 fits unsigned16. Linear interpolation is nearest/ties-away.
inline constexpr u16 SIN_QUARTER[257]={
    0, 201, 402, 603, 804, 1005, 1206, 1407, 1608, 1809, 2009, 2210, 2411, 2611, 2811, 3012,
    3212, 3412, 3612, 3812, 4011, 4211, 4410, 4609, 4808, 5007, 5205, 5404, 5602, 5800, 5998, 6195,
    6393, 6590, 6787, 6983, 7180, 7376, 7571, 7767, 7962, 8157, 8351, 8546, 8740, 8933, 9127, 9319,
    9512, 9704, 9896, 10088, 10279, 10469, 10660, 10850, 11039, 11228, 11417, 11605, 11793, 11980, 12167, 12354,
    12540, 12725, 12910, 13095, 13279, 13463, 13646, 13828, 14010, 14192, 14373, 14553, 14733, 14912, 15091, 15269,
    15447, 15624, 15800, 15976, 16151, 16326, 16500, 16673, 16846, 17018, 17190, 17361, 17531, 17700, 17869, 18037,
    18205, 18372, 18538, 18703, 18868, 19032, 19195, 19358, 19520, 19681, 19841, 20001, 20160, 20318, 20475, 20632,
    20788, 20943, 21097, 21251, 21403, 21555, 21706, 21856, 22006, 22154, 22302, 22449, 22595, 22740, 22884, 23028,
    23170, 23312, 23453, 23593, 23732, 23870, 24008, 24144, 24279, 24414, 24548, 24680, 24812, 24943, 25073, 25202,
    25330, 25457, 25583, 25708, 25833, 25956, 26078, 26199, 26320, 26439, 26557, 26674, 26791, 26906, 27020, 27133,
    27246, 27357, 27467, 27576, 27684, 27791, 27897, 28002, 28106, 28209, 28311, 28411, 28511, 28610, 28707, 28803,
    28899, 28993, 29086, 29178, 29269, 29359, 29448, 29535, 29622, 29707, 29792, 29875, 29957, 30038, 30118, 30196,
    30274, 30350, 30425, 30499, 30572, 30644, 30715, 30784, 30853, 30920, 30986, 31050, 31114, 31177, 31238, 31298,
    31357, 31415, 31471, 31527, 31581, 31634, 31686, 31737, 31786, 31834, 31881, 31927, 31972, 32015, 32058, 32099,
    32138, 32177, 32214, 32251, 32286, 32319, 32352, 32383, 32413, 32442, 32470, 32496, 32522, 32546, 32568, 32590,
    32610, 32629, 32647, 32664, 32679, 32693, 32706, 32718, 32729, 32738, 32746, 32753, 32758, 32762, 32766, 32767,
    32768
};
struct MathLut {
    u32 lp[256];
    u16 sin_quarter[257];
    u16 reserved; // explicit zero tail makes all 1540 uploaded bytes deterministic
    DW_HD u32 lp_word(u32 i) const { return lp[i&255]; }
    DW_HD u32 sin_word(u32 i) const { return sin_quarter[i]; }
};
static_assert(sizeof(MathLut)==1540,"integer math LUT is 1540 bytes including padding");
inline void init_math_lut(MathLut& a) {
    for(u32 i=0;i<256;++i)a.lp[i]=LP_WORDS[i];
    for(u32 i=0;i<257;++i)a.sin_quarter[i]=SIN_QUARTER[i];
    a.reserved=0;
}
template<class LUT> DW_HD inline Complex decode(const LUT& a,u8 q) {
    u32 w=a.lp_word(q);return {dw::signed16(w),dw::signed16(w>>16)};
}
template<class LUT> DW_HD inline Complex lut_entry(const LUT& a,u8 q) { return decode(a,q); }
// Internal half-turn16 units: 131072 units per full turn, retaining u/2
// exactly when evaluating the Klein embedding's half-angle.
template<class LUT> DW_HD inline i32 sin_half_units_q15(const LUT& a,i64 phase) {
    i64 r=phase%131072;if(r<0)r+=131072;u32 p=u32(r),q=p>>15,t=p&32767;
    if(q&1)t=32768-t;
    u32 i=t>>7,f=t&127;
    i32 v=i32(a.sin_word(i));
    if(f)v+=i32(round_div_const<128>(i64(i32(a.sin_word(i+1))-v)*f));
    return q>=2?-v:v;
}
template<class LUT> DW_HD inline i32 sin_q15(const LUT& a,i64 phase) {
    return sin_half_units_q15(a,i64(floor_mod_turn(phase))*2);
}
template<class LUT> DW_HD inline i32 cos_q15(const LUT& a,i64 phase) {
    return sin_q15(a,i64(floor_mod_turn(phase))+16384);
}

DW_HD inline Hadamard hadamard(Complex a,Complex b) {
    // 23170/32768 approximates 1/sqrt(2). Sums use wide intermediates;
    // each output is rounded once. The transform is not claimed exactly unitary.
    return {{saturate_i32(round_div_const<32768>((i64(a.x)+b.x)*23170)),
             saturate_i32(round_div_const<32768>((i64(a.y)+b.y)*23170))},
            {saturate_i32(round_div_const<32768>((i64(a.x)-b.x)*23170)),
             saturate_i32(round_div_const<32768>((i64(a.y)-b.y)*23170))}};
}
DW_HD inline u64 squared_norm(Complex z) { return u64(i64(z.x)*z.x)+u64(i64(z.y)*z.y); }
DW_HD inline u64 isqrt(u64 n) {
    // Restoring integer square root, floor(sqrt(n)), total for uint64.
    u64 root=0,bit=u64(1)<<62;while(bit>n)bit>>=2;
    while(bit){if(n>=root+bit){n-=root+bit;root=(root>>1)+bit;}else root>>=1;bit>>=2;}
    return root;
}
DW_HD inline i32 sqrt_nearest(u64 n) {
    u64 r=isqrt(n),rem=n-r*r;
    // Halfway thresholds lie between integers: rem > r selects r+1.
    if(rem>r)++r;
    return r>2147483647u?2147483647:i32(r);
}
DW_HD inline i32 radial_sdf(u64 distance_squared,i32 radius) {
    i32 d=sqrt_nearest(distance_squared)-radius;
    // Preserve exact squared-distance membership when rounding the magnitude
    // would otherwise turn a nearby interior or exterior point into a boundary.
    if(!d){u64 r2=u64(i64(radius)*radius);return (distance_squared>r2)-(distance_squared<r2);}
    return d;
}
DW_HD inline i32 log2_q16(u64 n) {
    // Lower approximation to logarithm with 16 fractional bits, using Q31
    // repeated squaring. The finite working precision can place the result one
    // Q16 unit below floor(log2(n)*65536); powers of two are exact.
    // The input is unsigned integer, NOT Q11. Zero has sentinel INT32_MIN;
    // callers handle exact zero before using a logarithm.
    if(!n)return (-2147483647-1);
    u64 tmp=n;u32 e=0;while(tmp>>1){tmp>>=1;++e;}
    u64 x=e>=31?n>>(e-31):n<<(31-e);u32 f=0;
    for(u32 k=0;k<16;++k){
        x=(x*x)>>31;
        if(x>=(u64(1)<<32)){x>>=1;f|=1u<<(15-k);}
    }
    return i32((e<<16)|f);
}
DW_HD inline i32 atan_step(u32 i) {
    // atan(2^-i) in Q32 turns, offline rounded constants.
    switch(i){
    case 0:return 536870912;
    case 1:return 316933406;
    case 2:return 167458907;
    case 3:return 85004756;
    case 4:return 42667331;
    case 5:return 21354465;
    case 6:return 10679838;
    case 7:return 5340245;
    case 8:return 2670163;
    case 9:return 1335087;
    case 10:return 667544;
    case 11:return 333772;
    case 12:return 166886;
    case 13:return 83443;
    case 14:return 41722;
    case 15:return 20861;
    case 16:return 10430;
    case 17:return 5215;
    case 18:return 2608;
    case 19:return 1304;
    case 20:return 652;
    case 21:return 326;
    case 22:return 163;
    case 23:return 81;
    default:return 0;
    }
}
DW_HD inline u16 atan2_turn16(i32 y0,i32 x0) {
    if(!x0&&!y0)return 0;
    if(!y0)return x0<0?32768:0;
    if(!x0)return y0<0?49152:16384;
    i64 x=i64(x0)*65536,y=i64(y0)*65536,a=0;
    if(x<0){x=-x;y=-y;a=2147483648LL;}
    for(u32 i=0;i<24;++i){
        i64 ox=x;
        if(y>0){x+=trunc_pow2(y,i);y-=trunc_pow2(ox,i);a+=atan_step(i);}
        else if(y<0){x-=trunc_pow2(y,i);y+=trunc_pow2(ox,i);a-=atan_step(i);}
        else break;
    }
    return u16(u64(round_div_const<65536>(a))&65535);
}
template<class LUT> DW_HD inline u8 complex_token(const LUT&,Complex z,i32 du=0,i32 dv=0) {
    u64 r2=squared_norm(z);if(!r2)return 0;
    // Q11 -> magnitude squared Q22, rho = log2(radius).
    // u=(rho+4)/7.5 = (log2(r2)-22+8)/15.
    i64 u=round_div_const<15>(i64(log2_q16(r2))-14*65536)+du;
    return chart_token(u,i64(atan2_turn16(z.y,z.x))+dv);
}
template<class LUT> DW_HD inline u8 complex_token(const LUT& a,i32 x,i32 y,i32 du=0,i32 dv=0) {
    return complex_token(a,Complex{x,y},du,dv);
}

DW_HD inline i32 delta_turn(i64 x) {
    i32 y=floor_mod_turn(x);return y>=32768?y-65536:y;
}
DW_HD inline V2 chart_delta(Chart a,Chart b) {
    // Canonical chart inputs; enumerate the three adjacent radial sheets.
    // Ties select the first sheet (-1,0,+1), matching the legacy binding.
    i64 best=9223372036854775807LL;V2 out{};
    for(i32 k=-1;k<=1;++k){
        i32 x=a.u-(b.u+k*65536);
        i32 y=delta_turn(i64(a.v)-((k&1)?-i64(b.v):i64(b.v)));
        i64 d=i64(x)*x+i64(y)*y;
        if(d<best){best=d;out={x,y};}
    }
    return out;
}
template<class LUT> DW_HD inline V4 klein(const LUT& a,i64 u,i64 v) {
    // Canonicalization guarantees identical integer embedding for every
    // (u+65536,-v) quotient-equivalent input, including negative winding.
    Chart c=fold(u,v);
    i32 cv=cos_q15(a,c.v),sv=sin_q15(a,c.v);
    i32 rad=2*GEOMETRY_ONE+4*cv;
    i32 cu=cos_q15(a,c.u),su=sin_q15(a,c.u);
    i32 chu=sin_half_units_q15(a,i64(c.u)+32768),shu=sin_half_units_q15(a,c.u);
    return {i32(round_div_const<32768>(i64(rad)*cu)),i32(round_div_const<32768>(i64(rad)*su)),
            i32(round_div_const<8192>(i64(sv)*chu)),i32(round_div_const<8192>(i64(sv)*shu))};
}
DW_HD inline i32 abs_i32_geometry(i32 a) { return a<0?-a:a; } // bounded Q18 geometry, never INT32_MIN
DW_HD inline i32 min_i32(i32 a,i32 b) { return a<b?a:b; }
DW_HD inline i32 max_i32(i32 a,i32 b) { return a>b?a:b; }
DW_HD inline i32 sd_box(i32 x,i32 y,i32 a,i32 b) {
    i32 qx=abs_i32_geometry(x)-a,qy=abs_i32_geometry(y)-b;
    i32 ox=max_i32(qx,0),oy=max_i32(qy,0);
    return sqrt_nearest(u64(i64(ox)*ox+i64(oy)*oy))+min_i32(max_i32(qx,qy),0);
}
DW_HD inline i32 sd_triangle(i32 x,i32 y,i32 r) {
    // Isosceles triangle (-r,-r),(r,-r),(0,r), all Q18.
    // Segment projections round to the nearest Q18 lattice point.
    V2 p[3]={{-r,-r},{r,-r},{0,r}};
    u64 best=~u64(0);bool inside=true,on_edge=false;
    for(u32 i=0;i<3;++i){
        V2 a=p[i],b=p[(i+1)%3];i64 ex=b.x-a.x,ey=b.y-a.y,px=i64(x)-a.x,py=i64(y)-a.y;
        i64 den=ex*ex+ey*ey,dot=px*ex+py*ey;
        // These products fit int64 for canonical chart deltas and r<=65536.
        i64 tq=dot<=0?0:(dot>=den?65536:round_div(dot*65536,den));
        i64 dx=px-round_div_const<65536>(tq*ex),dy=py-round_div_const<65536>(tq*ey);
        u64 d=u64(dx*dx+dy*dy);if(d<best)best=d;
        i64 cross=ex*py-ey*px;inside=inside&&(cross>=0);
        on_edge=on_edge||(cross==0&&dot>=0&&dot<=den);
    }
    if(on_edge)return 0;
    i32 d=sqrt_nearest(best);
    // Keep an interior/exterior point's sign even if a quantized projection
    // reaches zero. Membership is decided by exact integer cross products.
    if(!d)d=1;
    return inside?-d:d;
}
template<class LUT> DW_HD inline i32 support_sdf(const LUT& a,const dw::Op& o,Chart q) {
    // Shape law is the explicit v0.3 geometric interpretation of source pp8,12,14.
    // Radius is exact Q18: (low16(support)+1)/262144.
    // q and operator coordinates are canonical normalized Q16 charts.
    Chart c{i32(o.location&65535),i32(o.location>>16),0};V2 pd=chart_delta(q,c);
    i32 x=pd.x*4,y=pd.y*4,r=i32(o.support&65535)+1;
    switch((o.support>>16)%6){
    case 0:return radial_sdf(u64(i64(x)*x+i64(y)*y),r);
    case 1:{
        // Min of two box distance fields for the T union; this preserves
        // membership but need not be exact distance inside the overlap.
        i32 stem=sd_box(x,y+i32(round_div_const<10>(i64(r)*3)),i32(round_div_const<5>(r)),r);
        i32 bar=sd_box(x,y-i32(round_div_const<5>(i64(r)*3)),r,i32(round_div_const<5>(r)));
        return min_i32(stem,bar);
    }
    case 2:return sd_triangle(x,y,r);
    case 3:return sd_triangle(x,y,i32(round_div_const<4>(i64(r)*3)));
    case 4:{
        V4 p=klein(a,q.u,q.v),b=klein(a,c.u,c.v);
        i64 dx=p.x-b.x,dy=p.y-b.y,dz=p.z-b.z,dw_=p.w-b.w;
        return radial_sdf(u64(dx*dx+dy*dy+dz*dz+dw_*dw_),r);
    }
    default:return sqrt_nearest(u64(i64(x)*x+i64(y)*y));
    }
}
template<class LUT> DW_HD inline i32 support_sign(const LUT& a,const dw::Op& o,Chart q) {
    i32 s=support_sdf(a,o,q);return (s>0)-(s<0);
}
} // namespace dwi
