"""Guarda secuencias controladas del gestor. No ejecuta ni valida detectores."""
from dataclasses import replace
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tutor.config import Config,ROOT
from tutor.signals import Attention,Expression
from tutor.dialogue import Dialogue

c=Config(); rows=[]
scenarios={
 'final_normal':[(40,Attention.ATTENTIVE)],
 'final_por_desatencion':[(25,Attention.AWAY)],
 'recuperacion':[(12,Attention.AWAY),(8,Attention.ATTENTIVE)],
 'sin_deteccion':[(25,Attention.UNKNOWN)],
 'descanso':[(15,Attention.AWAY)],
 'chiste_sonrisa':[(24,Attention.ATTENTIVE)],
 'chiste_sin_reaccion':[(24,Attention.ATTENTIVE)],
 'chiste_modelo_error':[(24,Attention.ATTENTIVE)]}
for name,segments in scenarios.items():
 conf=replace(c,joke_after_s=1000.) if not name.startswith('chiste_') else c
 d=Dialogue(conf,['frase']*10); t=0.; observations=[]
 for duration,status in segments:
  for _ in range(round(duration/.1)):
   hand_event=name=='descanso' and (abs(t-1.)<1e-7 or abs(t-10.)<1e-7)
   happy=.8 if name=='chiste_sonrisa' and d.joke_started is not None and t>d.joke_started+.4 else .1
   exp=Expression(t,0,{'happy':happy},'happy' if happy>.5 else 'neutral')
   if name=='chiste_modelo_error': exp=Expression(t,0,error='Error simulado')
   d.update(t,status,hand_event,exp)
   observations.append({'time_s':round(t,2),'state':d.state.value,'attention':status.value,'hand_event':hand_event,'happy':None if exp.error else happy})
   t=round(t+.1,6)
 rows.append({'name':name,'config':conf.to_dict(),'final_state':d.state.value,'events':d.events,'signals':observations})
output=ROOT/'resultados/dialogos_simulados.json'
output.write_text(json.dumps({'command':sys.argv,'warning':'Señales artificiales. No evalúa precisión de visión.','scenarios':rows},ensure_ascii=False,indent=2))
for row in rows: print(row['name'],row['final_state'],[(x['to'],round(x['time_s'],1)) for x in row['events']])
