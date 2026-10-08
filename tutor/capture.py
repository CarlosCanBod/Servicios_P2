"""Captura independiente: reloj monotónico en cámara, tiempo de vídeo en fichero."""
from queue import Queue
from threading import Event, Thread
import math
import time
import cv2
from .workers import offer, latest

class Capture:
    def __init__(self, source, width):
        self.camera=isinstance(source,int)
        self.cap=cv2.VideoCapture(source)
        if not self.cap.isOpened():
            self.cap.release(); raise ValueError(f'No se pudo abrir la entrada: {source}')
        self.fps=float(self.cap.get(cv2.CAP_PROP_FPS)); self.width=width
        if not self.camera and (not math.isfinite(self.fps) or self.fps<=0):
            self.cap.release(); raise ValueError('El vídeo no tiene FPS válidos para temporizarlo')
        self.queue=Queue(maxsize=1); self.stop=Event(); self.done=False; self.error=None
        self.thread=Thread(target=self._run,daemon=True)
        self.started=time.monotonic(); self.thread.start()

    def _run(self):
        n=0; last_t=-1.
        try:
            while not self.stop.is_set():
                ok,frame=self.cap.read()
                if not ok:
                    if self.camera: self.error='La cámara dejó de entregar imágenes'
                    break
                if self.camera: t=time.monotonic()-self.started
                else:
                    # Algunos backends devuelven POS_MSEC=0 siempre: respaldo por FPS del fichero.
                    position=self.cap.get(cv2.CAP_PROP_POS_MSEC)/1000.
                    t=position if math.isfinite(position) and position>last_t else n/self.fps
                    t=max(t,n/self.fps)
                    if self.stop.wait(max(0.,self.started+t-time.monotonic())): break
                last_t=t; n+=1
                if frame.shape[1]!=self.width:
                    frame=cv2.resize(frame,(self.width,round(frame.shape[0]*self.width/frame.shape[1])))
                offer(self.queue,(frame,t,time.monotonic()))
        except Exception as exc: self.error=f'Captura: {type(exc).__name__}: {exc}'
        finally:
            self.cap.release(); self.done=True

    def read_latest(self): return latest(self.queue)

    def close(self):
        self.stop.set(); self.thread.join(timeout=1.)
