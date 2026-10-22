# Comprobaciones realizadas y pendientes

Se trabaja en `AlejandroLavandeira`, desde el main verificado a6e48f533f0402476f3e62cefa17db8fcc41af10. Los originales de P2 se verificaron por SHA-256 sin diferencias. El trabajo se comparte mediante un commit en esta rama para las pruebas del equipo. No se modifica P1 ni main y no se crea una PR. La memoria PDF y el vídeo de 2 minutos se posponen por instrucción de Alejandro.

## Instalación

Linux x86_64, Python 3.12.3. La instalación global inicial no podía importar cv2 por una incompatibilidad binaria con NumPy. No se modificó. Se crearon entornos locales y se comprobó que sus dependencias son consistentes.

La instalación directa de MediaPipe y DeepFace introdujo dos variantes de OpenCV. La prueba verificó, por inspección de metadatos, que MediaPipe 1.1.0 requiere opencv-contrib-python y DeepFace 0.0.101 requiere opencv-python. Se resolvió utilizando entornos diferentes. Ambos usan OpenCV 4.14.0.94, el número indicado en las notas del profesor; el MediaPipe instalado no expone mp.solutions. Los ejemplos actuales sí funcionan con Tasks. No se afirma que cualquier versión antigua tenga el mismo resultado.

Comando: `./instalar.sh`. Resultado: instalación fijada, ambos `pip check` sin dependencias rotas, imports correctos, tres modelos Tasks cargados y modelo Emotion de DeepFace preparado. Evidencia: `resultados/instalacion_verificada.txt`. Las regresiones posteriores están en `resultados/regresion.txt`.

## Reproducción inicial

El comando `scripts/baseline.py` sustituye solo cámara por vídeo y funciones de ventana por operaciones vacías. Ejecuta el código original mediante runpy, sin editarlo. La prueba no comprueba la interfaz original ni una cámara real. Estas reproducciones ocurrieron antes de implementar los detectores de la nueva aplicación; la lógica de decisión se comenzó tras el primer intento fallido de importación global.

| Ejemplo original | Fotogramas | Tiempo de ejecución (s) | Evidencia |
|---|---:|---:|---|
| Captura (`ejemplo0`) | 30 | 0,171 | `baseline_ejemplo0.txt` |
| Cara (`ejemplo1`) | 30 | 2,204 | `baseline_ejemplo1.txt` |
| Malla (`ejemplo2`) | 30 | 2,615 | `baseline_ejemplo2.txt` |
| DeepFace (`ejemplo4`) | 3 | 3,135 | `baseline_ejemplo4.txt` |

Tabla 1. Ejecuciones de los ejemplos originales con vídeo. Los tiempos incluyen inicialización; DeepFace incluye descarga inicial de pesos. No son FPS sostenidos ni una comparación justa entre algoritmos. Las evidencias están en `resultados/`.

El ejemplo4 produjo angry en sus tres fotogramas, pero clasificaba el fotograma completo con skip. Eso no demuestra esa expresión en la persona. El adaptador nuevo analiza una cara recortada; no se compara precisión sin anotaciones de referencia.

## Detectores reales

El fichero `video.mp4` contiene 286 fotogramas a 30 FPS: 9,533 s. Su hash SHA-256 es 26a62ebab244ad77f0a245f7f455a8053ac311bab4e1f414caa4e76986446e56. Las copias de p2data y de version 2025-26 son idénticas, no tres vídeos independientes.

Comando: `.venv-vision/bin/python scripts/diagnose_video.py`. Configuración: `config.json`, ancho 640 px, muestreo cada 0,1 s. Resultado: 96 muestras; cara válida en 96; 0 muestras de mano elevada; apertura e iris medibles en la mayor parte, con cinco aperturas ambiguas. La decisión temporal produjo 60 muestras atiende, 36 desconocida y ninguna no_atiende. La proporción de esas etiquetas no mide exactitud. Evidencia: `resultados/vision_video.json` y `vision_ejecucion.txt`.

Mediana de inferencia conjunta de cara, malla y manos: 23,38 ms; percentil 95: 27,59 ms. El percentil 95 significa que el 95 % de las duraciones registradas no lo superó. La ejecución recorrió el vídeo offline en 3,43 s; no se utiliza ese tiempo como reloj del diálogo.

Comando: `.venv/bin/python scripts/diagnose_expression.py`. Entrada: recortes definidos en el diagnóstico de visión, uno por segundo. Diez inferencias reales, cero errores; neutral en t=0 y happy en las nueve posteriores. Inicialización con pesos ya descargados: 1,91 s; primera inferencia: 75,5 ms; posteriores: aproximadamente 7,5-10,4 ms. Evidencia: `resultados/expresion_video.json`. No hay referencia humana de expresión ni una reacción real al chiste.

Comando: `.venv-vision/bin/python scripts/diagnose_hands.py`. Se descargó la imagen woman_hands.jpg utilizada por el notebook oficial de MediaPipe. Detectó dos manos, con 21 puntos cada una. La integración espacial sobre esa imagen detectó una cara y una mano elevada. Evidencia: `resultados/manos_imagen.json`, que incluye URL, hash y configuración. Una imagen positiva no demuestra la estabilidad del gesto ni la pausa/reanudación con cámara.

## Integración y ventana

Comando: `./ejecutar.sh tutor --input video.mp4 --headless --log resultados/integracion_video.json`. Resultado: 95 observaciones y 12 inferencias de expresión; sin errores registrados. El vídeo acaba con la lección aún en inicial y 5,87 s de avance efectivo; se informa fin_video. No se finge final bueno por EOF.

El bucle principal sin ventana tuvo mediana 0,098 ms y percentil 95 de 0,361 ms. Es duración del trabajo del bucle, excluyendo la espera intencionada; no mide latencia extremo a extremo cámara-pantalla. Las colas acotadas y la caducidad limitan la acumulación de resultados, aunque pueden descartarse frames.

Se abrieron y cerraron las cinco ventanas con el vídeo como fuente. Comandos: `./ejecutar.sh <cara|ojos|manos> --input video.mp4 --max-seconds 1`, `./ejecutar.sh expresion --input video.mp4 --max-seconds 2` y el tutor con el mismo límite. Las cuatro pruebas individuales terminaron sin error; evidencias `resultados/gui_detectores.json` y `gui_*.txt`. En la ventana del tutor, mediana del trabajo del bucle 11,79 ms y percentil 95 20,54 ms, incluyendo renderizado; 19 observaciones y tres expresiones, sin errores. Evidencia: `resultados/gui_tutor.json`. Se revisó visualmente una representación de la interfaz para comprobar legibilidad; esa representación de QA no es una prueba de expresión real.

La integración inicial permitió descubrir y corregir retrocesos del reloj y contaminación del sys.path al intentar usar multiprocessing entre entornos. La expresión se ejecuta ahora como un subproceso independiente con intérprete propio y tuberías atendidas por hilos. No se basa en modificar sys.path de un proceso ya iniciado.

## Lógica simulada

Comandos: `.venv-vision/bin/python -m unittest discover -s tests -v` y `.venv-vision/bin/python scripts/simular_dialogos.py`. Evidencias: `resultados/regresion.txt`, `dialogos_simulados.json` y `dialogos_simulados.txt`.

Se comprueban final normal, tres niveles de desatención hasta final malo, recuperación nivel a nivel, descanso con mano prioritaria, congelación con desconocido, ojos cerrados sostenidos, parpadeo breve, guiño, señal caducada, cambio de usuario, inferencia intermitente, chiste con aumento happy, sin reacción y error del clasificador. También invariantes de escala/rotación y transporte fragmentado entre procesos. Son pruebas de reglas y fórmulas, no de precisión de visión.

La ejecución con una entrada inexistente terminó con código 2 y mensaje claro, antes de iniciar modelos. Evidencia: `resultados/error_entrada.txt`.

## Relación con requisitos

La tabla 2 separa implementación y evidencia existente de validación pendiente. No se considera cerrada la práctica hasta revisar con Alejandro la cámara y las limitaciones.

| Requisito | Implementación | Evidencia actual | Pendiente con cámara |
|---|---|---|---|
| Cara/orientación | `vision.py`, `geometry.py:head_geometry` | Baseline cara, vídeo, geometría artificial | Giros, inclinación, pérdida de ojos |
| Apertura/mirada | `geometry.py:eye_geometry` | Vídeo, coordenadas artificiales, visor ojos | Gafas, guiño, mirar a pantalla frente a cámara, luz |
| Manos/descanso | `raised_hand`, `HandEdge`, `Dialogue` | Imagen positiva real, visor y señales simuladas | Subida, bajada, segunda subida, oclusión |
| Expresión/chiste | `expression.py`, `Dialogue` | Recortes reales y reacción simulada | Expresión antes/después de chiste |
| Avisos/finales | `attention.py`, `dialogue.py` | Regresiones y secuencias guardadas | Validación integral con persona |
| Entrada cámara/vídeo | `capture.py`, lanzador | Vídeo con y sin ventana, entrada errónea | Abrir cámara elegida por Alejandro |
| Multiusuario/errores | `PrimaryUser`, contratos None/caducidad | Selección y fallos simulados | Dos personas reales, sustitución en misma posición |

Tabla 2. Trazabilidad de requisitos. Los nombres de módulos pertenecen a `tutor/`; las comprobaciones de cámara están descritas en `docs/prueba_manual.md` y aún no se han realizado.

## Avisos sonoros (15 de octubre de 2026)

Por petición posterior del equipo se añade sonido al primer y segundo aviso. `tutor/audio.py` recibe los eventos de transición: una recuperación o una vuelta de descanso no produce pitidos. La reproducción se ejecuta como proceso externo y se consulta sin esperar en el bucle principal. Si llega el segundo aviso durante el primero, se conserva una única petición pendiente; no se solapan. Los fallos del reproductor se muestran y registran sin detener la percepción.

Se generó `assets/aviso.wav` con `scripts/generar_aviso.py`: dos tonos de 880 Hz y 0,18 s separados por 0,12 s; PCM mono, 16 bits y 44100 muestras/s. La amplitud digital es 0,20 del máximo y los extremos tienen rampas de 5 ms para evitar clics. El volumen audible depende del sistema.

Comando: `./ejecutar.sh tutor --test-sound`. `pw-play` completó la reproducción con código 0. Evidencias: `resultados/audio_20261015.json` y `audio_salida_20261015.txt`. No se ha confirmado con Alejandro que se oiga a volumen adecuado.

Comando de integración: `.venv-vision/bin/python scripts/prueba_audio_controlada.py --log resultados/audio_integracion_controlada_20261015.json`. Utiliza vídeo real para la captura y señales de atención artificiales para provocar avisos próximos. La primera ejecución detectó que se descartaba un aviso al estar ocupado el reproductor; se corrigió con la petición pendiente. La ejecución posterior completó dos reproducciones para dos avisos, sin errores; el final malo no genera otro pitido. Esta prueba verifica la coordinación de aplicación y audio, no precisión de visión.

Las 59 regresiones pasan; incluyen la secuencia de estados, reproducción pendiente, ausencia de esperas en el bucle, opción silenciosa, salida no disponible, proceso atascado y estructura del WAV. Comando: `.venv-vision/bin/python -m unittest discover -s tests -v`. Evidencia: `resultados/regresion_audio_20261015.txt`. También se ejecutó el tutor con el vídeo en modo `--headless --max-seconds 2`: terminó sin errores y sin solicitar sonido, como corresponde al diagnóstico silencioso.

## Revisión temporal y de estados (19-20 de octubre de 2026)

Se corrigieron las pausas por aperturas ambiguas y se revisaron temporizadores, chiste, gestos y final de entrada. Los valores y resultados anteriores se conservan como historial, no como descripción de la configuración actual. La configuración vigente, la crítica de decisiones y las pruebas están en [revision_logica.md](revision_logica.md). Las evidencias nuevas se guardan en `resultados/revision_20261019/`; pasan 96 regresiones. Los originales del profesor siguen intactos y no se ha validado todavía el ajuste personal de apertura ocular mediante un protocolo de cámara.

## Reanudación del descanso (21 de octubre de 2026)

Se reprodujo el bloqueo comunicado por Alejandro: después de una petición, bajar la mano fuera del encuadre no rearmaba el gesto. Ahora se distingue ausencia de mano en inferencias válidas de gesto ambiguo y señal no atribuible. Se permite rearmar tras 1 s sin manos detectadas con una única cara principal visible; se conserva la alternativa de bajada visible durante 0,5 s. Solo una nueva subida estable de 0,5 s genera otra petición.

Pasan 109 regresiones, incluidas trece comprobaciones nuevas de percepción, temporizadores, interfaz e integración. Se comprueban la segunda subida tras ausencia válida, la ausencia breve, el gesto ambiguo, los resultados repetidos o desordenados, los saltos entre inferencias, la falta de cara y las caras múltiples. La ausencia por sí sola nunca reanuda el descanso. Son pruebas con señales/modelos sustituidos, no una estimación de precisión visual.

El diagnóstico real de `video.mp4` produjo 96 muestras con cara y sin manos detectadas, ahora identificadas explícitamente como `hand_present=False` y `hand_up=None`. La imagen oficial produjo dos manos de 21 puntos y una mano elevada atribuida a la cara. El tutor completo terminó por `fin_video`, con 96 observaciones, 12 inferencias de expresión y cero errores registrados. El vídeo disponible no demuestra una secuencia real de pausa y reanudación. Se revisó además el texto de la interfaz mediante una imagen reconstruida del vídeo; no constituye una prueba con cámara.

Los registros, configuraciones, hashes de entradas y salidas se conservan en `resultados/manos_20261021/`. Comandos desde la raíz de P2:

```bash
.venv-vision/bin/python -m unittest discover -s tests -v
.venv-vision/bin/python scripts/diagnose_video.py --input video.mp4 --config config.json --output resultados/manos_20261021/vision_video.json
.venv-vision/bin/python scripts/diagnose_hands.py --output resultados/manos_20261021/manos_imagen.json
./ejecutar.sh tutor --input video.mp4 --headless --log resultados/manos_20261021/integracion_video.json
```

Queda pendiente repetir con Alejandro la secuencia descrita en [la prueba manual](prueba_manual.md#3-manos). Una oclusión de al menos un segundo también puede rearmar: la ausencia es una convención de interacción, no una prueba física de bajada. No se ha abierto su cámara, grabado el vídeo de entrega ni generado la memoria final.

## Indicaciones según el motivo (22 de octubre de 2026)

El mensaje genérico de espera se sustituye por una acción según el motivo técnico. `tutor/feedback.py` separa texto y decisión: no modifica paciencia, temporizadores ni estados. Las pérdidas breves que el filtro tolera conservan la lección. Si hay desatención fiable, el primer y segundo aviso mantienen su texto y añaden la corrección. Los descansos y finales conservan su mensaje. Una señal desconocida recibe ayuda para recuperar la medición, sin añadir un aviso de desatención.

Antes del cambio se reprodujo con modelos sustituidos que `inclinacion_excesiva` quedaba reemplazado por `sin_malla_correspondiente`: la prueba falló y su salida se conserva en `resultados/mensajes_20261022/regresion_motivo_antes.txt`. Ahora `vision.py` conserva por separado `head_error` y `eye_error` y prioriza el fallo de cabeza, coherentemente con la fusión.

Pasan 121 pruebas mediante `.venv-vision/bin/python -m unittest discover -s tests -v`; salida en `resultados/mensajes_20261022/regresion.txt`. Cubren la corrección de postura, acciones distintas por motivo, ausencia de acusación de cierre ante apertura ambigua, tolerancia temporal, conservación de avisos, descanso y finales, fallos técnicos y el espacio ocupado por los textos. `mensajes_simulados.json` conserva configuración, entradas y mensajes de ejemplo; son comprobaciones de selección de texto, no de precisión visual. La representación reconstruida con un fotograma del vídeo y señales simuladas se revisó visualmente para comprobar la legibilidad.

La prueba de integración usa `./ejecutar.sh tutor --input video.mp4 --headless --max-seconds 3 --log resultados/mensajes_20261022/integracion_video.json`; terminó por el límite de entrada, con 30 observaciones, cuatro inferencias de expresión y cero errores. El JSON conserva comando, configuración, hash de entrada y resultado. La revisión de posturas reales con cámara sigue pendiente según la tabla 2 de [la prueba manual](prueba_manual.md#5-tutor-completo).
