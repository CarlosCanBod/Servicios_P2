"""Evalúa recortes de cara del vídeo en el entorno separado de DeepFace."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import cv2
from tutor.expression import ExpressionDetector

p=argparse.ArgumentParser(); p.add_argument('--vision',default='resultados/vision_video.json'); p.add_argument('--output',default='resultados/expresion_video.json'); a=p.parse_args()
data=json.loads(Path(a.vision).read_text()); video=data['summary']['input']; cap=cv2.VideoCapture(video)
if not cap.isOpened(): p.error('No se pudo abrir vídeo')
if hashlib.sha256(Path(video).read_bytes()).hexdigest()!=data['summary']['input_sha256']: p.error('El vídeo difiere del diagnóstico de visión')
start=time.perf_counter(); detector=ExpressionDetector(); startup=time.perf_counter()-start
rows=[]; next_t=0.
try:
 for obs in data['observations']:
  if not obs['face'] or obs['time_s']+1e-8<next_t: continue
  next_t=obs['time_s']+1.
  cap.set(cv2.CAP_PROP_POS_MSEC,obs['time_s']*1000); ok,frame=cap.read()
  if not ok: continue
  width=data['summary']['config']['width']; frame=cv2.resize(frame,(width,round(frame.shape[0]*width/frame.shape[1])))
  x0,y0,x1,y1=obs['bbox']; rows.append(asdict(detector.analyze(frame[y0:y1,x0:x1],obs['time_s'],obs['user_id'])))
finally: cap.release()
summary={'command':sys.argv,'input':video,'input_sha256':data['summary']['input_sha256'],'startup_s':startup,
 'samples':len(rows),'errors':sum(bool(r['error']) for r in rows),'note':'Etiquetas de expresión, sin verdad de referencia ni precisión medida.'}
Path(a.output).write_text(json.dumps({'summary':summary,'expressions':rows},indent=2,ensure_ascii=False)); print(json.dumps({'summary':summary,'expressions':rows},indent=2,ensure_ascii=False))
