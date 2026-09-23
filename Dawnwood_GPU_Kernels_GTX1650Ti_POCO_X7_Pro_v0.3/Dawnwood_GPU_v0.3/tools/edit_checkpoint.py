"""Inspect/edit actual numerical operator records in a saved .dwk checkpoint."""
from pathlib import Path
import argparse,json,math,struct
FIELDS=['u','v','radius','height','phase','gain','coupling','shear','du','dv','mutationRate','reserved','program','seed','kind','flags']
def validate_checkpoint(data):
    """Validate the shared 0003 storage ABI before inspecting or editing records."""
    if len(data)<80 or data[:8]!=b'DWKN0003' or struct.unpack_from('<II',data,8)!=(128,64):
        raise ValueError('Checkpoint header/ABI mismatch')
    cfg=struct.unpack_from('<4I4f4I4f',data,16)
    count,ops,epoch,depth=cfg[:4]
    if not count or ops<31 or depth>30 or (1<<(depth+1))-1>ops:
        raise ValueError('Invalid count/operator count/tree depth')
    if any(not math.isfinite(cfg[i]) for i in (4,5,6,7,12,13,14,15)) or cfg[4]<=0 or not 0<=cfg[14]<=1 or cfg[8]>1 or cfg[9]>1:
        raise ValueError('Invalid numerical profile')
    if len(data)!=80+count*128+ops*64:
        raise ValueError('Checkpoint size mismatch')
    for i in range(count):
        state=struct.unpack_from('<24f4I4f',data,80+i*128)
        if any(not math.isfinite(x) for x in state[:24]+state[28:]):
            raise ValueError('Nonfinite state['+str(i)+']')
        if not (0<=state[0]<1 and 0<=state[1]<1 and state[25]<=1 and state[26]<ops and state[27]==i and state[31] in (0,1)):
            raise ValueError('Invalid chart, orientation, route, inverse reference or jitter in state['+str(i)+']')
    for i in range(ops):
        op=struct.unpack_from('<12f4I',data,80+count*128+i*64)
        if any(not math.isfinite(x) for x in op[:12]):
            raise ValueError('Nonfinite operator['+str(i)+']')
        if not (0<=op[0]<1 and 0<=op[1]<1 and op[2]>0 and op[3]>0):
            raise ValueError('Invalid chart or shape dimensions in operator['+str(i)+']')
        if any(((op[12]>>(4*k))&15)>8 for k in range(8)):
            raise ValueError('Unknown bytecode instruction in operator['+str(i)+']')
    return count,ops

def main():
    p=argparse.ArgumentParser();p.add_argument('checkpoint',type=Path);p.add_argument('--index',type=int,required=True);p.add_argument('--set',type=Path,help='JSON object of field/value replacements');p.add_argument('--out',type=Path);a=p.parse_args()
    b=bytearray(a.checkpoint.read_bytes())
    count,ops=validate_checkpoint(b)
    if not 0<=a.index<ops:raise ValueError('Checkpoint operator index out of range')
    offset=80+count*128+a.index*64;values=list(struct.unpack_from('<12f4I',b,offset));record=dict(zip(FIELDS,values))
    if a.set:
        changes=json.loads(a.set.read_text())
        if not isinstance(changes,dict):raise ValueError('Field replacements must be a JSON object')
        if not a.out:raise ValueError('--out is required when changing a checkpoint')
        for field,value in changes.items():
            if field not in record:raise ValueError('Unknown operator field: '+field)
            if field in FIELDS[12:]:
                if isinstance(value,str):value=int(value,0)
                if type(value) is not int or not 0<=value<2**32:raise ValueError('Integer fields require uint32')
            elif type(value) not in (int,float) or not math.isfinite(value):raise ValueError('Finite numerical fields required')
            record[field]=value
        if record['radius']<=0 or record['height']<=0:raise ValueError('Shape radius and height must be positive')
        if any((record['program']>>(4*i))&15>8 for i in range(8)):raise ValueError('Unknown bytecode instruction')
        struct.pack_into('<12f4I',b,offset,*[record[k] for k in FIELDS])
        validate_checkpoint(b)
        a.out.write_bytes(b)
        record=dict(zip(FIELDS,struct.unpack_from('<12f4I',b,offset)))
    print(json.dumps({'operator_index':a.index,'record':record},indent=2))
if __name__=='__main__':main()
