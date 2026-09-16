// DWI-N1: shared numerical equations, compiled as C++ and GLSL.
// Source relationships: source/double-slit-theory.pdf pp.3-16.
// Explicit numerical bindings are documented in docs/NUMERICAL_PROFILE.md.
#ifdef __cplusplus
#define DW_FN inline
#include <cmath>
#include <cstdint>
using uint = uint32_t;
#define DW_INOUT(T) T&
#define DW_OP_PARAMETER , const Operator* ops
#define DW_OP(i) ops[i]
inline float dw_sin(float x){return std::sin(x);} inline float dw_cos(float x){return std::cos(x);}
inline float dw_sqrt(float x){return std::sqrt(x);} inline float dw_exp(float x){return std::exp(x);}
inline float dw_floor(float x){return std::floor(x);} inline float dw_abs(float x){return std::fabs(x);}
#else
#define DW_FN
#define DW_INOUT(T) inout T
#define DW_OP_PARAMETER
#define DW_OP(i) opNext[i]
#define dw_sin sin
#define dw_cos cos
#define dw_sqrt sqrt
#define dw_exp exp
#define dw_floor floor
#define dw_abs abs
#endif
const float DW_PI=3.14159265358979323846;
const float DW_TAU=6.28318530717958647692;
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
DW_FN float dw_min(float a,float b){return a<b?a:b;}
DW_FN float dw_max(float a,float b){return a>b?a:b;}
DW_FN float dw_frac(float x){return x-dw_floor(x);}
DW_FN float dw_len2(float x,float y){return dw_sqrt(x*x+y*y);}
DW_FN float dw_len3(float x,float y,float z){return dw_sqrt(x*x+y*y+z*z);}
DW_FN uint dw_rng(uint x){x^=x<<13; x^=x>>17; x^=x<<5; return x;}
DW_FN uint dw_parity(uint x){x^=x>>16;x^=x>>8;x^=x>>4;return (0x6996u>>(x&15u))&1u;}
DW_FN void dw_wrap(DW_INOUT(float) u,DW_INOUT(float) v,DW_INOUT(uint) orientation){
 float wraps=dw_floor(u); uint flip=uint(dw_abs(wraps))&1u;
 u-=wraps; if(flip!=0u){v=-v;orientation^=1u;} v=dw_frac(v);
}
DW_FN void dw_embedding(DW_INOUT(State) s){
 float u=DW_TAU*s.u,v=DW_TAU*s.v;
 float r=2.0+dw_cos(v); s.px=r*dw_cos(u);s.py=r*dw_sin(u);
 s.pz=dw_sin(v)*dw_cos(0.5*u);s.pw=dw_sin(v)*dw_sin(0.5*u);
}
DW_FN float dw_segment(float x,float y,float ax,float ay,float bx,float by){
 float ex=bx-ax,ey=by-ay,dx=x-ax,dy=y-ay;
 float t=dw_max(0.0,dw_min(1.0,(dx*ex+dy*ey)/(ex*ex+ey*ey)));
 return dw_len2(dx-t*ex,dy-t*ey);
}
DW_FN float dw_triangle(float x,float y,float r,float h){
 float d=dw_min(dw_segment(x,y,-r,-h,r,-h),dw_min(dw_segment(x,y,r,-h,0.0,h),dw_segment(x,y,0.0,h,-r,-h)));
 bool inside=(y>=-h)&&(y<=h)&&(dw_abs(x)<=r*(h-y)/(2.0*h)); return inside?-d:d;
}
DW_FN float dw_box(float x,float y,float z,float a,float b,float c){
 float dx=dw_abs(x)-a,dy=dw_abs(y)-b,dz=dw_abs(z)-c;
 return dw_len3(dw_max(dx,0.0),dw_max(dy,0.0),dw_max(dz,0.0))+dw_min(dw_max(dx,dw_max(dy,dz)),0.0);
}
DW_FN float dw_shape(uint kind,float x,float y,float z,float r,float h){
 if(kind==0u)return dw_min(dw_box(x,y,z,r*0.3,h,0.06),dw_box(x,y-h*0.75,z,r,h*0.25,0.06));
 if(kind==1u){float a=dw_triangle(x,y,r,h),b=dw_abs(z)-0.06;return dw_len2(dw_max(a,0.0),dw_max(b,0.0))+dw_min(dw_max(a,b),0.0);}
 if(kind==2u)return dw_len2(x,y)-r;
 if(kind==3u){float q=dw_len2(x,y);float a=dw_segment(q,z,0.0,h,r,-h),b=dw_segment(q,z,0.0,-h,r,-h);bool inside=z>=-h&&z<=h&&q<=r*(h-z)/(2.0*h);float d=dw_min(a,b);return inside?-d:d;}
 if(kind==4u)return dw_len3(x,y,z)-r;
 return dw_len3(x,y,z);
}
DW_FN float dw_body(float x,Operator op){
 // Eight four-bit instructions form an editable scalar field expression.
 // 0 identity, 1 +gain, 2 -gain, 3 *coupling, 4 sin, 5 cos, 6 abs, 7 negate, 8 square.
 for(uint k=0u;k<8u;++k){uint code=(op.program>>(4u*k))&15u;
  if(code==1u)x+=op.gain;else if(code==2u)x-=op.gain;else if(code==3u)x*=op.coupling;
  else if(code==4u)x=dw_sin(x);else if(code==5u)x=dw_cos(x);else if(code==6u)x=dw_abs(x);else if(code==7u)x=-x;else if(code==8u)x*=x;
 }
 return x;
}
DW_FN float dw_field(State s,Operator op,uint kind){
 float best=1.0e20,bx=0.0,by=0.0;
 for(int m=-1;m<=1;++m){float x=s.u-op.u-float(m);float ov=(m==0)?op.v:-op.v;float y=s.v-ov;y-=dw_floor(y+0.5);float d=x*x+y*y;if(d<best){best=d;bx=x;by=y;}}
 float radius=dw_exp(s.rho);float x=bx+0.01*radius*dw_cos(s.theta),y=by+0.01*radius*dw_sin(s.theta);
 float z=0.2*(radius-0.35); if(s.orientation!=0u)z=-z;
 return dw_body(dw_shape(kind,x,y,z,op.radius,op.height),op);
}
DW_FN float dw_apply(State s,Operator op,float value){return dw_body(value+0.01*dw_field(s,op,op.kind%6u),op);}
DW_FN Operator dw_mutate(Operator op,Operator mutationOp,Operator pinion,State sourceState,State neighbour,Config cfg){
 if(cfg.feedback==0u)return op;
 op.seed=dw_rng(op.seed);uint j=(cfg.jitter!=0u)?((op.seed^sourceState.rng^neighbour.route)&1u):0u;
 float sign=(j!=0u)?1.0:-1.0;
 float rate=cfg.mutation*mutationOp.mutationRate*(1.0+0.1*dw_apply(sourceState,mutationOp,sourceState.field));
 op.u+=cfg.dt*(pinion.du+rate*dw_sin(sourceState.theta)+0.001*dw_field(sourceState,pinion,pinion.kind%6u));
 op.v+=cfg.dt*(pinion.dv+rate*dw_cos(neighbour.theta));uint orientation=op.flags&1u;dw_wrap(op.u,op.v,orientation);
 op.phase+=rate*sign+0.001*cfg.dt*(sourceState.history+neighbour.phaseResponse);
 op.gain+=0.1*rate*dw_sin(dw_field(sourceState,op,op.kind%6u)+sourceState.theta);
 op.shear+=0.1*rate*dw_cos(neighbour.field);
 uint first=op.program&15u;
 if(j!=0u){if(first==1u)first=2u;else if(first==2u)first=1u;else if(first==4u)first=5u;else if(first==5u)first=4u;}
 op.program=(op.program&0xfffffff0u)|first;op.flags=(op.flags&0xfffffffeu)|orientation;
 return op;
}
