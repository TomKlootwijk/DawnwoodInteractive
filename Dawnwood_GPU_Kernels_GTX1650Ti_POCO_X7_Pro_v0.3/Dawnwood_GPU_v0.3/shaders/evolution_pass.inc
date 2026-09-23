// Split evolution uses the same shared equations as the monolithic kernel.
// Scratch is indexed within one bounded dispatch chunk, never by population ID.
#include "numeric_types.inc"
layout(local_size_x=64) in;
layout(std430,binding=0) readonly buffer SIn { State stateIn[]; };
layout(std430,binding=1) buffer SOut { State stateOut[]; };
#include "operator_texture.inc"
layout(push_constant) uniform Parameters {Config cfg;};
#define DW_OP_ARGUMENT
#include "numeric_evolve.inc"
layout(std430,binding=5) buffer EvolutionWork { EvolutionScratch work[]; };
