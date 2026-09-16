"""BC5 storage experiment and full working-set accounting; Python standard library.

BC5 is two BC4 UNORM blocks. Each block stores two 8-bit endpoints followed by
16 three-bit selectors, little endian. This encoder deliberately uses min/max
endpoints; it is reproducible, not a production rate-distortion optimizer.
"""
from __future__ import annotations
import math
from typing import Sequence

def palette(a: int, b: int) -> list[float]:
    if not (0 <= a <= 255 and 0 <= b <= 255):
        raise ValueError('BC4 endpoints must be bytes')
    if a > b:
        return [a, b] + [((7-i)*a+i*b)/7 for i in range(1,7)]
    return [a, b] + [((5-i)*a+i*b)/5 for i in range(1,5)] + [0,255]

def encode_bc4(values: Sequence[int]) -> bytes:
    if len(values)!=16 or any(type(x) is not int or not 0<=x<=255 for x in values):
        raise ValueError('BC4 expects sixteen UNORM8 values')
    a,b=max(values),min(values); p=palette(a,b)
    packed=sum(min(range(8),key=lambda k:abs(p[k]-x)) << (3*i) for i,x in enumerate(values))
    return bytes([a,b])+packed.to_bytes(6,'little')

def decode_bc4(block: bytes) -> list[float]:
    if len(block)!=8:raise ValueError('BC4 blocks have eight bytes')
    p=palette(block[0],block[1]);v=int.from_bytes(block[2:],'little')
    return [p[(v>>(3*i))&7] for i in range(16)]

def encode_bc5(red: Sequence[int], green: Sequence[int]) -> bytes:
    return encode_bc4(red)+encode_bc4(green)

def decode_bc5(block: bytes) -> tuple[list[float],list[float]]:
    if len(block)!=16:raise ValueError('BC5 blocks have sixteen bytes')
    return decode_bc4(block[:8]),decode_bc4(block[8:])

def bc5_bytes(width:int,height:int,layers:int=1,mips:bool=False)->int:
    if any(type(v) is not int or v<=0 for v in (width,height,layers)):
        raise ValueError('Positive integer dimensions required')
    total=0
    while True:
        total+=16*((width+3)//4)*((height+3)//4)*layers
        if not mips or (width==height==1):return total
        width,height=max(1,width//2),max(1,height//2)

def memory_model(count:int,operators:int=31)->dict:
    if count<=0 or operators<31:raise ValueError('Positive count and at least 31 operators required')
    state,ops=count*128,operators*64
    return {'state_record_bytes':128,'operator_record_bytes':64,
            'two_state_buffers':2*state,'two_operator_buffers':2*ops,
            'reused_host_visible_staging':max(state,ops),
            'buffer_payload_total':2*state+2*ops+max(state,ops),
            'implicit_child_pointer_bytes':0,
            'comparison_two_uint32_child_pointers_per_operator':8*operators,
            'excluded':'driver allocation padding, pipelines, command buffers, runtime, OS and other applications'}

BAYER4=((0,8,2,10),(12,4,14,6),(3,11,1,9),(15,7,13,5))
def bayer(value:float,x:int,y:int)->int:
    if not math.isfinite(value) or not 0<=value<=1:raise ValueError('Display input must be in [0,1]')
    return int(value >= (BAYER4[y%4][x%4]+.5)/16)
