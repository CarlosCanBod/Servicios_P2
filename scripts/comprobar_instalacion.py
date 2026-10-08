"""Verifica imports, API Tasks y hashes de modelos sin abrir la cámara."""
from importlib.metadata import version,PackageNotFoundError
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import cv2
import mediapipe as mp
from tutor.config import ROOT,Config
from tutor.vision import Perception

providers=[]
for package in ('opencv-python','opencv-contrib-python','opencv-python-headless','opencv-contrib-python-headless'):
 try: providers.append((package,version(package)))
 except PackageNotFoundError: pass
if len(providers)!=1: raise RuntimeError(f'Se esperaba una sola distribución OpenCV: {providers}')
manifest=json.loads((ROOT/'models/manifest.json').read_text())
for entry in manifest['models']:
 path=ROOT/entry['path']
 if hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256']: raise RuntimeError(f'Modelo ausente o modificado: {path}')
perception=Perception(Config()); perception.close()
print('Python',sys.version.split()[0],'MediaPipe',mp.__version__,'OpenCV',cv2.__version__)
print('API antigua mp.solutions:',hasattr(mp,'solutions'))
print('Tres modelos Tasks cargados. Cámara sin abrir.')
