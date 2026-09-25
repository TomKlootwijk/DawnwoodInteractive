// DWI-XIR-0.2 additional portable FP32 functions, shared by C++ and GLSL.
// Include numeric_types.inc before this file. Do not include it a second time.
// See docs/SOURCE_MATH_V2.md at the repository root for domains and accuracy.
// These are explicit numerical bindings, not equations recovered from a PDF.
#ifndef DW_SOURCE_MATH_V2_INCLUDED
#define DW_SOURCE_MATH_V2_INCLUDED

DW_FN bool dw_source_log_valid(float x){
 uint bits=dw_float_bits(x),exponent=(bits>>23u)&255u;
 return (bits&0x80000000u)==0u&&exponent!=0u&&exponent!=255u;
}

DW_FN float dw_source_log(float x){
 if(!dw_source_log_valid(x))DW_RETURN_FLOAT(dw_bits_float(0x7fc00000u));
 uint bits=dw_float_bits(x);
 int exponent=int((bits>>23u)&255u)-127;
 DW_PRECISE float m=dw_bits_float((bits&0x7fffffu)|0x3f800000u);
 if(m>1.41421356237309504880f){m=m*0.5f;++exponent;}
 // |z| <= (sqrt(2)-1)/(sqrt(2)+1), approximately 0.171573.
 // log(m) = 2*atanh(z), evaluated through the term z^13/13.
 DW_PRECISE float z=dw_div(m-1.0f,m+1.0f),square=z*z;
 DW_PRECISE float polynomial=0.07692307692307692308f;
 polynomial=0.09090909090909090909f+square*polynomial;
 polynomial=0.11111111111111111111f+square*polynomial;
 polynomial=0.14285714285714285714f+square*polynomial;
 polynomial=0.2f+square*polynomial;
 polynomial=0.33333333333333333333f+square*polynomial;
 DW_PRECISE float twice=2.0f*z;
 DW_PRECISE float log_m=twice+(twice*square)*polynomial;
 DW_PRECISE float ef=float(exponent);
 DW_PRECISE float low=log_m+ef*0.000001428606765330187045f;
 DW_RETURN_FLOAT(ef*0.693145751953125f+low);
}

DW_FN bool dw_source_atan2_valid(float y,float x){
 uint ay=dw_float_bits(y)&0x7fffffffu,ax=dw_float_bits(x)&0x7fffffffu;
 bool valid_y=ay==0u||(ay>=0x00800000u&&ay<0x7f800000u);
 bool valid_x=ax==0u||(ax>=0x00800000u&&ax<0x7f800000u);
 return valid_y&&valid_x&&(ay!=0u||ax!=0u);
}

DW_FN float dw_source_atan2(float y,float x){
 if(!dw_source_atan2_valid(y,x))DW_RETURN_FLOAT(dw_bits_float(0x7fc00000u));
 uint y_bits=dw_float_bits(y),x_bits=dw_float_bits(x);
 uint y_sign=y_bits&0x80000000u,x_sign=x_bits&0x80000000u;
 uint ay_bits=y_bits&0x7fffffffu,ax_bits=x_bits&0x7fffffffu;
 // Explicit bit construction preserves signed zero on both C++ and GLSL.
 if(ay_bits==0u)DW_RETURN_FLOAT(dw_bits_float(y_sign|(x_sign==0u?0u:0x40490fdbu)));
 if(ax_bits==0u)DW_RETURN_FLOAT(dw_bits_float(y_sign|0x3fc90fdbu));
 DW_PRECISE float ay=dw_bits_float(ay_bits),ax=dw_bits_float(ax_bits);
 bool swapped=ay_bits>ax_bits;
 DW_PRECISE float ratio=swapped?dw_div(ax,ay):dw_div(ay,ax);
 uint ratio_bits=dw_float_bits(ratio);
 DW_PRECISE float angle=ratio;
 // At small ratios the cubic correction is less than 0.34 ULP. This branch
 // also preserves a subnormal quotient as bits without arithmetic on it.
 if(ratio_bits>0x39800000u){
  bool reduced=ratio>0.41421356237309504880f;
  DW_PRECISE float t=reduced?dw_div(ratio-1.0f,ratio+1.0f):ratio;
  DW_PRECISE float square=t*t,polynomial=0.04761904761904761905f;
  polynomial=-0.05263157894736842105f+square*polynomial;
  polynomial=0.05882352941176470588f+square*polynomial;
  polynomial=-0.06666666666666666667f+square*polynomial;
  polynomial=0.07692307692307692308f+square*polynomial;
  polynomial=-0.09090909090909090909f+square*polynomial;
  polynomial=0.11111111111111111111f+square*polynomial;
  polynomial=-0.14285714285714285714f+square*polynomial;
  polynomial=0.2f+square*polynomial;
  polynomial=-0.33333333333333333333f+square*polynomial;
  angle=t+(t*square)*polynomial;
  if(reduced)angle=(angle+0.0000000377489470793079817668f)+0.78539812564849853515625f;
 }
 if(swapped)angle=(1.5707962512969970703125f-angle)+0.0000000754978941586159635335f;
 if(x_sign!=0u)angle=(3.141592502593994140625f-angle)+0.000000150995788317231927067f;
 DW_RETURN_FLOAT(dw_bits_float(dw_float_bits(angle)|y_sign));
}

#endif
