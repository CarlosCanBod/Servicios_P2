"""Ejecuta ejemplos originales con vídeo, sin alterar sus archivos ni abrir GUI."""
import argparse
import os
from pathlib import Path
import runpy
import time
import cv2

parser = argparse.ArgumentParser()
parser.add_argument('example', choices=['ejemplo0.py','ejemplo1.py','ejemplo2.py','ejemplo4.py'])
parser.add_argument('--frames',type=int,default=10)
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
original_capture=cv2.VideoCapture
class Video:
    def __init__(self,*unused):
        self.cap=original_capture(str(root/'p2data/video.mp4')); self.count=0
    def isOpened(self): return self.cap.isOpened()
    def read(self):
        if self.count >= args.frames: return False,None
        self.count+=1
        return self.cap.read()
    def release(self): self.cap.release()
cv2.VideoCapture=Video
cv2.imshow=lambda *args: None
cv2.waitKey=lambda *args: -1
cv2.destroyAllWindows=lambda: None
os.chdir(root/'p2data')
start=time.perf_counter()
runpy.run_path(str(root/'p2data'/args.example),run_name='__main__')
print(f'{args.example}: {args.frames} fotogramas, {time.perf_counter()-start:.3f} s; GUI sustituida, fuente vídeo')
