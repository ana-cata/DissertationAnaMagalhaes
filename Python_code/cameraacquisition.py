# Dissertation - Biomedical Engineering
# 2020/2021
# Ana Catarina Monteiro Magalhães
#
# Water temperature and zebrafish vital signs Monitoring software
#
# File: cameraacquisition.py
# Date: 06-09-2021
#
# Description: This script receives the data sent by webcam and processes
# that information. Then, this information is sent to be displayed on QT inteface.
#
############################ imports ##########################################
import serial
from serial.tools import list_ports

import scipy.signal as signal
from scipy.signal import find_peaks
from scipy.optimize import curve_fit

import os
import sys
import pandas as pd
import numpy as np
import time
import random
import cv2

from PyQt5 import QtWidgets, QtCore, QtGui, uic
from PyQt5.QtWidgets import QWidget, QLabel, QApplication, QVBoxLayout
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import pyqtSignal, QObject, Qt

# from GUI_t import Ui_MainWindow_easypet_client
from teste import Ui_MainWindow

import multiprocessing
from multiprocessing import Process, Queue, Pipe, Event
import threading

############################ imports ##########################################
timestr = time.strftime("%Y%m%d-%H%M%S")
csvname = timestr + '.csv'     # File to save the original data
aviname = timestr + '.avi'    # Video file name
# parent_dir = r"C:\\Users\User\\Documents\\Universidade\\5ºano\\Dissertacao\\Python_p\\exemplomultipprocessing9"
# path = os.path.join(parent_dir, timestr)
# if not os.path.exists(path):
#     os.mkdir(path)
#     filename = os.path.join(path, csvname)
#     videoname = os.path.join(path, aviname)

class Camera_Capture: #P3 - Capture video
    def __init__(self, transferdata_cam,stop_event_cam):
         self.stop_event_cam =stop_event_cam
         self.transferdata_cam = transferdata_cam
         self.cap = cv2.VideoCapture(0)
         self.camera_reading_process()

    def camera_reading_process(self):
        while self.stop_event_cam.is_set() == False:
             ret, frame = self.cap.read()
             if ret:
                 print("P3 send {}".format("frame"))
                 self.transferdata_cam.put(frame) #Send the frame to the thread T3
        self.cap.release()

class CameraAcquisition(QtCore.QObject):
    imageReady = QtCore.pyqtSignal()
    def __init__(self, stop_event_cam, camera_is_recording, parent=None):
        super(CameraAcquisition, self).__init__(parent)
        # Variables

        self._image = QImage()
        self.width = 640
        self.height = 480
        self.codec = cv2.VideoWriter_fourcc('X', 'V', 'I', 'D')
        self.fps = 24
        self.out = cv2.VideoWriter(aviname, self.codec, self.fps, (self.width, self.height))
        self.m_busy= False
        self.busy_grabbing= False
        self.transferdata_cam = Queue()
        self.stop_event_cam =stop_event_cam
        self.m_timer = QtCore.QBasicTimer()
        self.first_frame =True
        self.camera_is_recording = camera_is_recording

    def start(self):
        self.m_timer.start(0,self)
        self.process_camera_acquisition = Process(target=Camera_Capture,  args=(
                                            self.transferdata_cam, self.stop_event_cam))
        self.process_camera_acquisition.start()

    def stop(self):
        self.m_timer.stop()
        while not self.transferdata_cam.empty():
            self.transferdata_cam.get()

        #Terminar processo P3
        self.process_camera_acquisition.kill()
        self.out.release()
        self.stop_event_cam.clear()
        self.camera_is_recording.clear()
        print("Terminei P3")

    def timerEvent(self,e):
        if e.timerId() != self.m_timer.timerId(): return

        if not self.busy_grabbing:
            threading.Thread(target=self.grab_frame).start() #T3 Recebe o frame lido da camera (de P3)


    def grab_frame(self):
        # print("T3")
        self.busy_grabbing= True
        frame = self.transferdata_cam.get()

        if not self.m_busy:
            threading.Thread(target=self.process_image, args=(frame,)).start() #(Dentro T3 cria-se T4) T4 converte o frame para QImage

        self.busy_grabbing= False

    def process_image(self, frame):
       # print("T4")
       self.m_busy= True
       if self.first_frame:     # O evento passa a True quando obtemos o primeiro frame da camera
           print("First Frame")
           self.first_frame = False
           self.camera_is_recording.set()
       self.out.write(frame)
       image = CameraAcquisition.ToQImage(frame)

       QtCore.QMetaObject.invokeMethod(self, "setImage",
       QtCore.Qt.QueuedConnection, QtCore.Q_ARG(QtGui.QImage, image))
       self.m_busy= False


    @staticmethod
    def ToQImage(im):
            im1 = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
            FlippedImage = cv2.flip(im1, 1)
            height1, width1, channel1 = FlippedImage.shape
            step1 = channel1 * width1
            qImg1 = QImage(FlippedImage.data, width1, height1, step1, QImage.Format_RGB888)
            pic = qImg1.scaled(640, 480, Qt.KeepAspectRatio)
            return pic.copy()

    def image(self):
        return self._image

    @QtCore.pyqtSlot(QImage)
    def setImage(self, image):
        if self._image == image: return
        self._image = image
        self.imageReady.emit()

    image = QtCore.pyqtProperty(QtGui.QImage, fset=setImage, fget=image, notify=imageReady)
