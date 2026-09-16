#pragma once
#include <cuda_runtime.h>
#include "dawnwood/core.hpp"
namespace dw {
struct Page { cudaTextureObject_t texture; cudaSurfaceObject_t surface; Aux* aux; };
struct alignas(16) Control {
    u64 epoch=0,cursor=0,total_blocks=0,visited=0,quant_error=0,seed=756;
    u32 active=0,pages=0,side=0,exact=0;
    Config cfg{};
};
struct Hot { cudaTextureObject_t ops[2],lut; Op* bank[2]; const V4* pairs=nullptr; };
__global__ void initialize_pairs(Hot hot) {
    u32 i=blockIdx.x*blockDim.x+threadIdx.x;if(i>=65536)return;
    float4 a=tex1Dfetch<float4>(hot.lut,int(i&255)),b=tex1Dfetch<float4>(hot.lut,int(i>>8));
    const_cast<V4*>(hot.pairs)[i]=pair_entry({a.x,a.y,a.z,a.w},{b.x,b.y,b.z,b.w});
}
// Self-test support: every LP8 pair, including zero and cancellation, is checked
// on the device that built the cache, at offsets straddling chart boundaries.
__global__ void pair_cache_checks(Hot hot,u32* failures) {
    u32 i=blockIdx.x*blockDim.x+threadIdx.x;if(i>=65536||!hot.pairs)return;
    float4 x=tex1Dfetch<float4>(hot.lut,int(i&255)),y=tex1Dfetch<float4>(hot.lut,int(i>>8));
    V4 p=hot.pairs[i];u32 errors=0;
    float hx=(x.x+y.x)*0.7071067811865475f,hy=(x.y+y.y)*0.7071067811865475f;
    float gx=(x.x-y.x)*0.7071067811865475f,gy=(x.y-y.y)*0.7071067811865475f;
    const float offsets[4]={0.f,1.f/65536.f,-1.01f,0.5f};
    for(u32 k=0;k<4;++k){float d=offsets[k];
        errors+=pair_token(p.x,p.y,d,-d)!=complex_token(hx,hy,d,-d);
        errors+=pair_token(p.z,p.w,-d,d)!=complex_token(gx,gy,-d,d);}
    if(errors)atomicAdd(failures,errors);
}
__device__ inline u64 window_index(const Control& c,u64 t) {
#if DW_REFERENCE_KERNEL
    return (c.cursor+t)%c.total_blocks;
#else
    // Construction and snapshot validation enforce cursor<total, active<=total.
    u64 index=c.cursor+t;return index>=c.total_blocks?index-c.total_blocks:index;
#endif
}
struct BlockAddress {u32 page,block,x,y;};
__device__ inline BlockAddress block_address(u64 index,u32 side) {
    u32 width=side/4;u64 per_page=u64(width)*width;
#if !DW_REFERENCE_KERNEL
    if((width&(width-1))==0){u32 shift=__ffs(width)-1;u32 block=u32(index&(per_page-1));
        return {u32(index>>(2*shift)),block,block&(width-1),block>>shift};}
#endif
    u32 block=u32(index%per_page);return {u32(index/per_page),block,block%width,block/width};
}
__device__ inline u32 page_coordinate(u32 value,u32 side) {
#if !DW_REFERENCE_KERNEL
    if((side&(side-1))==0)return value&(side-1);
#endif
    return value%side;
}
__device__ inline void read_pair(const Page& p,u32 x,u32 y,u32 exact,u8& r,u8& g) {
    if(exact){float2 v=tex2D<float2>(p.texture,float(x)+.5f,float(y)+.5f);r=u8(v.x*255.f+.5f);g=u8(v.y*255.f+.5f);}
    else {float4 v=tex2D<float4>(p.texture,float(x)+.5f,float(y)+.5f);r=u8(v.x*255.f+.5f);g=u8(v.y*255.f+.5f);}
}
__device__ inline void write_block(const Page& p,u32 bx,u32 by,u32 exact,const Stage& s) {
    if(exact){
        for(u32 k=0;k<16;++k){uchar2 v=make_uchar2(s.r[k],s.g[k]);surf2Dwrite(v,p.surface,int((4*bx+(k&3))*sizeof(uchar2)),int(4*by+k/4));}
    }else{uint4 v=make_uint4(s.bc5.x,s.bc5.y,s.bc5.z,s.bc5.w);surf2Dwrite(v,p.surface,int(bx*sizeof(uint4)),int(by));}
}
__global__ void initialize_page(Page p,u32 page,u32 side,u32 exact,u64 seed,u64 start,u64 count) {
    u64 b=start+u64(blockIdx.x)*blockDim.x+threadIdx.x;if(b>=start+count)return;
    u32 bw=side/4;Stage s{};seed_block(u64(page)*bw*bw+b,seed,s.r,s.g,s.aux);s.bc5=encode_bc5(s.r,s.g);
    write_block(p,u32(b%bw),u32(b/bw),exact,s);p.aux[b]=s.aux;
}
__global__ void evolve_window(const Page* pages,Control* control,Hot hot,Stage* staged) {
    __shared__ Op ops[OP_COUNT];__shared__ V4 lut[256];
    u32 bank=u32(control->epoch&1);
    // Cooperative software-managed residency: 1,984 B operators + 4,096 B LP LUT.
    for(u32 i=threadIdx.x;i<OP_COUNT;i+=blockDim.x){
        uint4 a=tex1Dfetch<uint4>(hot.ops[bank],int(4*i));
        uint4 b=tex1Dfetch<uint4>(hot.ops[bank],int(4*i+1));
        uint4 d=tex1Dfetch<uint4>(hot.ops[bank],int(4*i+2));
        uint4 e=tex1Dfetch<uint4>(hot.ops[bank],int(4*i+3));
        Op o{};o.location=a.x;o.support=a.y;o.links=a.z;o.coeff=a.w;
        o.code[0]=b.x;o.code[1]=b.y;o.code[2]=b.z;o.code[3]=b.w;
        o.code[4]=d.x;o.code[5]=d.y;o.code[6]=d.z;o.code[7]=d.w;
        o.last_rg=e.x;o.history=e.y;o.inverse_t=e.z;o.route=e.w;ops[i]=o;
    }
    for(u32 i=threadIdx.x;i<256;i+=blockDim.x){float4 v=tex1Dfetch<float4>(hot.lut,int(i));lut[i]={v.x,v.y,v.z,v.w};}
    __syncthreads();
    u64 t=u64(blockIdx.x)*blockDim.x+threadIdx.x;if(t>=control->active)return;
    Control c=*control;u64 global=window_index(c,t);BlockAddress address=block_address(global,c.side);
    u32 pn=address.page,b=address.block,bx=address.x,by=address.y;Page p=pages[pn];
    u8 r[16],g[16];for(u32 k=0;k<16;++k)read_pair(p,4*bx+(k&3),4*by+k/4,c.exact,r[k],g[k]);
    Aux a=p.aux[b];u32 j=c.cfg.jitter?jit(c.epoch,global,c.seed):0;u8 nr=r[0],ng=g[0];
    // Both chain directions are implicit. Payload selects the next hop, without host input.
    u32 target=pn;u32 h=mix(a.history^u32(global)^u32(c.epoch));
    for(u32 hop=0;hop<c.cfg.hops;++hop){u32 direction=j^parity(u32(nr)|(u32(ng)<<8))^((h>>(hop%32))&1);
#if DW_REFERENCE_KERNEL
        target=direction?(target+c.pages-1)%c.pages:(target+1)%c.pages;
#else
        target=direction?(target?target-1:c.pages-1):(target+1==c.pages?0:target+1);
#endif
        h+=0x61c88647u;u32 x=page_coordinate(h,c.side),y=page_coordinate(mix(h),c.side);read_pair(pages[target],x,y,c.exact,nr,ng);}
    staged[t]=evolve(r,g,a,nr,ng,ops,lut,c.epoch,global,c.seed,c.cfg,hot.pairs);
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
    u64 sample=(u64(old[i].location)+u64(old[i].history)*37+i+c->epoch)%c->active;
    hot.bank[bank^1][i]=mutate_op(old,i,staged[sample],c->epoch,c->seed,c->cfg);
}
__global__ void advance_interval(Control* c) {
    if(threadIdx.x==0&&blockIdx.x==0){c->cursor=window_index(*c,c->active);c->visited+=c->active;++c->epoch;}
}
__global__ void sample_pixels(Page p,u32 exact,u32 /*side*/,u8* result) {
    u32 i=threadIdx.x;if(i<16){u8 r,g;read_pair(p,i&3,i/4,exact,r,g);result[2*i]=r;result[2*i+1]=g;}
}
__global__ void primitive_checks(u32* out) {
    u32 i=threadIdx.x;if(i>=64)return;u16 r[8];for(u32 j=0;j<8;++j)r[j]=u16(mix(i*8+j));
    Op o=seed_op(i%OP_COUNT);o.code[0]=ins(i&15,0,1,2,34567);execute(o,r);
    out[2*i]=u32(r[0])|(u32(r[3])<<16);out[2*i+1]=mix(i)^parity(i);
}
} // namespace dw
