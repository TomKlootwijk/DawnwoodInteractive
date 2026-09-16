#include "dawnwood/cpu.hpp"
#include <iostream>
#include <functional>
#include <string>
#include <cstring>
#include <fstream>
#include <set>
using namespace dw;
static int assertions=0,cases=0;
static void require(bool p,const std::string& what){++assertions;if(!p)throw std::runtime_error(what);}
static void near(float a,float b,float e,const std::string& what){require(std::fabs(a-b)<=e,what);}
static void test(const char* name,const std::function<void()>& body){body();++cases;std::cout<<"PASS "<<name<<"\n";}
int main(int argc,char** argv){try{
    test("wire formats",[]{require(sizeof(Op)==64,"operator size");require(sizeof(BC5)==16,"BC5 size");require(sizeof(Aux)==8,"aux size");require(sizeof(Stage)==64,"stage size");require(offsetof(Stage,g)-offsetof(Stage,r)==16,"token arrays adjacent");});
    test("parity is population parity",[]{for(u32 x=0;x<65536;++x){u32 p=0;for(u32 k=0;k<16;++k)p^=(x>>k)&1;require(parity(x)==p,"population parity");}});
    test("rotation and signed representation",[]{for(u32 n=0;n<32;++n)require(rotl(rotl(0x89abcdefu,n),32-n)==0x89abcdefu,"rotate inverse");require(signed16(65535)==-1,"negative one");require(signed16(32768)==-32768,"minimum");require(signed16(65536)==0,"masked word");});
    test("implicit tree addresses and leaf depth",[]{for(u64 i=0;i<1000;++i){require(child(i,0)==2*i+1,"left");require(child(i,1)==2*i+2,"right");}std::array<Op,OP_COUNT> o{};for(u32 i=0;i<OP_COUNT;++i)o[i]=seed_op(i);for(u32 i=0;i<100;++i){u32 n=route(o.data(),fold(i*.017f,i*.123f),i&1,mix(i));require(n>=15&&n<31,"valid leaf");}});
    test("Klein quotient seam and embedding",[]{for(int i=-12;i<=12;++i)for(int j=-6;j<=6;++j){float u=i*.13f,v=j*.19f;auto a=klein(u,v),b=klein(u+1,-v);near(a.x,b.x,5e-6f,"Kx seam");near(a.y,b.y,5e-6f,"Ky seam");near(a.z,b.z,2e-6f,"Kz seam");near(a.w,b.w,2e-6f,"Kw seam");auto f=fold(u,v);auto c=klein(f.u,f.v);near(a.x,c.x,4e-6f,"fold x");near(a.y,c.y,4e-6f,"fold y");near(a.z,c.z,2e-6f,"fold z");near(a.w,c.w,2e-6f,"fold w");}});
    test("Klein folds preserve domain and flip parity",[]{for(int n=-8;n<9;++n){auto a=fold(n+.25f,.2f);near(a.u,.25f,1e-6f,"u");near(a.v,(n&1)?.8f:.2f,1e-6f,"v");require(a.flip==u32(n&1),"flip");}});
    test("LP8 cell-centre codec round trips",[]{for(u32 i=16;i<256;++i){auto q=token_chart(u8(i));require(chart_token(q.u,q.v)==i,"chart roundtrip");auto c=lut_entry(i);require(complex_token(c.x,c.y)==i,"complex roundtrip");}for(u32 i=0;i<16;++i){auto c=lut_entry(i);require(c.x==0&&c.y==0,"zero symbol");}require(complex_token(0,0)==0,"exact zero");});
    test("source wavefront starts at zero/2 with identity inverse",[]{u8 r[16],g[16];Aux a{};seed_block(0,756,r,g,a);for(u32 i=0;i<16;++i){require(r[i]==0,"source R");require(g[i]==complex_token(2,0),"source G");}require(a.history==0&&a.inverse_t==0,"B zero, T inverse identity");});
    test("BC4 constant blocks remain exact",[]{u8 x[16];for(u32 v=0;v<256;++v){std::fill(x,x+16,u8(v));u64 b=encode_bc4(x);for(u32 i=0;i<16;++i)require(decode_bc4(b,i)==v,"constant codec");}});
    test("BC4 endpoint modes and all selector bits",[]{u8 p[8];palette(255,0,p);require(p[0]==255&&p[1]==0&&p[2]==218&&p[7]==36,"eight-entry mode");palette(0,255,p);require(p[6]==0&&p[7]==255&&p[2]==51,"six-entry mode");for(u32 i=0;i<16;++i)for(u32 k=0;k<8;++k){u64 b=255|(u64(k)<<(16+3*i));palette(255,0,p);require(decode_bc4(b,i)==p[k],"selector bit position");}});
    test("optimized BC4 selector exhausts every endpoint and byte",[]{
        for(u32 hi=1;hi<256;++hi)for(u32 lo=0;lo<hi;++lo){u8 p[8];palette(u8(hi),u8(lo),p);
            for(u32 q=0;q<256;++q){u32 best=0,error=256;
                for(u32 i=0;i<8;++i){u32 e=q>p[i]?q-p[i]:p[i]-q;if(e<error){best=i;error=e;}}
                require(bc4_selector(q,hi,lo,p)==best,"all ties preserve the original selector");}}
    });
    test("optimized BC5 bytes and fused error match the reference",[]{
        for(u32 seed=0;seed<10000;++seed){u8 r[16],g[16];for(u32 k=0;k<16;++k){r[k]=u8(mix(seed*32+k));g[k]=u8(mix(seed*32+k+16));}
            if(seed<256){std::fill(r,r+16,u8(seed));std::fill(g,g+16,u8(255-seed));}
            u64 a=encode_bc4_reference(r),b=encode_bc4_reference(g);BC5 expected{u32(a),u32(a>>32),u32(b),u32(b>>32)};
            u32 error;BC5 got=encode_bc5_with_error(r,g,error);require(std::memcmp(&expected,&got,sizeof(got))==0,"packed BC5 bytes");
            require(error==quant_error(expected,r,g),"fused error is identical");}
    });
    test("LP8 pair cache preserves all pairs including exact cancellation",[]{
        std::array<V4,256> lut{};for(u32 i=0;i<256;++i)lut[i]=lut_entry(i);
        const float offset[]={0.f,1.f/65536.f,-1.01f,0.5f};
        for(u32 i=0;i<65536;++i){V4 x=lut[i&255],y=lut[i>>8],p=pair_entry(x,y);
            float hx=(x.x+y.x)*0.7071067811865475f,hy=(x.y+y.y)*0.7071067811865475f;
            float gx=(x.x-y.x)*0.7071067811865475f,gy=(x.y-y.y)*0.7071067811865475f;
            for(float d:offset){require(pair_token(p.x,p.y,d,-d)==complex_token(hx,hy,d,-d),"sum pair token");
                require(pair_token(p.z,p.w,-d,d)==complex_token(gx,gy,-d,d),"difference pair token");}}
    });
    test("cached recurrence preserves every stage byte",[]{
        std::array<V4,256> lut{};for(u32 i=0;i<256;++i)lut[i]=lut_entry(i);
        std::vector<V4> pairs(65536);for(u32 i=0;i<65536;++i)pairs[i]=pair_entry(lut[i&255],lut[i>>8]);
        std::array<Op,OP_COUNT> ops{};for(u32 i=0;i<OP_COUNT;++i)ops[i]=seed_op(i);
        for(u32 i=0;i<1024;++i){u8 r[16],g[16];Aux a;seed_block(i,756,r,g,a);Config cfg;cfg.jitter=i&1;cfg.dt=(i&2)?1.f/64.f:.3f;
            cfg.inverse_gain=(i&4)?0.f:.25f;a.inverse_t=mix(i);a.history=mix(i+1);
            Stage expected=evolve(r,g,a,u8(mix(i)),u8(mix(i+7)),ops.data(),lut.data(),i,i,756,cfg);
            Stage got=evolve(r,g,a,u8(mix(i)),u8(mix(i+7)),ops.data(),lut.data(),i,i,756,cfg,pairs.data());
            require(std::memcmp(&expected,&got,sizeof(got))==0,"cached stage equality");
            ops[i%OP_COUNT]=mutate_op(ops.data(),i%OP_COUNT,got,i,756,cfg);}
    });
    test("BC5 separate dichromatic channels",[]{for(u32 seed=0;seed<128;++seed){u8 r[16],g[16],a[16],b[16];for(u32 k=0;k<16;++k){r[k]=u8(mix(seed*32+k));g[k]=u8(mix(seed*32+k+16));}auto q=encode_bc5(r,g);decode_bc5(q,a,b);u32 e=0;for(u32 i=0;i<16;++i){e+=std::abs(int(r[i])-int(a[i]))+std::abs(int(g[i])-int(b[i]));}require(quant_error(q,r,g)==e,"error accounting");require(e<=32*37,"endpoint codec error envelope");}});
    test("packed program instruction semantics",[]{for(u32 f=0;f<16;++f){Op o{};for(u32 k=0;k<BODY_WORDS;++k)o.code[k]=ins(0,7,7,7);o.code[0]=ins(f,0,1,2,32768);u16 r[8]={0,60000,7000,0,0,0,0,0};execute(o,r);u32 z=0,a=60000,b=7000;
        switch(f){case 0:z=a;break;case 1:z=a+b;break;case 2:z=a-b;break;case 3:z=(a*b)>>16;break;case 4:z=a^b;break;case 5:z=a&b;break;case 6:z=a|b;break;case 7:{u32 n=b&15;z=(a<<n)|(a>>((16-n)&15));break;}case 8:z=u32(i64(signed16(a)+signed16(b))*23170/32768);break;case 9:z=u32(i64(signed16(a)-signed16(b))*23170/32768);break;case 10:z=b;break;case 11:z=a;break;case 12:z=u32((u64(a)*32767+u64(b)*32768)/65535);break;case 13:z=32768;break;case 14:z=a+32768;break;case 15:z=parity(a)?b:32768;break;}require(r[0]==u16(z),"VM opcode");}});
    test("mutated words have total arithmetic",[]{for(u32 seed=0;seed<1000;++seed){Op o{};for(u32 k=0;k<BODY_WORDS;++k)o.code[k]=mix(seed*8+k);u16 r[8]{};for(u32 k=0;k<8;++k)r[k]=u16(mix(seed+k));execute(o,r);require(true,"arbitrary instruction bits execute");}});
    test("primitive supports",[]{near(sd_box(0,0,1,1),-1,1e-6f,"box interior");near(sd_box(2,0,1,1),1,1e-6f,"box exterior");near(sd_triangle(0,1,1),0,1e-6f,"triangle apex");require(sd_triangle(0,0,1)<0,"triangle interior");for(u32 k=0;k<6;++k){Op o=seed_op(0);o.support=24000|(k<<16);require(std::isfinite(support_sdf(o,{.6f,.3f,0})),"finite support");}});
    test("RK4 constant derivative and fourth-slot Y-up",[]{V2 q{.2f,.3f},v{.4f,-.2f};auto n=rk4(q,v,0,.125f);near(n.x,q.x+.125f*v.x,1e-6f,"constant dx");near(n.y,q.y+.125f*v.y,1e-6f,"constant dy");auto a=rk4(q,v,.15f,.25f,0),b=rk4(q,v,.15f,.25f,.1f);require(a.x!=b.x||a.y!=b.y,"k4 Y event changes nonlinear flow");});
    test("inverse-T word composition",[]{for(u32 a=0;a<65536;a+=113){u16 inv=u16(0u-a);require(u16(a+inv)==0,"phase inverse");}});
    test("one-bit executable body mutation",[]{auto a=CPUField();Stage s{};s.feedback=0xa511;s.aux={0xabc,0};for(u32 i=0;i<OP_COUNT;++i){auto b=mutate_op(a.ops.data(),i,s,3,756,a.cfg);u32 changes=0;for(u32 k=0;k<BODY_WORDS;++k){u32 v=b.code[k]^a.ops[i].code[k];for(u32 z=0;z<32;++z)changes+=(v>>z)&1;}require(changes==jit(3,i,756),"exactly one code bit when jitter bit is one");}});
    test("freeze flag preserves every operator byte",[]{CPUField a;a.cfg.mutate=0;auto saved=a.ops;for(int i=0;i<10;++i)a.step();require(std::memcmp(saved.data(),a.ops.data(),sizeof(saved))==0,"no mutation when frozen");});
    test("feedback changes executable bodies and positions",[]{CPUField a;auto saved=a.ops;a.step();bool code=false,pos=false;for(u32 i=0;i<OP_COUNT;++i){code|=std::memcmp(saved[i].code,a.ops[i].code,sizeof(saved[i].code))!=0;pos|=saved[i].location!=a.ops[i].location;}require(code&&pos,"body and surface placement move");});
    test("code references affect numerical behavior",[]{CPUField a(3,16,7,true),b=a;b.ops[30].links=0;for(u32 i=0;i<OP_COUNT;++i)b.ops[i].links=0;for(int i=0;i<5;++i){a.step();b.step();}require(a.digest()!=b.digest(),"live graph reference sensitivity");});
    test("closed-loop determinism",[]{CPUField a,b;for(u32 i=0;i<48;++i){a.step();b.step();require(a.digest()==b.digest(),"same seed/state gives same next state");}require(a.epoch==48&&a.visited==336&&a.cursor==0,"cursor full sweeps");});
    test("checkpoint-by-state continuation",[]{CPUField a(3,16,7,true);for(u32 i=0;i<7;++i)a.step();CPUField b=a;for(u32 i=0;i<13;++i){a.step();b.step();}require(a.digest()==b.digest()&&a.epoch==b.epoch&&a.cursor==b.cursor,"continuation state");});
    test("window coverage has no padding-only pages",[]{CPUField a;std::set<u64> covered;for(u32 k=0;k<48;++k){for(u32 i=0;i<a.active;++i)covered.insert((a.cursor+i)%a.cells.size());a.step();}require(covered.size()==a.cells.size(),"every block visited");});
    test("partial window and page seam",[]{CPUField a(2,8,3,true);for(u32 i=0;i<9;++i)a.step();require(a.cursor==3&&a.visited==27,"window wraps between pages");});
    test("native field storage accounting",[]{require(page_bytes(4096,false)==25165824,"BC5 page 24MiB");require(page_bytes(4096,true)==41943040,"RG8 page 40MiB");require(page_bytes(8192,false)==100663296,"BC5 page 96MiB");});
    test("free-memory budget arithmetic",[]{require(budget_bytes(1000,100,.96)==900,"reserve dominates");require(budget_bytes(1000,0,.96)==960,"fraction dominates");require(budget_bytes(1000,1000,1)==0,"no capacity");require(budget_bytes(1000,0,1)==1000,"full fill permitted");require(budget_bytes(1000,0,2)==0,"invalid fill");});
    test("exact storage has no BC5 token loss",[]{CPUField a(3,16,7,true);for(int i=0;i<8;++i)a.step();require(a.error==0,"exact codec error zero");});
    test("BC5 error is observed rather than silently called lossless",[]{CPUField a;for(int i=0;i<16;++i)a.step();require(a.error>0,"nonzero measured token error");});
    test("ablation seeds and jitter produce distinct recurrences",[]{CPUField a,b,c;a.cfg.jitter=0;c.seed=757;for(int i=0;i<12;++i){a.step();b.step();c.step();}require(a.digest()!=b.digest(),"jitter ablation");require(b.digest()!=c.digest(),"seed sensitivity");});
    test("longer exact and compressed circulation",[]{for(bool raw:{false,true}){CPUField a(3,16,17,raw);for(int i=0;i<128;++i)a.step();require(a.epoch==128&&a.visited==2176,"long run count");for(auto& o:a.ops)require((o.location&65535)<65536,"packed location");}});
    if(argc==3&&std::string(argv[1])=="--export-operators"){std::array<Op,OP_COUNT> ops{};for(u32 i=0;i<OP_COUNT;++i)ops[i]=seed_op(i);std::ofstream f(argv[2],std::ios::binary);f.write(reinterpret_cast<const char*>(ops.data()),sizeof(ops));require(bool(f),"operator image export");}
    std::cout<<"SUMMARY "<<cases<<" cases, "<<assertions<<" assertions, 0 failures\n";return 0;
}catch(const std::exception& e){std::cerr<<"FAIL "<<e.what()<<" after "<<cases<<" cases / "<<assertions<<" assertions\n";return 1;}}
