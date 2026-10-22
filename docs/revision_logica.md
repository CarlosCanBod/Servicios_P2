# Revisión del filtro y del diálogo (19-20 de octubre de 2026)

Actualización del 21 de octubre: la exigencia de bajada visible descrita en esta revisión histórica se flexibiliza tras la prueba de Alejandro. La política vigente se explica al final de este documento y en [la prueba manual](prueba_manual.md#3-manos).

Alejandro informó de pausas al parpadear y de que sus ojos, poco abiertos de forma natural, no siempre se reconocían como abiertos. Se reprodujo el primer problema antes de cambiar código: una apertura ambigua en t=1,1 s pasaba inmediatamente a desconocida y, aun volviendo a una señal válida en t=1,2 s, no recuperaba atención hasta t=2,2 s. Bajar solo un umbral no corregía esa espera.

Se revisaron captura, percepción, filtrado de atención, diálogo, manos, expresión e interfaz frente a las seis páginas de [P2.pdf](../P2.pdf), incluida la máquina de estados final. Se conservan los estados del diagrama, la recuperación por niveles y el descanso del ejemplo 4. Los tiempos concretos son decisiones del prototipo, no valores impuestos por el enunciado. No se añaden cabeceos gestuales, identificación biométrica ni avatar. Los dos pitidos corresponden a la extensión pedida previamente por Alejandro.

## Apertura y tolerancia temporal

La apertura ocular se mide mediante EAR: distancias entre párpados divididas por la anchura del ojo. Es una medida sin unidades; no es un porcentaje de apertura. Los umbrales por defecto pasan de 0,22 a 0,18 para apertura clara y de 0,18 a 0,13 para cierre claro, en ambos ojos.

La banda intermedia no se interpreta automáticamente como cierre. Si ambos ojos ya estaban abiertos y siguen por encima de 0,13, se conserva esa referencia; si no hay referencia o un ojo se cierra mientras el otro no, la medida es ambigua. Mantener una clasificación dentro de una banda evita oscilaciones cerca del umbral. No se mantiene «cerrado» solo por permanecer en esa banda: una reapertura ambigua sigue siendo incertidumbre.

Si ya había atención confirmada, se conserva durante pérdidas visuales menores de 0,5 s, incluidos parpadeos ambiguos. Si vuelve una señal positiva dentro de ese margen, el tiempo de lección continúa sin otra espera. Un fotograma positivo aislado entre pérdidas repetidas no renueva indefinidamente la tolerancia: se exige un retorno estable de 0,2 s para limpiar ese episodio.

Si la pérdida supera el margen, una señal negativa fiable puede pasar a no_atiende; una señal no evaluable pasa a desconocida. Los datos caducados y los errores técnicos se invalidan directamente. El margen no inventa atención durante el arranque ni al cambiar de sesión.

La tolerancia es una decisión de interacción: permite que la lección avance durante esos instantes breves. No demuestra que el alumno haya seguido mirando en cada instante. Una pausa real requiere 0,2 s de señal positiva para recuperar la clasificación; en estados molestos se exige además 1 s continuo por nivel para recuperar el estado del diálogo.

## Problemas corregidos

La tabla 1 relaciona cada fallo o decisión débil con el cambio y su comprobación. Los nombres de los módulos pertenecen a `tutor/`; los tests están en `tests/`.

| Problema observado en código | Cambio | Comprobación |
|---|---|---|
| Apertura ambigua interrumpía inmediatamente y añadía un segundo de recuperación | `attention.py`: tolerancia de 0,5 s y vuelta sin nueva pausa si el episodio termina dentro del margen | Parpadeos de 0,10 a 0,49 s sin pausa simulada |
| Apertura natural de EAR=0,19 se rechazaba con 0,22 | `config.py`, `geometry.py`: apertura 0,18, cierre 0,13 y banda intermedia con referencia previa | Coordenadas oculares artificiales; ajuste personal pendiente |
| Alternar desconocido y negativo podía renovar la espera; un fotograma positivo podía limpiar pérdidas repetidas | Un inicio de episodio común y retorno positivo estable | Secuencias de señales alternantes y límites en 0,49/0,50 s |
| Cabeza desviada fiable se descartaba si fallaban los ojos | Se usa la orientación negativa fiable sin exigir una malla ocular completa | Cabeza desviada con ojos no evaluables |
| Una geometría central del párpado degenerada podía parecer mirada desviada | `geometry.py`: iris no fiable si la altura central es inferior a 1 px, tras comprobar cierre | Malla artificial degenerada sin falsa desatención |
| Un vistazo fugaz borraba paciencia acumulada | `dialogue.py`: la paciencia solo se limpia con recuperación estable | Episodios negativos separados por retornos cortos |
| Se sumaba recuperación a ambos lados de un intervalo desconocido | Se reinicia esa continuidad sin castigar el tiempo sin datos | Recuperación interrumpida por desconocido o salto del reloj |
| El chiste podía ignorar desatención fiable mientras valoraba una sonrisa | La desatención tiene prioridad y conserva sus avisos progresivos | Sonrisa estimada con atención negativa simulada |
| Exigir un aumento de happy penalizaba una sonrisa ya presente | Se admite sonrisa visible confirmada después del chiste, aunque ya estuviera presente | Caso ya sonriente y caso de aparición posterior |
| Una inferencia aislada, repetida, futura o anterior al chiste podía decidir reacción | `signals.py` y `dialogue.py`: timestamps, frescura y dos o más muestras nuevas que abarquen 0,4 s | Repetición de la misma salida, resultado futuro y ausencia de muestras posteriores |
| Se podía unir evidencia de sonrisa a través de un intervalo sin atención evaluable | Se descartan las muestras anteriores a la interrupción | Sonrisa anterior a desconocido no se usa como evidencia nueva |
| Volver de descanso podía dejar casi agotada la ventana del chiste | Se inicia una ventana completa al retomar ese estado | Pausa cerca del vencimiento y reanudación |
| Perder la mano podía interpretarse como bajada; un puño arriba podía rearmar | `vision.py`, `geometry.py`: bajada visible, banda espacial y tamaño mínimo de mano | Oclusión, mano diminuta, dedos flexionados y bajada visible |
| El bucle reiniciaba el gesto entre inferencias cuando los ojos eran desconocidos | `app.py`: gesto independiente de ojos, actualizado solo con observaciones nuevas y frescas | Integración sin hardware con mano sostenida y ojos desconocidos |
| Se consumía lección mientras solo aparecía «Como iba diciendo…» | `dialogue.py`: no sumar tiempo de contenido oculto | Espera de mensaje de recuperación sin avance de frases |
| Un proceso de expresión fallido podía dejar una etiqueta anterior utilizable | `app.py`: invalidar resultado y cerrar el trabajador fallido | Frescura, error de modelo y regreso sin penalización si la reacción no es evaluable |
| EOF podía descartar la última inferencia y el cierre de ventana dejar la aplicación activa | `app.py`: espera acotada al último resultado sin sumar lección; salida al cerrar ventana | EOF con inferencia retrasada; ventanas probadas con vídeo |

Tabla 1. Revisión de decisiones y regresiones. Las señales y coordenadas artificiales verifican reglas y fórmulas; no evalúan precisión de los detectores. La recuperación sigue bajando un nivel cada vez, y los finales permanecen terminales.

## Pruebas y resultados

Antes de cambiar código pasaban 59 tests; no cubrían el fallo de apertura ambigua comunicado. Tras incorporar las regresiones pasan 96. También pasan la compilación Python, la comprobación de dependencias de ambos entornos y la verificación de que los originales del profesor no han cambiado.

Comandos reproducibles:

```bash
.venv-vision/bin/python -m unittest discover -s tests -v
.venv-vision/bin/python scripts/validar_parpadeos.py
.venv-vision/bin/python scripts/simular_dialogos.py --output resultados/revision_20261019/dialogos_simulados.json
.venv-vision/bin/python scripts/diagnose_video.py --output resultados/revision_20261019/vision_despues.json
./ejecutar.sh tutor --input video.mp4 --headless --log resultados/revision_20261019/integracion_video.json
```

En la simulación temporal, pérdidas ambiguas de 0,10, 0,20, 0,30, 0,40 y 0,49 s no producen pausa después del arranque. Una pérdida de 0,51 s produce una pausa de 0,21 s y una de 0,70 s, de 0,40 s: se conserva la primera parte tolerada y después se confirma la recuperación. El paso de simulación es 0,01 s; la aplicación utiliza segundos con muestreo configurado a 0,1 s, de modo que el instante visible también depende del muestreo y del procesamiento.

Se comprobaron los estados normales, recuperación por niveles, desconocido, descanso, tres desenlaces del chiste y ambos finales con señales simuladas. Las trazas contienen configuración, entradas y transiciones; no son una demostración visual con una persona.

El vídeo real disponible aporta 96 muestras en cada diagnóstico. Antes se obtuvieron 60 atiende y 36 desconocida. Después se obtuvieron 83 atiende, una no_atiende y 12 desconocida. Son recuentos de salidas con umbrales y filtrado distintos, no porcentajes de acierto. La muestra negativa aparece al persistir señales negativas; no se ha forzado que todo el vídeo resulte atento. Hay medidas de mirada y aperturas no evaluables que se conservan como tales.

La integración real terminó por fin_video, con 96 observaciones, 12 inferencias de expresión y cero errores registrados. También se abrieron y cerraron el visor ocular y el tutor con vídeo. La imagen oficial de manos sigue dando dos manos de 21 puntos y una petición espacial válida; no demuestra una secuencia temporal de descanso real.

Las evidencias están en `resultados/revision_20261019/`, nombre conservado de la fecha de inicio: `regresion_antes.txt`, `regresion_despues.txt`, `parpadeos_simulados.json`, `dialogos_simulados.json`, `vision_antes.json`, `vision_despues.json`, `integracion_video.json`, `manos_imagen.json` y `verificacion.json`. Los JSON guardan comandos y configuración. Las duraciones de visión se registran en milisegundos, pero los recuentos no se utilizan para afirmar mejoras de precisión ni la ejecución concurrente de diagnósticos para comparar velocidad.

## Pendiente con cámara y límites

1. Probar que tus parpadeos naturales menores de 0,5 s permiten seguir avanzando y que un cierre real de más de 0,5 s sí pausa. Si una señal es ambigua de forma persistente se pausa sin acusar desatención.
2. Anotar EAR de ambos ojos con apertura natural y cierre real bajo la misma posición y luz. Los valores 0,18/0,13 son un punto de partida más tolerante, no una calibración personal. Una cara y unos ojos geométricamente no fiables no se arreglan rebajando indefinidamente umbrales.
3. Repetir gafas, guiño, iluminación y giros. No hay aún un ángulo máximo medido de pérdida de ojos, ni cifras de exactitud. EAR, iris y orientación 2D dependen de posición y visibilidad.
4. Verificar el descanso bajando la mano dentro del encuadre. Su ausencia, un puño arriba o una mano demasiado pequeña ya no se usan como prueba de bajada. El detector de cuerpo completo sigue fuera de alcance.
5. Probar sonrisa/reacción con la cámara y el modelo real. Happy sigue siendo una clasificación de expresión, no certeza de emoción interna ni atención. La falta de datos posteriores al chiste no justifica un aviso.
6. Revisar varios usuarios: se conserva la selección geométrica de la mayor cara inicial y se evita cambiar a otra distante. Otra persona en la misma posición puede confundirse; no hay identidad biométrica. Con varias caras se inhiben peticiones de mano. Los casos reales siguen pendientes.

La memoria PDF, el screencast y el ZIP continúan aplazados. Esta revisión deja código y notas actualizadas para las pruebas manuales; no se ha abierto la cámara de Alejandro ni publicado un nuevo commit.

## Corrección de la reanudación con mano fuera de imagen (21 de octubre)

Alejandro detectó que bajar la mano fuera del encuadre impedía reanudar. Se reprodujo antes del cambio con señales controladas: subida de 0 a 0,6 s, ausencia de 0,7 a 2,1 s y segunda subida de 2,2 a 3,4 s. Solo se producía el primer evento, en 0,5 s. La política anterior evitaba falsos rearmes, pero bloqueaba un uso natural del descanso.

`Observation.hand_present` separa una inferencia válida sin manos (`False`) de una mano con gesto ambiguo (`True` con `hand_up=None`) y una señal no atribuible (`None`). Solo se informa ausencia atribuible cuando hay una única cara válida y sigue seleccionada la cara principal. Fallos del modelo, falta de cara y varias caras no autorizan este rearme.

`HandEdge` conserva la bajada visible de 0,5 s y admite como alternativa 1 s continuo sin manos detectadas (`hand_absent_release_s`). Solo observaciones nuevas y frescas acumulan esa duración. Una interrupción ambigua o un salto entre inferencias rompe la continuidad. El rearme no genera evento: hace falta otra subida válida de 0,5 s, y mantenerla arriba solo genera una petición. Los temporizadores de bajada visible y ausencia no se suman entre sí.

La interfaz muestra «no detectada», «gesto no claro» o «no evaluable», y si está listo para otra subida. No detectar una mano no prueba que esté bajada: una oclusión de al menos un segundo puede rearmar. Esta convención permite el gesto fuera de imagen; se mantiene como limitación y se comprueba manualmente con Alejandro. Las pruebas automatizadas y sus evidencias se describen en [resultados](resultados.md#reanudación-del-descanso-21-de-octubre-de-2026).
