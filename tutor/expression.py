"""DeepFace recibe exclusivamente un recorte de la cara principal en BGR."""
import os
import time
from .signals import Expression

class ExpressionDetector:
    def __init__(self):
        # CPU y pocos hilos: la red pequeña no debe monopolizar la aplicación.
        os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL','3')
        os.environ.setdefault('TF_NUM_INTRAOP_THREADS','1')
        os.environ.setdefault('TF_NUM_INTEROP_THREADS','1')
        os.environ.setdefault('OMP_NUM_THREADS','1')
        os.environ.setdefault('DEEPFACE_BACKEND_ENGINE','tensorflow')
        from deepface import DeepFace
        self.deepface=DeepFace
        self.deepface.build_model('Emotion',task='facial_attribute')

    def analyze(self, crop, time_s, user_id):
        started=time.perf_counter()
        try:
            if crop is None or crop.size==0: raise ValueError('Recorte vacío')
            result=self.deepface.analyze(crop,actions=['emotion'],detector_backend='skip',
                enforce_detection=False,align=False,silent=True)[0]
            # analyze devuelve puntuaciones normalizadas a 100, no exactitud de la red.
            scores={k:float(v)/100. for k,v in result['emotion'].items()}
            import math
            if not scores or not all(math.isfinite(v) and 0<=v<=1.001 for v in scores.values()):
                raise ValueError('Puntuaciones inválidas')
            return Expression(time_s,user_id,scores,result['dominant_emotion'],latency_ms=(time.perf_counter()-started)*1000)
        except Exception as exc:
            return Expression(time_s,user_id,error=f'{type(exc).__name__}: {exc}',latency_ms=(time.perf_counter()-started)*1000)
