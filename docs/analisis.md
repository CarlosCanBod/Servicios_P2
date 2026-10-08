# Análisis previo de P2 (8 de octubre de 2026)

Se han leído las seis páginas de P2.pdf y revisado visualmente la última. No se encontró AGENTS.md en P2 ni en sus directorios ascendientes. El remoto anunció HEAD -> main, commit a6e48f533f0402476f3e62cefa17db8fcc41af10. Solo existía main. Se clonó en /tmp, se comparó y se incorporó la copia Git a P2 sin colisiones. La rama local AlejandroLavandeira parte de ese commit y no tiene upstream para evitar publicar sobre main por accidente. Durante la preparación inicial no se publicaron commits.

El material original está inventariado por SHA-256 en resultados/originales_sha256.json. Los ejemplos actuales del remoto son idénticos a p2data. Los originales permanecen separados de la aplicación. La carpeta version 2025-26 contiene la API antigua mp.solutions; no constituye el enunciado actual. Los dos vídeos locales son idénticos; no son dos conjuntos independientes.

## Alcance

Obligatorios: cuatro subsistemas, integración en tutor y memoria de hasta 15 páginas; código Python y vídeo breve en ZIP. El diagrama fija inicial -> ligeramente molesto -> claramente molesto -> final malo; una recuperación baja un nivel. Inicial -> análisis de emoción al contar chiste; sonrisa -> inicial; sin reacción visible -> ligeramente molesto; fin de lección -> final bueno. El descanso del ejemplo 4 requiere un estado adicional.

Orientativos: texto real o «Blah, blah», frecuencia de captura, duración de frases, umbrales de paciencia y chiste concreto. Se elige una lección breve de texto sin audio.

Extras expresamente excluidos: reconocimiento de cabeceos de afirmación/negación, sonidos para atraer atención y avatar del tutor. No se implementan edad, género o etnia: son capacidades de la biblioteca, no requisitos.

## Crítica previa

- ejemplo0: solo captura, FPS y ventana; no valida apertura ni temporiza una lección.
- ejemplo1: FaceDetector Tasks devuelve seis puntos y los dibuja. El timestamp crece 1 ms por fotograma, no refleja el tiempo de la entrada. No determina orientación.
- ejemplo2: FaceLandmarker Tasks dibuja contornos. No calcula apertura ni dirección de mirada; num_faces=1 no permite decidir entre usuarios.
- ejemplo4: DeepFace se ejecuta síncronamente en cada fotograma, con skip y sin recortar una cara. Puede clasificar fondo y ralentiza interfaz/captura. Sin manejo de errores del modelo.
- Ninguno integra manos o estados. No hay pruebas ni configuración del tutor.

## Decisiones a comprobar

Se usa MediaPipe Tasks actual, no se intenta mantener mp.solutions. La recomendación oficial de OpenCV exige una sola distribución que proporcione cv2; instalar python y contrib a la vez es conflictivo. La versión 4.14.0.94 citada en instrucciones existe, pero no restituye una API de MediaPipe. La compatibilidad se decidirá mediante instalación, imports y ejecución, no mediante las notas.

Iris y párpados frente a contar píxeles negros: aprovechan el modelo ya disponible y evitan umbrales de intensidad dependientes de luz y maquillaje. No son seguimiento ocular calibrado a pantalla. Se usan medidas geométricas relativas y bandas de incertidumbre. La orientación con seis puntos es una aproximación explicable, no una medición 3D de yaw/pitch. Se compensa la inclinación en el plano mediante la recta entre ojos.

DeepFace es la opción preferida del enunciado y ofrece análisis de un recorte BGR con actions=['emotion']. FER también arrastra TensorFlow y OpenCV contrib; cambiar no aporta una ventaja comprobada aquí. No se afirma que una etiqueta facial mida emoción interna o atención.

Percepción y expresión se ejecutan fuera del bucle de interfaz. Las colas tienen capacidad 1: se conserva lo reciente en lugar de acumular retraso. Los resultados caducan y se invalidan al cambiar de usuario.

## Estado tras la instalación y primer prototipo

Se comprobaron Python 3.12.3, MediaPipe 1.1.0 y los tres modelos actuales. La inspección de metadatos confirmó que MediaPipe necesita OpenCV contrib y DeepFace OpenCV estándar. Se aislaron en dos entornos con versiones fijadas; ambos pip check pasan. Cambiar OpenCV no restituyó mp.solutions. La expresión usa un subproceso propio, porque multiprocessing spawn copia sys.path del padre y no sirve para aislar bibliotecas entre estos entornos sin medidas adicionales.

Por instrucción posterior de Alejandro, se preparan ahora instalación y pruebas manuales con cámara; la memoria PDF y el vídeo (duración confirmada: dos minutos) quedan para cuando hayamos terminado esas revisiones. No se ha abierto la cámara ni se ha grabado ningún vídeo.

Alejandro ha solicitado compartir estos resultados mediante un commit en AlejandroLavandeira para que los compañeros prueben el prototipo. Se incluyen instalación, código, pruebas y evidencias reproducibles; los entornos y registros personales de cámara quedan excluidos.
