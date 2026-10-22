"""Prueba de integración de avisos y audio con atención ARTIFICIAL y vídeo del profesor.

Abre una ventana y reproduce dos pares de pitidos. No utiliza cámara ni mide
precisión de detectores. La sustitución de visión solo existe dentro de esta prueba.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tutor.app import main as tutor_main
from tutor.config import Config,ROOT
from tutor.signals import Observation

class ControlledVision:
    def __init__(self,*args): self.ready=True; self.error=None; self.pending=None
    def submit(self,packet):
        frame,t,user=packet
        self.pending=(Observation(t,user_id=user,face=True,head_front=False,
            eyes_open=True,gaze_front=False,hand_up=False,
            reason='PRUEBA_CONTROLADA_SENALES_ARTIFICIALES'),None)
    def receive(self):
        result=self.pending; self.pending=None; return result
    def close(self): pass


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--log',default=str(ROOT/'resultados/audio_controlado.json'))
    args=parser.parse_args()
    config=replace(Config(),away_hold_s=.1,warning_s=.4,escalate_s=.4,finish_s=.4)
    with tempfile.TemporaryDirectory(prefix='p2_audio_') as folder:
        config_path=Path(folder)/'config.json'; config_path.write_text(json.dumps(config.to_dict()))
        with patch('tutor.app.Worker',ControlledVision):
            code=tutor_main(['--input',str(ROOT/'video.mp4'),'--no-emotion',
                '--config',str(config_path),'--log',args.log])
    path=Path(args.log); record=json.loads(path.read_text())
    record['test_source']='Vídeo real como captura; señales de atención artificiales para probar avisos. No valida precisión de visión.'
    record['reproduction']=[sys.executable,str(Path(__file__).absolute()),'--log',args.log]
    path.write_text(json.dumps(record,ensure_ascii=False,indent=2))
    assert code==0 and record['summary']['state']=='final_malo'
    assert not record['summary']['errors']
    assert record['summary']['sound']['requested']==record['summary']['sound']['completed']==2
    assert [event['sound_requested'] for event in record['events']]==[True,True,False]
    print('Dos avisos y dos reproducciones completadas. Falta confirmar audición y volumen con la persona.')

if __name__=='__main__': main()
