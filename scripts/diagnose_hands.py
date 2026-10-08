"""Prueba positiva independiente de manos con una imagen del ejemplo oficial."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import cv2
import mediapipe as mp
from tutor.config import Config,ROOT
from tutor.geometry import raised_hand
from tutor.vision import Perception

p=argparse.ArgumentParser(); p.add_argument('--image',default='.cache/woman_hands.jpg'); p.add_argument('--output',default='resultados/manos_imagen.json'); a=p.parse_args()
image=cv2.imread(a.image)
if image is None: p.error('Imagen no encontrada o no decodificable')
c=Config(); h,w=image.shape[:2]; v=mp.tasks.vision
start=time.perf_counter()
with v.HandLandmarker.create_from_options(v.HandLandmarkerOptions(base_options=mp.tasks.BaseOptions(model_asset_path=str(ROOT/'models/hand_landmarker.task')),num_hands=2)) as detector:
 result=detector.detect(mp.Image(image_format=mp.ImageFormat.SRGB,data=cv2.cvtColor(image,cv2.COLOR_BGR2RGB)))
latency=(time.perf_counter()-start)*1000
# La integración sobre una sola imagen comprueba asociación espacial, no un gesto temporal.
perception=Perception(c)
try: observation,_=perception.process(image,0.)
finally: perception.close()
record={'command':sys.argv,'image_sha256':hashlib.sha256(Path(a.image).read_bytes()).hexdigest(),
 'source':'https://storage.googleapis.com/mediapipe-tasks/hand_landmarker/woman_hands.jpg',
 'sample_reference':'https://github.com/google-ai-edge/mediapipe-samples/blob/main/examples/hand_landmarker/python/hand_landmarker.ipynb',
 'hands':len(result.hand_landmarks),'landmarks_per_hand':[len(h) for h in result.hand_landmarks],
 'initialization_and_inference_ms':latency,'integration_face':observation.face,'integration_hand_up':observation.hand_up,
 'integration_reason':observation.reason,'config':c.to_dict(),
 'note':'Imagen real de ejemplo; sin gesto temporal ni evaluación de exactitud.'}
Path(a.output).write_text(json.dumps(record,indent=2)); print(json.dumps(record,indent=2))
if not result.hand_landmarks: raise SystemExit(1)
