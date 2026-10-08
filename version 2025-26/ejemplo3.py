#!/usr/bin/env python
# encoding: utf-8

import cv2 as cv
import mediapipe as mp
import numpy as np

# constants
map_face_mesh = mp.solutions.face_mesh

# official face landmarks
FACE_OVAL = [ 10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103,67, 109]
LIPS = [ 61, 146, 91, 181, 84, 17, 314, 405, 321, 375,291, 308, 324, 318, 402, 317, 14, 87, 178, 88, 95,185, 40, 39, 37,0 ,267 ,269 ,270 ,409, 415, 310, 311, 312, 13, 82, 81, 42, 183, 78 ]
LOWER_LIPS = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 308, 324, 318, 402, 317, 14, 87, 178, 88, 95]
UPPER_LIPS = [ 185, 40, 39, 37,0 ,267 ,269 ,270 ,409, 415, 310, 311, 312, 13, 82, 81, 42, 183, 78] 
LEFT_EYE = [ 362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385,384, 398 ]
LEFT_EYEBROW = [ 336, 296, 334, 293, 300, 276, 283, 282, 295, 285 ]
RIGHT_EYE = [ 33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161 , 246 ]  
RIGHT_EYEBROW = [ 70, 63, 105, 66, 107, 55, 65, 52, 53, 46 ]

BLACK = (0,0,0)
WHITE = (255,255,255)
BLUE = (255,0,0)
RED = (0,0,255)
CYAN = (255,255,0)
YELLOW =(0,255,255)
MAGENTA = (255,0,255)
GRAY = (128,128,128)
GREEN = (0,255,0)
PURPLE = (128,0,128)
ORANGE = (0,165,255)
PINK = (147,20,255)

# landmarks
def landmarks_detection(img, results, draw=False):
    _height, _width= img.shape[:2]
    mesh_coord = [(int(point.x*_width), int(point.y*_height)) for point in results.multi_face_landmarks[0].landmark]
    if draw:
        [cv.circle(img, p, 2, GREEN, -1) for p in mesh_coord]
    return mesh_coord

# eyes
def eyes_extractor(img, right_eye_coords, left_eye_coords):

    # creating gray image and mask
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    mask = np.zeros(gray.shape, dtype=np.uint8)

    # drawing Eyes Shape on mask with white color 
    cv.fillPoly(mask, [np.array(right_eye_coords, dtype=np.int32)], 255)
    cv.fillPoly(mask, [np.array(left_eye_coords, dtype=np.int32)], 255)

    # draw eyes image on mask, where white shape is 
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    eyes = cv.bitwise_and(gray, gray, mask=mask)
    
    # show
    cv.imshow('eyes draw', eyes)
    
    # getting minium and maximum x and y for right and left eyes 
    # RIGHT
    r_max_x = (max(right_eye_coords, key=lambda item: item[0]))[0]
    r_min_x = (min(right_eye_coords, key=lambda item: item[0]))[0]
    r_max_y = (max(right_eye_coords, key=lambda item: item[1]))[1]
    r_min_y = (min(right_eye_coords, key=lambda item: item[1]))[1]
    # LEFT
    l_max_x = (max(left_eye_coords, key=lambda item: item[0]))[0]
    l_min_x = (min(left_eye_coords, key=lambda item: item[0]))[0]
    l_max_y = (max(left_eye_coords, key=lambda item: item[1]))[1]
    l_min_y = (min(left_eye_coords, key=lambda item: item[1]))[1]

    # croping
    cropped_right = eyes[r_min_y: r_max_y, r_min_x: r_max_x]
    cropped_left = eyes[l_min_y: l_max_y, l_min_x: l_max_x]
    return cropped_right, cropped_left

# camera
camera = cv.VideoCapture(0)

with map_face_mesh.FaceMesh(min_detection_confidence =0.5, min_tracking_confidence=0.5) as face_mesh:
    while camera.isOpened():
        success, frame = camera.read()
        if not success:
            break
        
        # process frame
        _height, _width = frame.shape[:2]
        
        # mediapipe usa el formato RGB, opencv el formato BGR!!
        frame_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        results = face_mesh.process(frame_rgb)
        frame = cv.cvtColor(frame_rgb, cv.COLOR_RGB2BGR)

        # alter frame
        if results.multi_face_landmarks:
            # landmarks
            mesh_coords = landmarks_detection(frame, results, draw=False)
            
            # identify eyes
            _r_eye_coords = [mesh_coords[p] for p in RIGHT_EYE]
            _l_eye_coords = [mesh_coords[p] for p in LEFT_EYE]
            crop_r_eye, crop_l_eye = eyes_extractor(frame, _r_eye_coords, _l_eye_coords)
            
            # show eyes
            cv.imshow('right eye', crop_r_eye)
            cv.imshow('left eye', crop_l_eye)
            
            # process cropped eyes (as opencv frames)
            # ...

        # show
        cv.imshow("frame", frame)

        # keyboard
        key = cv.waitKey(1)
        if key == ord('q') or key == ord('Q'):
            break
            
    cv.destroyAllWindows()
    camera.release()
