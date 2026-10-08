#!/usr/bin/env python
# encoding: utf-8

import cv2 as cv
import mediapipe as mp

# constants
mp_face_detection = mp.solutions.face_detection

OJO1 = mp_face_detection.FaceKeyPoint.RIGHT_EYE
OJO2 = mp_face_detection.FaceKeyPoint.LEFT_EYE
NARIZ = mp_face_detection.FaceKeyPoint.NOSE_TIP
BOCA = mp_face_detection.FaceKeyPoint.MOUTH_CENTER
OREJA1 = mp_face_detection.FaceKeyPoint.RIGHT_EAR_TRAGION
OREJA2 = mp_face_detection.FaceKeyPoint.LEFT_EAR_TRAGION

RED = (0,0,255)
ORANGE = (0,165,255)
YELLOW =(0,255,255)

# camera
camera = cv.VideoCapture(0)

with mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5) as face_detection:
    while camera.isOpened():
        success, frame = camera.read()
        if not success:
            break
        
        # process frame
        _height, _width = frame.shape[:2]
        
        # mediapipe usa el formato RGB, opencv el formato BGR!!
        frame_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        results = face_detection.process(frame_rgb)
        frame = cv.cvtColor(frame_rgb, cv.COLOR_RGB2BGR)

        # alter frame
        if results.detections:
            for detection in results.detections:
                _nariz = mp_face_detection.get_key_point(detection, NARIZ)
                cv.circle(frame, (int(_nariz.x * _width), int(_nariz.y * _height)), 2, RED , -1)

                _ojo1 = mp_face_detection.get_key_point(detection, OJO1)
                cv.circle(frame, (int(_ojo1.x * _width), int(_ojo1.y * _height)), 2, ORANGE , -1)

                _ojo2 = mp_face_detection.get_key_point(detection, OJO2)
                cv.circle(frame, (int(_ojo2.x * _width), int(_ojo2.y * _height)), 2, YELLOW , -1)

        # show
        cv.imshow("frame", frame)

        # keyboard
        key = cv.waitKey(1)
        if key == ord('q') or key == ord('Q'):
            break
            
    cv.destroyAllWindows()
    camera.release()
