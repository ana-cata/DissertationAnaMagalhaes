import cv2
from scipy import stats
import numpy as np
video_name = '454-472-peixe2.MOV'
cap = cv2.VideoCapture(video_name)
success, frame = cap.read()

# Calculate the duration of the video
fps = cap.get(cv2.CAP_PROP_FPS)      # OpenCV2 version 2 used "CV_CAP_PROP_FPS"
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
print(frame_count)
duration_video = frame_count/fps
print(duration_video)

# Resize image of the video # values vary depending of the video orientation
scale_percent1 = 50 # percent of original size
scale_percent2 = 50 # percent of original size
width = int(frame.shape[0]* scale_percent1 / 100)
height = int(frame.shape[1] * scale_percent2 / 100)
dim = (width, height)
resized = cv2.resize(frame, dim)

# Conversion to gray_scale
gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
#     YCB = cv2.cvtColor(resized, cv2.COLOR_BGR2YCrCb)

#ROI
r = cv2.selectROI(gray)

avg = []
count = 0
frames = []

while success:

    # Resize image of the video
    scale_percent1 = 60 # percent of original size
    scale_percent2 = 50 # percent of original size
    width = int(frame.shape[0]* scale_percent1 / 100)
    height = int(frame.shape[1] * scale_percent2 / 100)
    dim = (width, height)
    resized = cv2.resize(frame, dim)

    # Conversion to gray_scale
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

    #ROI
    imCrop = gray[int(r[1]):int(r[1]+r[3]), int(r[0]):int(r[0]+r[2])]

    #Mean of the intensity of the ROI
    i = np.mean(imCrop)
    avg.append(i)
    print("Mean {}".format(i))

    cv2.imshow('frame', gray)
    success,frame = cap.read()

    frames.append(count)
    count += 1

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture and save to a file the list avg
cap.release()
cv2.destroyAllWindows()
with open('Mean.txt', 'w') as filehandle:
    for listitem in avg:
        filehandle.write('%f\n' % listitem)
    filehandle.write(video_name)

# cv2.imwrite("crop.jpeg",imCrop)
