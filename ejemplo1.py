#!/usr/bin/env python
# encoding: utf-8

import cv2 as cv
import mediapipe as mp

# ------------------------------------------------------------
# MediaPipe Tasks
# ------------------------------------------------------------

BaseOptions = mp.tasks.BaseOptions
FaceDetector = mp.tasks.vision.FaceDetector
FaceDetectorOptions = mp.tasks.vision.FaceDetectorOptions
RunningMode = mp.tasks.vision.RunningMode

# ------------------------------------------------------------
# Keypoints del Face Detector
#
# MediaPipe devuelve 6 puntos en este orden:
#
# 0 -> ojo derecho
# 1 -> ojo izquierdo
# 2 -> punta de la nariz
# 3 -> centro de la boca
# 4 -> tragion de la oreja derecha
# 5 -> tragion de la oreja izquierda
# ------------------------------------------------------------

OJO1 = 0
OJO2 = 1
NARIZ = 2
BOCA = 3
OREJA1 = 4
OREJA2 = 5

# Colores OpenCV = BGR
RED = (0, 0, 255)
ORANGE = (0, 165, 255)
YELLOW = (0, 255, 255)

# ------------------------------------------------------------
# Modelo
# ------------------------------------------------------------

MODEL_PATH = "face_detector.task"
#/absolute/path/to/face_detector.task'

# ------------------------------------------------------------
# Cámara
# ------------------------------------------------------------

camera = cv.VideoCapture(0)

if not camera.isOpened():
    raise RuntimeError("No se pudo abrir la cámara")

# ------------------------------------------------------------
# Configuración del detector
# ------------------------------------------------------------

options = FaceDetectorOptions(
    base_options=BaseOptions(
        model_asset_path=MODEL_PATH
    ),
    running_mode=RunningMode.VIDEO,
    min_detection_confidence=0.5,
)

# ------------------------------------------------------------
# Detector
# ------------------------------------------------------------

with FaceDetector.create_from_options(options) as face_detector:

    timestamp_ms = 0

    while camera.isOpened():

        success, frame = camera.read()

        if not success:
            break

        # Dimensiones de la imagen
        height, width = frame.shape[:2]

        # ----------------------------------------------------
        # OpenCV: BGR
        # MediaPipe: RGB
        # ----------------------------------------------------

        frame_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)

        # Crear imagen MediaPipe
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=frame_rgb
        )

        # ----------------------------------------------------
        # Procesar frame
        # ----------------------------------------------------

        results = face_detector.detect_for_video(
            mp_image,
            timestamp_ms
        )

        timestamp_ms += 1

        # ----------------------------------------------------
        # Dibujar puntos
        # ----------------------------------------------------

        for detection in results.detections:

            # Los 6 keypoints vienen normalizados:
            # x e y están aproximadamente entre 0 y 1.

            keypoints = detection.keypoints

            # Nariz
            nariz = keypoints[NARIZ]

            cv.circle(
                frame,
                (
                    int(nariz.x * width),
                    int(nariz.y * height)
                ),
                2,
                RED,
                -1
            )

            # Ojo derecho
            ojo1 = keypoints[OJO1]

            cv.circle(
                frame,
                (
                    int(ojo1.x * width),
                    int(ojo1.y * height)
                ),
                2,
                ORANGE,
                -1
            )

            # Ojo izquierdo
            ojo2 = keypoints[OJO2]

            cv.circle(
                frame,
                (
                    int(ojo2.x * width),
                    int(ojo2.y * height)
                ),
                2,
                YELLOW,
                -1
            )

        # ----------------------------------------------------
        # Mostrar
        # ----------------------------------------------------

        cv.imshow("frame", frame)

        # ----------------------------------------------------
        # Teclado
        # ----------------------------------------------------

        key = cv.waitKey(1) & 0xFF

        if key == ord("q") or key == ord("Q"):
            break

# ------------------------------------------------------------
# Liberar recursos
# ------------------------------------------------------------

camera.release()
cv.destroyAllWindows()

