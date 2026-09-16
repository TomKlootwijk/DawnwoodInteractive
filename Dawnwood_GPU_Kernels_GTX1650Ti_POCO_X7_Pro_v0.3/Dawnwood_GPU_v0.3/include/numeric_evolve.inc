DW_FN float dw_geometry(State s DW_OP_PARAMETER){float total=0.0;for(uint k=0u;k<6u;++k)total+=dw_field(s,DW_OP(7u+k),k);return dw_apply(s,DW_OP(0u),total/6.0);}
DW_FN Motion dw_derivative(State s,Config cfg,uint selected DW_OP_PARAMETER){
 Operator pinion=DW_OP(5u),chosen=DW_OP(selected),colon=DW_OP(6u),phi=DW_OP(2u);
 float field=dw_geometry(s DW_OP_ARGUMENT);
 float encoded=dw_exp(s.rho);float polarAngle=s.theta+0.01*dw_apply(s,phi,s.rho);float qx=encoded*dw_cos(polarAngle),qy=encoded*dw_sin(polarAngle);
 // Frobenius colon binding of the two 2x2 pinion tensors.
 float coupling=dw_apply(s,colon,qx*pinion.du+qy*pinion.dv+pinion.dv*qy+pinion.du*qx);
 float growth=dw_apply(s,DW_OP(4u),s.delta);
 float blended=dw_apply(s,DW_OP(14u),field+colon.coupling*coupling+0.01*growth);
 bool downstream=(selected==25u||selected==26u);
 float combined=downstream?blended:dw_apply(s,chosen,blended);
 Motion d;d.u=pinion.du+0.001*dw_apply(s,pinion,s.phaseResponse)+0.02*dw_sin(s.theta+DW_TAU*s.v)+cfg.fieldScale*dw_sin(combined);
 d.v=pinion.dv+0.02*dw_cos(DW_TAU*s.v+s.theta)+cfg.fieldScale*dw_sin(combined+phi.phase);
 d.rho=cfg.radialRate*(dw_sin(s.theta+(downstream?0.0:chosen.phase))-0.1*s.rho)+0.001*s.phaseResponse;
 d.theta=cfg.phaseRate+0.02*dw_apply(s,DW_OP(3u),combined)+0.01*s.delta;return d;
}
DW_FN State dw_stage(State s,Motion k,float h){s.u+=h*k.u;s.v+=h*k.v;s.rho+=h*k.rho;s.theta+=h*k.theta;return s;}
DW_FN State dw_evolve(State s,Config cfg,uint lane DW_OP_PARAMETER){
 uint rng=dw_rng(s.rng^DW_OP(20u).seed^DW_OP(20u).program),j=(cfg.jitter!=0u)?(rng&1u):0u;
 uint selected=0u;for(uint level=0u;level<cfg.depth;++level){uint b=((s.rng>>level)&1u)^j^s.orientation^(DW_OP(selected).flags&1u)^dw_parity(DW_OP(28u).seed^DW_OP(28u).program)^((DW_OP(27u).flags^DW_OP(27u).program)&1u)^((DW_OP(21u).seed^DW_OP(21u).program)&1u);selected=2u*selected+1u+b;}
 cfg.dt*=1.0+0.01*dw_apply(s,DW_OP(29u),0.0);
 float delta=s.theta-2.0*s.previousTheta+s.previousPreviousTheta;
 s.delta=dw_apply(s,DW_OP(13u),delta);
 Motion k1=dw_derivative(s,cfg,selected DW_OP_ARGUMENT);
 Motion k2=dw_derivative(dw_stage(s,k1,0.5*cfg.dt),cfg,selected DW_OP_ARGUMENT);
 Motion k3=dw_derivative(dw_stage(s,k2,0.5*cfg.dt),cfg,selected DW_OP_ARGUMENT);
 State fourth=dw_stage(s,k3,cfg.dt);float up=cfg.yup*dw_apply(s,DW_OP(16u),1.0);fourth.v+=up;fourth.v+=up;
 Motion k4=dw_derivative(fourth,cfg,selected DW_OP_ARGUMENT);
 State outState=s;
 outState.u+=cfg.dt*(k1.u+2.0*k2.u+2.0*k3.u+k4.u)/6.0;
 outState.v+=cfg.dt*(k1.v+2.0*k2.v+2.0*k3.v+k4.v)/6.0;
 outState.rho+=cfg.dt*(k1.rho+2.0*k2.rho+2.0*k3.rho+k4.rho)/6.0;
 outState.theta+=cfg.dt*(k1.theta+2.0*k2.theta+2.0*k3.theta+k4.theta)/6.0;
 outState.u+=cfg.dt*0.001*dw_apply(s,DW_OP(22u),s.field);
 dw_wrap(outState.u,outState.v,outState.orientation);
 float field=dw_geometry(outState DW_OP_ARGUMENT);
 float phase=DW_OP(1u).phase+0.01*dw_apply(outState,DW_OP(1u),field)+cfg.epsilon*((j!=0u)?1.0:-1.0)+0.02*dw_apply(outState,DW_OP(17u),field)+0.01*dw_apply(outState,DW_OP(15u),s.energy)+0.01*dw_apply(outState,DW_OP(24u),field);
 float ar=(s.ar+s.br)*0.7071067811865475244,ai=(s.ai+s.bi)*0.7071067811865475244;
 float br=(s.ar-s.br)*0.7071067811865475244,bi=(s.ai-s.bi)*0.7071067811865475244;
 float cs=dw_cos(phase),sn=dw_sin(phase);
 outState.ar=cs*ar-sn*ai;outState.ai=sn*ar+cs*ai;
 outState.br=cs*br+sn*bi;outState.bi=-sn*br+cs*bi;
 float angle=outState.theta+DW_OP(19u).phase+0.01*dw_apply(outState,DW_OP(19u),field),shear=DW_OP(19u).shear;
 cs=dw_cos(angle);sn=dw_sin(angle);
 float t00=cs,t01=cs*shear-sn,t10=sn,t11=sn*shear+cs;
 float det=t00*t11-t01*t10;
 outState.inv00=t11/det;outState.inv01=-t01/det;outState.inv10=-t10/det;outState.inv11=t00/det;
 outState.phaseResponse=dw_apply(outState,DW_OP(18u),outState.inv00*field+outState.inv01*outState.delta);
 float history=dw_apply(outState,DW_OP(23u),k1.v+k2.v+k3.v+k4.v+float(j)+outState.phaseResponse);
 outState.history=cfg.historyWeight*s.history+(1.0-cfg.historyWeight)*history;
 outState.field=field;outState.energy=outState.ar*outState.ar+outState.ai*outState.ai+outState.br*outState.br+outState.bi*outState.bi;
 outState.k1v=k1.v;outState.k2v=k2.v;outState.k3v=k3.v;outState.k4v=k4.v;
 outState.rng=rng;outState.route=selected;outState.alpha_ref=lane;
 outState.previousPreviousTheta=s.previousTheta;outState.previousTheta=s.theta;outState.lastJitter=float(j);
 dw_embedding(outState);return outState;
}
