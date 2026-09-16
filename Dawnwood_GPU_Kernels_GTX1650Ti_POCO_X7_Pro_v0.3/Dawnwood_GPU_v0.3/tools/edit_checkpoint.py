"""Inspect/edit actual numerical operator records in a saved .dwk checkpoint."""
from pathlib import Path
import argparse,json,math,struct
FIELDS=['u','v','radius','height','phase','gain','coupling','shear','du','dv','mutationRate','reserved','program','seed','kind','flags']
def main():
    p=argparse.ArgumentParser();p.add_argument('checkpoint',type=Path);p.add_argument('--index',type=int,required=True);p.add_argument('--set',type=Path,help='JSON object of field/value replacements');p.add_argument('--out',type=Path);a=p.parse_args()
    b=bytearray(a.checkpoint.read_bytes())
    if b[:8]!=b'DWKN0003' or struct.unpack_from('<II',b,8)!=(128,64):raise ValueError('Checkpoint ABI mismatch')
    count,ops=struct.unpack_from('<II',b,16)
    if len(b)!=80+count*128+ops*64 or not 0<=a.index<ops:raise ValueError('Checkpoint size/index mismatch')
    offset=80+count*128+a.index*64;values=list(struct.unpack_from('<12f4I',b,offset));record=dict(zip(FIELDS,values))
    if a.set:
        changes=json.loads(a.set.read_text())
        if not a.out:raise ValueError('--out is required when changing a checkpoint')
        for field,value in changes.items():
            if field not in record:raise ValueError('Unknown operator field: '+field)
            if field in FIELDS[12:]:
                if isinstance(value,str):value=int(value,0)
                if type(value) is not int or not 0<=value<2**32:raise ValueError('Integer fields require uint32')
            elif not isinstance(value,(int,float)) or not math.isfinite(value):raise ValueError('Finite numerical fields required')
            record[field]=value
        if record['radius']<=0 or record['height']<=0:raise ValueError('Shape radius and height must be positive')
        if any((record['program']>>(4*i))&15>8 for i in range(8)):raise ValueError('Unknown bytecode instruction')
        struct.pack_into('<12f4I',b,offset,*[record[k] for k in FIELDS]);a.out.write_bytes(b)
    print(json.dumps({'operator_index':a.index,'record':record},indent=2))
if __name__=='__main__':main()
