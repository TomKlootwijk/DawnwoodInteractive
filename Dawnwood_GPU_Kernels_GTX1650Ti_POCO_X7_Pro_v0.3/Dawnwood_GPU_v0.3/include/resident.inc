// DWI-RESIDENT-0.1: transactional mutation and explicit situated action.
// The host validates the immutable bank, plans and image before execution.
// Numerical laws remain bank data. This is not the complete source cycle.
#include "numeric_types.inc"

#ifdef __cplusplus
#define DW_RES_CONFIG_PARAMETER const uint* config,
#define DW_RES_CONFIG_ARGUMENT config,
#define DW_RES_IMAGES_PARAMETER const uint* oldWords,uint* newWords,
#define DW_RES_IMAGES_ARGUMENT oldWords,newWords,
#define DW_RES_CFG(i) config[i]
#define DW_RES_ARRAY_IN(T,N,S) const T* N
#define DW_RES_ARRAY_OUT(T,N,S) T* N
#else
#define DW_RES_CONFIG_PARAMETER
#define DW_RES_CONFIG_ARGUMENT
#define DW_RES_IMAGES_PARAMETER
#define DW_RES_IMAGES_ARGUMENT
#define DW_RES_CFG(i) configWords[i]
#define DW_RES_ARRAY_IN(T,N,S) T N[S]
#define DW_RES_ARRAY_OUT(T,N,S) out T N[S]
#endif

const uint DW_RES_LIMIT=16777215u;
const uint DW_RES_NO_TARGET=0xffffffffu;

struct DwResidentLayout {
 uint records,states,functions,heap,mutation,action,imageWords;
};

DW_FN bool dw_resident_finite(float value){
 return (dw_float_bits(value)&0x7f800000u)!=0x7f800000u;
}

// Same ordered FP32 instruction switch as DWI-XIR-0.1, with an explicit bank
// descriptor and local argument/result arrays. Bank validation is mandatory.
DW_FN uint dw_resident_eval(DW_RES_CONFIG_PARAMETER uint functions,uint heap,
 uint handle,DW_RES_ARRAY_IN(float,inputs,64),DW_RES_ARRAY_OUT(float,outputs,32)){
 uint descriptor=functions+6u*handle;
 uint code=heap+DW_RES_CFG(descriptor),outputRegisters=heap+DW_RES_CFG(descriptor+1u);
 uint instructionCount=DW_RES_CFG(descriptor+2u),outputWidth=DW_RES_CFG(descriptor+4u);
 DW_PRECISE float registers[256];
 DW_LOOP for(uint o=0u;o<32u;++o)outputs[o]=0.0f;
 DW_LOOP for(uint i=0u;i<instructionCount;++i){
  uint offset=code+4u*i,op=DW_RES_CFG(offset),a=DW_RES_CFG(offset+1u);
  uint b=DW_RES_CFG(offset+2u),c=DW_RES_CFG(offset+3u),reason=0u;
  DW_PRECISE float value=0.0f;
  if(op==0u)value=dw_bits_float(a);
  else if(op==1u)value=inputs[a];
  else if(op==2u)value=registers[a]+registers[b];
  else if(op==3u)value=registers[a]-registers[b];
  else if(op==4u)value=registers[a]*registers[b];
  else if(op==5u){if(registers[b]==0.0f)reason=1u;else value=dw_div(registers[a],registers[b]);}
  else if(op==6u)value=dw_sin(registers[a]);
  else if(op==7u)value=dw_cos(registers[a]);
  else if(op==8u)value=dw_exp(registers[a]);
  else if(op==9u){if(registers[a]<0.0f)reason=2u;else value=dw_sqrt(registers[a]);}
  else if(op==10u)value=dw_abs(registers[a]);
  else if(op==11u)value=dw_min(registers[a],registers[b]);
  else if(op==12u)value=dw_max(registers[a],registers[b]);
  else if(op==13u)value=-registers[a];
  else if(op==14u)value=dw_floor(registers[a]);
  else if(op==15u)value=registers[a]<registers[b]?1.0f:0.0f;
  else if(op==16u)value=registers[a]!=0.0f?registers[b]:registers[c];
  else if(op==17u){value=registers[a];if(value==0.0f)reason=4u;}
  else reason=3u; // Unreachable for a validated bank.
  if(reason==0u&&!dw_resident_finite(value))reason=3u;
  if(reason!=0u)return ((i+1u)<<16u)|reason;
  registers[i]=value;
 }
 DW_LOOP for(uint o=0u;o<outputWidth;++o)outputs[o]=registers[DW_RES_CFG(outputRegisters+o)];
 return 0u;
}

DW_FN void dw_resident_restore(DW_RES_IMAGES_PARAMETER uint base,uint words){
 DW_LOOP for(uint i=0u;i<words;++i)newWords[base+i]=oldWords[base+i];
}

DW_FN void dw_resident_fail(DW_RES_IMAGES_PARAMETER uint base,uint words,
 uint status,uint phase,uint target,uint step,uint detail){
 dw_resident_restore(DW_RES_IMAGES_ARGUMENT base,words);
 newWords[base+1u]=status;
 newWords[base+2u]=phase;
 newWords[base+3u]=target;
 newWords[base+4u]=step;
 newWords[base+5u]=detail;
}

DW_FN uint dw_resident_validate_record(DW_RES_CONFIG_PARAMETER DW_RES_IMAGES_PARAMETER
 DwResidentLayout layoutInfo,uint base,uint target,DW_INOUT(uint) detail){
 uint record=base+6u+layoutInfo.states+24u*target;
 DW_LOOP for(uint slot=0u;slot<3u;++slot){
  uint handle=newWords[record+slot];
  if(handle>=DW_RES_CFG(3u)){detail=slot;return 2u;}
  uint signature=DW_RES_CFG(layoutInfo.functions+6u*handle+5u);
  if(signature!=DW_RES_CFG(8u+4u*target+1u+slot)){detail=slot;return 4u;}
 }
 uint generation=newWords[record+3u],oldGeneration=oldWords[record+3u];
 if(generation>DW_RES_LIMIT||oldGeneration>=DW_RES_LIMIT||generation!=oldGeneration+1u){detail=3u;return 5u;}
 DW_LOOP for(uint word=4u;word<24u;++word){
  if(!dw_resident_finite(dw_bits_float(newWords[record+word]))){detail=word;return 6u;}
 }
 return 0u;
}

// phase is 1 for a mutation target, 2 for action. Bounds, initialized reads,
// legal bank selectors and exactly-once writes were checked by the host.
DW_FN uint dw_resident_plan(DW_RES_CONFIG_PARAMETER DW_RES_IMAGES_PARAMETER
 DwResidentLayout layoutInfo,uint base,uint phase,uint target,uint plan,uint steps,
 DW_INOUT(uint) failureStep,DW_INOUT(uint) detail){
 DW_PRECISE float frame[256];
 DW_PRECISE float inputs[64];
 DW_PRECISE float outputs[32];
 DW_LOOP for(uint i=0u;i<256u;++i)frame[i]=0.0f;
 DW_LOOP for(uint i=0u;i<64u;++i)inputs[i]=0.0f;
 DW_LOOP for(uint i=0u;i<32u;++i)outputs[i]=0.0f;
 DW_LOOP for(uint step=0u;step<steps;++step){
  failureStep=step;
  uint instruction=plan+8u*step,op=DW_RES_CFG(instruction);
  uint a=DW_RES_CFG(instruction+1u),b=DW_RES_CFG(instruction+2u);
  uint c=DW_RES_CFG(instruction+3u),d=DW_RES_CFG(instruction+4u);
  uint e=DW_RES_CFG(instruction+5u),f=DW_RES_CFG(instruction+6u);
  if(op==0u){
   frame[a]=dw_bits_float(b);
  }else if(op==1u){
   DW_LOOP for(uint i=0u;i<c;++i)frame[a+i]=dw_bits_float(oldWords[base+6u+b+i]);
  }else if(op==2u){
   uint selected=b==DW_RES_NO_TARGET?target:b;
   uint record=base+6u+layoutInfo.states+24u*selected;
   DW_LOOP for(uint i=0u;i<d;++i){
    uint word=c+i,bits=e==0u?oldWords[record+word]:newWords[record+word];
    frame[a+i]=word<4u?float(bits):dw_bits_float(bits);
   }
  }else if(op==3u||op==4u){
   uint handle=a,inputBase=b,outputBase=c;
   if(op==4u){
    uint selected=a==DW_RES_NO_TARGET?target:a;
    uint record=base+6u+layoutInfo.states+24u*selected;
    handle=c==0u?oldWords[record+b]:newWords[record+b];
    inputBase=d;outputBase=e;
   }
   if(handle>=DW_RES_CFG(3u)){detail=handle;return 2u;}
   uint descriptor=layoutInfo.functions+6u*handle;
   if(op==4u&&DW_RES_CFG(descriptor+5u)!=f){detail=b;return 4u;}
   uint inputWidth=DW_RES_CFG(descriptor+3u),outputWidth=DW_RES_CFG(descriptor+4u);
   // Copy arguments first: output ranges may overlap their input frame ranges.
   DW_LOOP for(uint i=0u;i<inputWidth;++i)inputs[i]=frame[inputBase+i];
   uint status=dw_resident_eval(DW_RES_CONFIG_ARGUMENT layoutInfo.functions,layoutInfo.heap,handle,inputs,outputs);
   if(status!=0u){detail=status;return 1u;}
   DW_LOOP for(uint i=0u;i<outputWidth;++i)frame[outputBase+i]=outputs[i];
  }else if(op==5u){
   uint record=base+6u+layoutInfo.states+24u*target;
   DW_LOOP for(uint i=0u;i<c;++i){
    uint word=a+i;
    DW_PRECISE float value=frame[b+i];
    if(!dw_resident_finite(value)){detail=word;return 6u;}
    if(word<4u){
     // 2^32 itself is exactly representable, unlike UINT32_MAX as FP32.
     // Reject it before conversion to avoid undefined/out-of-range casts.
     if(value<0.0f||value>=4294967296.0f||dw_floor(value)!=value){detail=word;return 3u;}
     newWords[record+word]=uint(value);
    }else newWords[record+word]=dw_float_bits(value);
   }
  }else if(op==6u){
   DW_LOOP for(uint i=0u;i<c;++i){
    DW_PRECISE float value=frame[b+i];
    if(!dw_resident_finite(value)){detail=a+i;return 6u;}
    newWords[base+6u+a+i]=dw_float_bits(value);
   }
  }else if(op==7u){
   if(!dw_resident_finite(frame[a])){detail=a;return 6u;}
   if(frame[a]==0.0f){detail=a;return 7u;}
  }else if(op==8u){
   frame[a]=float(oldWords[base]);
  }else if(op==9u){
   frame[a]=float(DW_RES_CFG(8u+4u*target));
  }else if(op==10u){
   // Snapshot/memmove semantics without a second 256-element temporary frame.
   if(a>b){DW_LOOP for(uint i=c;i>0u;--i)frame[a+i-1u]=frame[b+i-1u];}
   else {DW_LOOP for(uint i=0u;i<c;++i)frame[a+i]=frame[b+i];}
  }else{
   detail=op;return 3u; // Invalid plans are rejected before dispatch.
  }
 }
 return 0u;
}

#ifdef __cplusplus
DW_FN void dw_resident_step(const uint* config,const uint* oldWords,uint* newWords,uint lane,uint reverseTargets){
#else
DW_FN void dw_resident_step(uint lane,uint reverseTargets){
#endif
 if(lane>=DW_RES_CFG(0u))return;
 DwResidentLayout layoutInfo;
 layoutInfo.records=DW_RES_CFG(1u);layoutInfo.states=DW_RES_CFG(2u);
 layoutInfo.functions=8u+4u*layoutInfo.records;
 layoutInfo.heap=layoutInfo.functions+6u*DW_RES_CFG(3u);
 layoutInfo.mutation=layoutInfo.heap+DW_RES_CFG(4u);
 layoutInfo.action=layoutInfo.mutation+8u*DW_RES_CFG(5u);
 layoutInfo.imageWords=6u+layoutInfo.states+24u*layoutInfo.records;
 uint base=lane*layoutInfo.imageWords;
 dw_resident_restore(DW_RES_IMAGES_ARGUMENT base,layoutInfo.imageWords);
 if(oldWords[base+1u]!=0u)return;
 uint epoch=oldWords[base];
 if(epoch>=DW_RES_LIMIT){
  dw_resident_fail(DW_RES_IMAGES_ARGUMENT base,layoutInfo.imageWords,8u,3u,DW_RES_NO_TARGET,0u,epoch);
  return;
 }
 uint failureStep=0u,detail=0u;
 DW_LOOP for(uint ordinal=0u;ordinal<layoutInfo.records;++ordinal){
  uint target=reverseTargets!=0u?layoutInfo.records-1u-ordinal:ordinal;
  uint status=dw_resident_plan(DW_RES_CONFIG_ARGUMENT DW_RES_IMAGES_ARGUMENT
    layoutInfo,base,1u,target,layoutInfo.mutation,DW_RES_CFG(5u),failureStep,detail);
  if(status==0u){
   status=dw_resident_validate_record(DW_RES_CONFIG_ARGUMENT DW_RES_IMAGES_ARGUMENT layoutInfo,base,target,detail);
   failureStep=DW_RES_CFG(5u)-1u;
  }
  if(status!=0u){
   dw_resident_fail(DW_RES_IMAGES_ARGUMENT base,layoutInfo.imageWords,status,1u,target,failureStep,detail);
   return;
  }
 }
 uint status=dw_resident_plan(DW_RES_CONFIG_ARGUMENT DW_RES_IMAGES_ARGUMENT
   layoutInfo,base,2u,DW_RES_NO_TARGET,layoutInfo.action,DW_RES_CFG(6u),failureStep,detail);
 if(status!=0u){
  dw_resident_fail(DW_RES_IMAGES_ARGUMENT base,layoutInfo.imageWords,status,2u,DW_RES_NO_TARGET,failureStep,detail);
  return;
 }
 newWords[base]=epoch+1u;
}

#undef DW_RES_CONFIG_PARAMETER
#undef DW_RES_CONFIG_ARGUMENT
#undef DW_RES_IMAGES_PARAMETER
#undef DW_RES_IMAGES_ARGUMENT
#undef DW_RES_CFG
#undef DW_RES_ARRAY_IN
#undef DW_RES_ARRAY_OUT
