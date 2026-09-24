// Two physical pages represent ONE logical population. Mutation can read either
// page; all pages evolve against the same old state and changed operator LUT.
// Specialization disables the second page when the population fits in one.
layout(std430,binding=0) readonly buffer SIn { State stateIn[]; };
layout(std430,binding=1) buffer SOut { State stateOut[]; };
layout(std430,binding=6) readonly buffer SInOverflow { State stateInOverflow[]; };
layout(std430,binding=7) buffer SOutOverflow { State stateOutOverflow[]; };
layout(constant_id=1) const uint dw_state_page_records=33554431u;
layout(constant_id=2) const uint dw_state_paging=0u;
State dw_state_in(uint index){
 if(dw_state_paging!=0u&&index>=dw_state_page_records)return stateInOverflow[index-dw_state_page_records];
 return stateIn[index];
}
State dw_state_next(uint index){
 if(dw_state_paging!=0u&&index>=dw_state_page_records)return stateOutOverflow[index-dw_state_page_records];
 return stateOut[index];
}
void dw_state_out(uint index,State value){
 if(dw_state_paging!=0u&&index>=dw_state_page_records)stateOutOverflow[index-dw_state_page_records]=value;
 else stateOut[index]=value;
}
