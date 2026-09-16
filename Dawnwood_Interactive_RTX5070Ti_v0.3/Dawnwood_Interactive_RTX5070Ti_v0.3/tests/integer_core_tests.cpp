#include "dawnwood/integer_core.hpp"
#include <algorithm>
#include <array>
#include <cstring>
#include <functional>
#include <iostream>
#include <stdexcept>
#include <vector>
using namespace dwi;
namespace {
u64 checks=0;u32 cases=0;
void require(bool p,const char* text){++checks;if(!p)throw std::runtime_error(text);}
void test(const char* text,const std::function<void()>& fn){fn();++cases;std::cout<<"PASS "<<text<<"\n";}
using Operators=std::array<Op,OP_COUNT>;
using Masks=std::array<u32,MASK_WORDS>;
Masks build_masks(const Operators& ops,const MathLut& lut){
    Masks masks{};
    for(u32 i=0;i<15;++i)for(u32 q=0;q<256;++q)
        if(support_sdf(lut,ops[i],token_chart(u8(q)))>=0)masks[i*8+q/32]|=1u<<(q%32);
    return masks;
}
Operators seed_operators(){Operators ops{};for(u32 i=0;i<OP_COUNT;++i)ops[i]=dwi::seed_op(i);return ops;}
Operators random_operators(u32 seed){
    Operators result{};
    for(u32 i=0;i<OP_COUNT;++i){
        std::array<u32,16> words{};for(u32 j=0;j<16;++j)words[j]=mix(seed*9176+i*16+j);
        std::memcpy(&result[i],words.data(),sizeof(Op));
    }
    return result;
}
bool same_stage(const Stage& a,const Stage& b){return std::memcmp(&a,&b,sizeof(Stage))==0;}
bool same_op(const Op& a,const Op& b){return std::memcmp(&a,&b,sizeof(Op))==0;}
u32 bit_count(u32 x){u32 n=0;while(x){x&=x-1;++n;}return n;}
struct TraceLut {
    const MathLut& lut;mutable std::vector<u32> reads;
    u32 lp_word(u32 i)const{return lut.lp_word(i);}
    u32 sin_word(u32 i)const{reads.push_back(i);return lut.sin_word(i);}
};
struct Cell{std::array<u8,16> r{},g{};Aux aux{};};
// Small CPU execution model of the GPU's staged RG8 transaction. It deliberately
// includes neighbour reads, page/window wrap, simultaneous writes, feedback
// selection, operator bank switching, and mask regeneration.
struct Field{
    u32 pages=3,side=16,active=17;u64 seed=756,epoch=0,cursor=0,visited=0;
    Config cfg{};MathLut lut{};Operators ops{};Masks masks{};std::vector<Cell> cells;
    explicit Field(u32 n=17):active(n){
        init_math_lut(lut);ops=seed_operators();masks=build_masks(ops,lut);
        cells.resize(pages*(side/4)*(side/4));
        for(u64 i=0;i<cells.size();++i)dwi::seed_block(i,seed,cells[size_t(i)].r.data(),cells[size_t(i)].g.data(),cells[size_t(i)].aux);
    }
    void pair(u32 pn,u32 x,u32 y,u8& r,u8& g)const{
        u32 bw=side/4;const Cell& c=cells[pn*bw*bw+(y/4)*bw+x/4];u32 k=(y%4)*4+x%4;r=c.r[k];g=c.g[k];
    }
    template<bool MASKED>std::vector<Stage> step(){
        MemoryOps access{ops.data(),masks.data()};std::vector<Stage> stages(active);
        u64 bpp=u64(side/4)*(side/4);
        for(u32 t=0;t<active;++t){
            u64 idx=(cursor+t)%cells.size();const Cell& c=cells[size_t(idx)];u32 pn=u32(idx/bpp);
            u8 nr=c.r[0],ng=c.g[0];u32 j=cfg.jitter?jit(epoch,idx,seed):0,h=mix(c.aux.history^u32(idx)^u32(epoch));
            for(u32 hop=0;hop<cfg.hops;++hop){
                u32 dir=j^parity(u32(nr)|(u32(ng)<<8))^((h>>(hop&31))&1);
                pn=dir?(pn+pages-1)%pages:(pn+1)%pages;h+=0x61c88647u;pair(pn,h%side,mix(h)%side,nr,ng);
            }
            stages[t]=dwi::evolve<MASKED>(c.r.data(),c.g.data(),c.aux,nr,ng,access,lut,epoch,idx,seed,cfg);
            stages[t].quant_error=0; // RG8 commit is lossless, despite optional BC5 audit bytes.
        }
        Operators next=ops;
        for(u32 i=0;i<OP_COUNT;++i){
            u64 sample=(u64(ops[i].location)+u64(ops[i].history)*37+i+epoch)%active;
            next[i]=dwi::mutate_op(ops.data(),i,stages[size_t(sample)],epoch,seed,cfg);
        }
        for(u32 t=0;t<active;++t){
            Cell& c=cells[size_t((cursor+t)%cells.size())];const Stage& s=stages[t];
            std::copy(s.r,s.r+16,c.r.begin());std::copy(s.g,s.g+16,c.g.begin());c.aux=s.aux;
        }
        ops=next;masks=build_masks(ops,lut);
        cursor=(cursor+active)%cells.size();visited+=active;++epoch;return stages;
    }
};
void same_field(const Field& a,const Field& b){
    require(a.epoch==b.epoch&&a.cursor==b.cursor&&a.visited==b.visited,"entire control state");
    require(a.cells.size()==b.cells.size(),"cell count");
    require(std::memcmp(a.cells.data(),b.cells.data(),a.cells.size()*sizeof(Cell))==0,"every RG8 token and auxiliary word");
    require(std::memcmp(a.ops.data(),b.ops.data(),sizeof(Operators))==0,"every executable operator byte");
    require(a.masks==b.masks,"all regenerated masks");
}
}
int main(){try{
    MathLut lut{};init_math_lut(lut);
    test("config bounds and literal source seed", [&]{
        Config c;require(valid_config(c),"default integer configuration");
        c.dt_q16=0;require(!valid_config(c),"zero dt rejected");c.dt_q16=65537;require(!valid_config(c),"oversize dt rejected");
        c.dt_q16=65536;c.inverse_gain_q16=65536;require(valid_config(c),"largest supported scales");
        c.inverse_gain_q16=65537;require(!valid_config(c),"gain bound");
        for(u64 seed:{u64(0),u64(756),~u64(0)}){
            u8 r[16],g[16];Aux a{};dwi::seed_block(0,seed,r,g,a);
            for(u32 k=0;k<16;++k){require(r[k]==0,"wavefront first amplitude is zero");require(g[k]==complex_token(lut,Complex{4096,0}),"wavefront second amplitude quantizes two");}
            require(a.history==0&&a.inverse_t==0,"zero B and identity inverse T");
        }
        for(u64 i=1;i<1000;++i){u8 r[16],g[16];Aux a{};dwi::seed_block(i,756,r,g,a);
            for(u32 k=0;k<16;++k){Complex x=decode(lut,r[k]),y=decode(lut,g[k]);require(x.x==-y.x&&x.y==-y.y,"other cells seed exact antipodes");}
            require(a.inverse_t==0,"other cells identity inverse");
        }
        Operators ops=seed_operators();
        const u32 index[]={7,8,9,10,11,12},shape[]={1,2,0,3,4,5};
        for(u32 k=0;k<6;++k)require(((ops[index[k]].support>>16)%6)==shape[k],"named geometric primitive seed");
        for(u32 i=0;i<OP_COUNT;++i){
            Op legacy=dw::seed_op(i);
            require(std::memcmp(ops[i].code,legacy.code,sizeof(ops[i].code))==0,"seed program integer data retained");
            require((ops[i].location>>16)==u32((u64(i)*GOLD_Q16)%65536),"Fibonacci phase spacing");
        }
    });
    test("all LP8 mask decisions match signed supports under random operator data",[&]{
        for(u32 sample=0;sample<32;++sample){
            Operators ops=sample?random_operators(sample):seed_operators();Masks masks=build_masks(ops,lut);
            MemoryOps access{ops.data(),masks.data()};
            for(u32 i=0;i<15;++i)for(u32 q=0;q<256;++q)
                require(access.predicate(i,u8(q))==u32(support_sdf(lut,ops[i],token_chart(u8(q)))>=0),"complete packed mask domain");
            for(u32 q=0;q<256;++q)for(u32 j=0;j<2;++j)for(u32 h:{0u,1u,0xffffffffu,mix(sample+q)}){
                u32 direct=route<false>(access,lut,u8(q),j,h),cached=route<true>(access,lut,u8(q),j,h);
                require(direct==cached,"route leaf equality");
                require(direct>=15&&direct<31,"route valid leaf");
            }
        }
    });
    test("all stage bytes match direct and masked recurrence including extremes",[&]{
        for(u32 sample=0;sample<24;++sample){
            Operators ops=sample?random_operators(sample+400):seed_operators();Masks masks=build_masks(ops,lut);MemoryOps access{ops.data(),masks.data()};
            for(u32 q=0;q<256;++q){
                u8 r[16],g[16];for(u32 k=0;k<16;++k){r[k]=u8(k?q+mix(sample+k):q);g[k]=u8(mix(sample+q+k));}
                Aux a{mix(q+sample),mix(q+sample+1)};Config cfg;
                cfg.dt_q16=(q%3==0?1:(q%3==1?1024:65536));cfg.inverse_gain_q16=q&1?65536:0;cfg.jitter=(q>>1)&1;
                u8 nr=u8(mix(q+1)),ng=u8(mix(q+2));u64 epoch=(u64(sample)<<32)|q,index=(u64(q)<<32)|sample;
                Stage direct=evolve<false>(r,g,a,nr,ng,access,lut,epoch,index,756,cfg);
                Stage cached=evolve<true>(r,g,a,nr,ng,access,lut,epoch,index,756,cfg);
                require(same_stage(direct,cached),"complete 64-byte Stage equivalence");
                require((direct.feedback>>16&255)>=15&&(direct.feedback>>16&255)<31,"stored routed leaf");
                require(direct.quant_error==dw::quant_error(direct.bc5,direct.r,direct.g),"BC5 optional audit exact accounting");
            }
        }
    });
    test("modular inverse T cancels the recorded phase increment",[&]{
        Operators ops=seed_operators();
        // Neutralize programs so inverse words do not also affect the register
        // program: this isolates the promised modular phase operation.
        for(Op& op:ops)for(u32 k=0;k<BODY_WORDS;++k)op.code[k]=ins(0,7,7,7);
        Masks masks=build_masks(ops,lut);MemoryOps access{ops.data(),masks.data()};
        for(u32 q=0;q<256;++q){
            u8 r[16],g[16];std::fill(r,r+16,u8(q));std::fill(g,g+16,u8(q^8));
            Config cfg;cfg.inverse_gain_q16=65536;cfg.jitter=0;Aux zero{0,0};
            Stage base=evolve<true>(r,g,zero,13,47,access,lut,3,q,756,cfg);
            Aux previous_inverse{0,base.aux.inverse_t};
            Stage canceled=evolve<true>(r,g,previous_inverse,13,47,access,lut,3,q,756,cfg);
            require(canceled.aux.inverse_t==0,"previous inverse cancels same prescribed modular increment");
            Aux arbitrary{0,mix(q+900)};
            Stage shifted=evolve<true>(r,g,arbitrary,13,47,access,lut,3,q,756,cfg);
            require(u16(shifted.aux.inverse_t+arbitrary.inverse_t)==u16(base.aux.inverse_t),"red inverse composition");
            require(u16((shifted.aux.inverse_t>>16)+(arbitrary.inverse_t>>16))==u16(base.aux.inverse_t>>16),"green inverse composition");
        }
    });
    test("RK4 constant flow and event appears only at the fourth input",[&]{
        for(i32 dt:{1,1024,65536}){
            V2 q{12345,23456},drive{4096,-8192};V2 next=rk4(lut,q,drive,0,dt);
            require(next.x==q.x+mul_q16(dt,drive.x)&&next.y==q.y+mul_q16(dt,drive.y),"constant derivative integral");
        }
        TraceLut actual{lut,{}},expected{lut,{}};V2 q{12345,65535};
        V2 out=rk4(actual,q,{0,0},0,1024);
        // With zero derivative, every RK coordinate must stay at q. Only the
        // source's prescribed fourth input may read phase q.y+2, including wrap.
        for(u32 i=0;i<3;++i){sin_q15(expected,q.y);cos_q15(expected,q.x);}
        sin_q15(expected,i64(q.y)+2);cos_q15(expected,q.x);
        require(actual.reads==expected.reads,"lookup trace has fourth-slot plus-two Y event only");
        require(out.x==q.x&&out.y==q.y,"zero-coupling event does not invent movement");
    });
    test("operator freezing and precise executable one-bit mutation",[&]{
        Operators ops=seed_operators();Stage s{};s.feedback=0x015a33af;s.aux={0x99123311,0x11229988};
        Config cfg;cfg.mutate=0;
        for(u32 i=0;i<OP_COUNT;++i)require(same_op(mutate_op(ops.data(),i,s,19,756,cfg),ops[i]),"frozen entire 64-byte record");
        cfg.mutate=1;u32 changed_code=0,changed_position=0;
        for(u32 epoch=0;epoch<32;++epoch)for(u32 i=0;i<OP_COUNT;++i){
            Op next=mutate_op(ops.data(),i,s,epoch,756,cfg);u32 bits=0;
            for(u32 k=0;k<BODY_WORDS;++k)bits+=bit_count(next.code[k]^ops[i].code[k]);
            require(bits==jit(epoch,i,756),"exactly one executable bit iff jitter is one");
            require(next.history==s.aux.history&&next.inverse_t==s.aux.inverse_t&&next.last_rg==s.feedback,"feedback written into operator state");
            changed_code+=bits;changed_position+=next.location!=ops[i].location;
        }
        require(changed_code&&changed_position,"executables and positions actually change");
        cfg.jitter=0;
        for(u32 i=0;i<OP_COUNT;++i){Op next=mutate_op(ops.data(),i,s,19,756,cfg);
            require(std::memcmp(next.code,ops[i].code,sizeof(next.code))==0,"disabled jitter preserves executable words");
            require(next.location!=ops[i].location,"disabled jitter still advances specified continuous chart dynamics");
        }
    });
    test("CPU RG8 circulation keeps every state byte equal across routing paths",[&]{
        for(u32 active:{1u,17u,48u}){
            Field direct(active),cached(active);
            for(u32 step=0;step<48;++step){
                auto a=direct.step<false>(),b=cached.step<true>();require(a.size()==b.size(),"stage count");
                for(size_t i=0;i<a.size();++i)require(same_stage(a[i],b[i]),"every multistep stage byte");
                same_field(direct,cached);
            }
            require(direct.visited==u64(active)*48&&direct.cursor==0,"full sweep and page seam wrap");
        }
        Field baseline(17);for(u32 i=0;i<13;++i)baseline.step<true>();
        Field resumed=baseline;
        for(u32 i=0;i<25;++i){baseline.step<true>();resumed.step<false>();same_field(baseline,resumed);}
    });
    test("frozen field and recurrence dependency ablations",[&]{
        Field frozen(48);frozen.cfg.mutate=0;Operators saved=frozen.ops;
        for(u32 i=0;i<24;++i)frozen.step<true>();
        require(std::memcmp(saved.data(),frozen.ops.data(),sizeof(saved))==0,"frozen field preserves all operator bytes");
        Field baseline(48),no_jitter=baseline,no_hops=baseline,no_links=baseline;
        no_jitter.cfg.jitter=0;no_hops.cfg.hops=0;for(Op& o:no_links.ops)o.links=0;
        for(u32 i=0;i<16;++i){baseline.step<true>();no_jitter.step<true>();no_hops.step<true>();no_links.step<true>();}
        auto differs=[&](const Field& other){return std::memcmp(baseline.cells.data(),other.cells.data(),baseline.cells.size()*sizeof(Cell))!=0;};
        require(differs(no_jitter),"jitter changes circulating state");
        require(differs(no_hops),"VRAM neighbour references change state");
        require(differs(no_links),"operator references change state");
    });
    std::cout<<"SUMMARY "<<cases<<" cases, "<<checks<<" assertions, 0 failures\n";return 0;
}catch(const std::exception& e){std::cerr<<"FAIL "<<e.what()<<" after "<<cases<<" cases / "<<checks<<" assertions\n";return 1;}}

