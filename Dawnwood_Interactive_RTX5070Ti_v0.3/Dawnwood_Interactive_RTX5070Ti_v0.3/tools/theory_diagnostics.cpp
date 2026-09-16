// Independent numerical audit of the stated native binding, not a physical experiment.
#include "dawnwood/core.hpp"
#include <array>
#include <iomanip>
#include <iostream>
#include <algorithm>
#include <cmath>
#include <cstdint>
using namespace dw;
struct D2 {double x,y;};
static D2 derivative(D2 q){return {.4+.15*std::sin(6.2831853071795864769*q.y),-.2+.15*std::cos(6.2831853071795864769*q.x)};}
static D2 double_step(D2 q,double dt,double epsilon){
 auto a=derivative(q),b=derivative({q.x+dt*a.x/2,q.y+dt*a.y/2});
 auto c=derivative({q.x+dt*b.x/2,q.y+dt*b.y/2});
 auto d=derivative({q.x+dt*c.x,q.y+dt*c.y+epsilon});
 return {q.x+dt*(a.x+2*b.x+2*c.x+d.x)/6,q.y+dt*(a.y+2*b.y+2*c.y+d.y)/6};
}
static double norm(V4 z){return double(z.x)*z.x+double(z.y)*z.y;}
static double distance(D2 a,D2 b){return std::hypot(a.x-b.x,a.y-b.y);}
int main(){
 std::cout<<std::setprecision(17);
 std::array<V4,256> lut{};for(u32 i=0;i<256;++i)lut[i]=lut_entry(i);
 double max_hadamard_relative=0,energy_in=0,energy_out=0,min_ratio=1e300,max_ratio=0;
 u64 pairs=0,changed=0;u32 max_a=0,max_b=0;u8 max_r=0,max_g=0;
 for(u32 a=0;a<256;++a)for(u32 b=0;b<256;++b){
  auto x=lut[a],y=lut[b];float hx=(x.x+y.x)*0.7071067811865475f,hy=(x.y+y.y)*0.7071067811865475f;
  float gx=(x.x-y.x)*0.7071067811865475f,gy=(x.y-y.y)*0.7071067811865475f;
  double before=norm(x)+norm(y),henergy=double(hx)*hx+double(hy)*hy+double(gx)*gx+double(gy)*gy;
  if(before==0)continue;
  max_hadamard_relative=std::max(max_hadamard_relative,std::abs(henergy-before)/before);
  u8 r=complex_token(hx,hy),g=complex_token(gx,gy);double after=norm(lut[r])+norm(lut[g]);
  double ratio=after/before;min_ratio=std::min(min_ratio,ratio);
  if(ratio>max_ratio){max_ratio=ratio;max_a=a;max_b=b;max_r=r;max_g=g;}
  energy_in+=before;energy_out+=after;++pairs;if(std::abs(ratio-1)>1e-4)++changed;
 }
 double max_cancel_amp=0,max_cancel_raw_amp=0;u32 cancel_a=0,cancel_b=0,cancel_token=0;u64 cancel_nonzero=0;
 for(u32 h=1;h<=15;++h)for(u32 p=0;p<16;++p){u32 a=h*16+p,b=h*16+((p+8)&15);auto x=lut[a],y=lut[b];
  float hx=(x.x+y.x)*.7071067811865475f,hy=(x.y+y.y)*.7071067811865475f;u8 r=complex_token(hx,hy);
  double raw=std::hypot(hx,hy),amp=std::sqrt(norm(lut[r]));max_cancel_raw_amp=std::max(max_cancel_raw_amp,raw);
  if(amp>0)++cancel_nonzero;if(amp>max_cancel_amp){max_cancel_amp=amp;cancel_a=a;cancel_b=b;cancel_token=r;}
 }
 u32 roundtrip=0;for(u32 q=16;q<256;++q)roundtrip+=complex_token(lut[q].x,lut[q].y)!=q;
 double seam_error=0;for(int i=-120;i<=120;++i)for(int j=-60;j<=60;++j){float u=i*.013f,v=j*.019f;auto a=klein(u,v),b=klein(u+1,-v);
  seam_error=std::max(seam_error,double(std::max({std::abs(a.x-b.x),std::abs(a.y-b.y),std::abs(a.z-b.z),std::abs(a.w-b.w)})));}
 u32 inverse_failures=0;for(u32 q=0;q<65536;++q)inverse_failures+=u16(q+u16(0u-q))!=0;
 u8 source=complex_token(2,0);auto source_value=lut[source];
 std::cout<<"{\n  \"scope\": \"Independent CPU component algebra and double-precision binding analysis; no detector or physical double-slit experiment\",\n"
 <<"  \"hadamard\": {\"nonzero_input_pairs\": "<<pairs<<", \"maximum_float_relative_norm_residual_before_encoding\": "<<max_hadamard_relative<<"},\n"
 <<"  \"lp8_after_hadamard\": {\"pairs_with_relative_energy_change_over_1e_4\": "<<changed<<", \"aggregate_output_input_energy_ratio\": "<<energy_out/energy_in<<", \"minimum_pair_energy_ratio\": "<<min_ratio<<", \"maximum_pair_energy_ratio\": "<<max_ratio<<", \"maximum_ratio_witness\": {\"input_tokens\": ["<<max_a<<","<<max_b<<"], \"output_tokens\": ["<<u32(max_r)<<","<<u32(max_g)<<"]}},\n"
 <<"  \"opposite_phase_cancellation\": {\"pairs\": 240, \"nonzero_encoded_sum_pairs\": "<<cancel_nonzero<<", \"largest_float_sum_amplitude_before_encoding\": "<<max_cancel_raw_amp<<", \"largest_decoded_sum_amplitude_after_encoding\": "<<max_cancel_amp<<", \"largest_decoded_sum_witness\": {\"input_tokens\": ["<<cancel_a<<","<<cancel_b<<"], \"output_token\": "<<cancel_token<<"}},\n"
 <<"  \"lp8_nonzero_cell_center_roundtrip_failures\": "<<roundtrip<<",\n"
 <<"  \"klein_seam_maximum_coordinate_residual\": "<<seam_error<<",\n"
 <<"  \"phase_inverse_exhaustive_failures\": "<<inverse_failures<<",\n"
 <<"  \"source_amplitude_two\": {\"token\": "<<u32(source)<<", \"decoded_real\": "<<source_value.x<<", \"decoded_imag\": "<<source_value.y<<", \"decoded_magnitude\": "<<std::sqrt(norm(source_value))<<", \"absolute_complex_error\": "<<std::hypot(double(source_value.x)-2,source_value.y)<<"},\n";
 D2 ref{.2,.3};for(u32 i=0;i<131072;++i)ref=double_step(ref,1./131072,0);
 std::cout<<"  \"rk4_refinement\": {\"initial\": [0.2,0.3], \"drive\": [0.4,-0.2], \"coupling\": 0.15, \"time\": 1, \"event_epsilon\": "<<2./65536<<", \"reference\": ["<<ref.x<<","<<ref.y<<"], \"runs\": [\n";
 for(u32 steps=2;steps<=256;steps*=2){D2 classic{.2,.3},forced=classic;V2 native{.2f,.3f};double dt=1./steps;
  for(u32 i=0;i<steps;++i){classic=double_step(classic,dt,0);forced=double_step(forced,dt,2./65536);native=rk4(native,{.4f,-.2f},.15f,float(dt));}
  std::cout<<"    {\"steps\": "<<steps<<", \"classical_double_error\": "<<distance(classic,ref)<<", \"forced_double_error\": "<<distance(forced,ref)<<", \"native_float_forced_error\": "<<distance({native.x,native.y},ref)<<"}"<<(steps<256?",":"")<<"\n";
 }
 std::cout<<"  ]},\n  \"storage_upper_bound_12_gib\": {\"bc5_plus_aux_bytes_per_pair\": 1.5, \"bc5_pairs_before_overhead\": "<<u64((12ull<<30)/1.5)<<", \"rg8_plus_aux_bytes_per_pair\": 2.5, \"rg8_pairs_before_overhead\": "<<u64((12ull<<30)/2.5)<<"}\n}\n";
}
