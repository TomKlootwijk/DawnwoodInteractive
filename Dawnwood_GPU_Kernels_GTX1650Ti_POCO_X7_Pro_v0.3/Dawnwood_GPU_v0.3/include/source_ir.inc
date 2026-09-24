// DWI-XIR-0.1: bounded scalar FP32 SSA expression execution.
// This is a numerical body/field binding foundation, not a source-cycle runtime.
// The host validates the entire program before CPU or GPU execution. Opcodes
// produce register i, and each register operand must refer to an earlier i.
// All branches of select are eagerly evaluated by SSA, including their errors.
// Includes the existing N1 portable arithmetic; compile without FP contraction.
#include "numeric_types.inc"

#ifdef __cplusplus
#define DW_IR_WORD(i) words[i]
#define DW_IR_INPUT(i) inputs[i]
#define DW_IR_OUTPUT_REGISTER(i) outputRegisters[i]
#define DW_IR_OUTPUT(i) outputs[i]
DW_FN uint dw_ir_execute(const uint* words,const float* inputs,
 const uint* outputRegisters,float* outputs,uint instructionCount,uint outputWidth){
#else
// The shader supplies buffer access macros before including this file.
DW_FN uint dw_ir_execute(uint instructionCount,uint outputWidth,uint inputBase,uint outputBase){
#endif
 DW_PRECISE float registers[256];
 // Failure is lane-local. Its entire output row is positive zero, with the
 // first failing instruction/reason carried separately in the status word.
 DW_LOOP for(uint o=0u;o<outputWidth;++o)DW_IR_OUTPUT(o)=0.0f;
 DW_LOOP for(uint i=0u;i<instructionCount;++i){
  uint offset=4u*i,op=DW_IR_WORD(offset),a=DW_IR_WORD(offset+1u);
  uint b=DW_IR_WORD(offset+2u),c=DW_IR_WORD(offset+3u),reason=0u;
  DW_PRECISE float value=0.0f;
  if(op==0u)value=dw_bits_float(a);
  else if(op==1u)value=DW_IR_INPUT(a);
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
  else reason=3u; // Unreachable after mandatory host validation.
  if(reason==0u&&(dw_float_bits(value)&0x7f800000u)==0x7f800000u)reason=3u;
  if(reason!=0u)return ((i+1u)<<16u)|reason;
  registers[i]=value;
 }
 DW_LOOP for(uint o=0u;o<outputWidth;++o)DW_IR_OUTPUT(o)=registers[DW_IR_OUTPUT_REGISTER(o)];
 return 0u;
}
#ifdef __cplusplus
#undef DW_IR_WORD
#undef DW_IR_INPUT
#undef DW_IR_OUTPUT_REGISTER
#undef DW_IR_OUTPUT
#endif
