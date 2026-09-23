DW_FN float dw_geometry(State s DW_OP_PARAMETER){DW_PRECISE float total=0.0f;DW_LOOP for(uint k=0u;k<6u;++k)total+=dw_field(s,DW_OP(7u+k),k);DW_RETURN_FLOAT(dw_apply(s,DW_OP(0u),dw_div(total,6.0f)));}
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
DW_FN State dw_evolve(State previousState,Config config,uint lane DW_OP_PARAMETER){
 DW_PRECISE State s=previousState;DW_PRECISE Config cfg=config;
 uint rng=dw_rng(s.rng^DW_OP(20u).seed^DW_OP(20u).program),j=(cfg.jitter!=0u)?(rng&1u):0u;
 uint selected=0u;DW_LOOP for(uint level=0u;level<cfg.depth;++level){uint b=((s.rng>>level)&1u)^j^s.orientation^(DW_OP(selected).flags&1u)^dw_parity(DW_OP(28u).seed^DW_OP(28u).program)^((DW_OP(27u).flags^DW_OP(27u).program)&1u)^((DW_OP(21u).seed^DW_OP(21u).program)&1u);selected=2u*selected+1u+b;}
 cfg.dt*=1.0f+0.01f*dw_apply(s,DW_OP(29u),0.0f);
 DW_PRECISE float delta=s.theta-2.0f*s.previousTheta+s.previousPreviousTheta;
 s.delta=dw_apply(s,DW_OP(13u),delta);
 // Keep one derivative call site so device compilers need not expand four copies
 // of the nested field interpreter. Stage inputs and FP32 operation order match
 // the explicit RK4 stages, including two separate Y-up additions in stage 3.
 DW_PRECISE Motion previousSlope;previousSlope.u=0.0f;previousSlope.v=0.0f;previousSlope.rho=0.0f;previousSlope.theta=0.0f;
 DW_PRECISE Motion k1=previousSlope,k2=previousSlope,k3=previousSlope,k4=previousSlope;
 DW_LOOP for(uint stage=0u;stage<4u;++stage){
  DW_PRECISE State stageState=s;
  if(stage==1u||stage==2u)stageState=dw_stage(s,previousSlope,0.5f*cfg.dt);
  else if(stage==3u){stageState=dw_stage(s,previousSlope,cfg.dt);DW_PRECISE float up=cfg.yup*dw_apply(s,DW_OP(16u),1.0f);stageState.v+=up;stageState.v+=up;}
  DW_PRECISE Motion slope=dw_derivative(stageState,cfg,selected DW_OP_ARGUMENT);
  if(stage==0u)k1=slope;else if(stage==1u)k2=slope;else if(stage==2u)k3=slope;else k4=slope;
  previousSlope=slope;
 }
 DW_PRECISE State outState=s;
 outState.u+=dw_div(cfg.dt*(k1.u+2.0f*k2.u+2.0f*k3.u+k4.u),6.0f);
 outState.v+=dw_div(cfg.dt*(k1.v+2.0f*k2.v+2.0f*k3.v+k4.v),6.0f);
 outState.rho+=dw_div(cfg.dt*(k1.rho+2.0f*k2.rho+2.0f*k3.rho+k4.rho),6.0f);
 outState.theta+=dw_div(cfg.dt*(k1.theta+2.0f*k2.theta+2.0f*k3.theta+k4.theta),6.0f);
 outState.u+=cfg.dt*0.001f*dw_apply(s,DW_OP(22u),s.field);
 dw_wrap(outState.u,outState.v,outState.orientation);
 DW_PRECISE float field=dw_geometry(outState DW_OP_ARGUMENT);
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
 outState.rng=rng;outState.route=selected;outState.alpha_ref=lane;
 outState.previousPreviousTheta=s.previousTheta;outState.previousTheta=s.theta;outState.lastJitter=float(j);
 dw_embedding(outState);return outState;
}
