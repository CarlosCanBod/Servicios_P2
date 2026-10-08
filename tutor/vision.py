"""Los tres modelos MediaPipe comparten una imagen RGB y timestamps crecientes."""
import time
from contextlib import ExitStack
from .config import ROOT
from .geometry import head_geometry, eye_geometry, raised_hand, iou
from .signals import Observation

class PrimaryUser:
    """Bloqueo geométrico: la mayor cara inicial; no cambiar al perderla.

    No es reconocimiento de identidad. Otra persona que ocupe el mismo lugar
    puede confundirse. Se requiere reinicio explícito de sesión para reselección.
    """
    def __init__(self, config): self.c=config; self.box=None

    def select(self, boxes):
        if not boxes: return None
        if self.box is None:
            index=max(range(len(boxes)),key=lambda i:(boxes[i][2]-boxes[i][0])*(boxes[i][3]-boxes[i][1]))
        else:
            index=max(range(len(boxes)),key=lambda i:iou(boxes[i],self.box))
            if iou(boxes[index],self.box)<self.c.track_iou: return None
        self.box=boxes[index]
        return index

class Perception:
    def __init__(self, config):
        import mediapipe as mp
        self.mp=mp; self.c=config; self.stack=ExitStack(); self.primary=PrimaryUser(config)
        self.user_id=0; self.last_ms=-1
        vision=mp.tasks.vision; base=mp.tasks.BaseOptions; mode=vision.RunningMode.VIDEO
        try:
            self.detector=self.stack.enter_context(vision.FaceDetector.create_from_options(vision.FaceDetectorOptions(
                base_options=base(model_asset_path=str(ROOT/'face_detector.task')),
                running_mode=mode,min_detection_confidence=config.face_confidence)))
            self.face=self.stack.enter_context(vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
                base_options=base(model_asset_path=str(ROOT/'face_landmarker.task')),
                running_mode=mode,num_faces=config.max_faces,
                min_face_detection_confidence=config.face_confidence,
                min_face_presence_confidence=config.face_confidence,min_tracking_confidence=config.face_confidence)))
            self.hands=self.stack.enter_context(vision.HandLandmarker.create_from_options(vision.HandLandmarkerOptions(
                base_options=base(model_asset_path=str(ROOT/'models/hand_landmarker.task')),
                running_mode=mode,num_hands=2,min_hand_detection_confidence=config.face_confidence,
                min_hand_presence_confidence=config.face_confidence,min_tracking_confidence=config.face_confidence)))
        except Exception:
            self.stack.close(); raise

    def close(self): self.stack.close()

    def process(self, frame, time_s, user_id=0):
        import cv2
        import numpy as np
        started=time.perf_counter()
        if user_id!=self.user_id:
            self.user_id=user_id; self.primary=PrimaryUser(self.c)
        obs=Observation(time_s=time_s,user_id=user_id)
        h,w=frame.shape[:2]
        # OpenCV entrega BGR; MediaPipe recibe RGB. Trabajamos sin espejar las medidas.
        rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        image=self.mp.Image(image_format=self.mp.ImageFormat.SRGB,data=np.ascontiguousarray(rgb))
        timestamp=max(self.last_ms+1,round(time_s*1000)); self.last_ms=timestamp
        detections=self.detector.detect_for_video(image,timestamp).detections
        boxes=[]; accepted=[]
        for d in detections:
            b=d.bounding_box
            box=(max(0,b.origin_x),max(0,b.origin_y),min(w,b.origin_x+b.width),min(h,b.origin_y+b.height))
            if min(box[2]-box[0],box[3]-box[1])>=self.c.min_face_px and d.categories[0].score>=self.c.face_confidence:
                boxes.append(box); accepted.append(d)
        obs.metrics['faces']=len(boxes)
        index=self.primary.select(boxes)
        # Los modelos de ojos y manos se comprueban incluso sin cara; no atribuimos sus salidas.
        faces=self.face.detect_for_video(image,timestamp).face_landmarks
        hands=self.hands.detect_for_video(image,timestamp).hand_landmarks
        obs.metrics['hands']=len(hands)
        if index is not None:
            obs.face=True; obs.bbox=boxes[index]
            keypoints=[(point.x*w,point.y*h) for point in accepted[index].keypoints]
            obs.head_front,metrics=head_geometry(keypoints,self.c); obs.metrics.update(metrics)
            meshes=[np.array([(point.x*w,point.y*h) for point in face]) for face in faces]
            mesh_boxes=[(p[:,0].min(),p[:,1].min(),p[:,0].max(),p[:,1].max()) for p in meshes]
            best=max(range(len(meshes)),key=lambda i:iou(obs.bbox,mesh_boxes[i])) if meshes else None
            if best is not None and iou(obs.bbox,mesh_boxes[best])>=0.2:
                obs.eyes_open,obs.gaze_front,metrics=eye_geometry(meshes[best],self.c); obs.metrics.update(metrics)
            else: obs.metrics['error']='sin_malla_correspondiente'
            obs.reason=obs.metrics.get('error','medicion_valida')
            if len(boxes)==1:
                raised=[raised_hand([(p.x*w,p.y*h) for p in hand],obs.bbox) for hand in hands]
                obs.hand_up=any(raised) if all(v is not None for v in raised) else None
            else: obs.hand_up=None
            x0,y0,x1,y1=obs.bbox
            crop=frame[y0:y1,x0:x1].copy()
        else:
            obs.reason='usuario_principal_perdido' if self.primary.box else 'sin_cara_fiable'
            crop=None
        obs.latency_ms=(time.perf_counter()-started)*1000
        return obs,crop
