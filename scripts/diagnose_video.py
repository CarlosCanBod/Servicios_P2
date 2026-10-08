"""Muestreo reproducible de visión: no mide exactitud sin anotaciones humanas."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import cv2
import numpy as np
from tutor.config import Config
from tutor.vision import Perception
from tutor.attention import AttentionFilter

p=argparse.ArgumentParser(); p.add_argument('--input',default='video.mp4'); p.add_argument('--output',default='resultados/vision_video.json'); p.add_argument('--config',default='config.json')
a=p.parse_args(); c=Config.load(a.config); cap=cv2.VideoCapture(a.input)
if not cap.isOpened(): p.error('No se pudo abrir el vídeo')
fps=cap.get(cv2.CAP_PROP_FPS)
if not np.isfinite(fps) or fps<=0: p.error('FPS inválidos')
rows=[]; af=AttentionFilter(c); perception=Perception(c); n=0; next_t=0.; start=time.perf_counter()
try:
 while True:
  ok,frame=cap.read()
  if not ok: break
  t=n/fps; n+=1
  if t+1e-8<next_t: continue
  next_t=t+c.sample_s
  frame=cv2.resize(frame,(c.width,round(frame.shape[0]*c.width/frame.shape[1])))
  obs,crop=perception.process(frame,t)
  status,reason=af.update(obs,t)
  rows.append({**asdict(obs),'attention':status.value,'attention_reason':reason})
finally:
 cap.release(); perception.close()
lat=[r['latency_ms'] for r in rows]
summary={'command':sys.argv,'input':a.input,'input_sha256':hashlib.sha256(Path(a.input).read_bytes()).hexdigest(),
 'config':c.to_dict(),'decoded_frames':n,'fps':fps,'duration_s':n/fps,'samples':len(rows),
 'elapsed_s':time.perf_counter()-start,'latency_median_ms':float(np.median(lat)),'latency_p95_ms':float(np.percentile(lat,95)),
 'face_samples':sum(r['face'] for r in rows),'hand_positive_samples':sum(r['hand_up'] is True for r in rows),
 'attention_counts':{s:sum(r['attention']==s for r in rows) for s in ['atiende','no_atiende','desconocida']},
 'warning':'Recuentos de salidas; no son porcentajes de acierto. Sin etiquetas de referencia.'}
Path(a.output).parent.mkdir(parents=True,exist_ok=True); Path(a.output).write_text(json.dumps({'summary':summary,'observations':rows},indent=2,ensure_ascii=False))
print(json.dumps(summary,indent=2,ensure_ascii=False))
