# Dissertation - Biomedical Engineering
# 2020/2021
# Ana Catarina Monteiro Magalhães
#
# Computer vision for zebrafish heart beat detection
#
# File: video_analysis.py
# Date: 06-09-2021
#
# Description: In this script a video of the zebrafish is upload and the user
# selects the region of interest (ROI), region of the zebrafish heart, and the
# software calculates the intensity average of the selected pixels for every frame.
#
########################## imports #############################################

import cv2
from scipy import stats
import numpy as np

###############################################################################
# Upload of the interst video
video_name = '454-472-peixe2.MOV'
cap = cv2.VideoCapture(video_name)
success, frame = cap.read()

# Calculate the duration of the video
fps = cap.get(cv2.CAP_PROP_FPS)
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
print(frame_count)
duration_video = frame_count/fps
print(duration_video)

# Resize image of the video
# The scaling values vary depending of the video orientation
scale_percent1 = 50 # percent of original size
scale_percent2 = 50 # percent of original size
width = int(frame.shape[0]* scale_percent1 / 100)
height = int(frame.shape[1] * scale_percent2 / 100)
dim = (width, height)
resized = cv2.resize(frame, dim)

# Conversion to gray_scale
gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

# Selection of the ROI
r = cv2.selectROI(gray)

avg = []
count = 0
frames = []

while success:
    # Resize frames of the video
    scale_percent1 = 60 # percent of original size
    scale_percent2 = 50 # percent of original size
    width = int(frame.shape[0]* scale_percent1 / 100)
    height = int(frame.shape[1] * scale_percent2 / 100)
    dim = (width, height)
    resized = cv2.resize(frame, dim)

    # Conversion to gray_scale
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

    # ROI
    imCrop = gray[int(r[1]):int(r[1]+r[3]), int(r[0]):int(r[0]+r[2])]

    # Mean of the pixels intensity of the ROI
    i = np.mean(imCrop)
    avg.append(i)
    print("Mean {}".format(i))

    cv2.imshow('frame', gray)
    success,frame = cap.read()

    frames.append(count)
    count += 1

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture and save to a file the list average
cap.release()
cv2.destroyAllWindows()
with open('Mean.txt', 'w') as filehandle:
    for listitem in avg:
        filehandle.write('%f\n' % listitem)
    filehandle.write(video_name)
