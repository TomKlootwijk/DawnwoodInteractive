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
    """Legacy v0.3/v0.4 full-staging buffer model, retained for old evidence."""
    if count<=0 or operators<31:raise ValueError('Positive count and at least 31 operators required')
    state,ops=count*128,operators*64
    return {'model':'legacy_v0.3_v0.4_buffer_payload',
            'current_runtime_model':False,
            'state_record_bytes':128,'operator_record_bytes':64,
            'two_state_buffers':2*state,'two_operator_buffers':2*ops,
            'reused_host_visible_staging':max(state,ops),
            'buffer_payload_total':2*state+2*ops+max(state,ops),
            'implicit_child_pointer_bytes':0,
            'comparison_two_uint32_child_pointers_per_operator':8*operators,
            'excluded':'driver allocation padding, pipelines, command buffers, runtime, OS and other applications'}

def memory_model_v05(count:int,operators:int=31,*,max_image_dimension_2d:int|None=None,
                     split_evolution:bool=False,state_dispatch_limit:int=65536)->dict:
    """v0.5 resource payload arithmetic, not measured Vulkan allocations.

    Match the runtime's four RGBA32_UINT texels per operator, at most 256
    operators per row, reusable staging capped at 16 MiB, and optional bounded
    split-evolution scratch (96 bytes per active chunk state). Supplying the
    probed image dimension applies that limit; omitting it models the normal
    256-record row cap without asserting device capability.
    """
    if type(count) is not int or type(operators) is not int or count<=0 or operators<31:
        raise ValueError('Positive integer count and at least 31 integer operators required')
    if type(split_evolution) is not bool or type(state_dispatch_limit) is not int or not 0<state_dispatch_limit<=65536:
        raise ValueError('Split evolution requires a bool; state dispatch limit must be 1..65536')
    per_row=min(256,operators)
    if max_image_dimension_2d is not None:
        if type(max_image_dimension_2d) is not int or max_image_dimension_2d<4:
            raise ValueError('Image dimension must hold four texels per operator')
        per_row=min(per_row,max_image_dimension_2d//4)
    width=per_row*4
    height=(operators+per_row-1)//per_row
    if max_image_dimension_2d is not None and height>max_image_dimension_2d:
        raise ValueError('Operator LUT exceeds maxImageDimension2D')
    state,ops=count*128,operators*64
    image=width*height*16
    staging=min(16*1024*1024,max(state,image))
    scratch=min(count,state_dispatch_limit)*96 if split_evolution else 0
    return {'model':'v0.5_integer_LUT_and_bounded_staging_payload',
            'current_runtime_model':True,'measured_allocation':False,
            'state_record_bytes':128,'operator_record_bytes':64,
            'two_state_buffers':2*state,'two_operator_record_payloads':2*ops,
            'operator_lut_format':'RGBA32_UINT','operator_lut_width':width,
            'operator_lut_height':height,'operator_lut_texels_per_record':4,
            'max_image_dimension_2d':max_image_dimension_2d,
            'two_operator_image_texel_payloads':2*image,
            'two_operator_images_unused_row_texel_bytes':2*(image-ops),
            'reused_host_visible_staging':staging,'staging_cap_bytes':16*1024*1024,
            'split_evolution':split_evolution,'state_dispatch_limit':state_dispatch_limit,
            'evolution_scratch_record_bytes':96,'evolution_scratch_bytes':scratch,
            'buffer_payload_total':2*state+staging+scratch,
            'image_texel_payload_total':2*image,
            'resource_payload_total':2*state+staging+scratch+2*image,
            'one_host_snapshot_payload':state+ops,
            'host_snapshot_note':'Separate CPU vector payload, excluded from resource total; run releases the initial snapshot before readback. Verification retains additional snapshots.',
            'implicit_child_pointer_bytes':0,
            'comparison_two_uint32_child_pointers_per_operator':8*operators,
            'excluded':'Vulkan allocation alignment and image tiling, driver/compiler/pipeline memory, command buffers, host snapshots, runtime, OS and other applications',
            'authority':'Use actual device allocated_buffer_bytes, allocated_image_bytes, allocated_total_bytes and per-heap reports for measured Vulkan allocation; this model does not prove fit.'}

BAYER4=((0,8,2,10),(12,4,14,6),(3,11,1,9),(15,7,13,5))
def bayer(value:float,x:int,y:int)->int:
    if not math.isfinite(value) or not 0<=value<=1:raise ValueError('Display input must be in [0,1]')
    return int(value >= (BAYER4[y%4][x%4]+.5)/16)
