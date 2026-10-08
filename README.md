# P2 · Tutor visual

Base de trabajo para probar con cámara. La memoria, el screencast de 2 minutos y el ZIP se prepararán después de validar la aplicación con el equipo.

Equipo: Alejandro Lavandeira Casais, Carlos Adrián Cancela Bodlak y Yago Martínez Pena.

## Empezar con tu cámara

Para probar una copia nueva de la rama del equipo (Linux y Python 3.12):

```bash
git clone --branch AlejandroLavandeira https://github.com/CarlosCanBod/Servicios_P2.git
cd Servicios_P2
./instalar.sh
```

Abre una terminal en esta carpeta. No es necesario activar entornos ni ejecutar `pip` por tu cuenta:

```bash
./ejecutar.sh cara --input 0
```

Deberías ver tu imagen, seis puntos sobre la cara y los valores `roll_deg`, `yaw_ratio`, `pitch_ratio` y `frontal`. Empieza solo, con buena luz, a unos 50-80 cm de la cámara y mirando hacia ella. Pulsa **q** para cerrar cada prueba. **r** reselecciona la cara principal; en el tutor completo también reinicia la lección.

Después prueba, una ventana cada vez:

```bash
./ejecutar.sh ojos --input 0
./ejecutar.sh manos --input 0
./ejecutar.sh expresion --input 0
./ejecutar.sh tutor --input 0
```

Si `0` no corresponde a tu cámara, cambia el índice; si falla, conserva el mensaje de error. No se ha abierto ni validado tu cámara automáticamente. Para comprobar la instalación sin usar cámara:

```bash
./ejecutar.sh tutor --input video.mp4
```

Los pasos y resultados esperados están en [la revisión manual](docs/prueba_manual.md). Las pruebas guardan valores y configuración en `resultados/`; **no graban imágenes ni vídeo**. Los registros de cámara están ignorados por Git.

## Instalación reproducible

Entorno comprobado: Linux x86_64, Python 3.12.3. OpenCV 4.14.0.94; MediaPipe 1.1.0; DeepFace 0.0.101, TensorFlow y tf-keras 2.21.0; NumPy 2.5.3. No se ha validado esta combinación en Windows, macOS u otras versiones de Python.

```bash
./instalar.sh
```

El script crea dos entornos locales con versiones fijadas y revisa imports, modelos, dependencias y regresiones. En este ordenador ya se ha ejecutado. En una instalación nueva necesita conexión y espacio para TensorFlow. Si el sistema no permite crear entornos, instala el paquete `python3-venv` correspondiente a Python 3.12. Se puede elegir otro ejecutable 3.12 con `P2_PYTHON=python3.12 ./instalar.sh`.

MediaPipe exige `opencv-contrib-python` y DeepFace exige `opencv-python`. Ambas distribuciones aportan `cv2`: instalarlas juntas puede sobrescribir archivos. Por eso `.venv-vision` contiene la primera y `.venv` contiene la segunda. El lanzador escoge los intérpretes correctos; no debes mezclar paquetes entre ellos. Ambos entornos pasan `pip check`. Los archivos `requirements-vision.lock.txt` y `requirements-expression.lock.txt` fijan también las dependencias transitivas. Python 3.12 es el entorno verificado, no una afirmación de que la práctica solo pueda funcionar con esa versión.

Los modelos de cara del profesor se conservan en la raíz. El modelo de manos está en `models/hand_landmarker.task`, con origen y hashes en `models/manifest.json`. DeepFace descarga sus pesos oficiales en `~/.deepface/weights` si faltan; `instalar.sh` los carga antes de empezar. El script comprueba que las tres Tasks cargan, sin abrir cámara. No intenta recuperar `mp.solutions`: esa API no está en el MediaPipe instalado, incluso usando OpenCV 4.14.

## Cómo está organizado el código

| Bloque | Archivo | Qué hace y por qué |
|---|---|---|
| Captura | `tutor/capture.py` | Lee cámara o vídeo en un hilo, conserva el fotograma reciente y libera la fuente |
| Percepción | `tutor/vision.py` | Detecta cara, malla ocular y manos con timestamps del origen; selecciona una cara |
| Geometría | `tutor/geometry.py` | Calcula orientación relativa, apertura e iris con coordenadas en píxeles |
| Atención | `tutor/attention.py` | Fusiona señales y exige estabilidad; trata lo desconocido explícitamente |
| Diálogo | `tutor/dialogue.py` | Aplica los estados del enunciado, los tiempos y la prioridad de la mano |
| Expresión | `tutor/expression.py` | Clasifica solo el recorte de cara, mediante DeepFace |
| Procesos | `tutor/workers.py` y `tutor/expression_service.py` | Aíslan inferencias, descartan trabajo antiguo e impiden bloquear la interfaz |
| Interfaz | `tutor/interface.py` | Muestra señales, diagnóstico y texto de la lección en español |
| Integración | `tutor/app.py` | Coordina reloj, resultados, caducidad, estados, controles y registros |
| Pruebas individuales | `scripts/probar_detector.py` | Ejecuta un subsistema cada vez, sin diálogo |
| Configuración | `config.json` | Expone tiempos, umbrales geométricos y resolución |

Tabla 1. Organización de la aplicación: cada bloque separa una responsabilidad del prototipo.

Una detección no demuestra atención real. Se usa una regla del prototipo: cabeza aproximadamente frontal + ojos abiertos + iris aproximadamente centrado. El iris no se calibra con posiciones de pantalla; cámara y pantalla no son necesariamente el mismo objetivo. Con ojos cerrados de forma sostenida se admite una señal negativa; falta de cara, guiño, geometría inválida o datos caducados producen desconocido. Lo desconocido congela la lección y los avisos.

La expresión tiene siete clases en el modelo instalado, aunque el enunciado habla de seis: angry, disgust, fear, happy, sad, surprise y neutral. Las puntuaciones son salidas del clasificador; no son porcentajes de precisión ni certezas sobre emociones internas.

Los detalles de decisiones, revisión del material inicial y fuentes primarias están en [el análisis](docs/analisis.md) y [las fuentes](docs/fuentes.md). Los ejemplos del profesor, incluidos los antiguos, permanecen intactos. `p2data/` se conserva localmente; los ejemplos actuales ya están también en la raíz por proceder del repositorio.

## Comprobaciones automatizadas

```bash
.venv-vision/bin/python -m unittest discover -s tests -v
.venv-vision/bin/python scripts/diagnose_video.py
.venv/bin/python scripts/diagnose_expression.py
./ejecutar.sh tutor --input video.mp4 --headless --log resultados/integracion_video.json
```

El diagnóstico de expresión usa los rectángulos y el hash del diagnóstico de visión anterior; ejecútalos en ese orden. Para el ejemplo oficial de manos:

```bash
mkdir -p .cache
curl -fL https://storage.googleapis.com/mediapipe-tasks/hand_landmarker/woman_hands.jpg -o .cache/woman_hands.jpg
.venv-vision/bin/python scripts/diagnose_hands.py
```

Las mediciones realizadas y lo pendiente están en [resultados y límites](docs/resultados.md). Los tests de decisión utilizan señales simuladas y los de geometría coordenadas artificiales; no evalúan la exactitud de la visión. EOF significa fin del vídeo, no final bueno de la lección.
