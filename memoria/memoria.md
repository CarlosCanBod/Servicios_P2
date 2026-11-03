# Práctica 2. Interacción no verbal

Tutor visual para el seguimiento de una lección

**Robótica de Servicios · Curso 2026-2027**

Alejandro Lavandeira Casais  
Carlos Adrián Cancela Bodlak  
Yago Martínez Pena

## 1. Objetivo y alcance

Desarrollamos un tutor visual que muestra una lección y adapta su respuesta a señales captadas por una cámara o procedentes de un vídeo. Integramos cuatro funciones: estimación de la orientación de la cabeza, apertura de los ojos y dirección aproximada de la mirada, detección de una mano levantada y clasificación de expresión facial. Un gestor de diálogo decide cuándo continuar, detener la lectura, pedir atención, conceder un descanso o finalizar.

Utilizamos MediaPipe para obtener puntos de referencia de cara, ojos y manos, y DeepFace para clasificar el recorte de la cara. Con OpenCV capturamos y visualizamos las imágenes. Estimamos la atención mediante una regla basada en señales visibles: no medimos el estado mental del alumno. Del mismo modo, una etiqueta de expresión no permite conocer con certeza sus sentimientos.

El enunciado plantea un diagrama de estados y varios ejemplos. Conservamos su progresión de avisos y finales, y añadimos el estado de descanso necesario para el ejemplo de la mano. No implementamos gestos de afirmación o negación mediante cabeceos, tos ni representación gráfica de un tutor. Los dos pitidos corresponden al aviso de los ejemplos. Elegimos tiempos y umbrales configurables para el prototipo; el enunciado no exige estos valores concretos.

## 2. Diseño e implementación

### 2.1. Organización y flujo de datos

La tabla 1 resume el recorrido de cada imagen. Separamos los bloques para que una inferencia lenta no obligue a detener la interfaz y para distinguir una medición desconocida de una señal negativa.

| Bloque | Función principal |
|---|---|
| Captura e interfaz | OpenCV lee cámara o vídeo; un hilo mantiene la imagen más reciente y la ventana muestra señales, mensajes y estado. |
| Percepción | Detectamos la cara principal, la malla facial y hasta dos manos con MediaPipe; después calculamos las magnitudes geométricas. |
| Expresión | Analizamos en otro proceso un recorte de la cara con DeepFace y obtenemos puntuaciones por clase. |
| Decisión | Estabilizamos la atención y los gestos con un filtro; la máquina de estados decide el diálogo. |

*Tabla 1. Bloques de la aplicación y su responsabilidad. La separación permite probar cada parte por separado; no garantiza un tiempo de respuesta máximo.*

Para la captura utilizamos un reloj monotónico con la cámara y el tiempo del fichero con vídeo. Redimensionamos la imagen a 640 píxeles de ancho por defecto. OpenCV entrega los canales en orden BGR y MediaPipe recibe RGB. Las colas tienen capacidad limitada y conservan trabajo reciente; si los modelos no llegan a procesar todas las imágenes, podemos descartar algunas. Por ello, el intervalo configurado de 0,1 s entre envíos a visión no implica una frecuencia efectiva fija de 10 imágenes por segundo.

Ejecutamos MediaPipe y DeepFace en entornos separados. En nuestra instalación, el primero requiere la distribución de OpenCV con módulos adicionales y el segundo la distribución estándar; ambas proporcionan el módulo cv2. Ejecutamos la expresión mediante un intérprete independiente que se comunica con el proceso principal por tuberías. Durante la instalación preparamos los pesos de DeepFace si todavía no están disponibles. Cara, malla y manos comparten el mismo proceso de visión: si uno de esos modelos tarda demasiado, puede retrasar las demás mediciones, aunque la interfaz siga respondiendo.

### 2.2. Cara y orientación de la cabeza

El detector devuelve un rectángulo y seis puntos aproximados por cara: centro del ojo derecho, centro del ojo izquierdo, nariz, boca, oreja derecha y oreja izquierda. Son puntos sobre una imagen bidimensional: el eje x crece hacia la derecha y el eje y hacia abajo. La figura 1 representa su disposición; los nombres «ojo A» y «ojo B» evitan depender de si la imagen se presenta espejada.

[[FIGURA_CARA]]

*Figura 1. Esquema de los seis puntos que devuelve el detector facial. Tomamos el centro entre ojos como referencia y calculamos la orientación a partir de los dos ojos, la nariz y la boca. Las orejas también forman parte de la salida del modelo.*

Distinguimos los resultados del detector y de la malla. El detector da la caja y los seis puntos; el localizador facial aporta una malla más densa para los párpados y los iris. Asociamos ambos solo cuando sus rectángulos solapan lo suficiente. Rechazamos cajas cuya anchura o altura sea inferior a 65 píxeles y detecciones por debajo de la confianza configurada, 0,60. Estos valores no demuestran por sí solos que todos los puntos sean correctos.

Seleccionamos inicialmente la cara válida de mayor área. En las siguientes observaciones buscamos el rectángulo que más se solapa con el seleccionado. Medimos el solapamiento mediante IoU: área de intersección dividida entre área de unión. Exigimos un IoU mínimo de 0,15 para conservar la asociación.

Este seguimiento es geométrico, no biométrico. Si la cara principal desaparece, el programa no cambia automáticamente a otra cara lejana. Otra persona que ocupe una posición similar puede confundirse con la seleccionada. Cuando detectamos más de una cara válida, inhibimos la atribución de manos para reducir asociaciones erróneas.

Para estimar la orientación construimos dos ejes a partir de la línea que une los ojos y proyectamos sobre ellos la nariz y la boca. Dividimos el desplazamiento lateral de la nariz por la distancia entre ojos; para la relación vertical comparamos las alturas proyectadas de nariz y boca. Ambas son razones bidimensionales sin unidades, no ángulos de giro reales. Expresamos la inclinación lateral de la línea de ojos en grados. Si supera 35° en valor absoluto, declaramos la orientación no evaluable y la interfaz pide enderezar la cabeza, siempre que el detector haya encontrado puntos válidos.

La figura 1 permite seguir el cálculo. Si A y B son los centros de los ojos, d es su distancia y C su punto medio, obtenemos el eje horizontal u al dividir el vector B−A por d. El eje vertical v es perpendicular a u. Para una nariz N y una boca M calculamos las proyecciones (N−C)·u, (N−C)·v y (M−C)·v, donde · representa el producto escalar. Así obtenemos estas dos razones:

`desplazamiento lateral = ((N−C)·u) / d`

`relación vertical = ((N−C)·v) / ((M−C)·v)`

Aceptamos orientación frontal si el valor absoluto de la primera razón es como máximo 0,23 y la segunda está entre 0,25 y 0,78. Calculamos la inclinación lateral con `atan2` a partir de la diferencia vertical y horizontal entre ojos. Si la distancia entre ojos es menor de 10 px o la geometría de boca es degenerada, no forzamos una orientación. La compensación de inclinación es útil dentro del margen, pero no elimina los errores debidos a perspectiva, puntos ocultos o baja resolución.

### 2.3. Apertura de ojos y mirada

La malla facial proporciona puntos de contorno e iris. Para estimar la apertura utilizamos el cociente de aspecto del ojo, o EAR: la suma de dos distancias entre párpados dividida por dos veces la anchura del ojo. Es una magnitud sin unidades que disminuye al cerrarse los párpados. La figura 2 identifica las distancias usadas. Si h1 y h2 son las dos separaciones entre puntos de los párpados y w es la distancia entre las esquinas del ojo, calculamos `EAR = (h1 + h2) / (2 · w)`. Por ejemplo, con h1 = h2 = 6 px y w = 40 px obtenemos EAR = 0,15.

[[FIGURA_OJO]]

*Figura 2. Esquema del cálculo de apertura para un ojo. Medimos h1, h2 y w en píxeles; el cociente EAR no tiene unidades.*

Si ambos ojos presentan un EAR igual o inferior a 0,13, los consideramos cerrados. Si ambos alcanzan al menos 0,18, los consideramos abiertos. Entre ambos valores aplicamos histéresis: si la observación anterior era de ojos abiertos y ninguno baja del umbral de cierre, conservamos esa referencia; de otro modo la apertura es ambigua. La banda reduce oscilaciones cerca de un límite y evita interpretar automáticamente un guiño como cierre de los dos ojos.

Proyectamos la posición del iris sobre los ejes de cada ojo. Consideramos la mirada aproximadamente centrada si las dos posiciones relativas quedan entre 0,30 y 0,70 horizontalmente y entre 0,15 y 0,85 verticalmente. Si la geometría es degenerada, los iris aparecen fuera del ojo o sus posiciones son inconsistentes, devolvemos un resultado desconocido. No calibramos un punto concreto de la pantalla y, si la cámara está desplazada respecto a ella, mirar a la pantalla puede no coincidir con la dirección considerada frontal.

Para cada ojo calculamos el valor horizontal como la proyección del vector que va de una esquina al iris sobre el vector entre esquinas, dividida por la longitud al cuadrado de este último. Obtenemos el valor vertical de forma análoga con los puntos superior e inferior del párpado. Una posición relativa cercana a 0 está próxima a un extremo y una cercana a 1 al otro. Además, si la altura central del párpado es inferior a 1 px, o si los valores horizontales de los dos iris difieren más de 0,25, no consideramos que la mirada esté bien medida. Estas comprobaciones evitan convertir una geometría inválida en un desvío fiable.

### 2.4. Mano levantada y descanso

El detector de manos devuelve 21 puntos por mano. Aproximamos la posición de la palma con la muñeca y los nudillos y comprobamos su proximidad horizontal a la cara. Una petición requiere una mano de tamaño suficiente y al menos tres dedos extendidos. La consideramos levantada si la palma está por encima de una altura relativa de 0,65 dentro del rectángulo de cara o, con la palma más baja, si al menos tres dedos apuntan hacia arriba y sus puntas alcanzan esa zona. La consideramos bajada visible cuando tanto la palma como, si son evaluables, las puntas quedan en la zona inferior delimitada por 0,75. Entre ambos límites hay una banda ambigua.

Obtenemos la posición de la palma promediando cinco puntos: muñeca y base de los cuatro dedos largos. Si la cara va desde y0 hasta y1, su altura es H = y1−y0 y la altura relativa de la palma es `(palma_y−y0)/H`. Como y crece hacia abajo, una razón menor significa que la palma aparece más arriba. Por ejemplo, 0,50 sitúa la palma aproximadamente a media altura de la cara; 1,00 coincide con el borde inferior. Para la proximidad admitimos la palma dentro de una banda horizontal que se extiende 1,3 veces la anchura facial a cada lado.

Para cada dedo largo usamos tres puntos: base, articulación intermedia y punta. Lo contamos como extendido si la distancia desde base a punta supera 1,35 veces la distancia de base a articulación y si el coseno entre los dos segmentos es al menos 0,5. Esta segunda condición descarta parte de los dedos flexionados. Para la alternativa con palma más baja, al menos tres de esos dedos deben apuntar hacia arriba; usamos la mediana de sus puntas para reducir el efecto de un punto aislado. Consideramos demasiado pequeña una mano de menos de 20 px de extensión máxima. Las condiciones son heurísticas geométricas y pueden fallar con oclusiones o perspectivas extremas.

No localizamos el hombro ni estimamos la postura completa: expresamos la altura respecto a la caja de la cara. Para emitir una petición exigimos una subida estable de 0,5 s. Mantener la mano arriba no genera eventos repetidos. Para permitir otra petición, exigimos una bajada visible de 0,5 s o un segundo sin manos detectadas con una única cara principal atribuible; después hace falta otra subida estable. La ausencia prolongada no demuestra una bajada física: una oclusión también puede rearmar el gesto. Mostramos marcadores de palma y puntas en pantalla para facilitar el diagnóstico.

### 2.5. Expresión facial

La caja de la cara seleccionada nos permite recortar la imagen antes de enviarla a DeepFace. En una matriz de imagen el primer índice es la fila y el segundo la columna, de modo que usamos los límites verticales y horizontales de la caja. Clasificamos ese recorte sin volver a ejecutar un detector de cara dentro de DeepFace. Si la caja es `(x0, y0, x1, y1)`, obtenemos `imagen[y0:y1, x0:x1]`: primero seleccionamos filas y después columnas. El recorte conserva el orden BGR de OpenCV. Llamamos a `DeepFace.analyze` para la acción `emotion`, con el detector interno en modo `skip`, porque ya hemos seleccionado la región de cara. El resultado contiene las puntuaciones de las clases y una etiqueta dominante; dividimos cada puntuación entre 100 para trabajar en la escala de 0 a 1. Comprobamos que estén las siete clases, que los valores sean finitos y válidos, que su suma esté próxima a 1 y que exista la clase dominante. Si la salida está incompleta o es inválida, la tratamos como un error. No volvemos a entrenar la red.

La versión instalada devuelve siete clases: enfado, disgusto, miedo, felicidad, tristeza, sorpresa y neutralidad. Normalizamos las puntuaciones a una escala de 0 a 1. Para el chiste utilizamos la clase happy como indicador de una sonrisa visible: no es una probabilidad calibrada de emoción ni una medida de atención. Solo consideramos resultados recientes, posteriores al chiste, de la sesión y cara seleccionadas. Exigimos happy de al menos 0,55 en muestras distintas que abarquen 0,4 s. Solicitamos la inferencia como mínimo cada 0,8 s, por lo que la reacción observable puede tardar más que ese mínimo de confirmación.

### 2.6. Atención y máquina de estados

La atención tiene tres salidas: atiende, no atiende y desconocida. Consideramos que el alumno atiende cuando la cabeza es aproximadamente frontal, los ojos están abiertos y la mirada está centrada. Una cabeza desviada, cierre de ambos ojos o mirada desviada, si son fiables, producen una señal negativa. Si falta la cara o una medición necesaria no es fiable, devolvemos la salida desconocida. Invalidamos directamente un error del modelo o una observación caducada.

El filtro usa tiempos en segundos. Tras confirmar atención, conserva esa clasificación durante pérdidas visuales breves de hasta 0,5 s, para no detener la lección con un parpadeo aislado. Cuando la pérdida supera ese margen, una señal negativa sostenida puede producir desatención; una señal ambigua pasa a desconocida. La vuelta a atención requiere por defecto 0,2 s de señal positiva estable. El instante exacto mostrado también depende del muestreo y del tiempo de inferencia.

La figura 3 muestra la cadena principal de estados y la tabla 2 detalla todas las entradas y salidas, incluidos el chiste y el descanso. Activamos los avisos por desatención confirmada, no por falta de medición. Contamos los valores de 4, 6 y 8 s por nivel: el segundo aviso requiere 6 s adicionales después del primero, y el final malo 8 s adicionales después del segundo. Ante una señal desconocida congelamos la lección y la paciencia; en el descanso también las detenemos, sin generar quejas. Si no recuperamos una medida fiable, esa espera puede prolongarse indefinidamente.

[[FIGURA_ESTADOS]]

*Figura 3. Cadena principal del diálogo. Contamos los tiempos de avance en cada nivel después de confirmar desatención; la recuperación baja un nivel por cada segundo de atención continua. El chiste, el descanso y el final bueno aparecen en la tabla 2.*

| Estado | Entrada | Salidas y condiciones |
|---|---|---|
| Inicial | Al arrancar, al recuperarse desde ligeramente molesto o al terminar la evaluación del chiste sin penalización. | Con atención avanza la frase; tras 4 s de desatención confirmada entra en ligeramente molesto. A los 12 s de lección efectiva presenta el chiste. Al acabar las frases pasa a final bueno. |
| Ligeramente molesto | Por desatención persistente desde inicial o análisis de expresión, por falta de reacción visible con muestras suficientes, o por recuperación desde claramente molesto. | Emite el primer aviso y puede solicitar sonido según el motivo. Tras 6 s adicionales de desatención pasa a claramente molesto; con 1 s continuo de atención vuelve a inicial. |
| Claramente molesto | Tras 6 s de desatención en ligeramente molesto. | Emite el segundo aviso. Tras 8 s adicionales pasa a final malo; con 1 s continuo de atención vuelve a ligeramente molesto. |
| Análisis de expresión | Una vez, al alcanzar 12 s de lección efectiva en inicial. | Sonrisa confirmada después del chiste: inicial. Sin reacción visible tras 5 s y con muestras válidas suficientes: ligeramente molesto. Sin muestras suficientes o con una reacción positiva no confirmada: inicial sin penalización. La desatención puede activar el aviso de 4 s. |
| Descanso | Por una subida estable de la mano desde un estado no terminal. | Congela lección y paciencia. Tras bajar o retirar la mano y confirmar una nueva subida, vuelve al estado anterior y restaura la paciencia guardada. Si vuelve al chiste, inicia otra ventana completa. |
| Final bueno | Al consumirse todas las frases. | Muestra el mensaje de finalización y termina; no acepta nuevos gestos. |
| Final malo | Tras agotarse la paciencia en claramente molesto. | Muestra el mensaje de cierre y termina; no acepta nuevos gestos. |

*Tabla 2. Entradas y salidas de cada estado. La máquina incorpora descanso para implementar el ejemplo de la mano; los finales son terminales.*

La recuperación requiere 1 s continuo de atención por nivel: desde claramente molesto volvemos primero a ligeramente molesto y después a inicial. Una mirada positiva demasiado breve no elimina toda la paciencia acumulada. La mano tiene prioridad sobre los avisos mientras la sesión no haya terminado. Presentamos un chiste una vez tras 12 s de lección efectiva; su ventana de evaluación dura 5 s de atención evaluable. Si no disponemos de suficientes resultados válidos, volvemos a inicial sin acusar falta de reacción. La lección contiene diez frases y cada una dura 3 s de contenido efectivo: 30 s en total, además de pausas y mensajes.

No implementamos los temporizadores contando fotogramas. El diálogo calcula el tiempo transcurrido entre actualizaciones y solo acumula intervalos válidos para una misma clasificación. Ante una señal desconocida congela la paciencia, reinicia la continuidad de recuperación y descarta la evidencia anterior de sonrisa. Una detección positiva aislada no renueva indefinidamente la tolerancia ante pérdidas encadenadas. La tabla 3 reúne los tiempos de la configuración inicial.

| Acción | Tiempo configurado y efecto |
|---|---|
| Envío a visión y caducidad | Al menos 0,1 s entre envíos; no utilizamos como actual una observación de más de 0,8 s. |
| Pérdida o parpadeo | 0,5 s de tolerancia o confirmación según la señal; invalidamos directamente un error técnico. |
| Recuperar atención | 0,2 s para confirmar la señal visual; después, 1 s continuo por nivel de molestia. |
| Avisos y final malo | 4 s hasta el primer aviso; 6 s adicionales hasta el segundo; 8 s adicionales hasta el final. |
| Mano | 0,5 s de subida; para rearmar, 0,5 s de bajada visible o 1 s sin manos atribuibles. |
| Lección y chiste | 3 s por frase; chiste a los 12 s de lección efectiva; ventana de reacción de 5 s evaluables. |
| Expresión | Envíos separados al menos 0,8 s; resultado válido hasta 2,5 s; confirmación de sonrisa durante 0,4 s entre muestras distintas. |
| Mensaje de recuperación | «Como iba diciendo...» permanece 2 s; ese intervalo no consume el contenido de las frases. |

*Tabla 3. Temporizadores predeterminados en segundos. La confirmación y la latencia de los modelos pueden retrasar la transición visible respecto al instante en que comienza un gesto.*

La tabla 4 reúne los umbrales geométricos principales. Elegimos estos valores para la configuración inicial y podemos ajustarlos; no los hemos calibrado para todas las personas ni condiciones de luz.

| Magnitud | Umbral o criterio configurado |
|---|---|
| Cara y puntos oculares | Confianza mínima 0,60; caja de cara de al menos 65 px de ancho y alto; distancia entre ojos de al menos 10 px. |
| Orientación de cabeza | Inclinación lateral máxima de 35°; desplazamiento lateral relativo de nariz de hasta 0,23 y relación vertical entre 0,25 y 0,78. |
| Apertura | Ambos EAR ≤ 0,13: cerrados. Ambos EAR ≥ 0,18: abiertos. La banda intermedia utiliza la referencia anterior cuando procede. |
| Iris | Posición horizontal entre 0,30 y 0,70; vertical entre 0,15 y 0,85. Las dos medidas deben ser fiables. |
| Mano | Extensión mínima de 20 px y al menos tres dedos extendidos; alturas relativas 0,65 para subir y 0,75 para bajar. |
| Cara principal | Elegimos la caja de mayor área y la conservamos si el IoU con la caja anterior es al menos 0,15. |
| Expresión | `happy` ≥ 0,55 en muestras posteriores al chiste, con confirmación temporal suficiente. |

*Tabla 4. Criterios de percepción. Las relaciones y puntuaciones son adimensionales; los tamaños mínimos están en píxeles y la inclinación en grados.*

Aplicamos las transiciones por prioridad: un final ya fijado no cambia; después atendemos un evento de mano; si estamos en descanso esperamos; a continuación tratamos los datos desconocidos, la desatención y, por último, el chiste o la lección. Solicitamos el sonido al entrar en un aviso por desatención persistente o ausencia de reacción visible. No lo repetimos en cada fotograma ni al retroceder de un nivel de molestia por recuperación.

## 3. Resultados y dificultades observadas

Durante las comprobaciones con cámara observamos cómo responde el tutor a diferentes gestos y condiciones. La tabla 5 reúne las situaciones que revisamos y lo que vimos. Estas observaciones son cualitativas: no anotamos el número de intentos ni calculamos tasas de acierto, de modo que no podemos extender los resultados a todas las personas o entornos.

| Situación | Observación y alcance |
|---|---|
| Ojos cerrados | Al cerrar los ojos, el tutor detuvo el avance de la lección. |
| Guiño | Al guiñar un ojo, el sistema quedó en duda sobre la apertura y detuvo el tiempo de la lección. |
| Inclinación | Al inclinar la cabeza en exceso, el tutor detuvo el avance. |
| Gafas | Con las gafas utilizadas, el funcionamiento fue correcto en las condiciones de nuestra comprobación. |
| Iluminación | Observamos que la luz influyó notablemente en las detecciones, aunque no medimos un intervalo en lux. |
| Mano y descanso | Conseguimos pausar y reanudar la lección con la mano después de ajustar la regla del gesto. |
| Varias personas | No realizamos una comprobación real con varios usuarios. |

*Tabla 5. Observaciones del equipo durante el uso con cámara. Los resultados describen nuestras condiciones de comprobación y no son porcentajes de precisión.*

Una dificultad apareció al solicitar un descanso: al volver a levantar la mano, el tutor podía mostrarla como bajada y no reanudar. Primero permitimos rearmar el gesto después de un intervalo sin manos detectadas. Después ampliamos la regla para admitir una palma más baja si los dedos apuntan hacia arriba y sus puntas alcanzan la zona de la cara. Con ese ajuste conseguimos pausar y reanudar. Aun así, una mano abierta cerca de la cara podría activar el gesto sin intención de pedir un descanso; no medimos la frecuencia de esa situación.

La tabla también muestra que una misma interacción puede producir resultados distintos según la visibilidad de los puntos. La iluminación, las monturas y la posición de la cámara condicionan las medidas de ojos y mirada. Cuando no logramos una medida fiable, el tutor conserva la incertidumbre: detiene el avance tras la tolerancia y no acumula paciencia negativa durante ese intervalo.

## 4. Cuestiones y limitaciones

**Cabeza inclinada y giro.** Compensamos una inclinación lateral moderada al construir los ejes de los ojos. Por encima de 35° declaramos la orientación no evaluable, siempre que el detector haya encontrado los puntos necesarios. No medimos un ángulo real máximo de giro antes de perder los ojos. El límite lateral de la nariz es una razón de imagen, no un ángulo 3D.

**Ojos cerrados y guiño.** Los umbrales permiten identificar cierres bilaterales. Toleramos temporalmente un cierre corto; si solo un ojo está cerrado, la apertura puede quedar ambigua. En nuestra comprobación con cámara, cerrar los ojos detuvo la lectura y un guiño produjo una señal dudosa que también detuvo el avance. Estas observaciones no demuestran que detectemos correctamente todos los cierres o guiños.

**Gafas, estornudo e iluminación.** El sistema funcionó correctamente con las gafas que utilizamos y observamos que la iluminación influyó notablemente. Son observaciones cualitativas: otras monturas, reflejos y movimientos pueden ocultar o desplazar los puntos estimados. Un estornudo puede combinar movimiento y cierre breve; el filtro amortigua pérdidas cortas, pero no disponemos de una medición específica de estornudos. Tampoco calculamos una tasa de acierto con gafas ni un intervalo de iluminación en lux. Si los puntos dejan de ser fiables, el sistema debe mostrar una señal desconocida en lugar de concluir que el alumno no atiende.

**Varios usuarios.** Mantenemos por solapamiento la cara inicialmente seleccionada e inhibimos la atribución de manos cuando hay varias caras válidas. No identificamos a la persona: una sustitución en la misma zona puede confundirse y una oclusión puede interrumpir el seguimiento. Si la cara de otra persona no aparece como válida, su mano podría atribuirse al usuario principal. No realizamos una comprobación real con varios usuarios.

**Expresión y reacción al chiste.** Podemos confirmar después del chiste una sonrisa que ya estaba presente; no exigimos un aumento de puntuación. Esto evita penalizar una expresión anterior, pero no demuestra que el chiste haya provocado la sonrisa. Ante un fallo, puntuaciones incompletas o falta de muestras suficientes, volvemos al diálogo sin penalizar. El recorte procede de la caja facial y no lo alineamos con una postura normalizada, por lo que su clasificación también puede variar con la orientación o la iluminación.

Las mejoras más útiles serían recoger secuencias anotadas bajo condiciones variadas, calibrar apertura ocular y mirada por usuario y medir falsos positivos, falsos negativos y latencia de extremo a extremo. Una evaluación con gafas, distintas posiciones de cámara y varias personas permitiría decidir si compensa sustituir alguna regla por un modelo más complejo.

## 5. Reproducción y conclusión

Utilizamos Linux, Python 3.12, MediaPipe 1.1.0, OpenCV 4.14.0.94 y DeepFace 0.0.101. Desde la carpeta de la aplicación ejecutamos `./instalar.sh` para crear los dos entornos y preparar los modelos; puede hacer falta conexión para instalar dependencias y descargar los pesos de DeepFace. Con `./ejecutar.sh tutor --input 0` iniciamos la cámara y con `./ejecutar.sh tutor --input video.mp4` usamos un fichero. La configuración reside en `config.json` y la lección en `leccion.txt`.

Con reglas geométricas sencillas, un filtro temporal y una máquina de estados construimos el diálogo solicitado sin entrenar modelos propios. Al tratar explícitamente las señales desconocidas evitamos que una pérdida de detección se convierta automáticamente en un aviso. Nuestras observaciones describen las situaciones comprobadas; no bastan para afirmar precisión general ni para deducir atención o emociones reales. Aprendimos a combinar medidas visuales inciertas con temporizadores y estados, y a ajustar una regla a partir de lo observado, como hicimos con la mano. También comprobamos que el funcionamiento en un caso concreto no demuestra precisión en todas las condiciones.
