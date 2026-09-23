// Exact mutable SDF descriptors in a real integer texture. Four RGBA32UI
// texels carry the existing 64-byte record without quantization or filtering.
// flags packs binary controls (orientation is bit 0); program remains eight
// FOUR-bit instructions because the nine-opcode vocabulary cannot fit one bit.
layout(binding=2) uniform usampler2D opInTexture;
layout(rgba32ui,binding=3) uniform writeonly uimage2D opOutTexture;
layout(binding=4) uniform usampler2D opNextTexture;
ivec2 dw_lut_coord(uint word,ivec2 shape){return ivec2(int(word%uint(shape.x)),int(word/uint(shape.x)));}
Operator dw_texture_operator(usampler2D table,uint index){
 ivec2 shape=textureSize(table,0);uint first=4u*index;
 vec4 a=uintBitsToFloat(texelFetch(table,dw_lut_coord(first,shape),0));
 vec4 b=uintBitsToFloat(texelFetch(table,dw_lut_coord(first+1u,shape),0));
 vec4 c=uintBitsToFloat(texelFetch(table,dw_lut_coord(first+2u,shape),0));
 uvec4 d=texelFetch(table,dw_lut_coord(first+3u,shape),0);
 Operator result;result.u=a.x;result.v=a.y;result.radius=a.z;result.height=a.w;
 result.phase=b.x;result.gain=b.y;result.coupling=b.z;result.shear=b.w;
 result.du=c.x;result.dv=c.y;result.mutationRate=c.z;result.reserved=c.w;
 result.program=d.x;result.seed=d.y;result.kind=d.z;result.flags=d.w;return result;
}
void dw_store_operator(uint index,Operator value){
 ivec2 shape=imageSize(opOutTexture);uint first=4u*index;
 imageStore(opOutTexture,dw_lut_coord(first,shape),floatBitsToUint(vec4(value.u,value.v,value.radius,value.height)));
 imageStore(opOutTexture,dw_lut_coord(first+1u,shape),floatBitsToUint(vec4(value.phase,value.gain,value.coupling,value.shear)));
 imageStore(opOutTexture,dw_lut_coord(first+2u,shape),floatBitsToUint(vec4(value.du,value.dv,value.mutationRate,value.reserved)));
 imageStore(opOutTexture,dw_lut_coord(first+3u,shape),uvec4(value.program,value.seed,value.kind,value.flags));
}
#ifdef DW_MUTATION_PASS
shared Operator dw_mutation_controls[2];
void dw_stage_operators(){
 uint lane=gl_LocalInvocationID.x;
 if(lane<2u)dw_mutation_controls[lane]=dw_texture_operator(opInTexture,lane==0u?5u:30u);
 barrier();
}
#else
// All lanes reach this barrier, including lanes past cfg.count. The 31 core
// descriptors stay in workgroup shared storage for the dispatch. Larger trees
// still use exact texture point reads for records outside this core window.
shared Operator dw_core_operators[31];
void dw_stage_operators(){
 uint lane=gl_LocalInvocationID.x;
 if(lane<31u)dw_core_operators[lane]=dw_texture_operator(opNextTexture,lane);
 barrier();
}
Operator dw_load_operator(uint index){if(index<31u)return dw_core_operators[index];return dw_texture_operator(opNextTexture,index);}
#undef DW_OP
#define DW_OP(i) dw_load_operator(i)
#endif
