// CPU diagnostics of the actual Dawnwood integer primitives. Floating point is
// used ONLY to summarize overlaps, norms, and ideal reference curves here.
// These readouts are not a measurement or normalization stage in the kernel.
#include "dawnwood/integer_pair_cache.hpp"
#include <algorithm>
#include <array>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
using namespace dwi;
struct State {Complex a,b;};
static u64 checks=0;
static void require(bool p,const char* message){++checks;if(!p)throw std::runtime_error(message);}
static double norm(Complex z){return double(squared_norm(z));}
static double norm(State s){return norm(s.a)+norm(s.b);}
static State h(State s){Hadamard out=hadamard(s.a,s.b);return {out.plus,out.minus};}
static bool equal(Complex a,Complex b){return a.x==b.x&&a.y==b.y;}
static bool equal(State a,State b){return equal(a.a,b.a)&&equal(a.b,b.b);}
static double fidelity(State a,State b){
    double na=norm(a),nb=norm(b);if(!na||!nb)return 0;
    i64 re=i64(a.a.x)*b.a.x+i64(a.a.y)*b.a.y+i64(a.b.x)*b.b.x+i64(a.b.y)*b.b.y;
    i64 im=i64(a.a.x)*b.a.y-i64(a.a.y)*b.a.x+i64(a.b.x)*b.b.y-i64(a.b.y)*b.b.x;
    return std::max(0.0,std::min(1.0,(double(re)*double(re)+double(im)*double(im))/(na*nb)));
}
static double relative_squared_error(State a,State b){
    auto component=[](Complex x,Complex y){double dx=double(x.x)-y.x,dy=double(x.y)-y.y;return dx*dx+dy*dy;};
    return (component(a.a,b.a)+component(a.b,b.b))/norm(a);
}
static State encode_decode(const MathLut& lut,State s){return {decode(lut,complex_token(lut,s.a)),decode(lut,complex_token(lut,s.b))};}
static Complex rotate(const MathLut& lut,Complex z,u16 phase){
    // Composition of the production integer trig and rounding primitives.
    // This two-arm diagnostic circuit is not an alternate field recurrence.
    i32 c=cos_q15(lut,phase),s=sin_q15(lut,phase);
    return {i32(round_div_const<32768>(i64(z.x)*c-i64(z.y)*s)),
            i32(round_div_const<32768>(i64(z.x)*s+i64(z.y)*c))};
}
struct Summary {
    std::string name;std::vector<double> fidelities,norm_ratios,errors;u64 exact=0,zero_output=0;
    u32 worst_r=0,worst_g=0;double worst=2;
    void add(u32 r,u32 g,State before,State after){
        double f=fidelity(before,after);fidelities.push_back(f);norm_ratios.push_back(norm(after)/norm(before));
        errors.push_back(relative_squared_error(before,after));exact+=equal(before,after);zero_output+=norm(after)==0;
        if(f<worst){worst=f;worst_r=r;worst_g=g;}
    }
};
static double quantile(std::vector<double> v,double q){std::sort(v.begin(),v.end());double p=q*(v.size()-1);size_t i=size_t(p);return v[i]+(v[std::min(i+1,v.size()-1)]-v[i])*(p-double(i));}
static void metric_json(std::ostream& f,const std::vector<double>& v){
    f<<"{\"min\":"<<*std::min_element(v.begin(),v.end())<<",\"p05\":"<<quantile(v,.05)
     <<",\"median\":"<<quantile(v,.5)<<",\"p95\":"<<quantile(v,.95)<<",\"max\":"<<*std::max_element(v.begin(),v.end())<<"}";
}
static void summary_json(std::ostream& f,const Summary& s){
    f<<"{\"name\":\""<<s.name<<"\",\"count\":"<<s.fidelities.size()<<",\"normalized_state_overlap_fidelity\":";
    metric_json(f,s.fidelities);f<<",\"unnormalized_output_input_norm_ratio\":";metric_json(f,s.norm_ratios);
    f<<",\"relative_squared_component_error\":";metric_json(f,s.errors);
    f<<",\"exact_component_recoveries\":"<<s.exact<<",\"zero_outputs\":"<<s.zero_output
     <<",\"fidelity_below_0_99\":"<<std::count_if(s.fidelities.begin(),s.fidelities.end(),[](double x){return x<.99;})
     <<",\"fidelity_below_0_90\":"<<std::count_if(s.fidelities.begin(),s.fidelities.end(),[](double x){return x<.9;})
     <<",\"fidelity_below_0_50\":"<<std::count_if(s.fidelities.begin(),s.fidelities.end(),[](double x){return x<.5;})
     <<",\"worst_fidelity_input_tokens\":["<<s.worst_r<<","<<s.worst_g<<"]}";
}
struct SweepRow {u32 phase;double ideal,raw_p,encoded_p,raw_energy,encoded_energy,raw_total_ratio,encoded_total_ratio;};
struct Sweep {u32 radial;std::vector<SweepRow> rows;double raw_error=0,encoded_error=0;};
static void sweep_json(std::ostream& f,const Sweep& s){
    auto visibility=[&](bool encoded){double lo=1e300,hi=0;for(const auto& r:s.rows){double x=encoded?r.encoded_energy:r.raw_energy;lo=std::min(lo,x);hi=std::max(hi,x);}return (hi-lo)/(hi+lo);};
    f<<"{\"radial_bin\":"<<s.radial<<",\"max_raw_probability_error\":"<<s.raw_error
     <<",\"max_encoded_probability_error\":"<<s.encoded_error
     <<",\"raw_port_visibility\":"<<visibility(false)<<",\"encoded_port_visibility\":"<<visibility(true)<<",\"rows\":[";
    for(size_t i=0;i<s.rows.size();++i){const auto& r=s.rows[i];if(i)f<<",";
        f<<"{\"phase_step\":"<<r.phase<<",\"ideal_probability\":"<<r.ideal<<",\"raw_probability\":"<<r.raw_p
         <<",\"encoded_probability\":"<<r.encoded_p<<",\"raw_port_energy_over_input\":"<<r.raw_energy
         <<",\"encoded_port_energy_over_input\":"<<r.encoded_energy
         <<",\"raw_total_norm_ratio\":"<<r.raw_total_ratio<<",\"encoded_total_norm_ratio\":"<<r.encoded_total_ratio<<"}";
    }f<<"]}";
}
int main(int argc,char** argv){try{
    const std::string output=argc>1?argv[1]:"results/integer/quantum_mechanism_checks.json";
    MathLut lut{};init_math_lut(lut);
    Summary raw{"raw_integer_H_squared"},middle{"H_LP8_H_before_final_encoding"},full{"H_LP8_H_LP8"},
            first{"first_H_LP8_vs_first_H_raw"};
    u64 excluded_zero_pairs=0,first_wrapped_ports=0,first_wrapped_pairs=0,first_low_wrap=0,first_high_wrap=0;
    u64 exact_token_recoveries=0,final_wrapped_pairs=0,final_wrapped_ports=0;
    Summary no_wrap{"H_LP8_H_LP8_subset_without_first_stage_wrap"},no_any_wrap{"H_LP8_H_LP8_subset_without_any_radial_wrap"};
    for(u32 r=0;r<256;++r)for(u32 g=0;g<256;++g){
        State input{decode(lut,u8(r)),decode(lut,u8(g))};if(norm(input)==0){++excluded_zero_pairs;continue;}
        State once=h(input),twice=h(once),quantized_once=encode_decode(lut,once);
        State middle_twice=h(quantized_once),full_twice=encode_decode(lut,middle_twice);
        raw.add(r,g,input,twice);middle.add(r,g,input,middle_twice);full.add(r,g,input,full_twice);
        first.add(r,g,once,quantized_once);
        bool wrapped=false;
        for(Complex z:{once.a,once.b}){PairChart chart=direct_pair_chart(z);
            if(chart.u!=PAIR_ZERO&&(chart.u<0||chart.u>=65536)){
                ++first_wrapped_ports;wrapped=true;first_low_wrap+=chart.u<0;first_high_wrap+=chart.u>=65536;
            }
        }
        first_wrapped_pairs+=wrapped;if(!wrapped)no_wrap.add(r,g,input,full_twice);
        bool final_wrapped=false;
        for(Complex z:{middle_twice.a,middle_twice.b}){PairChart chart=direct_pair_chart(z);
            if(chart.u!=PAIR_ZERO&&(chart.u<0||chart.u>=65536)){++final_wrapped_ports;final_wrapped=true;}}
        final_wrapped_pairs+=final_wrapped;
        if(!wrapped&&!final_wrapped)no_any_wrap.add(r,g,input,full_twice);
        u8 a=complex_token(lut,middle_twice.a),b=complex_token(lut,middle_twice.b);
        exact_token_recoveries+=(a==(r<16?0:r)&&b==(g<16?0:g));
    }
    require(raw.fidelities.size()==65280&&excluded_zero_pairs==256,"exhaustive LP8 pair population");
    require(*std::min_element(raw.fidelities.begin(),raw.fidelities.end())>.999,"raw H squared fidelity floor");
    require(raw.zero_output==0,"raw H does not erase nonzero pair");
    const double pi=std::acos(-1.0);std::vector<Sweep> equal_phase,interferometer;
    for(u32 radial:{1u,9u,15u}){
        Sweep eq{radial},mz{radial};Complex base=decode(lut,u8(radial<<4));
        for(u32 step=0;step<16;++step){
            State input{base,decode(lut,u8((radial<<4)|step))},raw_out=h(input),encoded=encode_decode(lut,raw_out);
            double ideal=std::pow(std::cos(pi*double(step)/16),2);
            double p=norm(raw_out.a)/norm(raw_out),pq=norm(encoded.a)/norm(encoded);
            eq.rows.push_back({step,ideal,p,pq,norm(raw_out.a)/norm(input),norm(encoded.a)/norm(input),norm(raw_out)/norm(input),norm(encoded)/norm(input)});
            eq.raw_error=std::max(eq.raw_error,std::abs(p-ideal));eq.encoded_error=std::max(eq.encoded_error,std::abs(pq-ideal));
            if(step==0){require(norm(raw_out.b)==0&&norm(encoded.b)==0,"equal arms exact dark minus port");}
            if(step==8){require(norm(raw_out.a)==0&&norm(encoded.a)==0,"antipodal arms exact dark plus port");}
            State start{base,{0,0}},arms=h(start);arms.b=rotate(lut,arms.b,u16(step*4096));
            State result=h(arms);
            State quant_arms=encode_decode(lut,h(start));
            quant_arms.b=decode(lut,complex_token(lut,rotate(lut,quant_arms.b,u16(step*4096))));
            State quant_result=encode_decode(lut,h(quant_arms));
            double ideal_dark=std::pow(std::sin(pi*double(step)/16),2);
            double raw_dark=norm(result.b)/norm(result),encoded_dark=norm(quant_result.b)/norm(quant_result);
            mz.rows.push_back({step,ideal_dark,raw_dark,encoded_dark,norm(result.b)/norm(start),norm(quant_result.b)/norm(start),norm(result)/norm(start),norm(quant_result)/norm(start)});
            mz.raw_error=std::max(mz.raw_error,std::abs(raw_dark-ideal_dark));
            mz.encoded_error=std::max(mz.encoded_error,std::abs(encoded_dark-ideal_dark));
            if(step==0)require(norm(result.b)==0&&norm(quant_result.b)==0,"H phase-zero H exact dark minus port");
            if(step==8)require(norm(result.a)==0&&norm(quant_result.a)==0,"H phase-pi H exact dark plus port");
        }
        equal_phase.push_back(eq);interferometer.push_back(mz);
    }
    std::ofstream f(output);if(!f)throw std::runtime_error("cannot write diagnostic JSON");
    f<<std::setprecision(17)
     <<"{\n\"schema_version\":1,\n\"implementation\":\"actual dwi integer_math.hpp and integer_pair_cache.hpp primitives\",\n"
     <<"\"scope\":\"CPU mechanism diagnostics only; no claim of physical quantum behavior, entanglement, measurement, or a full quantum simulator\",\n"
     <<"\"readout\":\"Fidelity and Born-style probabilities are normalized host diagnostics only. The kernel does not normalize state or implement measurement. Norm ratios separately expose amplitude amplification or loss hidden by normalization.\",\n"
     <<"\"fidelity_definition\":\"abs(conj(a)*a_out + conj(b)*b_out)^2 / ((abs(a)^2+abs(b)^2)*(abs(a_out)^2+abs(b_out)^2)); zero output -> diagnostic fidelity 0\",\n"
     <<"\"population\":{\"all_token_pairs\":65536,\"both_zero_alias_pairs_excluded\":"<<excluded_zero_pairs<<",\"nonzero_pairs\":65280,\"note\":\"16 zero-amplitude token aliases are retained in the pair enumeration; amplitudes otherwise come from the production Q11 LP8 decode LUT\"},\n"
     <<"\"recovery_diagnostics\":[";
    std::array<const Summary*,6> summaries{{&raw,&middle,&full,&first,&no_wrap,&no_any_wrap}};
    for(size_t i=0;i<summaries.size();++i){if(i)f<<",";summary_json(f,*summaries[i]);}
    f<<"],\n\"LP8_loss\":{\"first_H_quotient_wrapped_pairs\":"<<first_wrapped_pairs<<",\"first_H_quotient_wrapped_ports\":"<<first_wrapped_ports
     <<",\"first_H_low_radius_wraps\":"<<first_low_wrap<<",\"first_H_high_radius_wraps\":"<<first_high_wrap
     <<",\"final_H_quotient_wrapped_pairs\":"<<final_wrapped_pairs<<",\"final_H_quotient_wrapped_ports\":"<<final_wrapped_ports
     <<",\"full_sequence_exact_canonical_token_recoveries\":"<<exact_token_recoveries
     <<",\"interpretation\":\"LP8 wraps normalized log radius through the Klein quotient. A value below or above the representable radial band may become a very different amplitude and reverse phase. Normalized overlap alone does not certify conserved norm or reversible state storage.\"},\n"
     <<"\"equal_amplitude_phase_sweeps\":{\"port\":\"plus\",\"ideal_probability\":\"cos(delta_phase/2)^2\",\"sweeps\":[";
    for(size_t i=0;i<equal_phase.size();++i){if(i)f<<",";sweep_json(f,equal_phase[i]);}
    f<<"]},\n\"H_phase_H_interferometer\":{\"input\":\"production LP8 radial-bin phase-zero-centre amplitude in arm a; arm b zero\",\"port\":\"minus\",\"ideal_probability\":\"sin(delta_phase/2)^2\",\"encoded_sequence\":\"H then LP8 decode/encode both arms; integer Q15 phase rotation of second arm then LP8; H then LP8 both outputs\",\"sweeps\":[";
    for(size_t i=0;i<interferometer.size();++i){if(i)f<<",";sweep_json(f,interferometer[i]);}
    f<<"]},\n\"assertions\":"<<checks<<",\"failures\":0\n}\n";if(!f)throw std::runtime_error("failed writing diagnostic JSON");
    std::cout<<std::setprecision(10);
    for(const Summary* s:summaries)std::cout<<"METRIC "<<s->name<<" fidelity_min="<<*std::min_element(s->fidelities.begin(),s->fidelities.end())
        <<" fidelity_median="<<quantile(s->fidelities,.5)<<" norm_ratio_min="<<*std::min_element(s->norm_ratios.begin(),s->norm_ratios.end())
        <<" norm_ratio_median="<<quantile(s->norm_ratios,.5)<<" norm_ratio_max="<<*std::max_element(s->norm_ratios.begin(),s->norm_ratios.end())<<"\n";
    std::cout<<"METRIC wrapped_first_H_pairs="<<first_wrapped_pairs<<" wrapped_ports="<<first_wrapped_ports<<" low="<<first_low_wrap<<" high="<<first_high_wrap<<"\n";
    for(const Sweep& s:equal_phase)std::cout<<"METRIC equal_phase radial="<<s.radial<<" raw_max_probability_error="<<s.raw_error<<" LP8_max_probability_error="<<s.encoded_error<<"\n";
    for(const Sweep& s:interferometer)std::cout<<"METRIC H_phase_H radial="<<s.radial<<" raw_max_probability_error="<<s.raw_error<<" LP8_max_probability_error="<<s.encoded_error<<"\n";
    std::cout<<"JSON "<<output<<"\nSUMMARY "<<checks<<" assertions, 0 failures; diagnostic deviations reported without converting them into passing physical claims\n";
    return 0;
}catch(const std::exception& e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
