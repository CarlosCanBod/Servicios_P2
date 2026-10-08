"""Orquestación: captura/UI rápidas; percepción y expresión en procesos aislados."""
import argparse
from dataclasses import asdict
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
import cv2
from .attention import AttentionFilter, HandEdge
from .capture import Capture
from .config import Config, ROOT
from .dialogue import Dialogue
from .interface import render
from .signals import Attention
from .workers import Worker, vision_worker, ExpressionWorker


def main(argv=None):
    parser=argparse.ArgumentParser(description='Tutor visual P2. q: salir; r: nueva sesión.')
    parser.add_argument('--input',default='0',help='Índice de cámara o ruta de vídeo')
    parser.add_argument('--config',default=str(ROOT/'config.json'))
    parser.add_argument('--lesson',default=str(ROOT/'leccion.txt'))
    parser.add_argument('--headless',action='store_true',help='No abrir ventana; sí ejecutar todos los modelos')
    parser.add_argument('--no-emotion',action='store_true',help='Solo diagnóstico: omite expresión y su reacción')
    parser.add_argument('--emotion-python',default=str(ROOT/'.venv/bin/python'))
    parser.add_argument('--max-seconds',type=float,help='Límite en segundos de entrada')
    parser.add_argument('--log',default=str(ROOT/'resultados/sesion.json'))
    args=parser.parse_args(argv)
    if args.max_seconds is not None and (not math.isfinite(args.max_seconds) or args.max_seconds<=0): parser.error('--max-seconds debe ser positivo')
    try:
        config=Config.load(args.config)
        phrases=[line.strip() for line in Path(args.lesson).read_text().splitlines() if line.strip()]
        dialogue=Dialogue(config,phrases)
    except (OSError,ValueError,TypeError) as exc: parser.error(str(exc))
    source=int(args.input) if args.input.isdecimal() else args.input
    if not isinstance(source,int) and not Path(source).is_file(): parser.error(f'Entrada inexistente: {source}')
    if not args.headless and sys.platform.startswith('linux') and not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')):
        parser.error('No hay sesión gráfica. Utiliza --headless para diagnóstico.')
    vision=None; emotion=None; capture=None
    obs=None; expression=None; frame=None; user_id=0
    af=AttentionFilter(config); hand=HandEdge(config)
    rows=[]; expressions=[]; events=[]; errors=[]; ui_latencies=[]
    status=Attention.UNKNOWN; reason='inicializando'; stop_reason='error'; code=0
    start=time.monotonic(); last_submit=-1.; last_emotion=-1.; now=0.; finished_at=None
    try:
        vision=Worker(vision_worker,(config,))
        if not args.no_emotion:
            emotion=ExpressionWorker(Path(args.emotion_python).absolute())
        # Preparar los modelos antes de reproducir un vídeo corto evita perder su inicio.
        # El límite evita esperar indefinidamente una descarga fallida.
        while time.monotonic()-start<60:
            vision.receive()
            if emotion: emotion.receive()
            if vision.error: raise RuntimeError(f'Visión: {vision.error}')
            if emotion and emotion.error:
                errors.append(f'Expresión: {emotion.error}'); emotion.close(); emotion=None
            if vision.ready and (emotion is None or emotion.ready): break
            time.sleep(0.02)
        else: raise RuntimeError('Los modelos no se inicializaron en 60 segundos')
        capture=Capture(source,config.width)
        print('Tutor listo. Entrada:',args.input,flush=True)
        last_frame_wall=None
        while True:
            tick=time.perf_counter()
            packet=capture.read_latest()
            if packet:
                frame,frame_time,last_frame_wall=packet
                now=max(now,frame_time,time.monotonic()-capture.started)
                if frame_time-last_submit>=config.sample_s-1e-8:
                    vision.submit((frame.copy(),frame_time,user_id)); last_submit=frame_time
            elif last_frame_wall is not None:
                # En ausencia de nuevos frames el reloj sigue: las salidas deben caducar.
                now=max(now,time.monotonic()-capture.started)
            result=vision.receive()
            if result:
                candidate,crop=result
                if candidate.user_id==user_id:
                    obs=candidate
                    if emotion and crop is not None and obs.time_s-last_emotion>=config.emotion_period_s:
                        emotion.submit((crop,obs.time_s,user_id)); last_emotion=obs.time_s
                    rows.append(asdict(obs))
                    if obs.reason.startswith('error_vision') and obs.reason not in errors: errors.append(obs.reason)
            if emotion:
                exp=emotion.receive()
                if exp and exp.user_id==user_id:
                    expression=exp; expressions.append(asdict(exp))
                    if exp.error and exp.error not in errors: errors.append(exp.error)
            status,reason=af.update(obs,now)
            fresh_exp=expression if (expression and expression.user_id==user_id and obs and obs.face
                and now-expression.time_s<=config.emotion_stale_s) else None
            # Solo las nuevas observaciones añaden tiempo al gesto; repetir una salida no lo hace.
            hand_event=False
            if result and obs and obs.user_id==user_id and now-obs.time_s<=config.stale_s:
                hand_event=hand.update(obs.hand_up,obs.time_s)
            elif status==Attention.UNKNOWN:
                hand.update(None,now)
            dialogue.update(now,status,hand_event,fresh_exp)
            if dialogue.events:
                for event in dialogue.events:
                    event['session']=user_id; print(json.dumps(event,ensure_ascii=False),flush=True)
                events.extend(dialogue.events); dialogue.events.clear()
            runtime_error=vision.error or (emotion.error if emotion else None) or capture.error
            if runtime_error and runtime_error not in errors: errors.append(runtime_error)
            if frame is not None and not args.headless:
                view=render(frame,obs,status,reason,dialogue,fresh_exp,runtime_error or (errors[-1] if errors else None))
                cv2.imshow('P2 - Tutor visual',view)
                key=cv2.waitKey(1)&0xff
                if key in (ord('q'),27): stop_reason='usuario'; break
                if key==ord('r'):
                    user_id+=1; obs=None; expression=None; af.reset(); hand=HandEdge(config)
                    dialogue=Dialogue(config,phrases); last_submit=-1.; last_emotion=-1.; finished_at=None
            ui_latencies.append((time.perf_counter()-tick)*1000)
            if dialogue.finished:
                if finished_at is None: finished_at=time.monotonic()
                if args.headless or time.monotonic()-finished_at>=3.:
                    stop_reason=dialogue.state.value; break
            if args.max_seconds is not None and now>=args.max_seconds: stop_reason='limite_entrada'; break
            if capture.done and packet is None and not dialogue.finished:
                stop_reason='error_captura' if capture.error else 'fin_video'
                code=2 if capture.error else 0
                break
            if vision.error: code=2; stop_reason='error_vision'; break
            time.sleep(0.01)
    except (OSError,ValueError,RuntimeError) as exc:
        errors.append(f'{type(exc).__name__}: {exc}'); print(errors[-1],file=sys.stderr); code=2
    except KeyboardInterrupt: stop_reason='interrupcion_usuario'
    finally:
        if capture: capture.close()
        if vision: vision.close()
        if emotion: emotion.close()
        if not args.headless: cv2.destroyAllWindows()
        import numpy as np
        summary={'command':[sys.executable,*sys.argv], 'config':config.to_dict(),'input':args.input,
            'input_sha256':hashlib.sha256(Path(source).read_bytes()).hexdigest() if isinstance(source,str) and Path(source).is_file() else None,
            'lesson_sha256':hashlib.sha256(Path(args.lesson).read_bytes()).hexdigest(),
            'stop_reason':stop_reason,'state':dialogue.state.value,'lesson_s':dialogue.lesson_s,
            'elapsed_wall_s':time.monotonic()-start,'observations':len(rows),'expressions':len(expressions),
            'ui_loop_median_ms':float(np.median(ui_latencies)) if ui_latencies else None,
            'ui_loop_p95_ms':float(np.percentile(ui_latencies,95)) if ui_latencies else None,
            'errors':errors,'emotion_disabled':args.no_emotion,
            'note':'EOF no equivale a final bueno. Simular señales no valida visión.'}
        path=Path(args.log); path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps({'summary':summary,'observations':rows,'expressions':expressions,'events':events},ensure_ascii=False,indent=2))
        print(json.dumps(summary,ensure_ascii=False,indent=2))
    return code
