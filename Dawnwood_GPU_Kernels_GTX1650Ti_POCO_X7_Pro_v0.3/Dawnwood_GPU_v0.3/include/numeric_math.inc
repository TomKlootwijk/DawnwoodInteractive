// DWI-N1-0.5 portable FP32 elementary functions. See docs/PORTABLE_MATH_v0.5.md.
// These are explicit approximations to the same real functions, not device-native
// sin/cos/exp instructions. Basic operations must not contract or reassociate.
// Division and square root use the device primitive only as an estimate. Exact
// integer products correct that estimate before round-to-nearest/even encoding.
DW_FN void dw_normal_mantissa(uint bits,DW_INOUT(uint) mantissa,DW_INOUT(int) exponent){
 exponent=int((bits>>23u)&255u);mantissa=bits&0x7fffffu;
 if(exponent!=0){mantissa|=0x800000u;return;}
 exponent=1;DW_LOOP while(mantissa<0x800000u){mantissa<<=1u;--exponent;}
}
DW_FN bool dw_wide_above(uint ah,uint al,uint bh,uint bl){return ah>bh||(ah==bh&&al>bl);}
DW_FN float dw_div(float a,float b){
 uint ab=dw_float_bits(a),bb=dw_float_bits(b),sign=(ab^bb)&0x80000000u;
 ab&=0x7fffffffu;bb&=0x7fffffffu;
 if(ab>0x7f800000u||bb>0x7f800000u||(ab==0u&&bb==0u)||(ab==0x7f800000u&&bb==0x7f800000u))DW_RETURN_FLOAT(dw_bits_float(0x7fc00000u));
 if(ab==0x7f800000u||bb==0u)DW_RETURN_FLOAT(dw_bits_float(sign|0x7f800000u));
 if(ab==0u||bb==0x7f800000u)DW_RETURN_FLOAT(dw_bits_float(sign));
 uint ma,mb;int ea,eb;dw_normal_mantissa(ab,ma,ea);dw_normal_mantissa(bb,mb,eb);
 bool lower=ma<mb;uint shift=lower?24u:23u;int exponent=ea-eb+127-int(lower);
 DW_PRECISE float estimate=float(ma)/float(mb);
 DW_PRECISE float scaled=estimate*(lower?16777216.0f:8388608.0f);
 uint q=uint(scaled),ph,pl;dw_mul_wide(q,mb,ph,pl);
 uint th=ma>>(32u-shift),tl=ma<<shift;
 DW_LOOP while(dw_wide_above(ph,pl,th,tl)){--q;uint old=pl;pl-=mb;ph-=uint(old<mb);}
 uint rl=tl-pl,rh=th-ph-uint(tl<pl);
 DW_LOOP while(rh!=0u||rl>=mb){++q;uint old=rl;rl-=mb;rh-=uint(old<mb);}
 if(exponent<=0){
  if(exponent< -23)DW_RETURN_FLOAT(dw_bits_float(sign));
  shift=uint(1-exponent);uint result=q>>shift,tail=q&((1u<<shift)-1u),midpoint=1u<<(shift-1u);
  result+=uint(tail>midpoint||(tail==midpoint&&(rl!=0u||(result&1u)!=0u)));
  DW_RETURN_FLOAT(dw_bits_float(sign|result));
 }
 uint twice=rl<<1u;q+=uint(twice>mb||(twice==mb&&(q&1u)!=0u));
 if(q==0x1000000u){q>>=1u;++exponent;}
 if(exponent>=255)DW_RETURN_FLOAT(dw_bits_float(sign|0x7f800000u));
 DW_RETURN_FLOAT(dw_bits_float(sign|(uint(exponent)<<23u)|(q&0x7fffffu)));
}
DW_FN float dw_sqrt(float x){
 uint bits=dw_float_bits(x),absolute=bits&0x7fffffffu;
 if(absolute==0u)DW_RETURN_FLOAT(x);
 if(bits==0x7f800000u)DW_RETURN_FLOAT(x);
 if((bits&0x80000000u)!=0u||absolute>0x7f800000u)DW_RETURN_FLOAT(dw_bits_float(0x7fc00000u));
 uint mantissa;int e;dw_normal_mantissa(absolute,mantissa,e);e-=127;
 uint odd=uint((e%2)!=0);int exponent=(e-int(odd))/2+127;
 mantissa<<=odd;
 DW_PRECISE float normalized=float(mantissa)*0.00000011920928955078125f;
 DW_PRECISE float estimate=dw_native_sqrt(normalized)*8388608.0f;
 uint q=uint(estimate),ph,pl;dw_mul_wide(q,q,ph,pl);
 uint th=mantissa>>9u,tl=mantissa<<23u;
 DW_LOOP while(dw_wide_above(ph,pl,th,tl)){--q;dw_mul_wide(q,q,ph,pl);}
 DW_LOOP while(true){uint next=q+1u,nh,nl;dw_mul_wide(next,next,nh,nl);if(dw_wide_above(nh,nl,th,tl))break;q=next;ph=nh;pl=nl;}
 // Exact remainder is an integer. The midpoint square is q*q+q+1/4,
 // so equality is impossible and remainder>q means round upward.
 uint remainder=tl-pl;q+=uint(remainder>q);
 if(q==0x1000000u){q>>=1u;++exponent;}
 DW_RETURN_FLOAT(dw_bits_float((uint(exponent)<<23u)|(q&0x7fffffu)));
}
// 256 fractional bits of 2/pi, least-significant word first; mathematical constant.
DW_FN uint dw_two_over_pi_word(uint i){
 if(i==0u)return 0xdebbc561u;if(i==1u)return 0xfe5163abu;
 if(i==2u)return 0x3c439041u;if(i==3u)return 0xdb629599u;
 if(i==4u)return 0xf534ddc0u;if(i==5u)return 0xfc2757d1u;
 if(i==6u)return 0x4e441529u;return 0xa2f9836eu;
}
DW_FN float dw_trig_reduce(float x,DW_INOUT(uint) quadrant){
 DW_PRECISE float ax=dw_abs(x);
 if(ax<=128.0f){
  DW_PRECISE float n=dw_floor(ax*0.63661977236758134308f+0.5f);
  quadrant=uint(n)&3u;
  // Short-significand split constants keep products exact in this branch.
  DW_PRECISE float r=ax-n*1.5703125f;
  r-=n*0.0004837512969970703125f;
  r-=n*0.0000000754978941586159635335f;
  DW_RETURN_FLOAT(r);
 }
 uint bits=dw_float_bits(ax),exponent=(bits>>23u)&255u;
 if(exponent==255u){quadrant=0u;DW_RETURN_FLOAT(dw_bits_float(0x7fc00000u));}
 uint mantissa=(bits&0x7fffffu)|0x800000u,product[9],carry=0u;
 DW_LOOP for(uint i=0u;i<8u;++i){uint hi,lo;dw_mul_wide(dw_two_over_pi_word(i),mantissa,hi,lo);uint sum=lo+carry;hi+=uint(sum<lo);product[i]=sum;carry=hi;}
 product[8]=carry;
 // ax=mantissa*2^(unbiasedExponent-23), hence this binary-point position.
 uint point=406u-exponent,word=point>>5u,offset=point&31u;
 uint integral=product[word]>>offset;
 if(offset>30u)integral|=product[word+1u]<<(32u-offset);
 uint roundBit=(product[(point-1u)>>5u]>>((point-1u)&31u))&1u;
 quadrant=(integral+roundBit)&3u;
 if(roundBit!=0u){
  // Exact complement before conversion avoids cancellation near an integer.
  carry=1u;DW_LOOP for(uint i=0u;i<9u;++i){uint p=~product[i],sum=p+carry;product[i]=sum;carry=uint(sum<p);}
 }
 uint start=point-24u;word=start>>5u;offset=start&31u;
 uint first=product[word]>>offset;if(offset>8u)first|=product[word+1u]<<(32u-offset);first&=0xffffffu;
 start=point-48u;word=start>>5u;offset=start&31u;
 uint second=product[word]>>offset;if(offset>8u)second|=product[word+1u]<<(32u-offset);second&=0xffffffu;
 DW_PRECISE float fraction=float(first)*0.000000059604644775390625f+float(second)*0.000000000000003552713678800500929355621337890625f;
 DW_PRECISE float r=fraction*1.5707962512969970703125f;
 r+=fraction*0.0000000754978941586159635335f;
 DW_RETURN_FLOAT(roundBit!=0u?-r:r);
}
DW_FN float dw_sin_poly(float r){
 DW_PRECISE float z=r*r,p=1.0f/6227020800.0f;
 p=-1.0f/39916800.0f+z*p;p=1.0f/362880.0f+z*p;
 p=-1.0f/5040.0f+z*p;p=1.0f/120.0f+z*p;p=-1.0f/6.0f+z*p;
 DW_RETURN_FLOAT(r+(r*z)*p);
}
DW_FN float dw_cos_poly(float r){
 DW_PRECISE float z=r*r,p=1.0f/479001600.0f;
 p=-1.0f/3628800.0f+z*p;p=1.0f/40320.0f+z*p;
 p=-1.0f/720.0f+z*p;p=1.0f/24.0f+z*p;p=-0.5f+z*p;
 DW_RETURN_FLOAT(1.0f+z*p);
}
DW_FN float dw_sin(float x){
 uint q;DW_PRECISE float r=dw_trig_reduce(x,q);
 DW_PRECISE float result=(q&1u)!=0u?dw_cos_poly(r):dw_sin_poly(r);
 if((q&2u)!=0u)result=-result;
 if((dw_float_bits(x)&0x80000000u)!=0u)result=-result;
 DW_RETURN_FLOAT(result);
}
DW_FN float dw_cos(float x){
 uint q;DW_PRECISE float r=dw_trig_reduce(x,q);
 DW_PRECISE float result=(q&1u)!=0u?dw_sin_poly(r):dw_cos_poly(r);
 if(((q+1u)&2u)!=0u)result=-result;
 DW_RETURN_FLOAT(result);
}
DW_FN float dw_exp(float x){
 uint xb=dw_float_bits(x);
 if((xb&0x7fffffffu)>0x7f800000u)DW_RETURN_FLOAT(dw_bits_float(0x7fc00000u));
 if(x>=88.72283935546875f)DW_RETURN_FLOAT(dw_bits_float(0x7f800000u));
 if(x<=-103.97208404541015625f)DW_RETURN_FLOAT(0.0f);
 DW_PRECISE float nf=dw_floor(x*1.4426950408889634074f+0.5f);
 int n=int(nf);DW_PRECISE float r=x-nf*0.693145751953125f;
 r-=nf*0.000001428606765330187045f;
 DW_PRECISE float p=1.0f/40320.0f;
 p=1.0f/5040.0f+r*p;p=1.0f/720.0f+r*p;p=1.0f/120.0f+r*p;
 p=1.0f/24.0f+r*p;p=1.0f/6.0f+r*p;p=0.5f+r*p;p=1.0f+r*p;p=1.0f+r*p;
 uint pb=dw_float_bits(p);int exponent=int((pb>>23u)&255u)+n;
 if(exponent>=255)DW_RETURN_FLOAT(dw_bits_float(0x7f800000u));
 if(exponent>0)DW_RETURN_FLOAT(dw_bits_float((pb&0x7fffffu)|(uint(exponent)<<23u)));
 // Build subnormal results as bits, round-to-nearest/even. Later arithmetic may FTZ.
 uint shift=uint(1-exponent),mantissa=(pb&0x7fffffu)|0x800000u;
 if(shift>24u)DW_RETURN_FLOAT(0.0f);
 uint outBits=mantissa>>shift,remainder=mantissa&((1u<<shift)-1u),halfway=1u<<(shift-1u);
 outBits+=uint(remainder>halfway||(remainder==halfway&&(outBits&1u)!=0u));
 DW_RETURN_FLOAT(dw_bits_float(outBits));
}
