// Independent CPU diagnostics of the integer-1 binding. Compile with MSVC:
// cl /nologo /O2 /EHsc /std:c++17 /Iinclude tools\integer_theory_diagnostics.cpp
// This program uses real arithmetic ONLY for diagnostic statistics/reference
// formulas, never as a replacement for the dwi integer operations under audit.
// Redirect stdout to JSON, then attach source/binary SHA-256 provenance at build.
#include "dawnwood/integer_core.hpp"
#include <algorithm>
#include <array>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <vector>
using namespace dwi;
constexpr double PI=3.1415926535897932384626433832795;
constexpr double ENERGY_SCALE=4194304.0;
static double energy(Complex a){return double(squared_norm(a))/ENERGY_SCALE;}
static double amplitude(Complex a){return std::sqrt(energy(a));}
static double pct(std::vector<double> v,double p){
 if(v.empty())return 0;std::sort(v.begin(),v.end());double at=p*(v.size()-1);
 size_t lo=size_t(at),hi=std::min(lo+1,v.size()-1);return v[lo]+(v[hi]-v[lo])*(at-lo);
}
static void stats(const std::vector<double>& a){
 double sum=0;for(double x:a)sum+=x;
 std::cout<<"{\"count\":"<<a.size()<<",\"mean\":"<<(a.empty()?0:sum/a.size())
 <<",\"minimum\":"<<(a.empty()?0:*std::min_element(a.begin(),a.end()))
 <<",\"p50\":"<<pct(a,.5)<<",\"p95\":"<<pct(a,.95)<<",\"p99\":"<<pct(a,.99)
 <<",\"maximum\":"<<(a.empty()?0:*std::max_element(a.begin(),a.end()))<<"}";
}
static i32 nearest(i64 n,i64 d){return i32(n>=0?(n+d/2)/d:-((-n+d/2)/d));}
struct RKTrace {V2 a,b,c,d,arg4,result;};
static RKTrace trace_rk(const MathLut& lut,V2 q,V2 drive,i32 k,i32 dt,i32 event){
 // Independent explicit stage assembly, with simple CPU integer division.
 auto f=[&](V2 z){return V2{drive.x+nearest(i64(k)*sin_q15(lut,z.y),32768),
                           drive.y+nearest(i64(k)*cos_q15(lut,z.x),32768)};};
 RKTrace t{};t.a=f(q);
 t.b=f({q.x+nearest(i64(dt)*t.a.x,131072),q.y+nearest(i64(dt)*t.a.y,131072)});
 t.c=f({q.x+nearest(i64(dt)*t.b.x,131072),q.y+nearest(i64(dt)*t.b.y,131072)});
 t.arg4={q.x+nearest(i64(dt)*t.c.x,65536),q.y+nearest(i64(dt)*t.c.y,65536)+event};
 t.d=f(t.arg4);
 t.result={q.x+nearest(i64(dt)*(i64(t.a.x)+2*t.b.x+2*t.c.x+t.d.x),393216),
           q.y+nearest(i64(dt)*(i64(t.a.y)+2*t.b.y+2*t.c.y+t.d.y),393216)};
 return t;
}
static void v2(V2 q){std::cout<<"["<<q.x<<","<<q.y<<"]";}
int main(){
 MathLut lut{};init_math_lut(lut);std::cout<<std::setprecision(17);
 std::cout<<"{\n\"model\":\"integer-1\",\n\"snapshot_version\":4,\n"
 <<"\"scope\":\"CPU integer components and declared real-valued diagnostic references; no GPU performance measurement, physical experiment or full dynamical norm-conservation claim\",\n"
 <<"\"compiler\":{\"family\":\"MSVC\",\"msc_full_ver\":"<<_MSC_FULL_VER
 <<",\"compile_date\":\""<<__DATE__<<"\",\"compile_time\":\""<<__TIME__<<"\"},\n";

 std::vector<double> norm_error,encoded_ratio,encoded_error;double ein_total=0,eout_total=0;
 double max_ratio=-1,min_ratio=1e300;u32 max_a=0,max_b=0,max_r=0,max_g=0,min_a=0,min_b=0,min_r=0,min_g=0;
 u64 significant=0,zero_pairs=0;
 for(u32 a=0;a<256;++a)for(u32 b=0;b<256;++b){Complex x=decode(lut,u8(a)),y=decode(lut,u8(b));
  Hadamard h=hadamard(x,y);double before=energy(x)+energy(y),raw=energy(h.plus)+energy(h.minus);
  u8 r=complex_token(lut,h.plus),g=complex_token(lut,h.minus);double after=energy(decode(lut,r))+energy(decode(lut,g));
  if(before==0){++zero_pairs;continue;}
  norm_error.push_back(std::abs(raw-before)/before);double ratio=after/before;
  encoded_ratio.push_back(ratio);encoded_error.push_back(std::abs(ratio-1));significant+=std::abs(ratio-1)>1e-4;
  if(ratio>max_ratio){max_ratio=ratio;max_a=a;max_b=b;max_r=r;max_g=g;}
  if(ratio<min_ratio){min_ratio=ratio;min_a=a;min_b=b;min_r=r;min_g=g;}
  ein_total+=before;eout_total+=after;
 }
 std::cout<<"\"exhaustive_pair_energy\":{\"all_pairs\":65536,\"zero_input_pairs_excluded_from_ratios\":"<<zero_pairs
 <<",\"raw_integer_hadamard_relative_norm_error\":";stats(norm_error);
 std::cout<<",\"after_lp8_output_input_energy_ratio\":";stats(encoded_ratio);
 std::cout<<",\"after_lp8_absolute_relative_energy_error\":";stats(encoded_error);
 std::cout<<",\"after_lp8_pairs_with_relative_error_over_1e_4\":"<<significant
 <<",\"aggregate_output_input_energy_ratio\":"<<eout_total/ein_total
 <<",\"maximum_ratio_witness\":{\"input_tokens\":["<<max_a<<","<<max_b<<"],\"output_tokens\":["<<max_r<<","<<max_g<<"]}"
 <<",\"minimum_ratio_witness\":{\"input_tokens\":["<<min_a<<","<<min_b<<"],\"output_tokens\":["<<min_r<<","<<min_g<<"]}},\n";

 u32 anti_raw=0,anti_encoded=0,equal_raw=0,roundtrips=0;
 for(u32 q=0;q<256;++q){Complex x=decode(lut,u8(q)),y=decode(lut,u8(q^8));
  Hadamard h=hadamard(x,y),eq=hadamard(x,x);anti_raw+=h.plus.x!=0||h.plus.y!=0;
  anti_encoded+=complex_token(lut,h.plus)!=0;equal_raw+=eq.minus.x!=0||eq.minus.y!=0;
  if(q>=16)roundtrips+=complex_token(lut,x)!=q;
 }
 std::cout<<"\"exact_cancellation\":{\"all_symbols_including_zero_aliases\":256,\"nonzero_symbols\":240,\"antipodal_raw_nonzero_failures\":"<<anti_raw
 <<",\"antipodal_encoded_nonzero_failures\":"<<anti_encoded<<",\"equal_input_difference_nonzero_failures\":"<<equal_raw
 <<",\"nonzero_cell_roundtrip_failures\":"<<roundtrips<<"},\n";

 const u32 radial=8,base=radial*16;double nominal_r=std::exp2(-4.0+(radial-.5)*.5);
 std::cout<<"\"phase_sweep\":{\"base_token\":"<<base<<",\"radial_nibble\":"<<radial<<",\"nominal_radius\":"<<nominal_r
 <<",\"comparison\":\"Each row uses actual decoded Q11 inputs. raw_expected energies are the exact real Hadamard identity for those inputs; nominal_ideal uses equal nominal radius and phi=k*2pi/16. Encoded values include quotient quantization and are not detector probabilities.\",\"points\":[\n";
 double sweep_max_abs=0,encoded_sweep_max_abs=0;
 for(u32 k=0;k<16;++k){Complex x=decode(lut,u8(base)),y=decode(lut,u8(base+k));Hadamard h=hadamard(x,y);
  double ex=energy(x),ey=energy(y),dot=double(i64(x.x)*y.x+i64(x.y)*y.y)/ENERGY_SCALE;
  double exact_plus=(ex+ey+2*dot)/2,exact_minus=(ex+ey-2*dot)/2;
  u8 r=complex_token(lut,h.plus),g=complex_token(lut,h.minus);double ep=energy(decode(lut,r)),em=energy(decode(lut,g));
  double idealp=nominal_r*nominal_r*(1+std::cos(k*2*PI/16)),idealm=nominal_r*nominal_r*(1-std::cos(k*2*PI/16));
  sweep_max_abs=std::max({sweep_max_abs,std::abs(energy(h.plus)-exact_plus),std::abs(energy(h.minus)-exact_minus)});
  encoded_sweep_max_abs=std::max({encoded_sweep_max_abs,std::abs(ep-idealp),std::abs(em-idealm)});
  std::cout<<"{\"phase_index\":"<<k<<",\"phase_turns\":"<<k/16.0<<",\"phase_radians\":"<<k*2*PI/16
  <<",\"input_tokens\":["<<base<<","<<base+k<<"],\"input_energy\":"<<ex+ey
  <<",\"raw_expected_plus\":"<<exact_plus<<",\"raw_expected_minus\":"<<exact_minus
  <<",\"integer_plus\":"<<energy(h.plus)<<",\"integer_minus\":"<<energy(h.minus)
  <<",\"nominal_ideal_plus\":"<<idealp<<",\"nominal_ideal_minus\":"<<idealm
  <<",\"encoded_plus\":"<<ep<<",\"encoded_minus\":"<<em
  <<",\"output_tokens\":["<<u32(r)<<","<<u32(g)<<"]}"<<(k==15?"":",")<<"\n";
 }
 std::cout<<"],\"maximum_integer_port_energy_error_against_decoded_input_identity\":"<<sweep_max_abs
 <<",\"maximum_encoded_port_energy_error_against_nominal_ideal\":"<<encoded_sweep_max_abs<<"},\n";

 std::vector<double> lut_amp_errors,encoding_amp_errors,complex_errors;u64 amplitude_outside=0;
 for(u32 q=16;q<256;++q){double target=std::exp2(-4.0+((q>>4)-.5)*.5);
  lut_amp_errors.push_back(std::abs(amplitude(decode(lut,u8(q)))-target)/target);}
 const u32 radial_steps=15*64,angle_steps=256;
 for(u32 i=0;i<radial_steps;++i){double r=std::exp2(-4.0+7.5*(i+.5)/radial_steps);
  for(u32 j=0;j<angle_steps;++j){double phi=2*PI*(j+.5)/angle_steps;
   Complex input{i32(std::llround(r*std::cos(phi)*2048)),i32(std::llround(r*std::sin(phi)*2048))};
   double actual=amplitude(input);if(actual<std::exp2(-4.0)||actual>=std::exp2(3.5)){++amplitude_outside;continue;}
   Complex decoded=decode(lut,complex_token(lut,input));encoding_amp_errors.push_back(std::abs(amplitude(decoded)-actual)/actual);
   double dx=double(decoded.x)-input.x,dy=double(decoded.y)-input.y;
   complex_errors.push_back(std::hypot(dx,dy)/(actual*2048));
  }
 }
 std::cout<<"\"amplitude_accuracy\":{\"lut_cell_center_relative_amplitude_error\":";stats(lut_amp_errors);
 std::cout<<",\"lp8_encoding_sample_definition\":\"960 log-radius midpoints across [-4,3.5) times 256 phase midpoints, quantized to Q11; samples outside actual input magnitude [2^-4,2^3.5) are excluded and counted\",\"attempted_samples\":"<<u64(radial_steps)*angle_steps
 <<",\"q11_inputs_outside_nominal_radius_window\":"<<amplitude_outside
 <<",\"lp8_encoding_in_window_relative_amplitude_error\":";stats(encoding_amp_errors);
 std::cout<<",\"lp8_encoding_in_window_relative_complex_error\":";stats(complex_errors);
 std::cout<<"},\n";

 u8 sr[16],sg[16];Aux seed_aux{};dwi::seed_block(0,756,sr,sg,seed_aux);Complex sv=decode(lut,sg[0]);
 u8 encoded_two=complex_token(lut,Complex{4096,0});
 std::cout<<"\"source_wavefront\":{\"desired\":[0,2,0,1],\"R_token\":"<<u32(sr[0])<<",\"G_token\":"<<u32(sg[0])
 <<",\"encoded_exact_q11_amplitude_two\":"<<u32(encoded_two)<<",\"B_word\":"<<seed_aux.history<<",\"A_word\":"<<seed_aux.inverse_t
 <<",\"decoded_G_q11\":["<<sv.x<<","<<sv.y<<"],\"decoded_G_magnitude\":"<<amplitude(sv)
 <<",\"relative_amplitude_error\":"<<std::abs(amplitude(sv)-2)/2
 <<",\"absolute_complex_error\":"<<std::hypot(double(sv.x)/2048-2,double(sv.y)/2048)
 <<",\"decoded_phase_degrees\":"<<std::atan2(double(sv.y),sv.x)*180/PI<<"},\n";

 u64 seam_cases=0,seam_fail=0;u32 inverse_fail=0;
 for(u32 i=0;i<4096;++i){i64 u=i64(dw::mix(i)&1048575)-524288,v=i64(dw::mix(i+9000)&1048575)-524288;
  for(i32 n=-4;n<=4;++n){V4 a=klein(lut,u,v),b=klein(lut,u+i64(n)*65536,(n&1)?-v:v);
   ++seam_cases;seam_fail+=a.x!=b.x||a.y!=b.y||a.z!=b.z||a.w!=b.w;}}
 for(u32 p=0;p<65536;++p)inverse_fail+=u16(p+u16(0u-p))!=0;
 std::cout<<"\"exact_invariants\":{\"klein_quotient_cases\":"<<seam_cases<<",\"klein_coordinate_mismatches\":"<<seam_fail
 <<",\"phase_inverse_words\":65536,\"phase_inverse_failures\":"<<inverse_fail<<"},\n";

 u64 rk_cases=0,rk_fail=0,event_arg_fail=0,event_output_changes=0;V2 witness_q{},witness_drive{},witness_forced{},witness_control{};
 RKTrace witness_trace{};i32 witness_dt=0,witness_k=0;bool found=false;
 for(i32 dt:{1024,8192,32768,65536})for(u32 i=0;i<4096;++i){
  V2 q{i32(dw::mix(i)&65535),i32(dw::mix(i+10000)&65535)};
  V2 drive{nearest(dw::signed16(dw::mix(i+20000)),2),nearest(dw::signed16(dw::mix(i+30000)),2)+25032};
  i32 k=i32(dw::mix(i+40000)%4097);RKTrace f=trace_rk(lut,q,drive,k,dt,2),n=trace_rk(lut,q,drive,k,dt,0);
  V2 actual=rk4(lut,q,drive,k,dt);++rk_cases;rk_fail+=actual.x!=f.result.x||actual.y!=f.result.y;
  event_arg_fail+=f.arg4.x!=n.arg4.x||f.arg4.y-n.arg4.y!=2;
  bool different=actual.x!=n.result.x||actual.y!=n.result.y;event_output_changes+=different;
  if(different&&!found){found=true;witness_q=q;witness_drive=drive;witness_dt=dt;witness_k=k;witness_forced=actual;witness_control=n.result;witness_trace=f;}
 }
 std::cout<<"\"forced_four_stage_map\":{\"comparison\":\"Native integer rk4 versus independently assembled integer stages with ties-away rounding; event-off is a control, not a change to delivered model\",\"cases\":"<<rk_cases
 <<",\"native_reference_mismatches\":"<<rk_fail<<",\"fourth_argument_two_unit_event_failures\":"<<event_arg_fail
 <<",\"event_changes_final_integer_output_cases\":"<<event_output_changes<<",\"event_visible_witness\":{\"q\":";v2(witness_q);
 std::cout<<",\"drive\":";v2(witness_drive);std::cout<<",\"coupling_q16\":"<<witness_k<<",\"dt_q16\":"<<witness_dt<<",\"forced_output\":";v2(witness_forced);
 std::cout<<",\"event_off_output\":";v2(witness_control);std::cout<<",\"fourth_argument\":";v2(witness_trace.arg4);
 std::cout<<"}},\n\"overall_structural_failures\":"<<anti_raw+anti_encoded+equal_raw+roundtrips+seam_fail+inverse_fail+rk_fail+event_arg_fail<<"\n}\n";
 return anti_raw+anti_encoded+equal_raw+roundtrips+seam_fail+inverse_fail+rk_fail+event_arg_fail?1:0;
}
