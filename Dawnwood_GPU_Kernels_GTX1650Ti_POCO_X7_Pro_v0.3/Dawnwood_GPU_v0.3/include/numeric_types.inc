// DWI-N1: shared numerical equations, compiled as C++ and GLSL.
// Source relationships: source/double-slit-theory.pdf pp.3-16.
// Explicit numerical bindings are documented in docs/NUMERICAL_PROFILE.md.
#ifdef __cplusplus
#define DW_FN inline
#define DW_PRECISE
#define DW_LOOP
#include <cmath>
#include <cstdint>
#include <cstring>
using uint = uint32_t;
#define DW_INOUT(T) T&
#define DW_OP_PARAMETER , const Operator* ops
#define DW_OP(i) ops[i]
inline float dw_native_sqrt(float x){return std::sqrt(x);}
inline float dw_floor(float x){return std::floor(x);} inline float dw_abs(float x){return std::fabs(x);}
inline uint dw_float_bits(float x){uint bits;std::memcpy(&bits,&x,sizeof(bits));return bits;}
inline float dw_bits_float(uint bits){float x;std::memcpy(&x,&bits,sizeof(x));return x;}
inline void dw_mul_wide(uint a,uint b,uint& hi,uint& lo){uint64_t p=uint64_t(a)*uint64_t(b);hi=uint(p>>32);lo=uint(p);}
#else
#define DW_FN
#define DW_PRECISE precise
#define DW_LOOP [[dont_unroll]]
#define DW_INOUT(T) inout T
#define DW_OP_PARAMETER
#define DW_OP(i) opNext[i]
#define dw_native_sqrt sqrt
#define dw_floor floor
#define dw_abs abs
#define dw_float_bits floatBitsToUint
#define dw_bits_float uintBitsToFloat
#define dw_mul_wide umulExtended
#endif
// GLSL precise prevents contraction/reassociation, matching the CPU compiler flags.
// A precise caller does not constrain expressions inside a called function.
// Retain shader loops to limit compiler expansion of nested field/body evaluation.
// DW_LOOP is a compilation-resource hint, not a numerical or performance guarantee.
// This return-only block avoids synthetic loops in generated SPIR-V.
#define DW_RETURN_FLOAT(value) { DW_PRECISE float dw_result=(value); return dw_result; }
#include "numeric_math.inc"
const float DW_PI=3.14159265358979323846f;
const float DW_TAU=6.28318530717958647692f;
const float DW_UNIT_MAX=0.999999940395355224609375f; // Greatest FP32 value below one.
// DWI-D1-0.1 is an explicit optional domain-coordinate binding. The ordinary
// DWI-N1 records do not set these bits and retain their original equations.
const uint DW_DOMAIN_PROFILE_FLAG=0x40000000u;
const uint DW_DOMAIN_LAW_FLAG=0x80000000u;
struct State {
 float u,v,rho,theta;
 float ar,ai,br,bi;
 float history,inv00,inv01,inv10;
 float inv11,field,delta,energy;
 float px,py,pz,pw;
 float k1v,k2v,k3v,k4v;
 uint rng,orientation,route,alpha_ref;
 float previousTheta,previousPreviousTheta,phaseResponse,lastJitter;
};
struct Operator {
 float u,v,radius,height;
 float phase,gain,coupling,shear;
 float du,dv,mutationRate,reserved;
 uint program,seed,kind,flags;
};
struct Config {
 uint count,opCount,epoch,depth;
 float dt,yup,epsilon,mutation;
 uint jitter,feedback,reserved0,reserved1;
 float phaseRate,radialRate,historyWeight,fieldScale;
};
struct Motion {float u,v,rho,theta;};
DW_FN float dw_min(float a,float b){DW_RETURN_FLOAT(a<b?a:b);}
DW_FN float dw_max(float a,float b){DW_RETURN_FLOAT(a>b?a:b);}
DW_FN float dw_frac(float x){DW_PRECISE float part=x-dw_floor(x);DW_RETURN_FLOAT(part==1.0f?DW_UNIT_MAX:part);}
DW_FN float dw_len2(float x,float y){DW_RETURN_FLOAT(dw_sqrt(x*x+y*y));}
DW_FN float dw_len3(float x,float y,float z){DW_RETURN_FLOAT(dw_sqrt(x*x+y*y+z*z));}
DW_FN uint dw_rng(uint x){x^=x<<13; x^=x>>17; x^=x<<5; return x;}
DW_FN uint dw_parity(uint x){x^=x>>16;x^=x>>8;x^=x>>4;return (0x6996u>>(x&15u))&1u;}
// a,b < modulus; subtraction avoids overflowing a+b even near UINT32_MAX.
DW_FN uint dw_addmod(uint a,uint b,uint modulus){return a>=modulus-b?a-(modulus-b):a+b;}
DW_FN uint dw_feedback_index(uint index,uint stride,uint epoch,uint offset,uint count){
 // Exact (stride*index+epoch+offset) mod count without requiring shader uint64.
 uint value=index%count,result=epoch%count;
 DW_LOOP while(stride!=0u){if((stride&1u)!=0u)result=dw_addmod(result,value,count);stride>>=1u;if(stride!=0u)value=dw_addmod(value,value,count);}
 return dw_addmod(result,offset%count,count);
}
DW_FN void dw_wrap(DW_PRECISE DW_INOUT(float) u,DW_PRECISE DW_INOUT(float) v,DW_INOUT(uint) orientation){
 // FP32 seam counts can exceed uint32; compute parity without an integer cast.
 DW_PRECISE float wraps=dw_floor(u),parity=wraps-2.0f*dw_floor(0.5f*wraps);bool flip=parity!=0.0f;
 u-=wraps;if(u==1.0f)u=DW_UNIT_MAX; // Tiny negative inputs can round the remainder to one.
 if(flip){v=-v;orientation^=1u;} v=dw_frac(v);
}
DW_FN void dw_embedding(DW_PRECISE DW_INOUT(State) s){
 DW_PRECISE float u=DW_TAU*s.u,v=DW_TAU*s.v;
 DW_PRECISE float r=2.0f+dw_cos(v); s.px=r*dw_cos(u);s.py=r*dw_sin(u);
 s.pz=dw_sin(v)*dw_cos(0.5f*u);s.pw=dw_sin(v)*dw_sin(0.5f*u);
}
DW_FN float dw_segment(float x,float y,float ax,float ay,float bx,float by){
 DW_PRECISE float ex=bx-ax,ey=by-ay,dx=x-ax,dy=y-ay;
 DW_PRECISE float t=dw_max(0.0f,dw_min(1.0f,dw_div(dx*ex+dy*ey,ex*ex+ey*ey)));
 DW_RETURN_FLOAT(dw_len2(dx-t*ex,dy-t*ey));
}
DW_FN float dw_triangle(float x,float y,float r,float h){
 // Retain one segment interpreter call site without changing edge coordinates
 // or the original nested minimum (including its signed-zero behavior).
 DW_PRECISE float edges[3];DW_LOOP for(uint edge=0u;edge<3u;++edge){
  DW_PRECISE float ax=-r,ay=-h,bx=r,by=-h;
  if(edge==1u){ax=r;ay=-h;bx=0.0f;by=h;}
  else if(edge==2u){ax=0.0f;ay=h;bx=-r;by=-h;}
  edges[edge]=dw_segment(x,y,ax,ay,bx,by);
 }
 DW_PRECISE float d=dw_min(edges[0],dw_min(edges[1],edges[2]));
 bool inside=(y>=-h)&&(y<=h)&&(dw_abs(x)<=dw_div(r*(h-y),2.0f*h)); DW_RETURN_FLOAT(inside?-d:d);
}
DW_FN float dw_box(float x,float y,float z,float a,float b,float c){
 DW_PRECISE float dx=dw_abs(x)-a,dy=dw_abs(y)-b,dz=dw_abs(z)-c;
 DW_RETURN_FLOAT(dw_len3(dw_max(dx,0.0f),dw_max(dy,0.0f),dw_max(dz,0.0f))+dw_min(dw_max(dx,dw_max(dy,dz)),0.0f));
}
DW_FN float dw_shape(uint kind,float x,float y,float z,float r,float h){
 if(kind==0u)DW_RETURN_FLOAT(dw_min(dw_box(x,y,z,r*0.3f,h,0.06f),dw_box(x,y-h*0.75f,z,r,h*0.25f,0.06f)));
 if(kind==1u){DW_PRECISE float a=dw_triangle(x,y,r,h),b=dw_abs(z)-0.06f;DW_RETURN_FLOAT(dw_len2(dw_max(a,0.0f),dw_max(b,0.0f))+dw_min(dw_max(a,b),0.0f));}
 if(kind==2u)DW_RETURN_FLOAT(dw_len2(x,y)-r);
 if(kind==3u){DW_PRECISE float q=dw_len2(x,y),edges[2];DW_LOOP for(uint edge=0u;edge<2u;++edge)edges[edge]=dw_segment(q,z,0.0f,edge==0u?h:-h,r,-h);bool inside=z>=-h&&z<=h&&q<=dw_div(r*(h-z),2.0f*h);DW_PRECISE float d=dw_min(edges[0],edges[1]);DW_RETURN_FLOAT(inside?-d:d);}
 if(kind==4u)DW_RETURN_FLOAT(dw_len3(x,y,z)-r);
 DW_RETURN_FLOAT(dw_len3(x,y,z));
}
// A protected law stores a=(phase,gain,coupling,shear), b=du, and the slab
// halfwidth in dv. State px/py/pz/pw are domain coordinates only in DWI-D1.
// These affine laws have exact Euclidean field definitions before FP32 rounding;
// their program is not an instruction applied to their scientific coefficients.
// Input validation supplies finite nonzero normals and kinds 0, 1, or 2.
DW_FN bool dw_domain_enabled(Operator header){return (header.flags&DW_DOMAIN_PROFILE_FLAG)!=0u;}
DW_FN float dw_domain_normal_sq(Operator law){
 DW_RETURN_FLOAT(law.phase*law.phase+law.gain*law.gain+law.coupling*law.coupling+law.shear*law.shear);
}
DW_FN float dw_domain_residual(State s,Operator law){
 DW_RETURN_FLOAT(law.phase*s.px+law.gain*s.py+law.coupling*s.pz+law.shear*s.pw-law.du);
}
DW_FN float dw_domain_distance(State s,Operator law){
 DW_PRECISE float residual=dw_domain_residual(s,law);
 if(law.kind==2u)residual=dw_abs(residual)-law.dv;
 DW_RETURN_FLOAT(dw_div(residual,dw_sqrt(dw_domain_normal_sq(law))));
}
DW_FN float dw_domain_violation(State s,Operator law){
 DW_PRECISE float distance=dw_domain_distance(s,law);
 DW_RETURN_FLOAT(law.kind==0u?dw_abs(distance):dw_max(distance,0.0f));
}
DW_FN float dw_body(float value,Operator op){
 DW_PRECISE float x=value;
 // Eight four-bit instructions form an editable scalar field expression.
 // 0 identity, 1 +gain, 2 -gain, 3 *coupling, 4 sin, 5 cos, 6 abs, 7 negate, 8 square.
 DW_LOOP for(uint k=0u;k<8u;++k){uint code=(op.program>>(4u*k))&15u;
  if(code==1u)x+=op.gain;else if(code==2u)x-=op.gain;else if(code==3u)x*=op.coupling;
  else if(code==4u)x=dw_sin(x);else if(code==5u)x=dw_cos(x);else if(code==6u)x=dw_abs(x);else if(code==7u)x=-x;else if(code==8u)x*=x;
 }
 DW_RETURN_FLOAT(x);
}
DW_FN float dw_field(State point,Operator op,uint kind){
 if((op.flags&DW_DOMAIN_LAW_FLAG)!=0u)DW_RETURN_FLOAT(dw_domain_distance(point,op));
 DW_PRECISE State s=point;
 // RK stages may leave the fundamental chart. Canonicalize this local copy
 // before searching the three neighboring lifts and transporting transverse sign.
 dw_wrap(s.u,s.v,s.orientation);
 DW_PRECISE float best=1.0e20f,bx=0.0f,by=0.0f;
 DW_LOOP for(int m=-1;m<=1;++m){DW_PRECISE float x=s.u-op.u-float(m);DW_PRECISE float ov=(m==0)?op.v:-op.v;DW_PRECISE float y=s.v-ov;y-=dw_floor(y+0.5f);DW_PRECISE float d=x*x+y*y;if(d<best){best=d;bx=x;by=y;}}
 DW_PRECISE float radius=dw_exp(s.rho);DW_PRECISE float x=bx+0.01f*radius*dw_cos(s.theta),y=by+0.01f*radius*dw_sin(s.theta);
 DW_PRECISE float z=0.2f*(radius-0.35f); if(s.orientation!=0u)z=-z;
 DW_RETURN_FLOAT(dw_body(dw_shape(kind,x,y,z,op.radius,op.height),op));
}
DW_FN float dw_apply(State s,Operator op,float value){
 if((op.flags&DW_DOMAIN_LAW_FLAG)!=0u)DW_RETURN_FLOAT(dw_domain_distance(s,op));
 DW_RETURN_FLOAT(dw_body(value+0.01f*dw_field(s,op,op.kind%6u),op));
}
DW_FN Operator dw_mutate(Operator previousOp,Operator mutationOp,Operator pinion,State sourceState,State neighbour,Config cfg){
 DW_PRECISE Operator op=previousOp;
 // A factual affine law is immutable, including its seed, body and anchor.
 // The existing mutable controller determines the solver's relaxation instead.
 if((op.flags&DW_DOMAIN_LAW_FLAG)!=0u)return op;
 if(cfg.feedback==0u)return op;
 op.seed=dw_rng(op.seed);uint j=(cfg.jitter!=0u)?((op.seed^sourceState.rng^neighbour.route)&1u):0u;
 DW_PRECISE float sign=(j!=0u)?1.0f:-1.0f;
 DW_PRECISE float rate=cfg.mutation*mutationOp.mutationRate*(1.0f+0.1f*dw_apply(sourceState,mutationOp,sourceState.field));
 op.u+=cfg.dt*(pinion.du+rate*dw_sin(sourceState.theta)+0.001f*dw_field(sourceState,pinion,pinion.kind%6u));
 op.v+=cfg.dt*(pinion.dv+rate*dw_cos(neighbour.theta));uint orientation=op.flags&1u;dw_wrap(op.u,op.v,orientation);
 op.phase+=rate*sign+0.001f*cfg.dt*(sourceState.history+neighbour.phaseResponse);
 op.gain+=0.1f*rate*dw_sin(dw_field(sourceState,op,op.kind%6u)+sourceState.theta);
 op.shear+=0.1f*rate*dw_cos(neighbour.field);
 uint first=op.program&15u;
 if(j!=0u){if(first==1u)first=2u;else if(first==2u)first=1u;else if(first==4u)first=5u;else if(first==5u)first=4u;}
 op.program=(op.program&0xfffffff0u)|first;op.flags=(op.flags&0xfffffffeu)|orientation;
 return op;
}
