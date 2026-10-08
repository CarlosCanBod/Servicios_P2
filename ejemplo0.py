#!/usr/bin/env python
# encoding: utf-8

import cv2 as cv
import time

def _text_with_background(
    img, text, font=cv.FONT_HERSHEY_COMPLEX, fontScale=1.0, textPos=(10,10),
    textThickness=1,textColor=(0,255,0), bgColor=(0,0,0), pad_x=3, pad_y=3, bgOpacity=0.5):
    (t_w, t_h), _= cv.getTextSize(text, font, fontScale, textThickness)
    x, y = textPos
    overlay = img.copy()
    cv.rectangle(overlay, (x-pad_x, y+pad_y), (x+t_w+pad_x, y-t_h-pad_y), bgColor,-1)
    new_img = cv.addWeighted(overlay, bgOpacity, img, 1 - bgOpacity, 0)
    cv.putText(new_img,text, textPos,font, fontScale, textColor,textThickness )
    img = new_img
    return img

# camera
#camera = cv.VideoCapture("video.mp4")
camera = cv.VideoCapture(0)

# fps
frame_counter = 0
start_time = time.time()

# main loop
while(True):
    frame_counter += 1
    ret, frame = camera.read()
    if not ret:
        # end of video stream
        break

    # fps
    end_time = time.time() - start_time
    fps = frame_counter/end_time

    # alter frame
    frame = _text_with_background(frame, f'FPS: {round(fps, 1)}', textPos=(20,50), bgOpacity=0.9)

    # show frame
    cv.imshow('frame', frame)
    
    # check keyboard
    key = cv.waitKey(1)
    if key == ord('q') or key == ord('Q'):
        # please end
        break

# end of main loop
cv.destroyAllWindows()
camera.release()

