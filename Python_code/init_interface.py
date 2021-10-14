# Dissertation - Biomedical Engineering
# 2020/2021
# Ana Catarina Monteiro Magalhães
#
# Water temperature and zebrafish vital signs Monitoring software
#
# File: init_interface.py
# Date: 06-09-2021
#
# Description: This script receives the data sent by the Arduino Uno and processes
# that information. Then, this information is displayed on QT inteface. In this
# script it is also receives information from the webcam and it is also displayed
# on the QT interface.
#
############################ imports ###########################################
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
import math
import multiprocessing
from multiprocessing import Process, Queue, Pipe, Event

from PyQt5 import QtWidgets, QtCore, QtGui, uic
from PyQt5.QtWidgets import QWidget, QLabel, QApplication, QVBoxLayout
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import pyqtSignal, QObject, Qt

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

#importing classes form others files
from mainwindow import Ui_MainWindow            # Estabilish comunication between
                                                # Qt and the python script.
from cameraacquisition import CameraAcquisition # File with the camera process
                                                # and threads.

################################################################################

# File names
timestr = time.strftime("%Y%m%d-%H%M%S")
csvname = timestr + '.csv'      # File to save the original sensors data
aviname = timestr + '.avi'      # Video file name

# Sampling period
ta = 0.01

# Number of samples   for 10 s
samples_10s = int((10/ta)-1)

# Interface - T1
class StartGUI(Ui_MainWindow):
    def __init__(self, window):
        Ui_MainWindow.__init__(self)                # Load interface file
        self.setupUi(window)
        self.custom_signals = CustomSignalsClass()
        SignalsConnection.__init__(self)
        self.custom_signals.update_value_in_label_trigger.emit("None")
        self.window = window

        init_plot.__init__(self) # Updates the graphic present in the interface
        self.cameraacquisition_class = CameraAcquisition(stop_event_cam, camera_is_recording)
        self.cameraacquisition_class.imageReady.connect(self._update_camera_image)

    def start_acquisition(self):
        # Stop the events and the the threads
        if self.pushButton.isChecked() == False:
            stop_event.set()
            stop_event_cam.set()
            self.cameraacquisition_class.stop()
            print('STOP')

        # Start the Arduino thread and the camera thread
        else:
            self.arduino_acquisitionthread = ArduinoNewAcquisition(self.custom_signals, self.pushButton.isChecked())
            self.cameraacquisition_class.start()
            print('START')

    # Updates the interface with the new values of water temperature and heart rate
    def update_values(self, string_input):
        self.label.setText(string_input)

    # Updates the interface with the new frame
    def _update_camera_image(self):
        self.label_image.setPixmap(QPixmap.fromImage(self.cameraacquisition_class.image))

# Class to update the graph that shows the reading of the heartbeat sensors
class init_plot:
    def __init__(self):
        self.figure_images = plt.figure()
        self.canvas_images = FigureCanvas(self.figure_images)
        self.figure_images.set_facecolor('none')
        self.canvas_images.setStyleSheet("background-color:transparent;")
        self.layout_images = QtWidgets.QGridLayout(self.widget)
        self.layout_images.setContentsMargins(0, 0, 0, 0)
        self.layout_images.addWidget(self.canvas_images)
        self.ax = self.figure_images.add_subplot(111) # create an axis
        self.xdata = list(range(200))
        self.ydata = [random.randint(0, 10) for i in range(samples_10s+1)]
        init_plot.plot(self)

    def plot(self, t = [], data_filter = [[]]):
        self.ydata = data_filter[0]
        self.xdata = np.array(t)
        self.ax.axes.set_ylim(-1,1)
        self.ax.plot(self.xdata, self.ydata, 'r')
        self.ax.set_xlabel('Time (s)')
        self.ax.set_title('Heartbeat')
        self.canvas_images.draw()
        self.canvas_images.flush_events()
        self.ax.cla()

# P2 - Receives data from Arduino Uno
class WorkingProcessor:
    def __init__(self, transferdata, stop_event, camera_is_recording):
        self.transferdata = transferdata
        self.stop_event = stop_event
        self.camera_is_recording = camera_is_recording
        self.name_serial_equipment = "Arduino Uno"
        self.serial_reading_process()

    def serial_reading_process(self):
        #Open Serial to comunicate with Arduino Uno
        ser = serial.Serial()
        port = self._check_connected_equipment()
        print(port)
        ser.baudrate  = 115200
        ser.port = port[0][0]
        ser.open()
        ser.flushInput()

        # Data acquisition from the Arduino Uno
        while self.stop_event.is_set() == False:
            x = []
            # Waits until there is 3 elements in the serial
            while len(x) != 3:
                # Read a '\n' terminated line
                ser_bytes = ser.readline()
                decoded_bytes = ser_bytes[0:len(ser_bytes) - 2].decode("utf-8")
                x = decoded_bytes.split(',')

            # self.camera_is_recording is an event that stays True when the
            # first frame from the webcam is received.
            if self.camera_is_recording.is_set():
                # Data received from Arduino Uno is saved to a file when the first
                # frame is recieved.
                with open(csvname, "a") as f:
                    # The first column has the time, the second column has the heart
                    # rate sensors readings and the third column has the thermistors
                    # readings.
                    f.write('%.2f,%d,%.2f \n' % (float(x[2]), float(x[0]), float(x[1])))

            datatosend = x
            print("P2 send {}".format(datatosend))
            self.transferdata.put(datatosend)   # Sends raw data read from Arduino
                                                # to the main process.

        ser.close()

    # Check if the serial port is available
    def _check_connected_equipment(self):
        ports_available = list(list_ports.comports())
        fishy_port = []
        for port in ports_available:
            print(port[0], '\n', port[1], '\n', port[2], '\n -----------')
            if port[1].startswith(self.name_serial_equipment):
                fishy_port.append(port)
        return fishy_port

# Data filter
class Filter_ArduinoData:
    def __init__(self, data):
        self.data = data
    def filter_data(self):
        # Filter order
        N = 2
         # Cutoff frequency
        Wn = [0.008, 0.07]
        # Butterworth  bandpass filter
        B, A = signal.butter(N, Wn, 'bandpass', output='ba')
        # Apply the filtar to the data received by the Arduino
        smooth_data = signal.filtfilt(B, A, self.data)
        return smooth_data

# Heart Rate calculation
class Calculate_Heartbeat:
    def __init__(self, t, filtered):
        self.filtered = filtered
        self.t = t


    def findpeaks(self):
        peaks, _ = find_peaks(self.filtered, height = 0.4, distance = 20,
                        threshold = 0.005)  # Returns the indices of the peaks

        heart_beat = []
        for n in range(len(peaks) - 1):
            # Time distance between two consecutive peaks
            delta_t = self.t[peaks[n + 1]] - self.t[peaks[n]]
            if delta_t < 1.5:
                # Conversion the heart rate to beats per minute (bpm)
                f_min = 60/delta_t
                heart_beat.append(f_min)
            else:
                print("error")

        return round(np.mean(heart_beat),1)


class ArduinoNewAcquisition():
    def __init__(self, signals, button_state = False):
        self.custom_signals = signals
        self.button_state = button_state
        self.start_acquisition_arduino()

    def start_acquisition_arduino(self):
        self.thread_start_acquisition = GenericThread(self.start_acquisition2thread)
        self.thread_start_acquisition.start()

    # T2
    def start_acquisition2thread(self):
        t = []
        a =[]
        heart_beat = []
        T = []

        transferdata = Queue()  # Communication channel between processes (P1 and P2)

        global process_reading_data_acquisition

        # Booting process P2
        process_reading_data_acquisition = Process(target=WorkingProcessor,
                                                   args=( transferdata,stop_event, camera_is_recording))
        process_reading_data_acquisition.start()

        n = 0
        while stop_event.is_set() == False:
            datareceive = transferdata.get() # P2 data reception - arduino raw data
            n += 1
            t.append(float(datareceive[2]))     # Time
            a.append(float(datareceive[0]))     # Hear beat reading
            T.append(float(datareceive[1]))     # Temperature reading

            if len(t) > samples_10s:
                # Arduino raw data filtering
                data_filter = Filter_ArduinoData(a[-samples_10s:]).filter_data()
                # Calculation of heart rate
                p = Calculate_Heartbeat(t[-samples_10s:], data_filter)
                # Mean of the last 10 s of temperature readings of the thermistor
                temperature = round(sum(T[-samples_10s:])/float(len(T[-samples_10s:])),2)

                if n % int(0.25/ta) == 0:
                    # Normalization of the data
                    data_filter = data_filter/max(data_filter)
                     # Sending data to init_plot function (T1 - interface)
                    self.custom_signals.trigger.emit(t[-samples_10s:], [data_filter])
                if n % int(2.5/ta) == 0:
                    # Sending the updated values of heart rate and water temperature
                    # to T1 (interface)
                    self.custom_signals.update_value_in_label_trigger.emit("{} bpm \n\n{} ºC".format(p.findpeaks(),temperature)) # Upadate the hear beat and temperature values in the GUI

        process_reading_data_acquisition.join()
        print("Finished arduino thread ")
        stop_event.clear()

class CustomSignalsClass(QObject):
    # Define new signals.
    # Signal to sent the values of heart rate e water temperature to T1
    update_value_in_label_trigger = pyqtSignal(str)
    # Signal to send filtered data to the class init_plot
    trigger = pyqtSignal(list, list)

class SignalsConnection:
    def __init__(self):
        self.pushButton.clicked.connect(lambda: self.start_acquisition())

        self.custom_signals.update_value_in_label_trigger.connect(lambda string_input="None":
                                                                    self.update_values(string_input))

        self.custom_signals.trigger.connect(lambda t = [], data_filter = []:
                                                init_plot.plot(self,t,data_filter))

class GenericThread(QtCore.QThread):
    ''' GenericThread Function
    Its composed by 3 functions that allows to start, pause and run functions in different threads generated by pyQT
    Asynchronous running. For parallel processing use  multiprocessing library
    '''
    def __init__(self, function, *args, **kwargs):
        QtCore.QThread.__init__(self)
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def __del__(self):
        self.wait()

    def run(self):
        self.function(*self.args, **self.kwargs)
        return

class MyMainWindow(QtWidgets.QMainWindow):
    def closeEvent(self, event):
        quit_msg = "Are you sure you want to Exit the software?"
        warning_msg = "WARNING: Acquisition is still running, \n please stop before leave the program!"

# Main Process P1
if __name__ == "__main__":
    multiprocessing.freeze_support()

    stop_event = Event()
    stop_event_cam = Event()
    camera_is_recording = Event()

    app = QtWidgets.QApplication(sys.argv)
    window = MyMainWindow()
    StartGUI(window)
    window.showMaximized()
    sys.exit(app.exec_())
