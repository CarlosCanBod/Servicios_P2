"""Prueba visual de UN subsistema. No graba imágenes ni ejecuta el diálogo."""
import argparse
from dataclasses import asdict
import json
import os
import math
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import cv2
import mediapipe as mp
from PIL import Image,ImageDraw,ImageFont
import numpy as np
from tutor.config import Config,ROOT
from tutor.geometry import head_geometry,eye_geometry
from tutor.vision import PrimaryUser
from tutor.workers import ExpressionWorker


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('detector',choices=['cara','ojos','manos','expresion'])
    parser.add_argument('--input',default='0')
    parser.add_argument('--config',default=str(ROOT/'config.json'))
    parser.add_argument('--max-seconds',type=float)
    parser.add_argument('--log')
    a=parser.parse_args()
    if a.max_seconds is not None and (not math.isfinite(a.max_seconds) or a.max_seconds<=0): parser.error('--max-seconds debe ser positivo y finito')
    if sys.platform.startswith('linux') and not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')): parser.error('Necesitas una sesión gráfica para probar un detector')
    try: c=Config.load(a.config)
    except (OSError,ValueError,TypeError) as exc: parser.error(str(exc))
    source=int(a.input) if a.input.isdecimal() else a.input
    cap=cv2.VideoCapture(source)
    if not cap.isOpened(): parser.error(f'No se pudo abrir la entrada {a.input}')
    model=None; expression=None; rows=[]; error=None; selected=PrimaryUser(c)
    v=mp.tasks.vision; base=mp.tasks.BaseOptions; mode=v.RunningMode.VIDEO
    user_id=0; frames=0; start=time.monotonic(); last_ms=-1; next_sample=0.; last_expr=-10.; exp=None
    if isinstance(source,str):
        fps=cap.get(cv2.CAP_PROP_FPS)
        if not np.isfinite(fps) or fps<=0: cap.release(); parser.error('Vídeo sin FPS válidos')
    try:
        if a.detector in ('cara','expresion'):
            model=v.FaceDetector.create_from_options(v.FaceDetectorOptions(base_options=base(model_asset_path=str(ROOT/'face_detector.task')),running_mode=mode,min_detection_confidence=c.face_confidence))
        elif a.detector=='ojos':
            model=v.FaceLandmarker.create_from_options(v.FaceLandmarkerOptions(base_options=base(model_asset_path=str(ROOT/'face_landmarker.task')),running_mode=mode,num_faces=1))
        else:
            model=v.HandLandmarker.create_from_options(v.HandLandmarkerOptions(base_options=base(model_asset_path=str(ROOT/'models/hand_landmarker.task')),running_mode=mode,num_hands=2))
        if a.detector=='expresion':
            expression=ExpressionWorker(ROOT/'.venv/bin/python')
            deadline=time.monotonic()+60
            while not expression.ready and not expression.error and time.monotonic()<deadline:
                expression.receive(); time.sleep(.02)
            if not expression.ready: raise RuntimeError(expression.error or 'Expresión no inicializada')
        start=time.monotonic()
        print(f'Prueba de {a.detector}. q: salir; r: reseleccionar cara. No se graba vídeo.',flush=True)
        while True:
            ok,frame=cap.read()
            if not ok:
                if isinstance(source,int): error='La cámara no entrega imágenes'
                break
            t=time.monotonic()-start if isinstance(source,int) else frames/fps
            frames+=1
            if isinstance(source,str): time.sleep(max(0,start+t-time.monotonic()))
            if frame.shape[1]!=c.width: frame=cv2.resize(frame,(c.width,round(frame.shape[0]*c.width/frame.shape[1])))
            h,w=frame.shape[:2]
            timestamp=max(last_ms+1,round(t*1000)); last_ms=timestamp
            img=mp.Image(image_format=mp.ImageFormat.SRGB,data=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB))
            tick=time.perf_counter(); result=model.detect_for_video(img,timestamp)
            metrics={}; lines=[]; bbox=None
            if a.detector in ('cara','expresion'):
                detections=result.detections
                boxes=[(max(0,d.bounding_box.origin_x),max(0,d.bounding_box.origin_y),min(w,d.bounding_box.origin_x+d.bounding_box.width),min(h,d.bounding_box.origin_y+d.bounding_box.height)) for d in detections]
                index=selected.select(boxes); metrics['caras']=len(boxes)
                if index is not None:
                    bbox=boxes[index]
                    pts=np.array([(p.x*w,p.y*h) for p in detections[index].keypoints])
                    frontal,values=head_geometry(pts,c); metrics.update(values); metrics['frontal']=frontal
                    if a.detector=='expresion' and t-last_expr>=c.emotion_period_s:
                        x0,y0,x1,y1=bbox; expression.submit((frame[y0:y1,x0:x1].copy(),t,user_id)); last_expr=t
                    for x,y in pts: cv2.circle(frame,(int(x),int(y)),3,(0,220,255),-1)
                else: metrics['estado']='Sin cara principal evaluable'
                if expression:
                    received=expression.receive()
                    if received and received.user_id==user_id: exp=received
                    valid=exp if exp and bbox and t-exp.time_s<=c.emotion_stale_s else None
                    metrics['expresion']=asdict(valid) if valid else None
                    label=valid.label if valid and not valid.error else 'no evaluable'
                    lines=[f'Expresión estimada: {label}', 'No es una certeza sobre la emoción ni la atención.',expression.error or '']
            elif a.detector=='ojos':
                if result.face_landmarks:
                    mesh=np.array([(p.x*w,p.y*h) for p in result.face_landmarks[0]])
                    opened,gaze,values=eye_geometry(mesh,c)
                    metrics.update(values); metrics.update(ojos_abiertos=opened,mirada_frontal=gaze)
                    for i in (33,133,159,145,362,263,386,374,468,473):
                        cv2.circle(frame,tuple(mesh[i].astype(int)),2,(0,220,255),-1)
                else: metrics['estado']='Sin malla de cara'
            else:
                metrics['manos']=len(result.hand_landmarks)
                for hand in result.hand_landmarks:
                    for p in hand: cv2.circle(frame,(int(p.x*w),int(p.y*h)),3,(0,220,255),-1)
                lines=['Aquí se comprueba detección de manos.', 'En el tutor se exige palma alta, dedos extendidos y una sola cara.']
            metrics['latency_ms']=(time.perf_counter()-tick)*1000
            if t>=next_sample:
                rows.append({'time_s':t,'metrics':metrics}); next_sample=t+c.sample_s
            if bbox: cv2.rectangle(frame,bbox[:2],bbox[2:],(50,220,110),2)
            if a.detector!='expresion':
                lines+=[' | '.join(f'{k}: {v:.3f}' if isinstance(v,float) else f'{k}: {v}' for k,v in list(metrics.items())[i:i+3]) for i in range(0,len(metrics),3)]
            canvas=Image.new('RGB',(max(960,w),h+220),(20,26,37)); canvas.paste(Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)))
            draw=ImageDraw.Draw(canvas); path='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
            font=ImageFont.truetype(path,17) if Path(path).exists() else ImageFont.load_default()
            draw.text((14,h+10),f'Detector: {a.detector} | q: salir | r: reseleccionar',font=font,fill='white')
            for i,line in enumerate(lines[:7]): draw.text((14,h+42+i*24),line,font=font,fill=(180,225,220))
            cv2.imshow(f'P2 - {a.detector}',cv2.cvtColor(np.asarray(canvas),cv2.COLOR_RGB2BGR))
            key=cv2.waitKey(1)&0xff
            if key in (ord('q'),27): break
            if key==ord('r'):
                selected=PrimaryUser(c); exp=None; user_id+=1
            if a.max_seconds and t>=a.max_seconds: break
    except (RuntimeError,OSError,ValueError) as exc:
        error=f'{type(exc).__name__}: {exc}'; print(error,file=sys.stderr)
    finally:
        cap.release(); cv2.destroyAllWindows()
        if model: model.close()
        if expression: expression.close()
        path=Path(a.log or ROOT/f'resultados/prueba_{a.detector}.json')
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps({'command':sys.argv,'config':c.to_dict(),'input':a.input,
            'detector':a.detector,'elapsed_s':time.monotonic()-start,'error':error,
            'manual_observation':None,'samples':rows},ensure_ascii=False,indent=2))
        print('Registro:',path,flush=True)
    return 2 if error else 0

if __name__=='__main__': raise SystemExit(main())
