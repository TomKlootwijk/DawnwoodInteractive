"""Export downstream RGBA-role values and Bayer bits from an actual checkpoint."""
from pathlib import Path
import argparse,csv,struct
from packing import bayer
from edit_checkpoint import validate_checkpoint

def main():
    p=argparse.ArgumentParser();p.add_argument('checkpoint',type=Path);p.add_argument('--out',type=Path,required=True);p.add_argument('--width',type=int,default=64);a=p.parse_args()
    if a.width<1:raise ValueError('Positive display width required')
    data=a.checkpoint.read_bytes()
    count,ops=validate_checkpoint(data)
    with a.out.open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['index','R_intensity','G_intensity','B_history','A_inverse_reference','inverse_00','inverse_01','inverse_10','inverse_11','Bayer_R_fraction'])
        for i in range(count):
            values=struct.unpack_from('<24f4I4f',data,80+128*i)
            red=values[4]**2+values[5]**2;green=values[6]**2+values[7]**2;total=red+green
            value=red/total if total else 0.
            w.writerow([i,red,green,values[8],values[27],values[9],values[10],values[11],values[12],bayer(value,i%a.width,i//a.width)])
    print(a.out)
if __name__=='__main__':main()
