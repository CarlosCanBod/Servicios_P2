"""Geometría en píxeles (x hacia la derecha, y hacia abajo), nunca x/y mezclados."""
import math
import numpy as np


def iou(a, b):
    """Solapamiento relativo de rectángulos (x0,y0,x1,y1)."""
    x0,y0=max(a[0],b[0]),max(a[1],b[1])
    x1,y1=min(a[2],b[2]),min(a[3],b[3])
    overlap=max(0,x1-x0)*max(0,y1-y0)
    area=lambda p:max(0,p[2]-p[0])*max(0,p[3]-p[1])
    return overlap/max(area(a)+area(b)-overlap,1e-9)


def head_geometry(points, c):
    """Seis puntos de FaceDetector; devuelve frontal/None y métricas explicables.

    Se proyectan nariz y boca en ejes ligados a los ojos para compensar roll.
    yaw_ratio es desplazamiento lateral / distancia entre ojos. pitch_ratio es
    altura de nariz / altura de boca. Son aproximaciones 2D, no ángulos 3D.
    """
    p=np.asarray(points,dtype=float)
    if p.shape!=(6,2) or not np.isfinite(p).all(): return None, {'error':'puntos_invalidos'}
    eyes=sorted(p[:2],key=lambda point:point[0]); left,right=eyes
    delta=right-left; distance=float(np.linalg.norm(delta))
    if distance<c.min_eye_px: return None, {'error':'ojos_pequenos'}
    horizontal=delta/distance; vertical=np.array([-horizontal[1],horizontal[0]])
    center=(left+right)/2; nose=p[2]-center; mouth=p[3]-center
    roll=math.degrees(math.atan2(delta[1],delta[0]))
    mouth_y=float(mouth@vertical)
    if mouth_y<distance*0.15: return None, {'error':'geometria_degenerada'}
    yaw=float(nose@horizontal/distance); pitch=float(nose@vertical/mouth_y)
    metrics={'roll_deg':roll,'yaw_ratio':yaw,'pitch_ratio':pitch}
    if abs(roll)>c.roll_max_deg: return None, {**metrics,'error':'inclinacion_excesiva'}
    return abs(yaw)<=c.yaw_max and c.pitch_low<=pitch<=c.pitch_high, metrics


# Los seis puntos recorren el contorno: esquina, dos arriba, esquina, dos abajo.
RIGHT_EYE=(33,160,158,133,153,144)
LEFT_EYE=(362,385,387,263,373,380)


def eye_geometry(mesh, c):
    """EAR=(dos distancias verticales)/(2*anchura); iris proyectado sobre cada ojo."""
    p=np.asarray(mesh,dtype=float)
    if len(p)<478 or not np.isfinite(p).all(): return None,None,{'error':'malla_invalida'}
    ears=[]; horizontal=[]; vertical=[]
    for indices, iris, top, bottom in ((RIGHT_EYE,468,159,145),(LEFT_EYE,473,386,374)):
        a,b,d,e,f,g=p[list(indices)]
        width=float(np.linalg.norm(a-e))
        if width<c.min_eye_px: return None,None,{'error':'ojos_pequenos'}
        ears.append(float((np.linalg.norm(b-g)+np.linalg.norm(d-f))/(2*width)))
        corners=sorted((a,e),key=lambda point:point[0]); axis=corners[1]-corners[0]
        horizontal.append(float((p[iris]-corners[0])@axis/(axis@axis)))
        v=p[bottom]-p[top]
        vertical.append(float((p[iris]-p[top])@v/max(float(v@v),1e-9)))
    metrics={'ear_right':ears[0],'ear_left':ears[1],
             'iris_x_right':horizontal[0],'iris_x_left':horizontal[1],
             'iris_y_right':vertical[0],'iris_y_left':vertical[1]}
    closed=[ear<=c.ear_closed for ear in ears]; opened=[ear>=c.ear_open for ear in ears]
    if all(closed): return False,None,metrics
    if not all(opened): return None,None,{**metrics,'error':'guino_o_apertura_ambigua'}
    if (any(x<0 or x>1 for x in horizontal+vertical) or abs(horizontal[0]-horizontal[1])>0.25):
        return True,None,{**metrics,'error':'iris_no_fiable'}
    gaze=(all(c.gaze_low<=x<=c.gaze_high for x in horizontal)
          and all(c.gaze_vertical_low<=y<=c.gaze_vertical_high for y in vertical))
    return True,gaze,metrics


def raised_hand(points, bbox):
    """Petición visible: palma encima de la boca y tres dedos extendidos.

    Solo se asocia por proximidad a una cara, no por identidad. Con varias caras
    la percepción inhibe esta señal para no atribuir la mano de otro alumno.
    """
    p=np.asarray(points,dtype=float)
    if p.shape!=(21,2) or not np.isfinite(p).all(): return None
    x0,y0,x1,y1=bbox; width=x1-x0; height=y1-y0
    palm=p[[0,5,9,13,17]].mean(axis=0)
    near=(x0-1.3*width<=palm[0]<=x1+1.3*width)
    above=palm[1]<y0+0.65*height
    extended=0
    for mcp,pip,tip in ((5,6,8),(9,10,12),(13,14,16),(17,18,20)):
        # La distancia al inicio del dedo evita contar un puño como mano abierta.
        extended+=np.linalg.norm(p[tip]-p[mcp])>1.35*np.linalg.norm(p[pip]-p[mcp])
    return bool(near and above and extended>=3)
