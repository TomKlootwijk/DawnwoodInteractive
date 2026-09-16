#pragma once
#include "dawnwood/core.hpp"
#include <array>
#include <vector>
#include <algorithm>
#include <stdexcept>
namespace dw {
struct Cell {std::array<u8,16> r{},g{};Aux aux{};};
class CPUField {
public:
    u32 pages,side,active;bool exact;u64 epoch=0,cursor=0,visited=0,error=0,seed;Config cfg;
    std::array<Op,OP_COUNT> ops{};std::array<V4,256> lut{};std::vector<Cell> cells;
    CPUField(u32 p=3,u32 s=16,u32 a=7,bool raw=false,u64 sd=756,Config c={}):pages(p),side(s),active(a),exact(raw),seed(sd),cfg(c){
        if(!p||s<4||s%4||!a)throw std::runtime_error("Invalid CPU field dimensions");
        cells.resize(size_t(p)*(s/4)*(s/4));active=u32(std::min(u64(a),u64(cells.size())));
        for(u32 i=0;i<OP_COUNT;++i)ops[i]=seed_op(i);
        for(u32 i=0;i<256;++i)lut[i]=lut_entry(i);
        for(size_t i=0;i<cells.size();++i){auto& x=cells[i];seed_block(i,seed,x.r.data(),x.g.data(),x.aux);if(!exact){auto b=encode_bc5(x.r.data(),x.g.data());decode_bc5(b,x.r.data(),x.g.data());}}
    }
    void pair(u32 page,u32 x,u32 y,u8& r,u8& g) const {
        u32 bw=side/4;auto& cell=cells[size_t(page)*bw*bw+(y/4)*bw+x/4];u32 k=(y&3)*4+(x&3);r=cell.r[k];g=cell.g[k];
    }
    void step(){
        std::vector<Stage> stage(active);u64 bpp=u64(side/4)*(side/4);
        for(u32 t=0;t<active;++t){u64 idx=(cursor+t)%cells.size();auto& x=cells[idx];u32 pn=u32(idx/bpp);u8 nr=x.r[0],ng=x.g[0];
            u32 j=cfg.jitter?jit(epoch,idx,seed):0,h=mix(x.aux.history^u32(idx)^u32(epoch));
            for(u32 hop=0;hop<cfg.hops;++hop){u32 direction=j^parity(u32(nr)|(u32(ng)<<8))^((h>>(hop%32))&1);
                pn=direction?(pn+pages-1)%pages:(pn+1)%pages;h+=0x61c88647u;pair(pn,h%side,mix(h)%side,nr,ng);}
            stage[t]=evolve(x.r.data(),x.g.data(),x.aux,nr,ng,ops.data(),lut.data(),epoch,idx,seed,cfg);if(exact)stage[t].quant_error=0;
        }
        for(u32 t=0;t<active;++t){auto& x=cells[(cursor+t)%cells.size()];auto& s=stage[t];x.aux=s.aux;
            if(exact){std::copy(s.r,s.r+16,x.r.begin());std::copy(s.g,s.g+16,x.g.begin());}else decode_bc5(s.bc5,x.r.data(),x.g.data());error+=s.quant_error;}
        auto next=ops;for(u32 i=0;i<OP_COUNT;++i){u64 sample=(u64(ops[i].location)+u64(ops[i].history)*37+i+epoch)%active;next[i]=mutate_op(ops.data(),i,stage[sample],epoch,seed,cfg);}ops=next;
        cursor=(cursor+active)%cells.size();visited+=active;++epoch;
    }
    u64 digest()const{
        u64 h=14695981039346656037ull;auto byte=[&](u8 b){h^=b;h*=1099511628211ull;};
        for(auto& x:cells){for(u8 b:x.r)byte(b);for(u8 b:x.g)byte(b);for(u32 v:{x.aux.history,x.aux.inverse_t})for(u32 k=0;k<4;++k)byte(u8(v>>(8*k)));}
        for(auto& x:ops){const u8* b=reinterpret_cast<const u8*>(&x);for(size_t k=0;k<sizeof(x);++k)byte(b[k]);}return h;
    }
};
}
