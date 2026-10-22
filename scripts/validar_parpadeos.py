"""Reproduce pérdidas de distinta duración con señales artificiales, sin abrir cámara.

Los pasos de 0,01 s solo permiten revisar el límite de 0,5 s. No son una exigencia
de FPS para la aplicación ni una prueba de precisión de MediaPipe.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tutor.config import Config,ROOT
from tutor.signals import Attention,Observation
from tutor.attention import AttentionFilter
from tutor.dialogue import Dialogue


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',default=str(ROOT/'config.json'))
    parser.add_argument('--output',default=str(ROOT/'resultados/revision_20261019/parpadeos_simulados.json'))
    args=parser.parse_args(); config=Config.load(args.config); results=[]
    for duration in (.1,.2,.3,.4,.49,.51,.7):
        filt=AttentionFilter(config)
        dialogue=Dialogue(replace(config,joke_after_s=100.),['frase']*10)
        samples=[]; paused=0
        for i in range(301):
            t=i*.01; blink=1.<=t<1.+duration
            observation=Observation(t,face=True,head_front=True,eyes_open=None if blink else True,
                gaze_front=None if blink else True,reason='guino_o_apertura_ambigua' if blink else 'medicion_valida')
            attention,reason=filt.update(observation,t); dialogue.update(t,attention)
            if t>=.5 and attention!=Attention.ATTENTIVE: paused+=1
            samples.append({'time_s':round(t,2),'raw_eyes_open':observation.eyes_open,
                'attention':attention.value,'reason':reason,'lesson_s':dialogue.lesson_s})
        if duration<config.unknown_hold_s: assert paused==0 and not dialogue.events
        results.append({'loss_s':duration,'paused_s_after_startup':round(paused*.01,2),
                        'lesson_s':dialogue.lesson_s,'events':dialogue.events,'samples':samples})
    path=Path(args.output); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps({'command':sys.argv,'config':config.to_dict(),'simulation_step_s':.01,
        'note':'Señales artificiales; no evalúa detección de ojos reales.','cases':results},indent=2,ensure_ascii=False))
    for r in results: print(f"Pérdida {r['loss_s']:.2f} s -> pausa {r['paused_s_after_startup']:.2f} s, excluido arranque")

if __name__=='__main__': main()
