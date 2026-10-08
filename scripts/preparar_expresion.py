"""Carga los pesos oficiales de expresión; primera ejecución necesita conexión."""
from importlib.metadata import version,PackageNotFoundError
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tutor.expression import ExpressionDetector
providers=[]
for package in ('opencv-python','opencv-contrib-python','opencv-python-headless','opencv-contrib-python-headless'):
 try: providers.append((package,version(package)))
 except PackageNotFoundError: pass
if len(providers)!=1: raise RuntimeError(f'OpenCV duplicado: {providers}')
ExpressionDetector()
print('Expresión preparada. DeepFace',version('deepface'),'TensorFlow',version('tensorflow'),'tf-keras',version('tf-keras'))
