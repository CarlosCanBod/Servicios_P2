# Primera revisión con cámara

Esta revisión aún no se ha realizado con Alejandro. No se graba vídeo ni se guardan imágenes. Los comandos escriben valores numéricos y configuración en `resultados/prueba_<detector>.json`; el tutor usa `resultados/sesion.json`. Son archivos locales ignorados por Git. Guarda tus observaciones si alguna salida no coincide con lo que haces.

## 1. Cara y orientación

Ejecuta `./ejecutar.sh cara --input 0`. Empieza solo, mirando a la cámara y con la cara entera visible. Deben aparecer seis puntos; `frontal` debería ser `True`. Un punto perdido o una cara muy pequeña pueden dar un resultado no evaluable.

Mueve la cabeza despacio a izquierda y derecha, y mira hacia abajo. Anota cuándo `frontal` cambia a `False` o desaparece la detección. No hay un ángulo máximo de giro validado: `yaw_ratio` es un desplazamiento relativo, no grados. `pitch_ratio` compara la altura de nariz y boca respecto a los ojos. Las fórmulas están en `head_geometry`, en `tutor/geometry.py`.

Inclina la cabeza hacia un hombro. Los ejes geométricos giran con los ojos, así que una inclinación moderada no debería confundirse automáticamente con un giro lateral. Más de 35 grados de roll es no evaluable. Comprueba ambos sentidos; el resultado con tu cara está pendiente.

Pulsa `q` antes de abrir otra prueba.

## 2. Ojos y mirada

Ejecuta `./ejecutar.sh ojos --input 0`. Los puntos amarillos marcan esquinas, párpados e iris. `ear_right` y `ear_left` comparan apertura vertical con anchura: valores bajos indican párpados cercanos. Las etiquetas right/left corresponden a los grupos de landmarks de MediaPipe, no a derecha/izquierda de la pantalla.

Observa los valores con ojos abiertos, ciérralos dos segundos y vuelve a abrirlos. Ambos valores deberían bajar y `ojos_abiertos` pasar a `False`. Entre 0,18 y 0,22 se declara apertura ambigua. Si tus ojos abiertos caen cerca de esa banda, anota los valores antes de cambiar configuración.

Mantén la cabeza quieta y mira hacia los lados y arriba/abajo. Debería cambiar `mirada_frontal` cuando el iris sale de las bandas configuradas. Es una dirección aproximada respecto al ojo: mirar a un extremo de la pantalla puede salir de la banda si la cámara está descentrada. No hay una calibración exacta a píxeles de pantalla.

Guiña un ojo: se espera `None`/no evaluable, sin interpretarlo como ambos ojos cerrados. Prueba un parpadeo normal. En este visor se muestran medidas instantáneas; el filtro del tutor completo es el que evita avisos por parpadeos cortos.

Si tienes gafas, repite sin ellas y con ellas bajo la misma luz, si es posible. Cambia de luz frontal a luz lateral y evita comparar posiciones distintas. No existe todavía una conclusión empírica sobre gafas o iluminación para tu cámara.

## 3. Manos

Ejecuta `./ejecutar.sh manos --input 0`. Mete una mano abierta en el encuadre y comprueba que aparecen 21 puntos. Prueba ambas manos, un puño, una mano parcialmente oculta y la mano fuera de imagen. Este visor solo verifica el detector; no pide descansos.

En el tutor, una petición requiere palma por encima de aproximadamente el 65 % de la altura del rectángulo de cara, proximidad horizontal a la cara y tres dedos extendidos. Es una aproximación de petición visible; sin detector de cuerpo no se verifica una elevación respecto al hombro. Está en `raised_hand`, en `tutor/geometry.py`.

## 4. Expresión

Ejecuta `./ejecutar.sh expresion --input 0`. La carga inicial tarda unos segundos. Mira a la cámara con expresión neutra y después sonríe. Se espera alguna variación en las puntuaciones; no se exige una etiqueta concreta como prueba de lo que sientes. DeepFace analiza solo el recorte de la cara seleccionada, mediante `tutor/expression.py`.

Aparta la cara. Debe pasar a no evaluable, sin analizar el fondo. Una inferencia lenta no debería congelar la ventana. El clasificador puede confundir expresiones; no ajustes los umbrales para forzar una etiqueta a partir de una sola imagen.

## 5. Tutor completo

Ejecuta `./ejecutar.sh tutor --input 0`. Deja la cara visible y mira al frente hasta que la señal se estabilice durante un segundo. La lección debe avanzar; si indica desconocida, comprueba el motivo del panel antes de esperar una transición.

| Acción | Qué debería ocurrir con la configuración inicial | Código responsable |
|---|---|---|
| Parpadeo breve | Sin avisos progresivos; una apertura ambigua puede suspender momentáneamente el avance | `AttentionFilter` |
| Giro o mirada lateral fiable durante más de 0,6 s | Se detiene el avance; tras 4 s de desatención estable, primer aviso | `AttentionFilter`, `Dialogue` |
| Ojos cerrados más de 1 s | Señal negativa estable y el mismo circuito de avisos | `AttentionFilter` |
| Seguir desatendiendo | Tras 6 s más, segundo aviso; tras 8 s más, final malo | `Dialogue` |
| Recuperar mirada frontal | Estabilidad inicial de 1 s; en estados molestos se exige 1 s adicional para bajar cada nivel | `AttentionFilter`, `Dialogue` |
| Cara fuera de imagen o medida inválida | Desconocida; se congela el avance y la paciencia, sin final malo por ausencia | `AttentionFilter`, `Dialogue` |
| Mano abierta elevada durante 0,5 s | Descanso; tiene prioridad sobre los avisos | `raised_hand`, `HandEdge`, `Dialogue` |
| Mantener mano arriba | Sigue en descanso; no genera eventos repetidos | `HandEdge` |
| Bajar mano al menos 0,5 s y subirla otros 0,5 s | Reanuda el estado anterior | `HandEdge`, `Dialogue` |
| Chiste al acumular 12 s de lección | Observa expresión durante 5 s de señales evaluables | `Dialogue` |
| Aumento de happy tras el chiste | Vuelve a inicial si supera 0,55 y aumenta al menos 0,15 respecto a antes | `Dialogue` |
| Sin cambio visible con modelo válido | Primer aviso; esto es una regla del enunciado, no prueba de falta de atención real | `Dialogue` |
| Modelo de expresión fallido/caducado | Reacción no evaluable y regreso a inicial sin penalización | `Dialogue` |
| Completar 30 s efectivos de lección | Final bueno; el chiste y las pausas alargan el tiempo total | `Dialogue` |

Tabla 1. Secuencias manuales previstas. Los tiempos de avisos se cuentan desde que la desatención ya está estable; hay demora adicional de muestreo y procesamiento. La tabla describe comportamiento esperado, no pruebas reales ya superadas.

Al terminar, la ventana muestra el mensaje final unos tres segundos. `r` reinicia la sesión si lo pulsas antes de cerrar. Para comprobar cada final conviene iniciar una sesión nueva, sin acumular restos de una prueba anterior.

## 6. Casos adicionales del enunciado

- **Estornudo:** no hace falta provocarlo. Si ocurre naturalmente, observar si se pierde la cara o cae la apertura; una señal breve no debería provocar una cadena de avisos. Sigue pendiente de observación.
- **Varios usuarios:** la mayor cara válida inicial queda seleccionada por solapamiento entre rectángulos. Si desaparece, no se cambia a otra cara distante; usa `r` para seleccionar una nueva sesión. Otra persona en la misma posición puede confundirse: no hay identificación biométrica. Se detectan como máximo tres mallas. Las peticiones de mano se inhiben cuando FaceDetector acepta más de una cara, para reducir atribuciones erróneas.
- **Poca luz, oclusión o giro extremo:** si deja de ser medible, esperar desconocida. Eso no permite concluir que atiendas ni que desatiendas.

La selección de `ojos` en el visor individual utiliza una sola malla y no pretende resolver varios usuarios; esa política se comprueba en el tutor completo.

No cambies varios umbrales a la vez. Primero anota comando, luz aproximada, posición, gesto y valores observados; con esos datos revisaremos juntos `config.json`.
