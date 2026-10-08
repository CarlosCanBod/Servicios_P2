# Fuentes primarias consultadas (2026-10-08)

- [Enunciado local](../P2.pdf): seis páginas; estado de emoción, recuperación por niveles y entregables.
- [MediaPipe, configuración Python](https://developers.google.com/edge/mediapipe/solutions/setup_python): requisitos de plataforma, Tasks y rutas de modelos. La página actual anuncia Python 3.9 y posteriores; aquí se verifica 3.12.3.
- [Face Detector](https://developers.google.com/edge/mediapipe/solutions/vision/face_detector/python): detecciones y puntos de referencia normalizados.
- [Face Landmarker](https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker/python): 478 puntos, modo VIDEO con timestamps, ejecución bloqueante; LIVE_STREAM descarta entradas si está ocupado. Se usa VIDEO dentro de un trabajador independiente para mantener control explícito de tiempos.
- [Hand Landmarker](https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker/python): 21 puntos por mano y modo vídeo. No requiere estimar postura corporal completa.
- [Modelo Hand Landmarker](https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker): bundle float16 versión 1 descargado del enlace oficial de Google Storage.
- [OpenCV Python](https://github.com/opencv/opencv-python#installation-and-usage): instalar SOLO una de las cuatro distribuciones cv2. Tener python y contrib simultáneamente no es una solución de compatibilidad.
- [OpenCV VideoCapture](https://docs.opencv.org/4.x/d8/dfe/classcv_1_1VideoCapture.html): read/isOpened/release; las propiedades dependen del backend. Se distingue EOF de vídeo de fallo de cámara.
- [DeepFace](https://github.com/serengil/deepface): analyze, recortes BGR, acciones emotion, detector skip y backend TensorFlow.
- [DeepFace API fuente](https://github.com/serengil/deepface/blob/master/deepface/DeepFace.py): skip presupone una cara extraída; su face_confidence no sirve como confianza. Keras 3 requiere tf-keras con TensorFlow reciente. Se comprobará la versión instalada, que puede diferir de master.
- [FER, dependencias](https://github.com/justinshenk/fer/blob/master/pyproject.toml): alternativa admitida por el enunciado; TensorFlow y OpenCV contrib. No se ha comparado empíricamente su precisión con DeepFace.

Las puntuaciones de clases de expresión no son porcentajes de acierto del sistema ni probabilidades calibradas de emoción real. No se usa la cifra de precisión de reconocimiento de identidad del README de DeepFace: se refiere a otra tarea.
