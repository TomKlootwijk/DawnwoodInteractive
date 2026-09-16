// Dawnwood Interactive | Tom Klootwijk | NL200678942 | 10-07-1990
#include "kernels.cuh"
#include <algorithm>
#include <array>
#include <chrono>
#include <csignal>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
namespace fs=std::filesystem;
using namespace dw;
static void ck(cudaError_t e,const char* expression,const char* file,int line){
    if(e!=cudaSuccess){std::ostringstream s;s<<file<<":"<<line<<" "<<expression<<": "<<cudaGetErrorString(e);throw std::runtime_error(s.str());}
}
#define CUDA(call) ck((call),#call,__FILE__,__LINE__)
static volatile std::sig_atomic_t stop_requested=0;
static void on_signal(int){stop_requested=1;}
struct Options {
    int device=0;u32 side=4096,active=65536,pages=0,batch=8;u64 steps=256,seed=756,reserve=512ull<<20;
    double fill=.96;bool exact=false,probe=false,self_test=false,use_graph=true,persist=true;
    std::string cache_policy=DW_REFERENCE_KERNEL?"l1":"balanced";
    std::string report="run_report.json",operators,snapshot,resume;Config cfg{};
};
static std::string usage(){return R"(Dawnwood Interactive v0.3 - Tom Klootwijk - NL200678942 - 10-07-1990
Usage: dawnwood [options]
  --probe                    Query the device and memory; do not fill VRAM
  --self-test                Run actual CUDA texture / VM / recurrence checks
  --device N                 CUDA ordinal (default 0)
  --codec bc5|rg8             BC5 packed dichromatic field / exact token storage
  --fill F                   Fraction of currently free VRAM (default 0.96)
  --reserve-mib N             Leave at least N MiB free (default 512; 0 allowed)
  --pages N                  Exact page count instead of automatic capacity fill
  --page-side N              Physical texture side, multiple of 4 (default 4096)
  --blocks-per-step N         Number of 16-texel blocks evolved per Psi (65536)
  --steps N                  Psi intervals; 0 runs until Ctrl+C (default 256)
  --batch N                  Intervals between completion checks (default 8)
  --dt X                     RK4/Psi interval (default 0.015625)
  --hops N                   Data-directed texture-chain reads per block (2)
  --seed N                   Reproducible one-bit jitter seed (756)
  --freeze-operators         Hold operator bodies/positions fixed for comparison
  --no-jitter                Set the one-bit perturbation to zero
  --inverse-gain X            Contribution of the previous inverse-T (0.25)
  --operators FILE           Load a 31-record/1984-byte initial operator image
  --report FILE              JSON run report, without full field readback
  --snapshot FILE            Save the complete field after the run (large file)
  --resume FILE              Continue a complete v0.3 field snapshot
  --no-graph                 Launch the same four kernels without a CUDA Graph
  --cache-policy l1|balanced|shared  Cache preference (optimized: balanced; reference: l1)
  --no-l2-persist            Disable the hot-table L2 persistence preference
  --help                     This help
No renderer, ray traversal, managed-memory oversubscription or CPU texture paging.
)";}
static u64 number(const std::string& x){size_t n=0;if(x.empty()||x[0]=='-')throw std::runtime_error("Expected an unsigned integer: "+x);u64 v=std::stoull(x,&n,0);if(n!=x.size())throw std::runtime_error("Invalid integer: "+x);return v;}
static u32 word(const std::string& x){u64 v=number(x);if(v>std::numeric_limits<u32>::max())throw std::runtime_error("Value exceeds uint32: "+x);return u32(v);}
static double real(const std::string& x){size_t n=0;double v=std::stod(x,&n);if(n!=x.size()||!std::isfinite(v))throw std::runtime_error("Invalid finite number: "+x);return v;}
static Options parse(int argc,char** argv){
    Options o;
    for(int i=1;i<argc;++i){std::string a=argv[i];auto val=[&](){if(++i>=argc)throw std::runtime_error("Missing value for "+a);return std::string(argv[i]);};
        if(a=="--help"){std::cout<<usage();std::exit(0);}else if(a=="--probe")o.probe=true;else if(a=="--self-test")o.self_test=true;
        else if(a=="--device"){u32 d=word(val());if(d>u32(std::numeric_limits<int>::max()))throw std::runtime_error("Invalid device ordinal");o.device=int(d);}
        else if(a=="--codec"){std::string c=val();if(c!="bc5"&&c!="rg8")throw std::runtime_error("codec must be bc5 or rg8");o.exact=c=="rg8";}
        else if(a=="--fill")o.fill=real(val());else if(a=="--reserve-mib"){u64 v=number(val());if(v>(std::numeric_limits<u64>::max()>>20))throw std::runtime_error("reserve overflow");o.reserve=v<<20;}
        else if(a=="--pages")o.pages=word(val());else if(a=="--page-side")o.side=word(val());else if(a=="--blocks-per-step")o.active=word(val());
        else if(a=="--steps")o.steps=number(val());else if(a=="--batch")o.batch=word(val());else if(a=="--seed")o.seed=number(val());
        else if(a=="--dt")o.cfg.dt=float(real(val()));else if(a=="--hops")o.cfg.hops=word(val());else if(a=="--inverse-gain")o.cfg.inverse_gain=float(real(val()));
        else if(a=="--freeze-operators")o.cfg.mutate=0;else if(a=="--no-jitter")o.cfg.jitter=0;
        else if(a=="--operators")o.operators=val();else if(a=="--report")o.report=val();else if(a=="--snapshot")o.snapshot=val();else if(a=="--resume")o.resume=val();
        else if(a=="--no-graph")o.use_graph=false;else if(a=="--no-l2-persist")o.persist=false;
        else if(a=="--cache-policy"){o.cache_policy=val();if(o.cache_policy!="l1"&&o.cache_policy!="balanced"&&o.cache_policy!="shared")throw std::runtime_error("Invalid cache policy");}
        else throw std::runtime_error("Unknown option: "+a);
    }
    if(o.fill<=0||o.fill>1||!o.active||!o.batch||o.side<4||o.side%4||!std::isfinite(o.cfg.dt)||o.cfg.dt<=0||!std::isfinite(o.cfg.inverse_gain))throw std::runtime_error("Invalid size, fill, batch or interval");
    // A float chart uses floor-based reduction. Check arithmetic representability,
    // not a source-level spatial radius or execution-count restriction.
    if(double(o.cfg.dt)*(1.+std::abs(double(o.cfg.inverse_gain)))>1e12)throw std::runtime_error("Parameters exceed this float32 chart binding");
    return o;
}
static std::string json_string(const std::string& s){std::ostringstream o;o<<'"';for(unsigned char c:s){if(c=='"'||c=='\\')o<<'\\'<<char(c);else if(c<32)o<<"\\u"<<std::hex<<std::setw(4)<<std::setfill('0')<<int(c)<<std::dec;else o<<char(c);}o<<'"';return o.str();}
struct Stream {cudaStream_t p{};Stream(){CUDA(cudaStreamCreate(&p));}~Stream(){if(p)cudaStreamDestroy(p);}};
struct Event {cudaEvent_t p{};Event(){CUDA(cudaEventCreate(&p));}~Event(){if(p)cudaEventDestroy(p);}};
struct DeviceBuffer {
    void* p=nullptr;size_t bytes=0;
    DeviceBuffer()=default;explicit DeviceBuffer(size_t n){allocate(n);}~DeviceBuffer(){if(p)cudaFree(p);}
    DeviceBuffer(const DeviceBuffer&)=delete;DeviceBuffer& operator=(const DeviceBuffer&)=delete;
    void allocate(size_t n){if(p)throw std::runtime_error("Buffer already allocated");CUDA(cudaMalloc(&p,n));bytes=n;}
    template<class T>T* as()const{return static_cast<T*>(p);}
};
struct PageOwner {
    cudaArray_t array{};Page device{};u32 side=0;bool exact=false;
    PageOwner()=default;PageOwner(const PageOwner&)=delete;PageOwner& operator=(const PageOwner&)=delete;
    ~PageOwner(){if(device.texture)cudaDestroyTextureObject(device.texture);if(device.surface)cudaDestroySurfaceObject(device.surface);if(device.aux)cudaFree(device.aux);if(array)cudaFreeArray(array);}
    // OOM is returned only for capacity selection; unsupported texture formats remain errors.
    bool allocate(u32 n,bool raw){
        side=n;exact=raw;cudaChannelFormatDesc ch=raw?cudaCreateChannelDesc<uchar2>():cudaCreateChannelDesc<uint4>();
        cudaError_t e=cudaMallocArray(&array,&ch,raw?n:n/4,raw?n:n/4,cudaArraySurfaceLoadStore);
        if(e==cudaErrorMemoryAllocation){cudaGetLastError();return false;}CUDA(e);
        e=cudaMalloc(reinterpret_cast<void**>(&device.aux),size_t(n/4)*(n/4)*sizeof(Aux));
        if(e==cudaErrorMemoryAllocation){cudaGetLastError();return false;}CUDA(e);
        cudaResourceDesc r{};r.resType=cudaResourceTypeArray;r.res.array.array=array;
        cudaTextureDesc t{};t.addressMode[0]=cudaAddressModeClamp;t.addressMode[1]=cudaAddressModeClamp;
        // BC5's view already returns UNORM floats; the uint4 backing cannot request
        // integer normalization. RG8 does require explicit 8-bit normalization.
        t.filterMode=cudaFilterModePoint;t.readMode=raw?cudaReadModeNormalizedFloat:cudaReadModeElementType;t.normalizedCoords=0;
        cudaResourceViewDesc view{};view.format=cudaResViewFormatUnsignedBlockCompressed5;view.width=n;view.height=n;view.depth=0;
        CUDA(cudaCreateTextureObject(&device.texture,&r,&t,raw?nullptr:&view));CUDA(cudaCreateSurfaceObject(&device.surface,&r));return true;
    }
    size_t row_bytes()const{return exact?size_t(side)*2:size_t(side/4)*16;}
    size_t rows()const{return exact?side:side/4;}
};
struct HotOwner {
    DeviceBuffer arena;Hot hot{};size_t bank_stride=0;
    static size_t aligned(size_t n,size_t alignment){return ((n+alignment-1)/alignment)*alignment;}
    HotOwner(const cudaDeviceProp& prop,const std::array<Op,OP_COUNT>& ops){
        size_t align=std::max(size_t(prop.textureAlignment),size_t(16));bank_stride=aligned(sizeof(Op)*OP_COUNT,align);
        size_t table_at=2*bank_stride,pairs_at=table_at+sizeof(V4)*256;
        arena.allocate(pairs_at+(DW_REFERENCE_KERNEL?0:sizeof(V4)*65536));
        for(u32 b=0;b<2;++b){hot.bank[b]=reinterpret_cast<Op*>(static_cast<char*>(arena.p)+b*bank_stride);CUDA(cudaMemcpy(hot.bank[b],ops.data(),sizeof(Op)*OP_COUNT,cudaMemcpyHostToDevice));
            cudaResourceDesc r{};r.resType=cudaResourceTypeLinear;r.res.linear.devPtr=hot.bank[b];r.res.linear.sizeInBytes=sizeof(Op)*OP_COUNT;r.res.linear.desc=cudaCreateChannelDesc<uint4>();
            cudaTextureDesc t{};t.readMode=cudaReadModeElementType;CUDA(cudaCreateTextureObject(&hot.ops[b],&r,&t,nullptr));}
        std::array<V4,256> lut{};for(u32 i=0;i<256;++i)lut[i]=lut_entry(i);
        void* lp=static_cast<char*>(arena.p)+table_at;CUDA(cudaMemcpy(lp,lut.data(),sizeof(lut),cudaMemcpyHostToDevice));
        cudaResourceDesc r{};r.resType=cudaResourceTypeLinear;r.res.linear.devPtr=lp;r.res.linear.sizeInBytes=sizeof(lut);r.res.linear.desc=cudaCreateChannelDesc<float4>();
        cudaTextureDesc t{};t.readMode=cudaReadModeElementType;CUDA(cudaCreateTextureObject(&hot.lut,&r,&t,nullptr));
#if !DW_REFERENCE_KERNEL
        hot.pairs=reinterpret_cast<V4*>(static_cast<char*>(arena.p)+pairs_at);
        initialize_pairs<<<256,256>>>(hot);CUDA(cudaGetLastError());CUDA(cudaDeviceSynchronize());
#endif
    }
    ~HotOwner(){for(auto h:hot.ops)if(h)cudaDestroyTextureObject(h);if(hot.lut)cudaDestroyTextureObject(hot.lut);}
};
struct GraphOwner {cudaGraph_t graph{};cudaGraphExec_t exec{};~GraphOwner(){if(exec)cudaGraphExecDestroy(exec);if(graph)cudaGraphDestroy(graph);}};
static std::array<Op,OP_COUNT> initial_ops(const std::string& file){
    std::array<Op,OP_COUNT> out{};for(u32 i=0;i<OP_COUNT;++i)out[i]=seed_op(i);
    if(!file.empty()){std::ifstream f(file,std::ios::binary);if(!f)throw std::runtime_error("Cannot open operator image "+file);
        f.read(reinterpret_cast<char*>(out.data()),sizeof(out));if(!f||f.peek()!=std::char_traits<char>::eof())throw std::runtime_error("Operator image must be exactly 1984 bytes");}
    return out;
}
static void submit(Page* pages,Control* c,Hot h,Stage* s,u32 active,cudaStream_t stream){
    u32 grid=u32((u64(active)+THREADS-1)/THREADS);
    evolve_window<<<grid,THREADS,0,stream>>>(pages,c,h,s);CUDA(cudaGetLastError());
    commit_window<<<grid,THREADS,0,stream>>>(pages,c,s);CUDA(cudaGetLastError());
    mutate_operators<<<1,32,0,stream>>>(c,h,s);CUDA(cudaGetLastError());
    advance_interval<<<1,1,0,stream>>>(c);CUDA(cudaGetLastError());
}
static void check(bool okay,const char* text){if(!okay)throw std::runtime_error(std::string("GPU self-test: ")+text);std::cout<<"PASS "<<text<<"\n";}
static void self_test(const cudaDeviceProp& prop){
    Stream stream;DeviceBuffer bits(128*sizeof(u32)),pixels(32);std::array<u32,128> actual{};
    primitive_checks<<<1,64,0,stream.p>>>(bits.as<u32>());CUDA(cudaGetLastError());CUDA(cudaStreamSynchronize(stream.p));CUDA(cudaMemcpy(actual.data(),bits.p,bits.bytes,cudaMemcpyDeviceToHost));
    bool okay=true;for(u32 i=0;i<64;++i){u16 r[8];for(u32 j=0;j<8;++j)r[j]=u16(mix(i*8+j));Op o=seed_op(i%OP_COUNT);o.code[0]=ins(i&15,0,1,2,34567);execute(o,r);
        okay=okay&&(actual[2*i]==(u32(r[0])|(u32(r[3])<<16)))&&(actual[2*i+1]==(mix(i)^parity(i)));}
    check(okay,"64 CPU/GPU packed-instruction cases");
    auto ops=initial_ops("");HotOwner hot(prop,ops);std::array<V4,256> lut{};for(u32 i=0;i<256;++i)lut[i]=lut_entry(i);
    if(hot.hot.pairs){u32 failures=0;CUDA(cudaMemset(bits.p,0,sizeof(u32)));
        pair_cache_checks<<<256,256,0,stream.p>>>(hot.hot,bits.as<u32>());CUDA(cudaGetLastError());CUDA(cudaStreamSynchronize(stream.p));
        CUDA(cudaMemcpy(&failures,bits.p,sizeof(u32),cudaMemcpyDeviceToHost));check(failures==0,"all 65536 GPU pair-cache entries at four chart offsets");}
    for(u32 raw=0;raw<=1;++raw){
        PageOwner p;check(p.allocate(4,raw!=0),raw?"allocate exact RG8 texture":"allocate native BC5 texture view");
        DeviceBuffer table(sizeof(Page)),control(sizeof(Control)),staging(sizeof(Stage));CUDA(cudaMemcpy(table.p,&p.device,sizeof(Page),cudaMemcpyHostToDevice));
        initialize_page<<<1,THREADS,0,stream.p>>>(p.device,0,4,raw,756,0,1);CUDA(cudaGetLastError());CUDA(cudaStreamSynchronize(stream.p));
        sample_pixels<<<1,32,0,stream.p>>>(p.device,raw,4,pixels.as<u8>());CUDA(cudaGetLastError());CUDA(cudaStreamSynchronize(stream.p));
        u8 sampled[32],r[16],g[16];Aux a{};seed_block(0,756,r,g,a);if(!raw){BC5 b=encode_bc5(r,g);decode_bc5(b,r,g);}
        CUDA(cudaMemcpy(sampled,pixels.p,32,cudaMemcpyDeviceToHost));bool equal=true;
        for(u32 k=0;k<16;++k){int er=std::abs(int(sampled[2*k])-int(r[k])),eg=std::abs(int(sampled[2*k+1])-int(g[k]));equal=equal&&er<=int(!raw)&&eg<=int(!raw);}
        check(equal,raw?"RG8 texture tokens are exact":"BC5 hardware decoding agrees within one UNORM8 unit");
        Control c{};c.side=4;c.pages=1;c.active=1;c.total_blocks=1;c.exact=raw;c.cfg.hops=0;CUDA(cudaMemcpy(control.p,&c,sizeof(c),cudaMemcpyHostToDevice));
        // Reset the hot banks for each storage mode.
        for(u32 b=0;b<2;++b)CUDA(cudaMemcpy(hot.hot.bank[b],ops.data(),sizeof(ops),cudaMemcpyHostToDevice));
        u8 rr[16],gg[16];for(u32 k=0;k<16;++k){rr[k]=sampled[2*k];gg[k]=sampled[2*k+1];}
        Stage expected=evolve(rr,gg,a,rr[0],gg[0],ops.data(),lut.data(),0,0,756,c.cfg);
        submit(table.as<Page>(),control.as<Control>(),hot.hot,staging.as<Stage>(),1,stream.p);CUDA(cudaStreamSynchronize(stream.p));
        Stage got{};CUDA(cudaMemcpy(&got,staging.p,sizeof(got),cudaMemcpyDeviceToHost));
        check(std::memcmp(got.r,expected.r,32)==0,"one-interval CPU/GPU token recurrence");
        sample_pixels<<<1,32,0,stream.p>>>(p.device,raw,4,pixels.as<u8>());CUDA(cudaGetLastError());CUDA(cudaStreamSynchronize(stream.p));CUDA(cudaMemcpy(sampled,pixels.p,32,cudaMemcpyDeviceToHost));
        std::memcpy(r,got.r,16);std::memcpy(g,got.g,16);if(!raw)decode_bc5(got.bc5,r,g);equal=true;
        for(u32 k=0;k<16;++k)equal=equal&&(std::abs(int(sampled[2*k])-int(r[k]))<=int(!raw))&&(std::abs(int(sampled[2*k+1])-int(g[k]))<=int(!raw));
        check(equal,"commit then texture-read observes the new field");
        std::array<Op,OP_COUNT> changed{};CUDA(cudaMemcpy(changed.data(),hot.hot.bank[1],sizeof(changed),cudaMemcpyDeviceToHost));
        check(std::memcmp(changed.data(),ops.data(),sizeof(ops))!=0,"operator records evolve on device");
        bool code_changed=false;for(u32 i=0;i<OP_COUNT;++i)code_changed=code_changed||std::memcmp(changed[i].code,ops[i].code,sizeof(ops[i].code));check(code_changed,"executable body words mutate, not just a dispatch index");
        CUDA(cudaMemcpy(&c,control.p,sizeof(c),cudaMemcpyDeviceToHost));check(c.epoch==1&&c.visited==1&&c.cursor==0,"device-owned Psi and cursor advance");
    }
    std::cout<<"GPU self-test complete.\n";
}
// Complete snapshots contain data only, never CUDA handles or pointers.
struct SnapshotHeader {u64 magic;u32 version,side,pages,exact;u64 control_bytes,op_bytes;};
static constexpr u64 SNAP_MAGIC=0x3358545257445744ull;
static SnapshotHeader read_header(std::ifstream& f){SnapshotHeader h{};f.read(reinterpret_cast<char*>(&h),sizeof(h));
    if(!f||h.magic!=SNAP_MAGIC||h.version!=3||h.control_bytes!=sizeof(Control)||h.op_bytes!=sizeof(Op)*OP_COUNT||h.side<4||h.side%4||!h.pages||h.exact>1)throw std::runtime_error("Invalid or incompatible Dawnwood v0.3 snapshot");
    return h;
}
static void transfer_snapshot(const std::string& path,bool save,std::vector<std::unique_ptr<PageOwner>>& pages,HotOwner& hot,Control* control){
    if(save){
        fs::path target(path);if(!target.parent_path().empty())fs::create_directories(target.parent_path());std::string temp=path+".partial";
        if(fs::exists(target)||fs::exists(temp))throw std::runtime_error("Snapshot path already exists; choose a new file: "+path);
        std::ofstream f(temp,std::ios::binary);f.exceptions(std::ios::badbit|std::ios::failbit);
        SnapshotHeader h{SNAP_MAGIC,3,pages[0]->side,u32(pages.size()),u32(pages[0]->exact),sizeof(Control),sizeof(Op)*OP_COUNT};f.write(reinterpret_cast<const char*>(&h),sizeof(h));
        Control c{};CUDA(cudaMemcpy(&c,control,sizeof(c),cudaMemcpyDeviceToHost));
        // Canonicalize alignment padding for reproducible snapshot hashes.
        constexpr size_t tail=offsetof(Control,cfg)+sizeof(Config);
        std::memset(reinterpret_cast<char*>(&c)+tail,0,sizeof(Control)-tail);
        f.write(reinterpret_cast<const char*>(&c),sizeof(c));
        std::array<Op,OP_COUNT> o{};for(u32 b=0;b<2;++b){CUDA(cudaMemcpy(o.data(),hot.hot.bank[b],sizeof(o),cudaMemcpyDeviceToHost));f.write(reinterpret_cast<const char*>(o.data()),sizeof(o));}
        for(auto& p:pages){std::vector<char> data(p->row_bytes()*p->rows());CUDA(cudaMemcpy2DFromArray(data.data(),p->row_bytes(),p->array,0,0,p->row_bytes(),p->rows(),cudaMemcpyDeviceToHost));f.write(data.data(),data.size());
            data.resize(size_t(p->side/4)*(p->side/4)*sizeof(Aux));CUDA(cudaMemcpy(data.data(),p->device.aux,data.size(),cudaMemcpyDeviceToHost));f.write(data.data(),data.size());}
        f.close();fs::rename(temp,target);
    }else{
        std::ifstream f(path,std::ios::binary);if(!f)throw std::runtime_error("Cannot open snapshot "+path);SnapshotHeader h=read_header(f);f.exceptions(std::ios::badbit|std::ios::failbit);
        if(h.pages!=pages.size()||h.side!=pages[0]->side||bool(h.exact)!=pages[0]->exact)throw std::runtime_error("Snapshot allocation mismatch");
        Control c{};f.read(reinterpret_cast<char*>(&c),sizeof(c));u64 total=u64(h.pages)*(h.side/4)*(h.side/4);
        if(c.total_blocks!=total||c.pages!=h.pages||c.side!=h.side||c.exact!=h.exact||!c.active||c.active>total||c.cursor>=total||!std::isfinite(c.cfg.dt)||c.cfg.dt<=0||!std::isfinite(c.cfg.inverse_gain))throw std::runtime_error("Invalid snapshot control state");
        CUDA(cudaMemcpy(control,&c,sizeof(c),cudaMemcpyHostToDevice));std::array<Op,OP_COUNT> o{};for(u32 b=0;b<2;++b){f.read(reinterpret_cast<char*>(o.data()),sizeof(o));CUDA(cudaMemcpy(hot.hot.bank[b],o.data(),sizeof(o),cudaMemcpyHostToDevice));}
        for(auto& p:pages){std::vector<char> data(p->row_bytes()*p->rows());f.read(data.data(),data.size());CUDA(cudaMemcpy2DToArray(p->array,0,0,data.data(),p->row_bytes(),p->row_bytes(),p->rows(),cudaMemcpyHostToDevice));
            data.resize(size_t(p->side/4)*(p->side/4)*sizeof(Aux));f.read(data.data(),data.size());CUDA(cudaMemcpy(p->device.aux,data.data(),data.size(),cudaMemcpyHostToDevice));}
        f.exceptions(std::ios::badbit);if(f.peek()!=std::char_traits<char>::eof())throw std::runtime_error("Trailing bytes in snapshot");
    }
}
static u64 digest(const Op* ops){u64 h=14695981039346656037ull;auto b=reinterpret_cast<const u8*>(ops);for(size_t i=0;i<sizeof(Op)*OP_COUNT;++i){h^=b[i];h*=1099511628211ull;}return h;}
int main(int argc,char** argv){try{
    Options o=parse(argc,argv);std::cout<<"Dawnwood Interactive | Tom Klootwijk | NL200678942 | 10-07-1990\n";
    CUDA(cudaSetDevice(o.device));CUDA(cudaFree(nullptr));cudaDeviceProp prop{};CUDA(cudaGetDeviceProperties(&prop,o.device));
    size_t free0=0,total0=0;CUDA(cudaMemGetInfo(&free0,&total0));int runtime=0,driver=0;CUDA(cudaRuntimeGetVersion(&runtime));CUDA(cudaDriverGetVersion(&driver));
    std::cout<<prop.name<<" | compute "<<prop.major<<'.'<<prop.minor<<" | "<<total0<<" bytes total | "<<free0<<" free\n"
        <<"L2 "<<prop.l2CacheSize<<" | L2 persisting maximum "<<prop.persistingL2CacheMaxSize<<" | shared/block "<<prop.sharedMemPerBlock<<" | SMs "<<prop.multiProcessorCount<<"\n";
    if(o.probe){std::cout<<"CUDA runtime "<<runtime<<" / driver "<<driver<<"; texture alignment "<<prop.textureAlignment<<"; max2D "<<prop.maxTexture2D[0]<<'x'<<prop.maxTexture2D[1]<<"\n";return 0;}
    if(o.self_test){self_test(prop);return 0;}
    if(!o.resume.empty()){
        std::ifstream f(o.resume,std::ios::binary);if(!f)throw std::runtime_error("Cannot read snapshot");auto h=read_header(f);Control c{};f.read(reinterpret_cast<char*>(&c),sizeof(c));
        if(!f||!c.active)throw std::runtime_error("Truncated snapshot control");
        o.pages=h.pages;o.side=h.side;o.exact=h.exact!=0;o.active=c.active;o.cfg=c.cfg;o.seed=c.seed;
        std::cout<<"Resume uses stored field, operators, seed, dt and window size. --steps adds new intervals.\n";
    }
    if(o.side>u32(prop.maxTexture2D[0])||o.side>u32(prop.maxTexture2D[1])||o.side>u32(prop.maxSurface2D[0])||o.side>u32(prop.maxSurface2D[1]))throw std::runtime_error("Page exceeds reported texture/surface dimensions");
    Stream stream;auto initial=initial_ops(o.operators);HotOwner hot(prop,initial);DeviceBuffer control(sizeof(Control)),staging(size_t(o.active)*sizeof(Stage));
    CUDA(cudaFuncSetCacheConfig(evolve_window,o.cache_policy=="l1"?cudaFuncCachePreferL1:(o.cache_policy=="shared"?cudaFuncCachePreferShared:cudaFuncCachePreferEqual)));
    // Load/query kernels before measuring the payload budget (especially CUDA lazy loading).
    cudaFuncAttributes attr{};CUDA(cudaFuncGetAttributes(&attr,evolve_window));CUDA(cudaFuncGetAttributes(&attr,commit_window));CUDA(cudaFuncGetAttributes(&attr,mutate_operators));CUDA(cudaFuncGetAttributes(&attr,advance_interval));CUDA(cudaFuncGetAttributes(&attr,initialize_page));
    CUDA(cudaFuncGetAttributes(&attr,evolve_window));int resident_blocks=0;
    CUDA(cudaOccupancyMaxActiveBlocksPerMultiprocessor(&resident_blocks,evolve_window,THREADS,0));
    bool l2=false;size_t l2_bytes=0;
    if(o.persist&&prop.persistingL2CacheMaxSize>0&&prop.accessPolicyMaxWindowSize>=hot.arena.bytes){
        l2_bytes=std::min(hot.arena.bytes,size_t(prop.persistingL2CacheMaxSize));cudaError_t e=cudaDeviceSetLimit(cudaLimitPersistingL2CacheSize,l2_bytes);
        if(e==cudaSuccess){cudaStreamAttrValue a{};a.accessPolicyWindow.base_ptr=hot.arena.p;a.accessPolicyWindow.num_bytes=hot.arena.bytes;
            a.accessPolicyWindow.hitRatio=float(double(l2_bytes)/hot.arena.bytes);a.accessPolicyWindow.hitProp=cudaAccessPropertyPersisting;a.accessPolicyWindow.missProp=cudaAccessPropertyNormal;
            e=cudaStreamSetAttribute(stream.p,cudaStreamAttributeAccessPolicyWindow,&a);l2=e==cudaSuccess;}
        if(e!=cudaSuccess){std::cout<<"L2 preference not enabled: "<<cudaGetErrorString(e)<<"\n";cudaGetLastError();}
    }
    size_t payload_free=0,tt=0;CUDA(cudaMemGetInfo(&payload_free,&tt));u64 per=page_bytes(o.side,o.exact),budget=budget_bytes(payload_free,o.reserve,o.fill);
    u64 desired=o.pages?o.pages:budget/(per+sizeof(Page));
    if(!desired)throw std::runtime_error("No complete page fits the requested budget");
    if(desired>std::numeric_limits<u32>::max()||desired*(per+sizeof(Page))>budget)throw std::runtime_error("Requested pages exceed the selected free-memory budget; change reserve/fill/pages");
    DeviceBuffer table(size_t(desired)*sizeof(Page));std::vector<std::unique_ptr<PageOwner>> pages;pages.reserve(size_t(desired));
    for(u32 i=0;i<desired;++i){size_t now=0;CUDA(cudaMemGetInfo(&now,&tt));
        if(now<o.reserve||u64(now)-o.reserve<per){if(o.pages)throw std::runtime_error("Available memory changed while allocating explicit pages");break;}
        auto p=std::make_unique<PageOwner>();if(!p->allocate(o.side,o.exact)){if(o.pages)throw std::runtime_error("Explicit page allocation ran out of device memory");break;}
        if(o.resume.empty()){u64 count=u64(o.side/4)*(o.side/4);for(u64 first=0;first<count;first+=o.active){u64 n=std::min(u64(o.active),count-first);
            initialize_page<<<u32((n+THREADS-1)/THREADS),THREADS,0,stream.p>>>(p->device,i,o.side,o.exact,o.seed,first,n);CUDA(cudaGetLastError());}
            CUDA(cudaStreamSynchronize(stream.p));}
        pages.push_back(std::move(p));if((i+1)%16==0)std::cout<<"Packed "<<(i+1)<<" pages / "<<(u64(i+1)*per/(1ull<<20))<<" MiB\n";
    }
    if(pages.empty())throw std::runtime_error("No payload page allocated");
    // Array padding is measured through cudaMemGetInfo, not asserted to equal payload bytes.
    std::vector<Page> handles;for(auto& p:pages)handles.push_back(p->device);CUDA(cudaMemcpy(table.p,handles.data(),handles.size()*sizeof(Page),cudaMemcpyHostToDevice));
    Control c{};c.pages=u32(pages.size());c.side=o.side;c.exact=o.exact;c.total_blocks=u64(c.pages)*(o.side/4)*(o.side/4);c.active=u32(std::min(u64(o.active),c.total_blocks));c.seed=o.seed;c.cfg=o.cfg;
    CUDA(cudaMemcpy(control.p,&c,sizeof(c),cudaMemcpyHostToDevice));
    if(!o.resume.empty()){transfer_snapshot(o.resume,false,pages,hot,control.as<Control>());CUDA(cudaMemcpy(&c,control.p,sizeof(c),cudaMemcpyDeviceToHost));}
    size_t packed_free=0;CUDA(cudaMemGetInfo(&packed_free,&tt));
    std::cout<<"Field: "<<c.pages<<" pages | "<<c.total_blocks*16<<" dichromatic token pairs | "<<u64(c.pages)*per<<" payload bytes | free "<<packed_free<<"\n"
        <<"Hot shared per CTA: "<<(sizeof(Op)*OP_COUNT+sizeof(V4)*256)<<" bytes; L2 preference "<<(l2?"enabled":"unavailable/not enabled")<<"\n";
    GraphOwner graph;
    if(o.use_graph){CUDA(cudaStreamBeginCapture(stream.p,cudaStreamCaptureModeGlobal));submit(table.as<Page>(),control.as<Control>(),hot.hot,staging.as<Stage>(),c.active,stream.p);
        CUDA(cudaStreamEndCapture(stream.p,&graph.graph));
        // Explicit per-node policy survives graph replay independently of stream capture.
        if(l2){size_t n=0;CUDA(cudaGraphGetNodes(graph.graph,nullptr,&n));std::vector<cudaGraphNode_t> nodes(n);CUDA(cudaGraphGetNodes(graph.graph,nodes.data(),&n));
            for(auto node:nodes){cudaGraphNodeType type{};CUDA(cudaGraphNodeGetType(node,&type));if(type==cudaGraphNodeTypeKernel){cudaKernelNodeAttrValue a{};
                a.accessPolicyWindow.base_ptr=hot.arena.p;a.accessPolicyWindow.num_bytes=hot.arena.bytes;a.accessPolicyWindow.hitRatio=float(double(l2_bytes)/hot.arena.bytes);
                a.accessPolicyWindow.hitProp=cudaAccessPropertyPersisting;a.accessPolicyWindow.missProp=cudaAccessPropertyNormal;
                CUDA(cudaGraphKernelNodeSetAttribute(node,cudaKernelNodeAttributeAccessPolicyWindow,&a));}}}
        CUDA(cudaGraphInstantiate(&graph.exec,graph.graph,nullptr,nullptr,0));}
    Event start,end;CUDA(cudaEventRecord(start.p,stream.p));std::signal(SIGINT,on_signal);std::signal(SIGTERM,on_signal);
    u64 completed=0,start_epoch=c.epoch,start_visited=c.visited,start_error=c.quant_error;auto wall0=std::chrono::steady_clock::now();
    while(!stop_requested&&(o.steps==0||completed<o.steps)){
        u64 count=o.steps?std::min(u64(o.batch),o.steps-completed):o.batch;
        for(u64 i=0;i<count;++i){if(o.use_graph)CUDA(cudaGraphLaunch(graph.exec,stream.p));else submit(table.as<Page>(),control.as<Control>(),hot.hot,staging.as<Stage>(),c.active,stream.p);}
        CUDA(cudaStreamSynchronize(stream.p));completed+=count;
    }
    CUDA(cudaEventRecord(end.p,stream.p));CUDA(cudaEventSynchronize(end.p));float elapsed=0;CUDA(cudaEventElapsedTime(&elapsed,start.p,end.p));
    double wall=std::chrono::duration<double>(std::chrono::steady_clock::now()-wall0).count();CUDA(cudaMemcpy(&c,control.p,sizeof(c),cudaMemcpyDeviceToHost));
    std::array<Op,OP_COUNT> final_ops{};CUDA(cudaMemcpy(final_ops.data(),hot.hot.bank[c.epoch&1],sizeof(final_ops),cudaMemcpyDeviceToHost));
    size_t final_free=0;CUDA(cudaMemGetInfo(&final_free,&tt));u64 visited=c.visited-start_visited;
    if(!o.snapshot.empty()){std::cout<<"Writing full snapshot; this explicit export transfers the field to disk.\n";transfer_snapshot(o.snapshot,true,pages,hot,control.as<Control>());}
    fs::path report(o.report);if(!report.parent_path().empty())fs::create_directories(report.parent_path());std::ofstream f(report);if(!f)throw std::runtime_error("Cannot write report "+o.report);
    f<<std::setprecision(12)<<"{\n  \"project\": \"Dawnwood Interactive\",\n  \"version\": \"0.3\",\n  \"author\": {\"name\": \"Tom Klootwijk\", \"identifier\": \"NL200678942\", \"date_of_birth\": \"10-07-1990\"},\n"
     <<"  \"device\": "<<json_string(prop.name)<<",\n  \"compute_capability\": "<<json_string(std::to_string(prop.major)+"."+std::to_string(prop.minor))<<",\n"
     <<"  \"cuda_runtime\": "<<runtime<<",\n  \"cuda_driver\": "<<driver<<",\n  \"codec\": \""<<(o.exact?"rg8":"bc5")<<"\",\n"
     <<"  \"total_device_bytes\": "<<total0<<",\n  \"free_at_start\": "<<free0<<",\n  \"free_at_payload_planning\": "<<payload_free<<",\n"
     <<"  \"free_after_packing\": "<<packed_free<<",\n  \"free_at_end\": "<<final_free<<",\n  \"payload_bytes\": "<<u64(c.pages)*per<<",\n"
     <<"  \"pages\": "<<c.pages<<",\n  \"page_side\": "<<c.side<<",\n  \"token_pairs\": "<<c.total_blocks*16<<",\n  \"blocks_per_interval\": "<<c.active<<",\n"
     <<"  \"shared_hot_bytes_per_block\": "<<sizeof(Op)*OP_COUNT+sizeof(V4)*256<<",\n  \"l2_preference_enabled\": "<<(l2?"true":"false")<<",\n"
     <<"  \"start_epoch\": "<<start_epoch<<",\n  \"end_epoch\": "<<c.epoch<<",\n  \"visited_blocks_this_run\": "<<visited<<",\n"
     <<"  \"complete_sweeps_this_run\": "<<visited/c.total_blocks<<",\n  \"total_complete_sweeps\": "<<c.visited/c.total_blocks<<",\n"
     <<"  \"cuda_event_ms_including_launch_gaps\": "<<elapsed<<",\n  \"wall_seconds\": "<<wall<<",\n"
     <<"  \"token_pair_updates_per_second\": "<<(wall>0?double(visited)*16/wall:0)<<",\n"
     <<"  \"software_codec_mean_absolute_token_error\": "<<(visited?double(c.quant_error-start_error)/(double(visited)*32):0)<<",\n"
     <<"  \"operator_digest_fnv1a64\": \""<<std::hex<<digest(final_ops.data())<<std::dec<<"\",\n"
     <<"  \"scope\": \"Observed process allocation and updates; physical residency, cache hits and DRAM bandwidth require profiler measurements.\"";
    // Keep the exact recurrence parameters alongside every measured result.
    f<<",\n  \"kernel_variant\": \""<<(DW_REFERENCE_KERNEL?"reference":"optimized")<<"\",\n"
     <<"  \"seed\": "<<c.seed<<",\n  \"dt\": "<<c.cfg.dt<<",\n  \"hops\": "<<c.cfg.hops<<",\n"
     <<"  \"jitter\": "<<c.cfg.jitter<<",\n  \"mutation\": "<<c.cfg.mutate<<",\n  \"inverse_gain\": "<<c.cfg.inverse_gain<<",\n"
     <<"  \"graph_enabled\": "<<(o.use_graph?"true":"false")<<",\n  \"batch\": "<<o.batch<<",\n"
     <<"  \"cache_policy\": "<<json_string(o.cache_policy)<<",\n  \"l2_cache_bytes\": "<<prop.l2CacheSize<<",\n"
     <<"  \"hot_arena_bytes\": "<<hot.arena.bytes<<",\n  \"pair_table_bytes\": "<<(DW_REFERENCE_KERNEL?0:sizeof(V4)*65536)<<",\n"
     <<"  \"l2_persistence_requested_bytes\": "<<l2_bytes<<",\n  \"staging_bytes\": "<<staging.bytes<<",\n"
     <<"  \"evolve_registers_per_thread\": "<<attr.numRegs<<",\n  \"evolve_local_bytes_per_thread\": "<<attr.localSizeBytes<<",\n"
     <<"  \"evolve_shared_bytes_per_block\": "<<attr.sharedSizeBytes<<",\n  \"theoretical_resident_blocks_per_sm\": "<<resident_blocks<<",\n"
     <<"  \"theoretical_occupancy\": "<<double(resident_blocks*THREADS)/prop.maxThreadsPerMultiProcessor<<",\n"
     <<"  \"payload_fraction_of_total_device\": "<<double(u64(c.pages)*per)/total0<<",\n"
     <<"  \"observed_allocation_delta_bytes\": "<<(free0>=packed_free?free0-packed_free:0)<<"\n}\n";
    f.close();if(!f)throw std::runtime_error("Failed to complete report");
    fs::path opfile=report;opfile.replace_extension("operators.bin");std::ofstream of(opfile,std::ios::binary);of.write(reinterpret_cast<const char*>(final_ops.data()),sizeof(final_ops));if(!of)throw std::runtime_error("Failed to write final operator image");
    if(l2){cudaStreamAttrValue a{};CUDA(cudaStreamSetAttribute(stream.p,cudaStreamAttributeAccessPolicyWindow,&a));CUDA(cudaCtxResetPersistingL2Cache());}
    std::cout<<"Completed "<<completed<<" Psi intervals, "<<visited<<" block updates; report "<<o.report<<"\n";return 0;
}catch(const std::exception& e){std::cerr<<"Dawnwood: "<<e.what()<<"\n";return 1;}}
