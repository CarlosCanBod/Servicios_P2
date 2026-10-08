#!/usr/bin/env python
# encoding: utf-8

import cv2 as cv
import mediapipe as mp

# ============================================================
# MediaPipe Tasks
# ============================================================

BaseOptions = mp.tasks.BaseOptions
FaceLandmarker = mp.tasks.vision.FaceLandmarker
FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
RunningMode = mp.tasks.vision.RunningMode

# ============================================================
# Face landmarks
# ============================================================

FACE_OVAL = [
    10, 338, 297, 332, 284, 251, 389, 356, 454, 323,
    361, 288, 397, 365, 379, 378, 400, 377, 152, 148,
    176, 149, 150, 136, 172, 58, 132, 93, 234, 127,
    162, 21, 54, 103, 67, 109
]

LIPS = [
    61, 146, 91, 181, 84, 17, 314, 405, 321, 375,
    291, 308, 324, 318, 402, 317, 14, 87, 178, 88,
    95, 185, 40, 39, 37, 0, 267, 269, 270, 409,
    415, 310, 311, 312, 13, 82, 81, 42, 183, 78
]

LOWER_LIPS = [
    61, 146, 91, 181, 84, 17, 314, 405, 321, 375,
    291, 308, 324, 318, 402, 317, 14, 87, 178, 88,
    95
]

UPPER_LIPS = [
    185, 40, 39, 37, 0, 267, 269, 270, 409, 415,
    310, 311, 312, 13, 82, 81, 42, 183, 78
]

LEFT_EYE = [
    362, 382, 381, 380, 374, 373, 390, 249,
    263, 466, 388, 387, 386, 385, 384, 398
]

LEFT_EYEBROW = [
    336, 296, 334, 293, 300, 276, 283, 282, 295, 285
]

RIGHT_EYE = [
    33, 7, 163, 144, 145, 153, 154, 155,
    133, 173, 157, 158, 159, 160, 161, 246
]

RIGHT_EYEBROW = [
    70, 63, 105, 66, 107, 55, 65, 52, 53, 46
]

# ============================================================
# Colores OpenCV (BGR)
# ============================================================

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (255, 0, 0)
RED = (0, 0, 255)
CYAN = (255, 255, 0)
YELLOW = (0, 255, 255)
MAGENTA = (255, 0, 255)
GRAY = (128, 128, 128)
GREEN = (0, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (0, 165, 255)
PINK = (147, 20, 255)

# ============================================================
# Obtener coordenadas de landmarks
# ============================================================

def landmarks_detection(img, face_landmarks, draw=False):

    height, width = img.shape[:2]

    mesh_coord = [
        (
            int(point.x * width),
            int(point.y * height)
        )
        for point in face_landmarks
    ]

    if draw:
        for point in mesh_coord:
            cv.circle(
                img,
                point,
                2,
                GREEN,
                -1
            )

    return mesh_coord

# ============================================================
# Dibujar puntos de un grupo de landmarks
# ============================================================

def draw_landmarks(img, mesh_coord, indexes, color, radius=1):

    for index in indexes:

        cv.circle(
            img,
            mesh_coord[index],
            radius,
            color,
            -1,
            cv.LINE_AA
        )

# ============================================================
# Modelo
# ============================================================

MODEL_PATH = "face_landmarker.task"

# ============================================================
# Cámara
# ============================================================

camera = cv.VideoCapture(0)

if not camera.isOpened():
    raise RuntimeError("No se pudo abrir la cámara")

# ============================================================
# Configuración Face Landmarker
# ============================================================

options = FaceLandmarkerOptions(

    base_options=BaseOptions(
        model_asset_path=MODEL_PATH
    ),

    running_mode=RunningMode.VIDEO,

    num_faces=1,

    min_face_detection_confidence=0.5,

    min_face_presence_confidence=0.5,

    min_tracking_confidence=0.5,

    output_face_blendshapes=False,

    output_facial_transformation_matrixes=False
)

# ============================================================
# Face Landmarker
# ============================================================

with FaceLandmarker.create_from_options(options) as face_landmarker:

    timestamp_ms = 0

    while camera.isOpened():

        success, frame = camera.read()

        if not success:
            break

        # ----------------------------------------------------
        # Dimensiones
        # ----------------------------------------------------

        height, width = frame.shape[:2]

        # ----------------------------------------------------
        # OpenCV BGR -> MediaPipe RGB
        # ----------------------------------------------------

        frame_rgb = cv.cvtColor(
            frame,
            cv.COLOR_BGR2RGB
        )

        # ----------------------------------------------------
        # Crear imagen MediaPipe
        # ----------------------------------------------------

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=frame_rgb
        )

        # ----------------------------------------------------
        # Detectar landmarks
        # ----------------------------------------------------

        results = face_landmarker.detect_for_video(
            mp_image,
            timestamp_ms
        )

        timestamp_ms += 1

        # ----------------------------------------------------
        # Dibujar
        # ----------------------------------------------------

        if results.face_landmarks:

            # Puede haber varias caras, aunque hemos puesto
            # num_faces=1.
            for face_landmarks in results.face_landmarks:

                mesh_coords = landmarks_detection(
                    frame,
                    face_landmarks,
                    draw=False
                )

                # --------------------------------------------
                # LABIOS
                # --------------------------------------------

                draw_landmarks(
                    frame,
                    mesh_coords,
                    LIPS,
                    GREEN
                )

                # --------------------------------------------
                # OJO DERECHO
                # --------------------------------------------

                draw_landmarks(
                    frame,
                    mesh_coords,
                    RIGHT_EYE,
                    BLUE
                )

                # --------------------------------------------
                # OJO IZQUIERDO
                # --------------------------------------------

                draw_landmarks(
                    frame,
                    mesh_coords,
                    LEFT_EYE,
                    BLUE
                )

                # --------------------------------------------
                # CEJA DERECHA
                # --------------------------------------------

                draw_landmarks(
                    frame,
                    mesh_coords,
                    RIGHT_EYEBROW,
                    BLACK
                )

                # --------------------------------------------
                # CEJA IZQUIERDA
                # --------------------------------------------

                draw_landmarks(
                    frame,
                    mesh_coords,
                    LEFT_EYEBROW,
                    BLACK
                )

                # --------------------------------------------
                # CONTORNO DE LA CARA
                # --------------------------------------------

                draw_landmarks(
                    frame,
                    mesh_coords,
                    FACE_OVAL,
                    RED
                )

        # ----------------------------------------------------
        # Mostrar
        # ----------------------------------------------------

        cv.imshow(
            "frame",
            frame
        )

        # ----------------------------------------------------
        # Teclado
        # ----------------------------------------------------

        key = cv.waitKey(1) & 0xFF

        if key == ord("q") or key == ord("Q"):
            break

# ============================================================
# Liberar recursos
# ============================================================

camera.release()
cv.destroyAllWindows()

