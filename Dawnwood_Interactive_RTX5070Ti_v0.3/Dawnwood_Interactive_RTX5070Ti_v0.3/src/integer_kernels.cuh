#pragma once
#include <cuda_runtime.h>
#include "dawnwood/integer_core.hpp"
#ifndef DWI_DIRECT_TEXTURE
#define DWI_DIRECT_TEXTURE 0
#endif
#ifndef DWI_MASKED
#define DWI_MASKED 1
#endif
#ifndef DWI_PAIR_CACHE
#define DWI_PAIR_CACHE 0
#endif
namespace dwi {
struct Page {cudaTextureObject_t texture;cudaSurfaceObject_t surface;Aux* aux;};
struct alignas(16) Control {
    u64 epoch=0,cursor=0,total_blocks=0,visited=0,quant_error=0,seed=756;
    u32 active=0,pages=0,side=0,exact=0;Config cfg{};
};
struct Hot {cudaTextureObject_t ops[2],lut,masks[2];Op* bank[2];u32* mask_bank[2];cudaTextureObject_t pairs=0;};
struct TexturePairCache {
    cudaTextureObject_t texture;
    __device__ PairEntry pair(u32 i)const{uint2 p=tex1Dfetch<uint2>(texture,int(i));return {i32(p.x),u16(p.y),u16(p.y>>16)};}
};
__global__ void verify_pair_cache(Hot hot,u32* errors){
    u32 i=blockIdx.x*blockDim.x+threadIdx.x;if(i>=65536)return;
    TexturePairCache cache{hot.pairs};
    // LP words use integer texture reads, matching the recurrence's data path.
    u32 rw=tex1Dfetch<unsigned>(hot.lut,int(i&255)),gw=tex1Dfetch<unsigned>(hot.lut,int(i>>8));
    Hadamard h=hadamard({signed16(rw),signed16(rw>>16)},{signed16(gw),signed16(gw>>16)});
    PairChart a=direct_pair_chart(h.plus),b=direct_pair_chart(h.minus);
    PairChart pa=pair_plus_chart(cache,u8(i),u8(i>>8)),pb=pair_minus_chart(cache,u8(i),u8(i>>8));
    if(a.u!=pa.u||a.phase!=pa.phase||b.u!=pb.u||b.phase!=pb.phase)atomicAdd(errors,1u);
}
struct TextureMathLut {
    cudaTextureObject_t texture;
    __device__ u32 lp_word(u32 i)const{return tex1Dfetch<unsigned>(texture,int(i&255));}
    __device__ u32 sin_word(u32 i)const{return (tex1Dfetch<unsigned>(texture,int(256+(i>>1)))>>(16*(i&1)))&65535;}
};
struct TextureOps {
    cudaTextureObject_t texture,masks;
    __device__ Op op(u32 i)const{
        uint4 a=tex1Dfetch<uint4>(texture,int(4*i)),b=tex1Dfetch<uint4>(texture,int(4*i+1));
        uint4 d=tex1Dfetch<uint4>(texture,int(4*i+2)),e=tex1Dfetch<uint4>(texture,int(4*i+3));
        Op o{};o.location=a.x;o.support=a.y;o.links=a.z;o.coeff=a.w;
        o.code[0]=b.x;o.code[1]=b.y;o.code[2]=b.z;o.code[3]=b.w;
        o.code[4]=d.x;o.code[5]=d.y;o.code[6]=d.z;o.code[7]=d.w;
        o.last_rg=e.x;o.history=e.y;o.inverse_t=e.z;o.route=e.w;return o;
    }
    __device__ u32 predicate(u32 i,u8 q)const{return (tex1Dfetch<unsigned>(masks,int(i*8+(q>>5)))>>(q&31))&1;}
};
// Native CUDA texture ABI takes float coordinates. Build x+1/2 exactly with
// integer IEEE754 bit assembly. Supported texture dimensions keep exponent<=17.
__device__ inline float texel_center(u32 x){u32 n=2*x+1,e=31-__clz(n);return __uint_as_float(((e+126)<<23)|((n<<(23-e))&0x7fffff));}
// Native BC5 returns UNORM floats. Bitcast, then round v*255 using integers.
// No floating arithmetic or numeric conversions occur at this boundary.
__device__ inline u8 unorm8_bits(u32 bits){
    u32 e=(bits>>23)&255;if(!e)return 0;u64 n=u64((bits&0x7fffff)|0x800000)*255;
    u32 shift=150-e;if(shift>=64)return 0;return u8((n+(u64(1)<<(shift-1)))>>shift);
}
DW_HD inline u64 mod_u64(u64 n,u32 d){u64 r=0;for(int bit=63;bit>=0;--bit){r=(r<<1)|((n>>bit)&1);if(r>=d)r-=d;}return r;}
__device__ inline u64 window_index(const Control& c,u64 t) {
#if DW_REFERENCE_KERNEL
    return (c.cursor+t)%c.total_blocks;
#else
    // Construction and snapshot validation enforce cursor<total, active<=total.
    u64 index=c.cursor+t;return index>=c.total_blocks?index-c.total_blocks:index;
#endif
}
struct BlockAddress {u32 page,block,x,y;};
__device__ inline BlockAddress block_address(u64 index,u32 side){
    u32 width=side>>2,shift=__ffs(width)-1;u64 per=u64(width)*width;u32 block=u32(index&(per-1));
    return {u32(index>>(2*shift)),block,block&(width-1),block>>shift};
}
__device__ inline u32 page_coordinate(u32 value,u32 side){return value&(side-1);}
__device__ inline void read_pair(const Page& p,u32 x,u32 y,u32 exact,u8& r,u8& g) {
    if(exact){uint2 v=tex2D<uint2>(p.texture,texel_center(x),texel_center(y));r=u8(v.x);g=u8(v.y);}
    else {float4 v=tex2D<float4>(p.texture,texel_center(x),texel_center(y));r=unorm8_bits(__float_as_uint(v.x));g=unorm8_bits(__float_as_uint(v.y));}
}
__device__ inline void write_block(const Page& p,u32 bx,u32 by,u32 exact,const Stage& s) {
    if(exact){
        for(u32 k=0;k<16;++k){uchar2 v=make_uchar2(s.r[k],s.g[k]);surf2Dwrite(v,p.surface,int((4*bx+(k&3))*sizeof(uchar2)),int(4*by+k/4));}
    }else{uint4 v=make_uint4(s.bc5.x,s.bc5.y,s.bc5.z,s.bc5.w);surf2Dwrite(v,p.surface,int(bx*sizeof(uint4)),int(by));}
}
__global__ void initialize_page(Page p,u32 page,u32 side,u32 exact,u64 seed,u64 start,u64 count) {
    u64 b=start+u64(blockIdx.x)*blockDim.x+threadIdx.x;if(b>=start+count)return;
    u32 bw=side/4;Stage s{};dwi::seed_block(u64(page)*bw*bw+b,seed,s.r,s.g,s.aux);s.bc5=encode_bc5(s.r,s.g);
    write_block(p,u32(b&(bw-1)),u32(b>>(__ffs(bw)-1)),exact,s);p.aux[b]=s.aux;
}

__global__ void rebuild_masks(Hot hot,u32 bank){
    u32 word=blockIdx.x*blockDim.x+threadIdx.x;if(word>=MASK_WORDS)return;
    TextureMathLut lut{hot.lut};Op o=hot.bank[bank][word>>3];u32 value=0;
    for(u32 bit=0;bit<32;++bit){u8 token=u8((word&7)*32+bit);value|=u32(support_nonnegative_fast(lut,o,token_chart(token)))<<bit;}
    hot.mask_bank[bank][word]=value;
}
__global__ void rebuild_next_masks(Control* c,Hot hot){
    u32 word=threadIdx.x;if(word>=MASK_WORDS)return;u32 bank=u32(c->epoch&1)^1;
    TextureMathLut lut{hot.lut};Op o=hot.bank[bank][word>>3];u32 value=0;
    for(u32 bit=0;bit<32;++bit){u8 token=u8((word&7)*32+bit);value|=u32(support_nonnegative_fast(lut,o,token_chart(token)))<<bit;}
    hot.mask_bank[bank][word]=value;
}
__global__ void evolve_window(const Page* pages,Control* control,Hot hot,Stage* staged){
    u32 bank=u32(control->epoch&1);
#if DWI_DIRECT_TEXTURE
    TextureOps ops{hot.ops[bank],hot.masks[bank]};TextureMathLut lut{hot.lut};
#else
    __shared__ Op records[OP_COUNT];__shared__ MathLut math;__shared__ u32 masks[MASK_WORDS];
    TextureOps source{hot.ops[bank],hot.masks[bank]};TextureMathLut source_math{hot.lut};
    for(u32 i=threadIdx.x;i<OP_COUNT;i+=THREADS)records[i]=source.op(i);
    for(u32 i=threadIdx.x;i<256;i+=THREADS)math.lp[i]=source_math.lp_word(i);
    for(u32 i=threadIdx.x;i<257;i+=THREADS)math.sin_quarter[i]=u16(source_math.sin_word(i));
    for(u32 i=threadIdx.x;i<MASK_WORDS;i+=THREADS)masks[i]=tex1Dfetch<unsigned>(hot.masks[bank],int(i));
    __syncthreads();MemoryOps ops{records,masks};const MathLut& lut=math;
#endif
    u64 t=u64(blockIdx.x)*blockDim.x+threadIdx.x;if(t>=control->active)return;
    Control c=*control;u64 global=window_index(c,t);BlockAddress address=block_address(global,c.side);
    u32 pn=address.page,b=address.block,bx=address.x,by=address.y;Page p=pages[pn];
    u8 r[16],g[16];for(u32 k=0;k<16;++k)read_pair(p,4*bx+(k&3),4*by+k/4,c.exact,r[k],g[k]);
    Aux a=p.aux[b];u32 j=c.cfg.jitter?jit(c.epoch,global,c.seed):0;u8 nr=r[0],ng=g[0];
    u32 target=pn,h=mix(a.history^u32(global)^u32(c.epoch));
    for(u32 hop=0;hop<c.cfg.hops;++hop){u32 direction=j^parity(u32(nr)|(u32(ng)<<8))^((h>>(hop&31))&1);
        target=direction?(target?target-1:c.pages-1):(target+1==c.pages?0:target+1);
        h+=0x61c88647u;u32 x=page_coordinate(h,c.side),y=page_coordinate(mix(h),c.side);read_pair(pages[target],x,y,c.exact,nr,ng);}
#if DWI_PAIR_CACHE
    staged[t]=dwi::evolve<DWI_MASKED!=0>(r,g,a,nr,ng,ops,lut,c.epoch,global,c.seed,c.cfg,TexturePairCache{hot.pairs});
#else
    staged[t]=dwi::evolve<DWI_MASKED!=0>(r,g,a,nr,ng,ops,lut,c.epoch,global,c.seed,c.cfg);
#endif
    if(c.exact)staged[t].quant_error=0;
}
__global__ void commit_window(const Page* pages,Control* c,const Stage* staged) {
#if DW_REFERENCE_KERNEL
    __shared__ unsigned long long errors[THREADS];
    u64 t=u64(blockIdx.x)*blockDim.x+threadIdx.x;u64 e=0;
#else
    __shared__ u32 errors[THREADS/32];
    u64 t=u64(blockIdx.x)*blockDim.x+threadIdx.x;u32 e=0;
#endif
    if(t<c->active){u64 global=window_index(*c,t);BlockAddress a=block_address(global,c->side);
        Page p=pages[a.page];Stage s=staged[t];
        write_block(p,a.x,a.y,c->exact,s);p.aux[a.block]=s.aux;e=s.quant_error;}
#if DW_REFERENCE_KERNEL
    errors[threadIdx.x]=e;__syncthreads();
    for(u32 n=blockDim.x/2;n;n>>=1){if(threadIdx.x<n)errors[threadIdx.x]+=errors[threadIdx.x+n];__syncthreads();}
    if(threadIdx.x==0)atomicAdd(reinterpret_cast<unsigned long long*>(&c->quant_error),errors[0]);
#else
    // Each block contributes at most 128*32*255, so the local sum fits uint32.
    // All 128 lanes participate, including those outside a partial active window.
    u32 lane=threadIdx.x&31,warp=threadIdx.x>>5;
    for(u32 n=16;n;n>>=1)e+=__shfl_down_sync(0xffffffffu,e,n);
    if(lane==0)errors[warp]=e;__syncthreads();
    if(warp==0){e=lane<THREADS/32?errors[lane]:0;
        for(u32 n=16;n;n>>=1)e+=__shfl_down_sync(0xffffffffu,e,n);
        if(lane==0)atomicAdd(reinterpret_cast<unsigned long long*>(&c->quant_error),static_cast<unsigned long long>(e));}
#endif
}
__global__ void mutate_operators(Control* c,Hot hot,const Stage* staged) {
    u32 i=threadIdx.x+blockIdx.x*blockDim.x;if(i>=OP_COUNT)return;
    u32 bank=u32(c->epoch&1);const Op* old=hot.bank[bank];
    // The old body and its current location choose which field result rewrites it.
    u64 sample=mod_u64(u64(old[i].location)+u64(old[i].history)*37+i+c->epoch,c->active);
    hot.bank[bank^1][i]=dwi::mutate_op(old,i,staged[sample],c->epoch,c->seed,c->cfg);
}
__global__ void advance_interval(Control* c) {
    if(threadIdx.x==0&&blockIdx.x==0){c->cursor=window_index(*c,c->active);c->visited+=c->active;++c->epoch;}
}
__global__ void sample_pixels(Page p,u32 exact,u32 /*side*/,u8* result) {
    u32 i=threadIdx.x;if(i<16){u8 r,g;read_pair(p,i&3,i/4,exact,r,g);result[2*i]=r;result[2*i+1]=g;}
}
} // namespace dwi
