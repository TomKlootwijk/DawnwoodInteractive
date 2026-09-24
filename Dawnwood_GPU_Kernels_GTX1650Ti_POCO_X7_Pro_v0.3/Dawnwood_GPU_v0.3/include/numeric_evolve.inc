// Enabled profiles validate the exactly represented law count in op0.reserved,
// with protected records occupying 31..31+count-1 and routing confined to 0..30.
DW_FN float dw_domain_mean_violation(State s DW_OP_PARAMETER){
 uint count=uint(DW_OP(0u).reserved);DW_PRECISE float total=0.0f;
 DW_LOOP for(uint lawIndex=0u;lawIndex<count;++lawIndex)total+=dw_domain_violation(s,DW_OP(31u+lawIndex));
 DW_RETURN_FLOAT(dw_div(total,float(count)));
}
DW_FN void dw_domain_project(DW_PRECISE DW_INOUT(State) s DW_OP_PARAMETER){
 uint count=uint(DW_OP(0u).reserved);
 // One ordered cyclic sweep per epoch. Re-evaluate each law on the coordinates
 // produced by the preceding projection; do not mutate the stored domain laws.
 DW_LOOP for(uint lawIndex=0u;lawIndex<count;++lawIndex){
  DW_PRECISE Operator law=DW_OP(31u+lawIndex);
  DW_PRECISE float distance=dw_domain_distance(s,law);
  DW_PRECISE float response=dw_apply(s,DW_OP(30u),distance);
  DW_PRECISE float relaxation=dw_max(0.25f,dw_min(0.95f,0.6f+0.35f*dw_sin(response)));
  DW_PRECISE float residual=dw_domain_residual(s,law),excess=residual;
  if(law.kind==1u)excess=dw_max(residual,0.0f);
  else if(law.kind==2u){
   if(residual>law.dv)excess=residual-law.dv;
   else if(residual<-law.dv)excess=residual+law.dv;
   else excess=0.0f;
  }
  DW_PRECISE float amount=dw_div(relaxation*excess,dw_domain_normal_sq(law));
  s.px-=amount*law.phase;s.py-=amount*law.gain;s.pz-=amount*law.coupling;s.pw-=amount*law.shear;
 }
}
DW_FN float dw_geometry(State s DW_OP_PARAMETER){
 DW_PRECISE float total=0.0f;DW_LOOP for(uint k=0u;k<6u;++k)total+=dw_field(s,DW_OP(7u+k),k);
 if(dw_domain_enabled(DW_OP(0u))){
  DW_PRECISE float domainInput=dw_div(total,6.0f)+dw_domain_mean_violation(s DW_OP_ARGUMENT);
  DW_RETURN_FLOAT(dw_apply(s,DW_OP(0u),domainInput));
 }
 DW_RETURN_FLOAT(dw_apply(s,DW_OP(0u),dw_div(total,6.0f)));
}
DW_FN Motion dw_derivative(State s,Config cfg,uint selected DW_OP_PARAMETER){
 DW_PRECISE Operator pinion=DW_OP(5u),chosen=DW_OP(selected),colon=DW_OP(6u),phi=DW_OP(2u);
 DW_PRECISE float field=dw_geometry(s DW_OP_ARGUMENT);
 DW_PRECISE float encoded=dw_exp(s.rho),qx=0.0f,qy=0.0f,coupling=0.0f,growth=0.0f,blended=0.0f,combined=0.0f;
 bool downstream=(selected==25u||selected==26u);DW_PRECISE Motion d;
 // Reuse one field/body interpreter call site. Each request consumes precisely
 // the prior request's FP32 result; expressions retain their original grouping.
 // This limits expansion on drivers that inline SPIR-V function boundaries.
 DW_LOOP for(uint request=0u;request<7u;++request){
  DW_PRECISE Operator requestOp=phi;DW_PRECISE float value=s.rho;
  // Frobenius colon binding of the two 2x2 pinion tensors.
  if(request==1u){requestOp=colon;value=qx*pinion.du+qy*pinion.dv+pinion.dv*qy+pinion.du*qx;}
  else if(request==2u){requestOp=DW_OP(4u);value=s.delta;}
  else if(request==3u){requestOp=DW_OP(14u);value=field+colon.coupling*coupling+0.01f*growth;}
  else if(request==4u){if(downstream){combined=blended;continue;}requestOp=chosen;value=blended;}
  else if(request==5u){requestOp=pinion;value=s.phaseResponse;}
  else if(request==6u){requestOp=DW_OP(3u);value=combined;}
  DW_PRECISE float result=dw_apply(s,requestOp,value);
  if(request==0u){DW_PRECISE float polarAngle=s.theta+0.01f*result;qx=encoded*dw_cos(polarAngle);qy=encoded*dw_sin(polarAngle);}
  else if(request==1u)coupling=result;
  else if(request==2u)growth=result;
  else if(request==3u)blended=result;
  else if(request==4u)combined=result;
  else if(request==5u){
   d.u=pinion.du+0.001f*result+0.02f*dw_sin(s.theta+DW_TAU*s.v)+cfg.fieldScale*dw_sin(combined);
   d.v=pinion.dv+0.02f*dw_cos(DW_TAU*s.v+s.theta)+cfg.fieldScale*dw_sin(combined+phi.phase);
   d.rho=cfg.radialRate*(dw_sin(s.theta+(downstream?0.0f:chosen.phase))-0.1f*s.rho)+0.001f*s.phaseResponse;
  }else d.theta=cfg.phaseRate+0.02f*result+0.01f*s.delta;
 }
 return d;
}
DW_FN State dw_stage(State point,Motion k,float h){DW_PRECISE State s=point;s.u+=h*k.u;s.v+=h*k.v;s.rho+=h*k.rho;s.theta+=h*k.theta;return s;}
// Temporary per-lane work record for the same equations evaluated in bounded
// dispatch stages. Scalar std430 layout is exactly 96 bytes; this is not part
// of State, Operator, or the checkpoint ABI. All intermediate values are FP32.
struct EvolutionScratch {
 float dt,delta,up,field;
 uint selected,rng,j,reserved;
 Motion k1,k2,k3,k4;
};
DW_FN EvolutionScratch dw_prepare(State previousState,Config config DW_OP_PARAMETER){
 DW_PRECISE State s=previousState;DW_PRECISE Config cfg=config;
 uint rng=dw_rng(s.rng^DW_OP(20u).seed^DW_OP(20u).program),j=(cfg.jitter!=0u)?(rng&1u):0u;
 uint selected=0u;DW_LOOP for(uint level=0u;level<cfg.depth;++level){uint b=((s.rng>>level)&1u)^j^s.orientation^(DW_OP(selected).flags&1u)^dw_parity(DW_OP(28u).seed^DW_OP(28u).program)^((DW_OP(27u).flags^DW_OP(27u).program)&1u)^((DW_OP(21u).seed^DW_OP(21u).program)&1u);selected=2u*selected+1u+b;}
 cfg.dt*=1.0f+0.01f*dw_apply(s,DW_OP(29u),0.0f);
 DW_PRECISE float delta=s.theta-2.0f*s.previousTheta+s.previousPreviousTheta;
 s.delta=dw_apply(s,DW_OP(13u),delta);
 DW_PRECISE EvolutionScratch work;
 work.dt=cfg.dt;work.delta=s.delta;
 // The fourth stage uses this original point with updated delta, not its
 // displaced stage point. Its pure Y-up expression can therefore be stored now.
 work.up=cfg.yup*dw_apply(s,DW_OP(16u),1.0f);work.field=0.0f;
 work.selected=selected;work.rng=rng;work.j=j;work.reserved=0u;
 DW_PRECISE Motion zero;zero.u=0.0f;zero.v=0.0f;zero.rho=0.0f;zero.theta=0.0f;
 work.k1=zero;work.k2=zero;work.k3=zero;work.k4=zero;return work;
}
// stage is 0..3. Each stored slope must be available before the next stage;
// across GPU dispatches the caller provides the corresponding memory barrier.
DW_FN Motion dw_slope(State previousState,Config config,EvolutionScratch work,uint stage DW_OP_PARAMETER){
 DW_PRECISE State s=previousState;DW_PRECISE Config cfg=config;
 s.delta=work.delta;cfg.dt=work.dt;DW_PRECISE State stageState=s;
 if(stage==1u)stageState=dw_stage(s,work.k1,0.5f*cfg.dt);
 else if(stage==2u)stageState=dw_stage(s,work.k2,0.5f*cfg.dt);
 else if(stage==3u){stageState=dw_stage(s,work.k3,cfg.dt);stageState.v+=work.up;stageState.v+=work.up;}
 return dw_derivative(stageState,cfg,work.selected DW_OP_ARGUMENT);
}
DW_FN State dw_combine(State previousState,Config config,EvolutionScratch work DW_OP_PARAMETER){
 DW_PRECISE State s=previousState;DW_PRECISE Config cfg=config;
 s.delta=work.delta;cfg.dt=work.dt;
 DW_PRECISE Motion k1=work.k1,k2=work.k2,k3=work.k3,k4=work.k4;
 DW_PRECISE State outState=s;
 outState.u+=dw_div(cfg.dt*(k1.u+2.0f*k2.u+2.0f*k3.u+k4.u),6.0f);
 outState.v+=dw_div(cfg.dt*(k1.v+2.0f*k2.v+2.0f*k3.v+k4.v),6.0f);
 outState.rho+=dw_div(cfg.dt*(k1.rho+2.0f*k2.rho+2.0f*k3.rho+k4.rho),6.0f);
 outState.theta+=dw_div(cfg.dt*(k1.theta+2.0f*k2.theta+2.0f*k3.theta+k4.theta),6.0f);
 outState.u+=cfg.dt*0.001f*dw_apply(s,DW_OP(22u),s.field);
 dw_wrap(outState.u,outState.v,outState.orientation);
 return outState;
}
// combinedState still contains the original amplitude/history values. The
// geometry stage stores its new field in work.field, leaving those values intact.
DW_FN State dw_finish(State previousState,State combinedState,Config config,EvolutionScratch work,uint lane DW_OP_PARAMETER){
 DW_PRECISE State s=previousState,outState=combinedState;DW_PRECISE Config cfg=config;
 s.delta=work.delta;cfg.dt=work.dt;
 DW_PRECISE Motion k1=work.k1,k2=work.k2,k3=work.k3,k4=work.k4;
 DW_PRECISE float field=work.field;uint j=work.j;
 DW_PRECISE float phaseParts[4];
 // The four phase terms, inverse transform, feedback and history share a call
 // site while retaining their dependencies and the original FP32 expressions.
 DW_LOOP for(uint request=0u;request<7u;++request){
  uint index=1u;DW_PRECISE float value=field;
  if(request==1u)index=17u;
  else if(request==2u){index=15u;value=s.energy;}
  else if(request==3u)index=24u;
  else if(request==4u)index=19u;
  else if(request==5u){index=18u;value=outState.inv00*field+outState.inv01*outState.delta;}
  else if(request==6u){index=23u;value=k1.v+k2.v+k3.v+k4.v+float(j)+outState.phaseResponse;}
  DW_PRECISE float result=dw_apply(outState,DW_OP(index),value);
  if(request<4u){
   phaseParts[request]=result;
   if(request==3u){
    DW_PRECISE float phase=DW_OP(1u).phase+0.01f*phaseParts[0]+cfg.epsilon*((j!=0u)?1.0f:-1.0f)+0.02f*phaseParts[1]+0.01f*phaseParts[2]+0.01f*phaseParts[3];
    DW_PRECISE float ar=(s.ar+s.br)*0.7071067811865475244f,ai=(s.ai+s.bi)*0.7071067811865475244f;
    DW_PRECISE float br=(s.ar-s.br)*0.7071067811865475244f,bi=(s.ai-s.bi)*0.7071067811865475244f;
    DW_PRECISE float cs=dw_cos(phase),sn=dw_sin(phase);
    outState.ar=cs*ar-sn*ai;outState.ai=sn*ar+cs*ai;
    outState.br=cs*br+sn*bi;outState.bi=-sn*br+cs*bi;
   }
  }else if(request==4u){
   DW_PRECISE float angle=outState.theta+DW_OP(19u).phase+0.01f*result,shear=DW_OP(19u).shear;
   DW_PRECISE float cs=dw_cos(angle),sn=dw_sin(angle);
   DW_PRECISE float t00=cs,t01=cs*shear-sn,t10=sn,t11=sn*shear+cs;
   // T=R(angle)*H(shear): det(T)=cos^2(angle)+sin^2(angle).
   // Expanding the products above would cancel large shear terms in FP32.
   DW_PRECISE float det=cs*cs+sn*sn;
   outState.inv00=dw_div(t11,det);outState.inv01=dw_div(-t01,det);outState.inv10=dw_div(-t10,det);outState.inv11=dw_div(t00,det);
  }else if(request==5u)outState.phaseResponse=result;
  else outState.history=cfg.historyWeight*s.history+(1.0f-cfg.historyWeight)*result;
 }
 outState.field=field;outState.energy=outState.ar*outState.ar+outState.ai*outState.ai+outState.br*outState.br+outState.bi*outState.bi;
 outState.k1v=k1.v;outState.k2v=k2.v;outState.k3v=k3.v;outState.k4v=k4.v;
 outState.rng=work.rng;outState.route=work.selected;outState.alpha_ref=lane;
 outState.previousPreviousTheta=s.previousTheta;outState.previousTheta=s.theta;outState.lastJitter=float(j);
 if(dw_domain_enabled(DW_OP(0u))){
  // Preserve the full N1 wave/history/transport update above. Only the four
  // inspection-embedding slots acquire this explicitly versioned domain role.
  outState.px=s.px;outState.py=s.py;outState.pz=s.pz;outState.pw=s.pw;
  dw_domain_project(outState DW_OP_ARGUMENT);
  // Return unresolved domain error to the same state.field consumed by the
  // next mutation pass, closing the domain/controller feedback connection.
  outState.field=field+dw_domain_mean_violation(outState DW_OP_ARGUMENT);
 }else dw_embedding(outState);
 return outState;
}
DW_FN State dw_evolve(State previousState,Config config,uint lane DW_OP_PARAMETER){
 DW_PRECISE EvolutionScratch work=dw_prepare(previousState,config DW_OP_ARGUMENT);
 // The monolithic path uses the exact same helpers and storage values as the
 // split path; only the location of these FP32 intermediates differs.
 DW_LOOP for(uint stage=0u;stage<4u;++stage){
  DW_PRECISE Motion slope=dw_slope(previousState,config,work,stage DW_OP_ARGUMENT);
  if(stage==0u)work.k1=slope;else if(stage==1u)work.k2=slope;else if(stage==2u)work.k3=slope;else work.k4=slope;
 }
 DW_PRECISE State combinedState=dw_combine(previousState,config,work DW_OP_ARGUMENT);
 work.field=dw_geometry(combinedState DW_OP_ARGUMENT);
 return dw_finish(previousState,combinedState,config,work,lane DW_OP_ARGUMENT);
}
