# Primera revisión con cámara

Alejandro ha comunicado pausas al parpadear y dificultades con la apertura natural de sus ojos. Se han ajustado el filtro y los umbrales; la revisión completa de esta lista sigue pendiente. No se graba vídeo ni se guardan imágenes. Los comandos escriben valores numéricos y configuración en `resultados/prueba_<detector>.json`; el tutor usa `resultados/sesion.json`. Son archivos locales ignorados por Git. Guarda tus observaciones si alguna salida no coincide con lo que haces.

## 1. Cara y orientación

Ejecuta `./ejecutar.sh cara --input 0`. Empieza solo, mirando a la cámara y con la cara entera visible. Deben aparecer seis puntos; `frontal` debería ser `True`. Un punto perdido o una cara muy pequeña pueden dar un resultado no evaluable.

Mueve la cabeza despacio a izquierda y derecha, y mira hacia abajo. Anota cuándo `frontal` cambia a `False` o desaparece la detección. No hay un ángulo máximo de giro validado: `yaw_ratio` es un desplazamiento relativo, no grados. `pitch_ratio` compara la altura de nariz y boca respecto a los ojos. Las fórmulas están en `head_geometry`, en `tutor/geometry.py`.

Inclina la cabeza hacia un hombro. Los ejes geométricos giran con los ojos, así que una inclinación moderada no debería confundirse automáticamente con un giro lateral. Más de 35 grados de roll es no evaluable. Comprueba ambos sentidos; el resultado con tu cara está pendiente.

Pulsa `q` antes de abrir otra prueba.

## 2. Ojos y mirada

Ejecuta `./ejecutar.sh ojos --input 0`. Los puntos amarillos marcan esquinas, párpados e iris. `ear_right` y `ear_left` comparan apertura vertical con anchura: valores bajos indican párpados cercanos. Las etiquetas right/left corresponden a los grupos de landmarks de MediaPipe, no a derecha/izquierda de la pantalla.

Observa los valores con ojos abiertos, ciérralos dos segundos y vuelve a abrirlos. Ambos valores deberían bajar y `ojos_abiertos` pasar a `False`. Se considera apertura clara desde 0,18 y cierre claro hasta 0,13, en ambos ojos. En la banda intermedia se mantiene «abierto» si ambos ojos venían abiertos y no cruzan el umbral de cierre; sin esa referencia, la apertura es ambigua. No se conserva «cerrado» solo por estar en la banda. Anota los valores de apertura natural y cierre real antes de volver a cambiar umbrales.

Mantén la cabeza quieta y mira hacia los lados y arriba/abajo. Debería cambiar `mirada_frontal` cuando el iris sale de las bandas configuradas. Es una dirección aproximada respecto al ojo: mirar a un extremo de la pantalla puede salir de la banda si la cámara está descentrada. No hay una calibración exacta a píxeles de pantalla.

Guiña un ojo: se espera `None`/no evaluable, sin interpretarlo como ambos ojos cerrados. Prueba un parpadeo normal. Este visor muestra apertura y mirada del detector; el tutor completo aplica además la tolerancia temporal de 0,5 s. Por eso el visor puede mostrar una apertura ambigua durante un instante mientras el tutor conserva «atiende» y su tiempo sigue avanzando.

Si tienes gafas, repite sin ellas y con ellas bajo la misma luz, si es posible. Cambia de luz frontal a luz lateral y evita comparar posiciones distintas. No existe todavía una conclusión empírica sobre gafas o iluminación para tu cámara.

## 3. Manos

Ejecuta `./ejecutar.sh manos --input 0`. Mete una mano abierta en el encuadre y comprueba que aparecen 21 puntos. Prueba ambas manos, un puño, una mano parcialmente oculta y la mano fuera de imagen. Este visor solo verifica el detector; no pide descansos.

En el tutor, una petición requiere palma por encima de aproximadamente el 65 % de la altura del rectángulo de cara, proximidad horizontal a la cara y tres dedos extendidos. Es una aproximación de petición visible; sin detector de cuerpo no se verifica una elevación respecto al hombro. Está en `raised_hand`, en `tutor/geometry.py`.

Para rearmar la petición puedes bajar la mano dentro del encuadre, por debajo del 75 % de la altura del rectángulo de cara, durante al menos 0,5 s. También puedes bajarla fuera de la imagen: mantén la cara visible y espera al menos 1 s sin manos detectadas, hasta que el panel indique «Gesto: listo para otra subida». Una subida nueva de 0,5 s permite continuar. Los tiempos están en `hand_release_s`, `hand_absent_release_s` y `hand_hold_s` de `config.json`.

El panel distingue «Mano: no detectada» (el modelo funciona, pero no encuentra manos), «gesto no claro» (ve mano, sin reconocer subida ni bajada) y «no evaluable» (no hay cara principal atribuible, hay varias caras o falla la percepción). Una ausencia breve, una mano pequeña/ambigua o cerrar el puño arriba no rearman. La ausencia prolongada es una convención para permitir bajar fuera del encuadre: una oclusión larga también podría cumplirla. Por eso la ausencia solo rearma y nunca reanuda por sí misma.

## 4. Expresión

Ejecuta `./ejecutar.sh expresion --input 0`. La carga inicial tarda unos segundos. Mira a la cámara con expresión neutra y después sonríe. Se espera alguna variación en las puntuaciones; no se exige una etiqueta concreta como prueba de lo que sientes. DeepFace analiza solo el recorte de la cara seleccionada, mediante `tutor/expression.py`.

Aparta la cara. Debe pasar a no evaluable, sin analizar el fondo. Una inferencia lenta no debería congelar la ventana. El clasificador puede confundir expresiones; no ajustes los umbrales para forzar una etiqueta a partir de una sola imagen.

## 5. Tutor completo

Ejecuta `./ejecutar.sh tutor --input 0`. Deja la cara visible y mira al frente hasta que la señal se estabilice durante 0,2 s. La lección debe avanzar; si indica desconocida, comprueba el motivo del panel antes de esperar una transición. Parpadea normalmente y comprueba que el tiempo de lección sigue avanzando durante pérdidas menores de 0,5 s. Después cierra los ojos más de un segundo para contrastar ambos casos.

Antes puedes ejecutar `./ejecutar.sh tutor --test-sound`: deberías oír dos pitidos por la salida de audio del sistema. En la sesión normal deben sonar una sola vez al aparecer cada advertencia. Compara el primer y el segundo aviso, la permanencia en el mismo estado y la recuperación de atención: mantener un aviso visible no debe repetir el sonido, ni volver a un nivel menos molesto debe producir otro pitido. Si necesitas una sesión silenciosa, añade `--no-sound`. La salida del reproductor se ha comprobado sin errores; confirmar que se oye a un volumen adecuado queda pendiente de tu revisión.

| Acción | Qué debería ocurrir con la configuración inicial | Código responsable |
|---|---|---|
| Parpadeo o apertura ambigua menor de 0,5 s | Si ya atendías, se conserva «atiende» y la lección sigue; la vuelta breve no exige otra espera | `AttentionFilter` |
| Giro o mirada lateral fiable durante 0,5 s | Se detiene el avance; tras 4 s de desatención estable, primer aviso | `AttentionFilter`, `Dialogue` |
| Ojos cerrados de forma fiable durante 0,5 s | Señal negativa estable y el mismo circuito de avisos | `AttentionFilter` |
| Seguir desatendiendo | Tras 6 s más, segundo aviso; tras 8 s más, final malo | `Dialogue` |
| Recuperar mirada frontal tras una pausa real | Confirmación visual de 0,2 s; en estados molestos se exige después 1 s continuo por nivel; un vistazo más corto no borra paciencia | `AttentionFilter`, `Dialogue` |
| Cara fuera de imagen o medida inválida persistente | Tras la tolerancia de 0,5 s, desconocida: se congelan avance y paciencia. Un fallo técnico o dato caducado se invalida directamente | `AttentionFilter`, `Dialogue` |
| Mano abierta elevada durante 0,5 s | Descanso; tiene prioridad sobre los avisos | `raised_hand`, `HandEdge`, `Dialogue` |
| Mantener mano arriba | Sigue en descanso; no genera eventos repetidos | `HandEdge` |
| Bajar mano visible al menos 0,5 s, o fuera de imagen al menos 1 s con cara visible; volver a subirla 0,5 s | El panel confirma el rearme y la nueva subida reanuda el estado anterior | `HandEdge`, `Dialogue` |
| Mano no detectada brevemente, gesto ambiguo o pérdida de cara | No rearma por ese intervalo; permanecer sin mano tampoco reanuda por sí solo | `Perception`, `HandEdge` |
| Chiste al acumular 12 s de lección | Observa expresión durante 5 s de señales evaluables | `Dialogue` |
| Sonrisa visible después del chiste | Dos o más resultados nuevos con happy desde 0,55 y separación suficiente para confirmar 0,4 s; una sonrisa ya presente también sirve | `Dialogue` |
| Sin sonrisa en varias mediciones válidas después del chiste | Primer aviso; una salida anterior al chiste, futura, aislada o caducada no permite penalizar | `Dialogue` |
| Modelo de expresión fallido/caducado | Reacción no evaluable y regreso a inicial sin penalización | `Dialogue` |
| Completar 30 s efectivos de lección | Final bueno; el chiste y las pausas alargan el tiempo total | `Dialogue` |

Tabla 1. Secuencias manuales previstas. Los tiempos de avisos se cuentan desde que la desatención ya está estable; hay demora adicional de muestreo y procesamiento. La tabla describe comportamiento esperado, no pruebas reales ya superadas.

Las indicaciones se eligen en `tutor/feedback.py`, a partir del motivo que entrega el filtro. La tabla 2 relaciona las situaciones con su indicación. Prueba estas correcciones, manteniendo cada situación más de 0,5 s para superar la tolerancia:

| Situación | Indicación esperada | Comprobación |
|---|---|---|
| Cabeza inclinada lateralmente más allá del umbral configurado (35° por defecto) | «Endereza un poco la cabeza para que pueda evaluar tu mirada.» | Motivo `inclinacion_excesiva`; volver a posición frontal debe recuperar la lección |
| Rostro/ojos demasiado pequeños para medirlos | «Acerca un poco el rostro…» si aún detecta cara y entrega `ojos_pequenos` | Si pierde por completo la cara, debe pedir revisar el encuadre |
| Sacar la cara del encuadre | Revisar el encuadre o volver a la posición de la cara seleccionada | Motivo `sin_cara_fiable` o `usuario_principal_perdido`; no castigar el tiempo sin datos |
| No se localizan bien los ojos o iris | Mirar de frente y evitar taparlos | Indicación ligada a `sin_malla_correspondiente`, `malla_invalida` o `iris_no_fiable`, sin afirmar una causa concreta |
| Ojos cerrados, cabeza o mirada desviadas de forma fiable | Indicación de abrir los ojos, orientar la cabeza o dirigir la mirada al frente | Si aparecen avisos progresivos, deben conservar su texto y añadir la acción |
| Parpadeo breve con atención previamente confirmada | Se mantiene la frase de la lección | No debe aparecer una corrección fugaz dentro de la tolerancia |
| Descanso o final mientras se pierde la cara | Se mantiene el mensaje de descanso o final | Las indicaciones de percepción no deben ocultar esos estados |

Tabla 2. Revisión manual de mensajes según el motivo detectado. Son resultados esperados, no una medición de precisión de los detectores. Una mala lectura no demuestra por sí misma poca luz, uso de gafas ni cansancio.

Al terminar, la ventana muestra el mensaje final unos tres segundos. `r` reinicia la sesión si lo pulsas antes de cerrar. Para comprobar cada final conviene iniciar una sesión nueva, sin acumular restos de una prueba anterior.

## 6. Casos adicionales del enunciado

- **Estornudo:** no hace falta provocarlo. Si ocurre naturalmente, observar si se pierde la cara o cae la apertura; una señal breve no debería provocar una cadena de avisos. Sigue pendiente de observación.
- **Varios usuarios:** la mayor cara válida inicial queda seleccionada por solapamiento entre rectángulos. Si desaparece, no se cambia a otra cara distante; usa `r` para seleccionar una nueva sesión. Otra persona en la misma posición puede confundirse: no hay identificación biométrica. Se detectan como máximo tres mallas. Las peticiones de mano se inhiben cuando FaceDetector acepta más de una cara, para reducir atribuciones erróneas.
- **Poca luz, oclusión o giro extremo:** si deja de ser medible, esperar desconocida. Eso no permite concluir que atiendas ni que desatiendas.

La selección de `ojos` en el visor individual utiliza una sola malla y no pretende resolver varios usuarios; esa política se comprueba en el tutor completo.

No cambies varios umbrales a la vez. Primero anota comando, luz aproximada, posición, gesto y valores observados; con esos datos revisaremos juntos `config.json`.
