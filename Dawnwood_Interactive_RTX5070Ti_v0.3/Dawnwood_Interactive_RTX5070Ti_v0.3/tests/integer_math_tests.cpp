#include "dawnwood/integer_math.hpp"
#include <cmath>
#include <cstdint>
#include <functional>
#include <iostream>
#include <stdexcept>
#include <string>
#include <limits>
using namespace dwi;
namespace {
u64 checks=0;u32 cases=0;
void require(bool p,const char* what){++checks;if(!p)throw std::runtime_error(what);}
void test(const char* name,const std::function<void()>& fn){fn();++cases;std::cout<<"PASS "<<name<<"\n";}
double pi=std::acos(-1.0);
int phase_error(u16 a,u16 b){return std::abs(delta_turn(i32(a)-i32(b)));}
u16 reference_phase(i32 y,i32 x){
    double a=std::atan2(double(y),double(x))/(2*pi)*65536.0;
    return u16(std::llround(a));
}
dw::V4 reference_klein(Chart q){return dw::klein(float(q.u)/65536,float(q.v)/65536);}
}
int main(){try{
    MathLut lut{};init_math_lut(lut);
    test("explicit scales and compact wire format",[&]{
        require(sizeof(MathLut)==1540,"math LUT byte budget");
        require(CHART_ONE==65536&&COMPLEX_ONE==2048&&GEOMETRY_ONE==262144,"fixed-point units");
        require(offsetof(MathLut,sin_quarter)==1024,"packed trig offset");
        require(lut.sin_word(0)==0&&lut.sin_word(256)==32768,"sine endpoints");
    });
    test("rounding and signed boundary arithmetic",[]{
        require(round_div(1,2)==1&&round_div(-1,2)==-1,"ties away");
        require(round_div(2,3)==1&&round_div(-2,3)==-1,"nearest");
        require(round_div(1,3)==0&&round_div(-1,3)==0,"nearest zero");
        require(round_div(std::numeric_limits<i64>::min(),1)==std::numeric_limits<i64>::min(),"minimum int64");
        require(saturate_i32(2147483648LL)==2147483647,"positive saturation");
        require(saturate_i32(-2147483649LL)==(-2147483647-1),"negative saturation");
        require(mul_q16(-65536,32768)==-32768,"signed Q16 multiplication");
        require(floor_mod_turn(std::numeric_limits<i64>::min())==0,"minimum int64 modulo");
        require(fold(std::numeric_limits<i64>::min(),-1).v==65535,"minimum winding");
    });
    test("integer-only division lowering preserves exact arithmetic",[]{
        for(u32 i=0;i<100000;++i){
            u64 n=(u64(dw::mix(i))<<32)|dw::mix(i+1);
            u64 d=(u64(dw::mix(i+2))<<32)|dw::mix(i+3);if(!d)d=1;
            UDivMod got=divmod_u64(n,d);
            require(got.quotient==n/d&&got.remainder==n%d,"restoring uint64 divide and remainder");
            i64 signed_n=i64(n);
            require(round_div_const<15>(signed_n)==round_div(signed_n,15),"fixed divisor fifteen");
            require(round_div_const<65536>(signed_n)==round_div(signed_n,65536),"fixed divisor power of two");
            u32 shift=i%63;
            require(trunc_pow2(signed_n,shift)==signed_n/(i64(1)<<shift),"signed shift truncates toward zero");
        }
        for(u64 n:{u64(0),u64(1),u64(1)<<63,~u64(0)})for(u64 d:{u64(1),u64(2),u64(1)<<63,~u64(0)}){
            UDivMod got=divmod_u64(n,d);require(got.quotient==n/d&&got.remainder==n%d,"division extrema");
        }
        require(trunc_pow2(std::numeric_limits<i64>::min(),0)==std::numeric_limits<i64>::min(),"minimum signed shift zero");
        require(trunc_pow2(std::numeric_limits<i64>::min(),63)==-1,"minimum signed shift 63");
        require(trunc_pow2(std::numeric_limits<i64>::min(),64)==0,"large signed shift");
    });
    test("Klein chart quotient seams and negative windings",[]{
        for(i32 n=-100;n<=100;++n)for(i32 u:{0,1,32767,65535})for(i32 v:{0,1,32768,65535}){
            Chart c=fold(i64(n)*65536+u,v);
            require(c.u==u,"canonical radial coordinate");
            require(c.flip==u32(n&1),"negative winding parity");
            require(c.v==((n&1)?floor_mod_turn(-i64(v)):v),"phase reversal");
            auto a=fold(u,v),b=fold(i64(u)+65536,-i64(v));
            require(a.u==b.u&&a.v==b.v,"quotient chart coordinates");
        }
        require(delta_turn(32768)==-32768&&delta_turn(-32768)==-32768,"half-turn tie");
    });
    test("LP8 codec roundtrips and exact antipodal reconstruction",[&]{
        for(u32 q=0;q<256;++q){
            Complex z=decode(lut,u8(q)),opposite=decode(lut,u8(q^8));
            require(z.x==-opposite.x&&z.y==-opposite.y,"exact decoded antipode");
            require(complex_token(lut,z)==(q<16?0:q),"complex codec roundtrip");
            Chart c=token_chart(u8(q));
            if(q>=16)require(chart_token(c.u,c.v)==q,"chart codec roundtrip");
            else require(z.x==0&&z.y==0,"all high-zero aliases decode zero");
            Hadamard h=hadamard(z,opposite),same=hadamard(z,z);
            require(h.plus.x==0&&h.plus.y==0,"destructive cancellation");
            require(same.minus.x==0&&same.minus.y==0,"difference cancellation");
            require(complex_token(lut,h.plus)==0,"cancellation maps to canonical zero");
        }
        require(complex_token(lut,Complex{0,0},2147483647,(-2147483647-1))==0,"zero ignores chart offset");
        require(complex_token(lut,Complex{4096,0})!=0,"source amplitude two is nonzero");
        for(u32 q=16;q<256;++q){
            Complex a=decode(lut,u8(q));
            require(complex_token(lut,a,65536,0)==u8((q&240)|((15-(q&15))&15)),"radial wrap reverses phase");
        }
    });
    test("Hadamard pair cancellation and quantified energy error",[&]{
        double worst=0;
        for(u32 a=0;a<256;++a)for(u32 b=0;b<256;++b){
            Complex x=decode(lut,u8(a)),y=decode(lut,u8(b));Hadamard h=hadamard(x,y),rev=hadamard(y,x);
            require(h.plus.x==rev.plus.x&&h.plus.y==rev.plus.y,"commutative plus");
            require(h.minus.x==-rev.minus.x&&h.minus.y==-rev.minus.y,"antisymmetric minus");
            double ein=double(squared_norm(x))+double(squared_norm(y));
            double eout=double(squared_norm(h.plus))+double(squared_norm(h.minus));
            double component_bound=2.0*(std::abs(h.plus.x)+std::abs(h.plus.y)+std::abs(h.minus.x)+std::abs(h.minus.y))+4.0;
            // Coefficient error contributes <0.000041*input energy; four
            // nearest-integer component roundings contribute the absolute term.
            require(std::abs(eout-ein)<=0.0000411*ein+component_bound,"finite-precision energy bound");
            if(ein)worst=std::max(worst,std::abs(eout-ein)/ein);
        }
        std::cout<<"METRIC hadamard_max_relative_energy_error="<<worst<<"\n";
    });
    test("trigonometric LUT symmetry and independent accuracy",[&]{
        double worst=0;
        for(i32 p=0;p<65536;++p){
            i32 s=sin_q15(lut,p),c=cos_q15(lut,p);
            require(s==-sin_q15(lut,i64(p)+32768),"sine antipode");
            require(s==-sin_q15(lut,-i64(p)),"sine odd symmetry");
            require(c==sin_q15(lut,i64(p)+16384),"cosine quarter shift");
            double ideal=std::sin(double(p)*2*pi/65536)*32768;
            worst=std::max(worst,std::abs(s-ideal));
        }
        require(worst<=1.2,"quarter-wave interpolation max error");
        require(sin_q15(lut,16384)==32768&&sin_q15(lut,49152)==-32768,"exact peaks");
        std::cout<<"METRIC sine_max_q15_error="<<worst<<"\n";
    });
    test("integer square root and near-boundary signed radii",[]{
        for(u64 i=0;i<=100000;++i){
            require(isqrt(i*i)==i,"square root exact square");
            if(i){require(isqrt(i*i-1)==i-1,"below exact square");require(radial_sdf(i*i-1,i32(i))<0,"interior sign survives rounding");}
            require(isqrt(i*i+i)==i,"sqrt midpoint floor");
            require(radial_sdf(i*i,i32(i))==0,"exact radial boundary");
            if(i<100000)require(radial_sdf(i*i+1,i32(i))>0,"exterior sign survives rounding");
        }
        require(isqrt(~u64(0))==4294967295ULL,"maximum uint64 sqrt");
        require(isqrt(u64(1)<<63)==3037000499ULL,"sqrt 2^63");
    });
    test("integer logarithm and CORDIC independent reference",[]{
        i32 worst_log=0;int worst_phase=0;
        for(u32 e=0;e<64;++e)require(log2_q16(u64(1)<<e)==i32(e*65536),"log exact power of two");
        require(log2_q16(0)==(-2147483647-1),"zero log sentinel");
        for(u32 i=1;i<100000;++i){
            u64 n=(u64(dw::mix(i))<<32)|dw::mix(i+100000);if(!n)n=1;
            i32 expected=i32(std::floor(std::log2(double(n))*65536));
            worst_log=std::max(worst_log,std::abs(log2_q16(n)-expected));
            i32 x=i32(dw::mix(i)),y=i32(dw::mix(i+1));
            worst_phase=std::max(worst_phase,phase_error(atan2_turn16(y,x),reference_phase(y,x)));
        }
        for(i32 x:{(-2147483647-1),-1,0,1,2147483647})for(i32 y:{(-2147483647-1),-1,0,1,2147483647})
            if(x||y)worst_phase=std::max(worst_phase,phase_error(atan2_turn16(y,x),reference_phase(y,x)));
        require(worst_log<=1,"log within one Q16 log unit");
        require(worst_phase<=1,"CORDIC within one phase unit");
        require(atan2_turn16(0,0)==0,"zero phase convention");
        std::cout<<"METRIC log_max_q16_error="<<worst_log<<"\nMETRIC phase_max_turn16_error="<<worst_phase<<"\n";
    });
    test("embedding quotient identity and independent accuracy",[&]{
        double worst=0;
        for(u32 i=0;i<20000;++i){
            i32 u=i32(dw::mix(i)&65535),v=i32(dw::mix(i+1)&65535);
            V4 a=klein(lut,u,v),b=klein(lut,i64(u)+65536,-i64(v)),c=klein(lut,i64(u)-65536,-i64(v));
            require(a.x==b.x&&a.y==b.y&&a.z==b.z&&a.w==b.w,"positive seam exact");
            require(a.x==c.x&&a.y==c.y&&a.z==c.z&&a.w==c.w,"negative seam exact");
            double tu=double(u)*2*pi/65536,tv=double(v)*2*pi/65536;
            double rad=2+0.5*std::cos(tv);
            double reference[]={rad*std::cos(tu),rad*std::sin(tu),0.5*std::sin(tv)*std::cos(tu/2),0.5*std::sin(tv)*std::sin(tu/2)};
            i32 got[]={a.x,a.y,a.z,a.w};
            for(u32 j=0;j<4;++j)worst=std::max(worst,std::abs(double(got[j])-reference[j]*262144));
        }
        require(worst<=30,"Q18 embedding max error");
        std::cout<<"METRIC embedding_max_q18_error="<<worst<<"\n";
    });
    test("all signed primitive supports and boundary membership",[&]{
        require(sd_box(0,0,100,200)==-100,"box center");
        require(sd_box(100,0,100,200)==0,"box boundary");
        require(sd_box(103,204,100,200)==5,"box 3-4-5 corner");
        require(sd_triangle(0,100,100)==0,"triangle apex");
        require(sd_triangle(0,-100,100)==0,"triangle base");
        require(sd_triangle(0,0,100)<0,"triangle interior");
        require(sd_triangle(101,0,100)>0,"triangle exterior");
        double worst=0;
        for(u32 shape=0;shape<6;++shape){
            dw::Op op{};op.location=dw::pack16(20000,20000);op.support=23999|(shape<<16);
            Chart center{20000,20000,0};
            require(shape==5?support_sdf(lut,op,center)==0:support_sdf(lut,op,center)<0,"primitive center");
            require(support_sdf(lut,op,{50000,50000,0})>0,"primitive exterior");
            for(u32 i=0;i<3000;++i){
                Chart q{i32(dw::mix(i)&65535),i32(dw::mix(i+777)&65535),0};
                i32 got=support_sdf(lut,op,q);double real=dw::support_sdf(op,{float(q.u)/65536,float(q.v)/65536,0})*262144.0;
                worst=std::max(worst,std::abs(double(got)-real));
                // Sign disagreements within the stated quantization envelope are
                // audited as boundary changes, not treated as exact float identity.
                if(std::abs(real)>64)require((got<0)==(real<0),"primitive sign away from quantization band");
                require(support_sign(lut,op,q)==((got>0)-(got<0)),"signed support wrapper");
            }
        }
        require(worst<64,"integer support vs legacy real binding error envelope");
        std::cout<<"METRIC support_max_q18_error="<<worst<<"\n";
    });
    std::cout<<"SUMMARY "<<cases<<" cases, "<<checks<<" assertions, 0 failures\n";return 0;
}catch(const std::exception& e){std::cerr<<"FAIL "<<e.what()<<" after "<<cases<<" cases / "<<checks<<" assertions\n";return 1;}}
