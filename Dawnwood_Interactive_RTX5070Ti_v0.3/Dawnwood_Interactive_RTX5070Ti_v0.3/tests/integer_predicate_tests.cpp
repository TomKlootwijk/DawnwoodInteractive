// CPU validation of the exact >=0 specialization used to rebuild routing masks.
// These checks do not replace tests of the full signed-distance magnitudes.
#include "dawnwood/integer_core.hpp"
#include <array>
#include <chrono>
#include <cstring>
#include <iostream>
#include <random>
#include <string>
using namespace dwi;

namespace {
struct Counts {u64 negative=0,zero=0,positive=0,mismatches=0;};
std::array<Counts,6> counts{};
u64 comparisons=0,mismatches=0,assertions=0;
std::mt19937_64 random_words(0x4457495052454431ULL);
MathLut lut{};

u32 random32(){return u32(random_words());}
Op random_op(u32 shape,u32 radius){
    Op op{};std::array<u32,16> words{};
    for(u32& word:words)word=random32();
    std::memcpy(&op,words.data(),sizeof(op));
    // Mutation can use every high support bit; all aliases modulo six count.
    u32 high=shape+6*(random32()/6%((65535-shape)/6+1));
    op.support=(radius-1)|(high<<16);return op;
}
Op located(u32 shape,u32 radius,Chart center){
    Op op=random_op(shape,radius);op.location=pack16(u32(center.u),u32(center.v));return op;
}
Chart offset(Chart center,i32 du,i32 dv){return fold(i64(center.u)+du,i64(center.v)+dv);}
void require(bool okay,const char* text){
    ++assertions;
    if(!okay){++mismatches;std::cerr<<"ASSERTION FAILURE "<<text<<"\n";}
}
i32 compare(const Op& op,Chart q,const char* group){
    i32 full=support_sdf(lut,op,q);bool fast=support_nonnegative_fast(lut,op,q);
    u32 shape=(op.support>>16)%6;++comparisons;
    Counts& c=counts[shape];if(full<0)++c.negative;else if(full==0)++c.zero;else ++c.positive;
    if(fast!=(full>=0)){
        ++c.mismatches;++mismatches;
        if(mismatches<=16){
            Chart center{i32(op.location&65535),i32(op.location>>16),0};V2 delta=chart_delta(q,center);
            std::cerr<<"MISMATCH group="<<group<<" comparison="<<comparisons<<" shape="<<shape
                <<" radius_q18="<<((op.support&65535)+1)<<" support_word="<<op.support
                <<" location_word="<<op.location<<" chart=("<<q.u<<','<<q.v<<','<<q.flip<<')'
                <<" local_q18=("<<4*delta.x<<','<<4*delta.y<<") full_sdf="<<full
                <<" expected_nonnegative="<<(full>=0)<<" fast_nonnegative="<<fast<<"\n";
        }
    }
    return full;
}
template<class FN>void group(const char* name,FN fn){
    u64 before=comparisons,errors=mismatches;fn();
    std::cout<<(mismatches==errors?"PASS ":"FAIL ")<<name<<": "<<(comparisons-before)
        <<" comparisons, "<<(mismatches-errors)<<" mismatches\n";
}
void stencil(const Op& op,Chart center,i32 du,i32 dv,const char* name){
    for(i32 x=-1;x<=1;++x)for(i32 y=-1;y<=1;++y)compare(op,offset(center,du+x,dv+y),name);
}
}

int main(){
    init_math_lut(lut);auto start=std::chrono::steady_clock::now();
    group("all 256 LP8 tokens for 384 mutated operators covering all six shapes",[]{
        const u32 extremes[]={1,2,3,4,5,7,8,9,65533,65534,65535,65536};
        for(u32 shape=0;shape<6;++shape)for(u32 sample=0;sample<64;++sample){
            u32 radius=sample<12?extremes[sample]:(random32()&65535)+1;
            Op op=random_op(shape,radius);
            for(u32 token=0;token<256;++token)compare(op,token_chart(u8(token)),"all_tokens");
        }
    });
    group("72000 independent canonical chart/operator/radius cases",[]{
        for(u32 shape=0;shape<6;++shape)for(u32 sample=0;sample<12000;++sample){
            u32 radius=sample<3?sample+1:(random32()&65535)+1;Op op=random_op(shape,radius);
            Chart q{i32(random32()&65535),i32(random32()&65535),random32()&1};compare(op,q,"random_chart");
        }
    });
    group("radii 1,2,3 on local lattice and quotient seams",[]{
        const Chart centers[]={{0,0,0},{0,65535,0},{65535,0,0},{65535,65535,0},
            {32768,32768,0},{1,32767,0},{65534,32768,0}};
        for(u32 shape=0;shape<6;++shape)for(u32 radius:{1u,2u,3u})for(Chart center:centers){
            Op op=located(shape,radius,center);
            for(i32 du=-3;du<=3;++du)for(i32 dv=-3;dv<=3;++dv)compare(op,offset(center,du,dv),"tiny_radius");
            Chart equivalent=fold(i64(center.u)+65536,-i64(center.v));
            compare(op,equivalent,"quotient_equivalent_center");
        }
    });
    group("circle axis and Pythagorean exact boundaries plus adjacent lattice",[]{
        Chart center{32768,32768,0};
        for(u32 radius:{4u,8u,12u,16u,32u,64u,256u,4096u,32768u,65536u}){
            Op op=located(0,radius,center);i32 d=i32(radius/4);
            require(compare(op,center,"circle_center")<0,"positive circle radius has strict negative center");
            for(i32 sign:{-1,1}){
                require(compare(op,offset(center,sign*d,0),"circle_axis_boundary")==0,"circle axis boundary is exactly zero");
                require(compare(op,offset(center,0,sign*d),"circle_axis_boundary")==0,"circle axis boundary is exactly zero");
                stencil(op,center,sign*d,0,"circle_axis_stencil");stencil(op,center,0,sign*d,"circle_axis_stencil");
            }
        }
        for(u32 scale:{4u,8u,16u,64u,256u,1024u,8192u}){
            Op op=located(0,5*scale,center);
            for(i32 sx:{-1,1})for(i32 sy:{-1,1}){
                i32 x=sx*i32(3*scale/4),y=sy*i32(scale);
                require(compare(op,offset(center,x,y),"circle_3_4_5_boundary")==0,"Pythagorean circle boundary is exactly zero");
                stencil(op,center,x,y,"circle_3_4_5_stencil");
            }
        }
    });
    group("T box boundary/overlap neighborhoods and small rounded widths",[]{
        Chart center{32768,32768,0};
        for(u32 radius:{1u,2u,3u,4u,5u,8u,12u,20u,40u,80u,160u,320u,1280u,40960u,65520u,65536u}){
            Op op=located(1,radius,center);i32 r=i32(radius),a=i32(round_div_const<5>(r));
            i32 stem=-i32(round_div_const<10>(i64(r)*3)),bar=i32(round_div_const<5>(i64(r)*3));
            // Divide only to select nearby chart lattice points; every stencil
            // still compares the actual full signed distance at that point.
            for(i32 sx:{-1,1}){
                stencil(op,center,sx*a/4,stem/4,"T_stem_sides");
                stencil(op,center,0,(stem+sx*r)/4,"T_stem_ends");
                stencil(op,center,sx*r/4,bar/4,"T_bar_ends");
                stencil(op,center,0,(bar+sx*a)/4,"T_bar_sides");
                stencil(op,center,sx*a/4,(bar-a)/4,"T_reentrant_corner");
            }
            compare(op,center,"T_center");
        }
    });
    group("triangle/cone vertices, base, side midpoints and strict interiors",[]{
        Chart center{32768,32768,0};
        for(u32 shape:{2u,3u})for(u32 radius:{32u,64u,128u,256u,1024u,4096u,16384u,32768u,65536u}){
            Op op=located(shape,radius,center);
            i32 r=shape==3?i32(round_div_const<4>(i64(radius)*3)):i32(radius),d=r/4;
            const V2 edges[]={{-d,-d},{d,-d},{0,d},{0,-d},{d/2,0},{-d/2,0}};
            require(compare(op,center,"triangle_interior")<0,"triangle center is strictly inside");
            for(V2 edge:edges){
                require(compare(op,offset(center,edge.x,edge.y),"triangle_exact_boundary")==0,"triangle edge point is exactly zero");
                stencil(op,center,edge.x,edge.y,"triangle_edge_stencil");
            }
            // A point on a line extending an edge beyond its endpoint is not
            // itself on the triangle; this catches cross==0 over-generalization.
            require(compare(op,offset(center,2*d,-d),"triangle_edge_extension")>0,"triangle edge extension is outside");
            stencil(op,center,2*d,-d,"triangle_extension_stencil");
        }
    });
    group("ambient Klein sphere near rounded radial thresholds",[]{
        // At u=0 and a one-unit v step the integer LUT cosine remains at
        // its extremum: the embedding changes along exactly one axis.
        // This constructs a real, representable boundary, not a tolerance.
        Chart boundary_center{0,0,0},boundary_point{0,1,0};
        V4 b0=klein(lut,boundary_center.u,boundary_center.v);
        V4 b1=klein(lut,boundary_point.u,boundary_point.v);
        i64 bx=i64(b1.x)-b0.x,by=i64(b1.y)-b0.y,bz=i64(b1.z)-b0.z,bw=i64(b1.w)-b0.w;
        u64 boundary_squared=u64(bx*bx+by*by+bz*bz+bw*bw);
        u32 boundary_radius=u32(sqrt_nearest(boundary_squared));
        require(boundary_radius>1&&boundary_radius<65536,"sphere exact boundary radius is representable with adjacent radii");
        require(boundary_squared==u64(boundary_radius)*boundary_radius,"sphere boundary has exact integer embedding distance");
        require(compare(located(4,boundary_radius,boundary_center),boundary_point,"sphere_exact_boundary")==0,"ambient sphere boundary is exactly zero");
        require(compare(located(4,boundary_radius-1,boundary_center),boundary_point,"sphere_radius_below_boundary")>0,"ambient sphere smaller radius is outside");
        require(compare(located(4,boundary_radius+1,boundary_center),boundary_point,"sphere_radius_above_boundary")<0,"ambient sphere larger radius is inside");
        const Chart centers[]={{0,0,0},{0,65535,0},{32768,32768,0},{65535,12345,0},{12345,54321,0}};
        for(Chart center:centers){
            for(u32 radius:{1u,2u,3u,16u,65536u}){
                Op op=located(4,radius,center);
                require(compare(op,center,"sphere_center")<0,"ambient sphere center is strictly negative");
            }
            V4 c=klein(lut,center.u,center.v);
            for(i32 du=-512;du<=512;du+=37)for(i32 dv=-128;dv<=128;dv+=31){
                Chart q=offset(center,du,dv);V4 p=klein(lut,q.u,q.v);
                i64 dx=i64(p.x)-c.x,dy=i64(p.y)-c.y,dz=i64(p.z)-c.z,dw_=i64(p.w)-c.w;
                i32 nearest=sqrt_nearest(u64(dx*dx+dy*dy+dz*dz+dw_*dw_));
                for(i32 dr=-1;dr<=1;++dr){i32 r=nearest+dr;if(r<1||r>65536)continue;
                    compare(located(4,u32(r),center),q,"sphere_rounded_threshold");}
            }
        }
    });
    group("apex remains nonnegative with zero at its center",[]{
        for(u32 sample=0;sample<128;++sample){
            Chart center{i32(random32()&65535),i32(random32()&65535),0};
            Op op=located(5,(random32()&65535)+1,center);
            require(compare(op,center,"apex_center")==0,"apex center is zero");
            for(i32 du:{-2,-1,0,1,2})for(i32 dv:{-2,-1,0,1,2})
                require(compare(op,offset(center,du,dv),"apex_local_lattice")>=0,"apex full distance is never negative");
        }
    });
    for(u32 shape=0;shape<6;++shape){
        const Counts& c=counts[shape];
        require(c.positive>0,"each shape exercised positive distance");
        require(c.zero>0,"each shape exercised exact boundary");
        require(shape==5?c.negative==0:c.negative>0,"interior coverage for five supports; apex has no negative interior");
        std::cout<<"SHAPE "<<shape<<" negative="<<c.negative<<" zero="<<c.zero<<" positive="<<c.positive
            <<" predicate_mismatches="<<c.mismatches<<"\n";
    }
    auto milliseconds=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now()-start).count();
    std::cout<<"SUMMARY "<<comparisons<<" exact-predicate comparisons, "<<assertions
        <<" boundary/coverage assertions, "<<mismatches<<" failures; CPU elapsed_ms="<<milliseconds<<"\n";
    return mismatches?1:0;
}
