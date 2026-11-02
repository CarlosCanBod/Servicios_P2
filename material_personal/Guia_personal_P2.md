# Guía personal para presentar P2: tutor visual

Para Alejandro Lavandeira Casais, Carlos Adrián Cancela Bodlak y Yago Martínez Pena. Basada en el código de la rama `AlejandroLavandeira` revisado el 2 de noviembre de 2026. Es una guía de estudio personal compartida en la rama del equipo; debe quedar fuera del ZIP de entrega.

## 1. Explicación en un minuto

«Hemos hecho un tutor que muestra una lección de un fichero de texto y adapta su respuesta a señales visuales. OpenCV obtiene imágenes de cámara o vídeo. MediaPipe detecta una cara, puntos de los ojos y manos. Con esos puntos estimamos si la cabeza está orientada hacia la cámara, si los ojos están abiertos, hacia dónde se dirige aproximadamente la mirada y si se levanta una mano. DeepFace clasifica la expresión de un recorte de la cara. Un filtro temporal convierte esas mediciones en atención, desatención o señal desconocida, y una máquina de estados decide si continuar, avisar, descansar o terminar. Si no se puede medir una señal, no asumimos que el alumno esté desatendiendo. Los umbrales son configurables y las estimaciones dependen de las condiciones de la imagen.»

La cámara y la pantalla no están necesariamente en la misma posición: decir «aproximamos mirada frontal» es más preciso que afirmar que sabemos exactamente si mira a la pantalla. Ninguna clasificación facial garantiza conocer la emoción interna.

## 2. Qué pide el enunciado y qué hace nuestra versión

- Cuatro subsistemas: cara/orientación, ojos/mirada, manos y expresión; y un gestor de diálogo que los combine.
- El diagrama propone inicial, dos grados de molestia, análisis de emoción y dos finales. El ejemplo de la mano exige además un descanso. No usamos reconocimiento de gestos de afirmación/negación ni un avatar, que el enunciado presenta como extras que no se implementan.
- Los ejemplos incluyen dos pitidos al avisar; el programa los reproduce al primer y segundo aviso. No reproduce tos. Se incorporó el sonido por petición expresa de Alejandro.
- El chiste es una prueba orientativa de reacción visible. Aquí se comprueba `happy`; una sonrisa que ya existía también puede contar si se vuelve a observar de forma suficiente después del chiste. No calculamos puntos extra de alumno.
- El enunciado propone tiempos como ejemplos; 4, 6, 8 segundos y los demás valores son decisiones de nuestra configuración, no cifras impuestas por el profesor.
- La entrega pedida es código, memoria PDF de hasta 15 páginas y vídeo en un ZIP. Se nos indicó que el vídeo será de dos minutos. Su preparación sigue aplazada.

## 3. Reparto sugerido de una presentación de 5–10 minutos

Todos deben poder responder por cualquier bloque; este reparto es solo para presentar con continuidad.

1. **Alejandro, 2–3 minutos:** problema, entrada, demostración de cara/ojos y diferencia entre desconocido y desatención.
2. **Carlos Adrián, 2–3 minutos:** estados y tiempos, demostrar un aviso, recuperación y descanso.
3. **Yago, 2–3 minutos:** expresión, arquitectura de procesos, pruebas y límites. Mostrar dónde cambiar un parámetro.
4. Reservad tiempo para preguntas y para que el profesor solicite una modificación. Si una persona domina mejor un bloque, intercambiad los papeles.

## 4. Demostración: comandos y qué se debería ver

Desde la carpeta de P2:

```bash
cd /home/alejandro/Alejandro/Robotica_Servicios/P2
./ejecutar.sh tutor --input 0
```

`0` es el índice de cámara; si corresponde a otra cámara, probar `1`. El arranque de modelos puede tardar. No hay que iniciar los dos entornos manualmente: el lanzador escoge los intérpretes. Si faltan entornos, `./instalar.sh` los prepara; en un equipo nuevo puede necesitar conexión, espacio y Python 3.12. `q` o Escape sale; `r` reinicia lección y selección de cara. `r` no vuelve a leer `config.json`: tras modificar un parámetro hay que cerrar y volver a lanzar.

Orden sugerido, siempre dejando ver el panel y esperando a que se estabilice:

1. Mirar hacia la cámara. Ver cara, ojos, mirada y `atiende`; confirmar que avanza el tiempo de lección. Señalar el rectángulo verde de la cara principal.
2. Parpadear normalmente: tras haberse confirmado atención, una pérdida breve se tolera hasta 0,5 s y no debe detener la lectura inmediatamente. Cerrar después los ojos varios segundos: la señal debe llegar a desatención si el cierre se mide con fiabilidad. Tras 4 s de desatención confirmada aparece el primer aviso y suenan dos pitidos; volver a mirar permite recuperar.
3. Levantar una mano abierta junto a la cara y mantenerla unos 0,5 s: debe aparecer descanso. Bajarla fuera de imagen manteniendo visible la cara, esperar al menos 1 s y observar `Gesto: listo para otra subida`; volver a subirla 0,5 s. También puede bajarse de forma visible 0,5 s. La ausencia de mano por sí sola no reanuda.
4. Inclinar lateralmente la cabeza. Por encima de `roll_max_deg=35` el cálculo se declara no evaluable y se pide enderezarla, siempre que los puntos permitan medir esa inclinación. Volver al centro.
5. Si hay tiempo, esperar el chiste a los 12 s de lección efectiva y sonreír cuando aparezca. DeepFace tarda y las puntuaciones varían: no prometáis una etiqueta concreta antes de probarla.
6. Si el profesor pide el final malo, mantener una señal negativa fiable: tras el primer aviso, 6 s más llevan al segundo, y 8 s más al final. El tiempo desde que se empieza a cerrar los ojos puede ser mayor porque primero se debe detectar y confirmar el cierre.

Si desaparece la cara o el iris no es medible, el resultado puede pasar a `desconocida`: se congela la lección y la paciencia. Eso no demuestra que haya detectado desatención. Con varias caras no se atribuyen manos. La prueba real con vuestra cámara, luz y gafas sigue siendo necesaria: no sustituirla por las pruebas simuladas.

Otros comandos:

```bash
./ejecutar.sh cara --input 0
./ejecutar.sh ojos --input 0
./ejecutar.sh manos --input 0
./ejecutar.sh expresion --input 0
./ejecutar.sh tutor --input video.mp4
./ejecutar.sh tutor --test-sound
./ejecutar.sh tutor --input 0 --no-sound
.venv-vision/bin/python -m unittest discover -s tests -v
```

Los cuatro visores aíslan subsistemas. `--no-emotion` desactiva el modelo de expresión y su reacción: solo es apropiado para diagnosticar, no como demostración de la práctica completa. `--headless` ejecuta sin ventana y sin sonido por defecto; es para diagnóstico. `video.mp4` es la entrada disponible del profesor: al terminar el vídeo el programa informa `fin_video`, no simula un final bueno.

El registro por defecto es `resultados/sesion.json`, local e ignorado por Git. Incluye configuración, señales, eventos, errores y tiempos; no almacena fotogramas en ese JSON. `--log RUTA` elige otro archivo.

## 5. Recorrido completo de una imagen

1. `tutor/capture.py`: `Capture` abre `cv2.VideoCapture` en un hilo. Usa tiempo monotónico para cámara y el tiempo/FPS del archivo para vídeo. Ajusta el ancho a 640 píxeles de forma predeterminada y conserva solo el fotograma reciente.
2. `tutor/app.py`: entrega imágenes nuevas a visión como máximo aproximadamente cada `sample_s=0.1` s. El muestreo y las inferencias reales pueden ser más lentos: no significa que siempre procese 10 imágenes por segundo.
3. `tutor/vision.py`: convierte BGR de OpenCV a RGB para MediaPipe y pasa un timestamp creciente en milisegundos. FaceDetector obtiene rectángulos y seis puntos; FaceLandmarker produce la malla de cara y puntos de iris; HandLandmarker obtiene hasta dos manos.
4. Selecciona una cara principal; asocia una malla por solapamiento y calcula indicadores en `tutor/geometry.py`. Una `Observation` (`tutor/signals.py`) contiene valores `True`, `False` o `None`, motivo, métricas y tiempo.
5. De la caja `(x0,y0,x1,y1)` recorta `frame[y0:y1, x0:x1].copy()`. Una matriz de imagen se indexa primero por filas `y`, después por columnas `x`. El recorte sigue en BGR para DeepFace.
6. `tutor/expression.py`, en el proceso de expresión, llama a DeepFace con `actions=['emotion']`, `detector_backend='skip'`, `enforce_detection=False` y `align=False`: ya enviamos la cara recortada. La salida se convierte de escala 0–100 a 0–1. El `ejemplo4.py` del profesor procesa el fotograma completo; el tutor usa este recorte de la cara principal.
7. `tutor/attention.py` filtra la percepción en el tiempo y genera `atiende`, `no_atiende` o `desconocida`. `HandEdge` genera eventos de subida separados.
8. `tutor/dialogue.py` combina atención, mano, reacción y reloj. `tutor/feedback.py` elige indicaciones según el motivo y `tutor/interface.py` dibuja panel y mensaje. `tutor/audio.py` reproduce el aviso en las transiciones correspondientes.

**¿Por qué procesos separados?** MediaPipe y DeepFace requieren distribuciones distintas de OpenCV que comparten el módulo `cv2`. `.venv-vision` usa `opencv-contrib-python`; `.venv` usa `opencv-python` para DeepFace. La expresión se lanza con el intérprete de su entorno y tuberías atendidas por hilos. La visión usa un proceso trabajador. Las colas acotadas favorecen datos recientes y evitan acumular fotogramas; pueden descartarse muestras y no garantizan tiempo real estricto.

## 6. Cara y orientación: qué se calcula

FaceDetector aporta posición aproximada de ojos, nariz, boca y orejas, más un rectángulo. Se selecciona inicialmente la cara aceptada de mayor área. Después se busca el rectángulo con mayor **IoU**, solapamiento dividido por unión de las áreas; se exige al menos `track_iou=0.15`. La malla se asocia a la caja de cara si IoU ≥ 0,2; este último valor está escrito en `vision.py`, no en `config.json`.

Esto es seguimiento geométrico, no reconocimiento biométrico: si otra persona ocupa el mismo lugar se puede confundir. Si se pierde la cara principal no se cambia automáticamente a una lejana; `r` permite seleccionar una nueva sesión. Si hay más de una cara aceptada se inhibe la atribución de manos.

En `head_geometry` se usan ejes definidos por la línea entre los dos ojos. `roll_deg` es la inclinación lateral de esa línea, medida en grados. Hasta el umbral configurado se compensa geométricamente la inclinación; si |roll| supera 35°, se devuelve `None` y se recomienda enderezar la cabeza. Si no se detectan bien los puntos, no se puede medir el ángulo con fiabilidad.

`yaw_ratio` es desplazamiento lateral proyectado de la nariz dividido por la distancia entre ojos; `pitch_ratio` relaciona la altura proyectada de nariz y boca. No son ángulos en grados ni una reconstrucción 3D. Por defecto se acepta |yaw_ratio| ≤ 0,23 y pitch_ratio entre 0,25 y 0,78. La orientación es una aproximación 2D; no hay una medición validada del giro real máximo.

## 7. Ojos y mirada

El **EAR**, cociente de aspecto del ojo, relaciona dos distancias entre puntos superiores e inferiores del párpado con la anchura del ojo: `(altura_1 + altura_2) / (2 × anchura)`. Es una razón sin unidades. Si los dos EAR son ≤ `ear_closed=0.13`, se clasifican como cerrados. Si los dos son ≥ `ear_open=0.18`, se clasifican como abiertos. En la zona intermedia se conserva abierto solo si ya se había confirmado abierto y ambos ojos siguen por encima de 0,13; en otro caso es ambiguo (`None`). Esta histéresis reduce oscilaciones cerca de un umbral. Un guiño puede producir un resultado ambiguo: no se fuerza a «ambos cerrados».

La posición del iris se proyecta sobre los ejes de cada ojo. La mirada se considera aproximadamente frontal si ambos iris están entre 0,30 y 0,70 horizontalmente y entre 0,15 y 0,85 verticalmente. Si la geometría es degenerada, el iris cae fuera o las posiciones horizontales difieren demasiado, se declara no evaluable. No medimos el punto exacto de la pantalla ni hacemos calibración personal.

**No bajar umbrales a ciegas:** un `ear_open` menor puede admitir ojos naturalmente poco abiertos, pero también aceptar aperturas dudosas. `ear_closed` debe seguir siendo menor que `ear_open`. La sensibilidad real depende de persona, resolución, gafas, luz y posición; el ajuste actual no se ha validado exhaustivamente con la cámara de Alejandro.

## 8. Manos: qué es una petición

MediaPipe da 21 puntos por mano. En `raised_hand` se estima la palma con puntos de muñeca y nudillos. Se exige tamaño mínimo `min_hand_px=20`, proximidad horizontal a la cara, palma por encima de aproximadamente el 65 % de la altura de la caja de cara y al menos tres dedos extendidos según distancias y dirección de segmentos. No se comprueba la posición de hombro: no hay modelo corporal completo. Un puño arriba, una mano diminuta o una posición en la banda intermedia son ambiguos.

La geometría por fotograma no es el evento final: `HandEdge` exige `hand_hold_s=0.5` s de subida estable y solo emite un evento hasta rearmarse. Se rearma con una bajada visible de `hand_release_s=0.5` s o con `hand_absent_release_s=1.0` s sin manos detectadas, si hay una única cara principal atribuible y llegan inferencias válidas. Una señal ambigua, pérdida de cara o salto largo interrumpe la continuidad. Ausencia prolongada no demuestra físicamente una bajada: una oclusión larga también puede rearmar; se necesita una nueva subida para actuar.

## 9. Atención: tres resultados y filtro temporal

`AttentionFilter.classify` aplica prioridades: falta de cara → desconocida; cabeza desviada fiable → no atiende, incluso si la malla ocular falta; cabeza no evaluable → desconocida; ojos cerrados fiables → no atiende; ojos o mirada no evaluables → desconocida; mirada desviada fiable → no atiende; cabeza frontal, ojos abiertos y mirada centrada → atiende.

El filtro añade estabilidad temporal. Si ya estaba confirmado `atiende`, tolera pérdidas breves hasta 0,5 s por defecto para evitar parar por parpadeos o detecciones aisladas. El inicio de una pérdida se comparte si alternan causas; una única muestra buena no reinicia continuamente el margen. Después de una pérdida mantenida, se necesitan por defecto `attention_recover_s=0.2` s de atención visual estable para volver a `atiende`. Ese filtro es distinto de `recover_s=1` s para bajar cada nivel de enfado.

Una observación caducada más de `stale_s=0.8` s, futura o con error de visión se invalida. Los tiempos se calculan en segundos; los fotogramas solo aportan mediciones con su instante. La tolerancia no asegura atención real durante el parpadeo: es una decisión de interacción.

## 10. Máquina de estados: lo que hay que dibujar y explicar

Estados en `tutor/dialogue.py`:

| Estado | Función | Salidas principales |
|---|---|---|
| `inicial` | Muestra frases y suma tiempo efectivo si hay atención. | Desatención sostenida → `ligeramente_molesto`; chiste → `analisis_expresion`; fin → `final_bueno`; mano → `descanso`. |
| `ligeramente_molesto` | Primer aviso: «¿Qué? ¿Continuamos?» y dos pitidos. | 6 s adicionales de desatención → `claramente_molesto`; 1 s de recuperación → `inicial`; mano → descanso. |
| `claramente_molesto` | Segundo aviso y dos pitidos. | 8 s adicionales de desatención → `final_malo`; 1 s de recuperación → `ligeramente_molesto`; mano → descanso. |
| `analisis_expresion` | Muestra chiste y evalúa muestras posteriores. | Sonrisa confirmada → inicial; sin sonrisa tras suficientes muestras válidas → ligeramente molesto; datos insuficientes → inicial sin castigo. Desatención y mano tienen prioridad. |
| `descanso` | Congela lección y paciencia; no se queja. | Nueva subida confirmada → estado anterior, con paciencia guardada. Si vuelve al chiste empieza una ventana nueva. |
| `final_bueno` | Terminó la lección. | Terminal. |
| `final_malo` | Se agotó la paciencia. | Terminal. |

Trayectoria principal: `inicial --4 s--> ligeramente molesto --6 s--> claramente molesto --8 s--> final malo`. Son **4 + 6 + 8 = 18 s de desatención confirmada acumulada en los niveles**, no que el segundo aviso ocurra a los 6 s totales. Hay además detección, tolerancia y pequeñas demoras de muestreo. Se acumulan intervalos válidos cuando la señal permanece en el mismo estado; una recuperación breve no borra automáticamente la paciencia. Un retorno suficientemente estable reinicia paciencia y reduce un nivel por cada segundo. Un intervalo desconocido congela paciencia/lección y rompe continuidad de recuperación.

El descanso tiene prioridad sobre la desatención; los finales ya fijados tienen prioridad sobre todo. La señal desconocida no hace que el tutor se enfade más. En pausa se guarda el estado y `bad_s`. «Como iba diciendo...» se muestra durante `feedback_s=2` s al recuperar el estado inicial; durante esa indicación no se consumen frases ocultas.

La lección tiene actualmente diez líneas de `leccion.txt`, con `phrase_s=3` s cada una: **30 s de contenido efectivo**, no necesariamente 30 s de reloj. Paradas, chiste, mensajes de recuperación y espera de detección alargan la duración. El chiste se lanza una sola vez cuando `lesson_s` alcanza 12 s y el sistema sigue en estado inicial. El final se muestra unos 3 s en la ventana, o se termina inmediatamente en modo headless.

## 11. Chiste y expresión: detalles que suelen preguntar

DeepFace 0.0.101 devuelve en la instalación comprobada siete clases: `angry`, `disgust`, `fear`, `happy`, `sad`, `surprise` y `neutral`; el enunciado habla de seis. No se usan predicciones de edad, género ni etnia. No entrenamos la red; cargamos el modelo y sus pesos.

Cada `emotion_period_s=0.8` s como mínimo se puede enviar un recorte reciente. Una expresión de más de `emotion_stale_s=2.5` s, con error, del futuro, sin cara actual o de otra sesión no decide la reacción. Durante una ventana de `joke_window_s=5` s de atención evaluable se acepta `happy >= happy_min=0.55`, confirmado por dos o más resultados distintos que abarquen al menos `smile_hold_s=0.4` s. Como el periodo de inferencia es 0,8 s, la siguiente muestra suele llegar después del mínimo teórico de 0,4 s. Si no hay muestras posteriores válidas suficientes, se vuelve a inicial sin castigar. Si las hay y la última es negativa, pasa a ligeramente molesto; si la última es positiva pero no se ha confirmado el tiempo requerido, vuelve sin penalizar como reacción no confirmada.

`happy=0.55` es una puntuación del modelo, no una probabilidad calibrada ni una precisión del 55 %. La expresión no se utiliza para afirmar que la persona siente algo ni para sustituir el filtro geométrico de atención.

## 12. Parámetros: dónde están y cómo cambiarlos

Los valores se leen al arrancar desde `config.json`. `tutor/config.py` define valores por defecto y valida rangos. En `config.json` no se permiten comentarios ni comas sobrantes. Tras editar, cerrar y relanzar; `r` no recarga configuración. En una demostración, usad una copia temporal para conservar los valores originales:

```bash
cp config.json /tmp/p2_config_demo.json
# Editar /tmp/p2_config_demo.json con vuestro editor
./ejecutar.sh tutor --input 0 --config /tmp/p2_config_demo.json
```

Valores actuales y efecto principal:

| Parámetro | Valor | Qué cambia |
|---|---:|---|
| `sample_s` | 0,1 s | Intervalo mínimo entre envíos a visión. Reducirlo puede aumentar carga y no garantiza más inferencias terminadas. |
| `stale_s` | 0,8 s | Antigüedad máxima aceptada y hueco máximo para continuidad de ciertas señales. |
| `away_hold_s`, `closed_hold_s`, `unknown_hold_s` | 0,5 s cada uno | Confirmación/tolerancia de desvío, cierre y pérdida no evaluable. Cambiar uno solo no siempre cambia toda la gracia: el filtro también combina límites mediante `min`. |
| `attention_recover_s` | 0,2 s | Confirmación visual para volver a atención tras una pérdida real. |
| `recover_s` | 1 s | Atención continua para reducir un nivel de molestia y limpiar paciencia. |
| `warning_s`, `escalate_s`, `finish_s` | 4, 6, 8 s | Espera de cada nivel antes del primer aviso, segundo aviso y final malo. |
| `hand_hold_s` | 0,5 s | Subida estable para emitir una petición. |
| `hand_release_s`, `hand_absent_release_s` | 0,5 y 1 s | Rearme por mano bajada visible o ausencia de manos atribuible. |
| `phrase_s` | 3 s | Tiempo efectivo por línea de lección. |
| `joke_after_s`, `joke_window_s` | 12 y 5 s | Inicio del chiste según lección efectiva y ventana para reacción con atención evaluable. |
| `smile_hold_s`, `feedback_s` | 0,4 y 2 s | Confirmación de sonrisa mediante varias muestras; duración del mensaje de transición. |
| `emotion_period_s`, `emotion_stale_s` | 0,8 y 2,5 s | Periodo mínimo de envío a expresión y antigüedad máxima del resultado. |
| `happy_min` | 0,55 | Puntuación mínima de `happy` para una muestra positiva. |
| `ear_closed`, `ear_open` | 0,13 y 0,18 | Límites de cierre y apertura; cierre debe ser menor que apertura. |
| `gaze_low`, `gaze_high` | 0,30 y 0,70 | Franja frontal horizontal del iris. |
| `gaze_vertical_low`, `gaze_vertical_high` | 0,15 y 0,85 | Franja frontal vertical del iris. |
| `yaw_max` | 0,23 | Máximo desplazamiento lateral relativo de nariz; no son grados. |
| `pitch_low`, `pitch_high` | 0,25 y 0,78 | Intervalo de relación vertical nariz/boca; no son grados. |
| `roll_max_deg` | 35° | Inclinación lateral máxima admitida para evaluar orientación. |
| `min_eye_px`, `min_face_px`, `min_hand_px` | 10, 65, 20 px | Tamaño mínimo para aceptar respectivamente geometría ocular, caja de cara y extensión de mano. |
| `face_confidence` | 0,60 | Confianza mínima configurada en los modelos de detección/presencia/seguimiento correspondientes. |
| `track_iou` | 0,15 | Solapamiento mínimo de la cara seleccionada entre observaciones. |
| `max_faces` | 3 | Máximo de mallas faciales solicitadas al FaceLandmarker; no significa identificación de tres personas. |
| `width` | 640 px | Ancho de procesamiento. Cambia coste y tamaño de detalles detectables. |

Validaciones: números positivos finitos, `width` y `max_faces` enteros, límites bajos menores que altos, valores de confianza y rangos indicados por el código ≤ 1, `sample_s < stale_s`, `unknown_hold_s <= stale_s`, `smile_hold_s <= joke_window_s`. No se validan todas las combinaciones imaginables: que un JSON sea aceptado no significa que los umbrales produzcan buena visión.

### Cambios típicos que puede pedir el profesor

- **«Que avise antes»**: cambiar en la copia `warning_s` de 4 a 2, guardar y reiniciar. Esperar aproximadamente dos segundos de señal `no_atiende` confirmada; la detección previa añade demora. `escalate_s` y `finish_s` siguen siendo tiempos adicionales.
- **«Que espere más antes de parar por un parpadeo»**: revisar conjuntamente `unknown_hold_s`, `closed_hold_s` y `away_hold_s` y la función `AttentionFilter.update`; `unknown_hold_s` no puede superar `stale_s`. Explicar que una tolerancia mayor también retrasa la respuesta a una pérdida real.
- **«Hacer la mirada menos estricta»**: ensanchar con cuidado `gaze_low`/`gaze_high`, por ejemplo 0,25/0,75 en la copia. Se admitirá más desplazamiento, con posible aumento de falsos positivos. No declarar que es más preciso sin medirlo.
- **«Cabeza más inclinada»**: aumentar `roll_max_deg`, por ejemplo de 35 a 45 grados; se amplía el rango aceptado, sin garantizar que los puntos o la orientación sigan siendo fiables.
- **«Adelantar el chiste»**: bajar `joke_after_s`, por ejemplo a 3, y dejar `phrase_s=3`. Se dispara por tiempo de lección efectiva, no solo por esperar tres segundos de reloj. Hay que tener expresión activa y cara evaluable.
- **«Que la mano actúe más rápido»**: reducir `hand_hold_s`, por ejemplo 0,5 a 0,3; puede aumentar peticiones accidentales. Para reanudar aún hay que rearmar mediante bajada/ausencia y volver a subir.
- **«Cambiar las frases»**: editar una copia de `leccion.txt`, una línea por frase, y lanzar `./ejecutar.sh tutor --input 0 --lesson /tmp/p2_leccion.txt`. La duración total es número de líneas no vacías × `phrase_s` de contenido efectivo. Una lección demasiado corta puede acabar antes del chiste.
- **«Cambiar el texto de un aviso»**: `MESSAGES` en `tutor/dialogue.py`; las instrucciones específicas de causa están en `SIGNAL_MESSAGES` de `tutor/feedback.py`. Guardar y reiniciar.
- **«Cambiar el sonido»**: el archivo es `assets/aviso.wav`; `tutor/audio.py` lo solicita al recibir ciertos eventos. Se activa en el primer/segundo aviso de desatención y en el aviso por ausencia de reacción visible, no al recuperar ni por cada fotograma.

## 13. Temporizadores y variables del código

`now` y `time_s` representan segundos de sesión/entrada. `dt` es el intervalo desde la actualización anterior. `valid_dt` solo cuenta si la clasificación se mantuvo y el intervalo no excede `stale_s`; así no atribuimos todo un hueco a un estado. `lesson_s` cuenta contenido; `bad_s` cuenta desatención en el nivel actual; `recovery_s` cuenta recuperación; `joke_s` la ventana; `message_until` limita la indicación de transición. En las transiciones se reinician temporizadores de nivel; el descanso guarda y restaura la paciencia anterior.

En `AttentionFilter`: `candidate` y `since` registran clasificación candidata y su inicio; `stable` es la salida confirmada; `loss_since` evita que pérdidas alternas renueven la gracia. En `HandEdge`, `armed` permite una nueva petición, y `since` mide cuánto dura arriba, abajo o ausente. El estado puede ser `None`: eso significa que la señal no es evaluable o es ambigua, según el campo.

## 14. Preguntas directas y respuestas cortas

**¿Qué hace MediaPipe y qué hacemos nosotros?** MediaPipe devuelve detecciones y puntos. Nuestro código calcula relaciones geométricas, umbrales, estabilidad temporal, reglas de interacción y mensajes.

**¿Para qué sirve OpenCV?** Abre cámara/vídeo, obtiene y redimensiona imágenes, convierte colores, muestra la ventana y recoge teclas. NumPy facilita distancias, vectores y recortes. Pillow dibuja texto con tildes.

**¿Por qué BGR/RGB?** OpenCV entrega por defecto imágenes BGR; MediaPipe recibe RGB. El recorte que enviamos a DeepFace mantiene BGR.

**¿Qué significa no evaluable?** Que no hay datos suficientes o fiables para decidir esa propiedad. No significa atención ni desatención; en el diálogo detiene el avance y congela la paciencia una vez vencida la tolerancia.

**¿Por qué no reacciona exactamente a los 0,5 s?** Hay que detectar el cambio, obtener varias observaciones, confirmar el intervalo y procesar/mostrar el resultado; no funciona con un reloj de fotogramas exacto.

**¿Qué pasa si cierro los ojos un segundo?** Si ambos cierres se detectan de forma fiable, tras aproximadamente 0,5 s pasan a desatención y se congela la lección; el primer aviso requiere además 4 s de desatención confirmada. Si no se distinguen los ojos, el resultado puede ser desconocido en lugar de cierre.

**¿Qué pasa si solo guiño un ojo?** Puede quedar apertura ambigua; el margen breve evita reacción inmediata. No hay una regla que garantice detectar correctamente todos los guiños reales.

**¿Qué pasa si llevo gafas?** Los reflejos o monturas pueden ocultar iris o párpados. No hay una precisión medida con gafas; comprobar frente a la cámara y declarar la incertidumbre si se pierde la geometría.

**¿Y al estornudar?** El movimiento, cierre y oclusión pueden alterar puntos. Una pérdida breve está amortiguada, pero no hay una prueba real documentada ni garantía para todos los estornudos.

**¿Qué hace la luz?** Una iluminación insuficiente, contrastes o reflejos pueden impedir la detección. No hemos establecido un rango de iluminancia ni una tasa de acierto en lux.

**¿Cuánto puedo girar la cabeza?** No tenemos un ángulo máximo real medido para la pérdida de ojos. `yaw_max=0.23` es una razón 2D; `roll_max_deg=35` sí es un ángulo lateral configurado, no una garantía de detección.

**¿Por qué se detiene si estoy mirando la pantalla?** La cámara puede estar desplazada respecto a ella, el iris puede no estar centrado según nuestras bandas o los puntos pueden fallar. Comprobar motivo y valores; esto no mide atención mental.

**¿Qué ocurre con dos personas?** Inicialmente se escoge la cara válida más grande y después se conserva por solapamiento. Si hay varias caras aceptadas no se atribuye una mano. No es identificación; un cambio de persona en la misma posición puede confundirse.

**¿Para qué sirve el `None` de la mano?** Diferencia una mano/gesto ambiguo o no atribuible de una bajada visible (`False`). Además `hand_present=False` indica que el modelo no detectó mano en una inferencia válida atribuible; después de 1 s puede rearmar, sin demostrar una bajada física.

**¿Por qué se queda pausado aunque baje la mano?** Hay que esperar el rearme y realizar una nueva subida. La cara debe ser válida; varias caras, oclusión ambigua o falta de muestras impiden acumular el tiempo. Observar el indicador de gesto.

**¿Qué diferencia hay entre emoción y expresión?** La red clasifica patrones visibles de la cara. No conoce emociones internas ni demuestra por sí sola que alguien esté atento.

**¿Y si falla DeepFace?** Una salida errónea o caducada no sirve para reaccionar al chiste; si no hay suficientes muestras válidas se vuelve a inicial sin castigo. Si el trabajador falla, el programa registra el error y desactiva ese proceso; no se reutiliza una etiqueta vieja.

**¿Por qué dos entornos?** Las versiones verificadas de MediaPipe y DeepFace piden distribuciones diferentes de OpenCV que ambas instalan `cv2`; se aislaron para evitar sobrescrituras. No significa que sea imposible usar alguna otra combinación en un solo entorno.

**¿Cuál es la mejora futura más útil?** Calibrar por usuario y evaluar con datos anotados, variedad de luz, gafas y movimientos. También se podría estudiar un modelo 3D o reconocimiento temporal, pero no se ha demostrado aquí que mejore el sistema.

**¿Por qué los avisos suenan solo una vez?** Se solicita sonido por evento de transición, no en cada vuelta del bucle. La recuperación y la vuelta del descanso no vuelven a solicitar el aviso. El reproductor funciona en proceso externo.

**¿Por qué hay un sonido si los extras dicen que no?** El propio ejemplo de diálogo incluye dos pitidos; la prohibición cita otros sonidos típicos como la tos. Implementamos el pitido de ejemplo a petición del equipo y no añadimos tos.

**¿Las 121 pruebas demuestran precisión?** No. Comprueban reglas, geometría artificial, errores e integración controlada. Las inferencias con vídeo e imagen reales muestran ejecución, sin anotaciones de referencia ni cálculo de precisión.

## 15. Evidencias disponibles y límites al afirmarlas

- En esta revisión local pasan **121 pruebas automatizadas** con `.venv-vision/bin/python -m unittest discover -s tests -v`. Incluyen señales simuladas; no certifican precisión visual.
- En `resultados/manos_20261021/vision_video.json`, el diagnóstico del vídeo proporcionó 96 muestras con cara y sin manos detectadas. Una imagen de ejemplo de MediaPipe produjo dos manos con 21 puntos y una mano elevada atribuida. Una imagen no prueba estabilidad temporal ni pausa real.
- En `resultados/mensajes_20261022/integracion_video.json`, una ejecución limitada a 3 s registró 30 observaciones, cuatro inferencias de expresión y cero errores. No demuestra el funcionamiento de todos los gestos.
- Hay más evidencias y comandos en `docs/resultados.md`. El profesor puede ver pruebas de lógica y resultados reales por separado.
- Pendiente de comprobar con los tres integrantes y la cámara: postura, gafas, diferentes niveles de luz, parpadeo natural, mirada a la pantalla, dos personas, mano y reacción al chiste. No inventar porcentajes ni afirmar validación que no hayáis observado.

## 16. Dónde abrir el código para responder

| Pregunta | Archivo y elemento |
|---|---|
| Parámetros configurables y límites admitidos | `config.json`; `tutor/config.py`, `Config.validate` |
| Fuente, modelos, actualización y teclas | `tutor/app.py`, `main`; `tutor/capture.py`, `Capture` |
| Elegir y seguir cara; recorte | `tutor/vision.py`, `PrimaryUser.select`, `Perception.process` |
| Cabeza, EAR, iris, palma/dedos | `tutor/geometry.py`, `head_geometry`, `eye_geometry`, `raised_hand` |
| Señales y frescura | `tutor/signals.py`, `Observation`, `Expression.is_fresh` |
| Atención y gesto temporal | `tutor/attention.py`, `AttentionFilter`, `HandEdge` |
| Estados, tiempos, prioridades, chiste y finales | `tutor/dialogue.py`, `State`, `Dialogue.update`, `_smile` |
| Indicaciones específicas | `tutor/feedback.py`, `SIGNAL_MESSAGES`, `tutor_message` |
| Recorte y clasificación DeepFace | `tutor/vision.py`, `tutor/expression.py`, `ExpressionDetector.analyze` |
| Procesos y comunicación | `tutor/workers.py`, `tutor/expression_service.py`, `tutor/protocol.py` |
| Mensajes en pantalla | `tutor/interface.py`, `render` |
| Pitidos | `tutor/audio.py`, `is_attention_warning`, `WarningSound` |
| Prueba manual y limitaciones | `docs/prueba_manual.md`, `docs/resultados.md` |

Si os piden cambiar un cálculo que no está en `config.json`, abrid la función concreta y explicad primero qué señal usa y qué salidas `True`/`False`/`None` puede producir. Modificad una sola condición, guardad, reiniciad el programa y verificad una situación positiva, otra negativa y una ambigua si procede. Los cambios de código deben revisarse y volver a probarse; una demostración puntual no demuestra precisión general.
