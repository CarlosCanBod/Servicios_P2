#!/usr/bin/env python
# encoding: utf-8

import cv2 as cv
from fer import FER

emotion_detector = FER(mtcnn=True)

camera = cv.VideoCapture(0)

while(True):
    ret, frame = camera.read()
    if not ret:
        break

    cv.imshow('frame', frame)
    
    #face = emotion_detector.detect_emotions(frame)
    #print(face)

    dominant_emotion, emotion_score = emotion_detector.top_emotion(frame)
    print(dominant_emotion, emotion_score)

    key = cv.waitKey(1)
    if key == ord('q') or key == ord('Q'):
        break

cv.destroyAllWindows()
camera.release()

