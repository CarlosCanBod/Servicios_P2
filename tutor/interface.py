"""Vista diagnóstica en español; Pillow permite tildes que putText no dibuja."""
from pathlib import Path
import textwrap
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')

def render(frame, obs, attention, reason, dialogue, expression, error=None):
    h,w=frame.shape[:2]
    image=Image.new('RGB',(max(960,w+320),h+210),(19,25,36))
    image.paste(Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)),(0,0))
    draw=ImageDraw.Draw(image)
    font=ImageFont.truetype(str(FONT),16) if FONT.exists() else ImageFont.load_default()
    title=ImageFont.truetype(str(FONT),19) if FONT.exists() else font
    if obs and obs.bbox:
        draw.rectangle(obs.bbox,outline=(100,235,155),width=2)
    if obs is None:
        lines=['Esperando percepción...']
    else:
        flag=lambda value:'sí' if value is True else 'no' if value is False else 'no evaluable'
        lines=[f'Atención: {attention.value}',f'Motivo: {reason}',
            f'Cara: {flag(obs.face)}',f'Cabeza frontal: {flag(obs.head_front)}',
            f'Ojos abiertos: {flag(obs.eyes_open)}',f'Mirada centrada: {flag(obs.gaze_front)}',
            f'Mano elevada: {flag(obs.hand_up)}',f'Visión: {obs.latency_ms:.1f} ms']
        for key in ('roll_deg','yaw_ratio','pitch_ratio','ear_right','ear_left'):
            if key in obs.metrics: lines.append(f'{key}: {obs.metrics[key]:.3f}')
    for i,line in enumerate(lines): draw.text((w+12,10+i*23),line,font=font,fill=(224,230,240))
    y=h+12
    draw.text((16,y),f'Estado: {dialogue.state.value} | Lección: {dialogue.lesson_s:.1f} s',font=title,fill=(115,230,205))
    y+=32
    message='Señal no evaluable: la lección está en espera.' if attention.value=='desconocida' and dialogue.state.value not in ('descanso','final_bueno','final_malo') else dialogue.message
    for line in textwrap.wrap(message,width=90):
        draw.text((16,y),line,font=title,fill=(245,245,245)); y+=26
    label=expression.label if expression and not expression.error else 'no evaluable'
    score=expression.scores.get(label,0) if expression else 0
    draw.text((16,h+130),f'Expresión estimada: {label} ({score:.2f}). No mide emoción real ni atención.',font=font,fill=(195,204,219))
    draw.text((16,h+160),f'q: salir | r: reiniciar lección y seleccionar cara principal',font=font,fill=(195,204,219))
    if error: draw.text((16,h+185),str(error)[:108],font=font,fill=(255,145,145))
    return cv2.cvtColor(np.array(image),cv2.COLOR_RGB2BGR)
