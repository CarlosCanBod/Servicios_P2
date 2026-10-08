#!/usr/bin/env python
# encoding: utf-8

import cv2 as cv
from deepface import DeepFace

camera = cv.VideoCapture(0)

while(True):
    ret, frame = camera.read()
    if not ret:
        break

    cv.imshow('frame', frame)

    face = DeepFace.analyze(
        frame,
        actions=["emotion"],
        detector_backend="skip",
        enforce_detection=False
    )

    #print(face[0]['emotion'])  # all
    print(face[0]['dominant_emotion'])

    key = cv.waitKey(1)
    if key == ord('q') or key == ord('Q'):
        break

cv.destroyAllWindows()
camera.release()

