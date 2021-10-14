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
import math

from PyQt5 import QtWidgets, QtCore, QtGui, uic
from PyQt5.QtWidgets import QWidget, QLabel, QApplication, QVBoxLayout
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import pyqtSignal, QObject, Qt

#importing classes form others files
from teste import Ui_MainWindow
from cameraacquisition import CameraAcquisition

import multiprocessing
from multiprocessing import Process, Queue, Pipe, Event

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas # se quiserem usar o matplotlib
from matplotlib.figure import Figure
########################### imports #######################################

timestr = time.strftime("%Y%m%d-%H%M%S")
csvname = timestr + '.csv'     # File to save the original data
aviname = timestr + '.avi'    # Video file name
ta = 0.01
samples_10s = int((10/ta)-1)

#Erro: não se fecha o processo na thread tem de se enviar um sinal para terminar

# parent_dir = r"C:\\Users\User\\Documents\\Universidade\\5ºano\\Dissertacao\\Python_p\\exemplomultipprocessing9"
# path = os.path.join(parent_dir, timestr)
# if not os.path.exists(path):
#     os.mkdir(path)
#     filename = os.path.join(path, csvname)
#     videoname = os.path.join(path, aviname)

class StartGUI(Ui_MainWindow):
    def __init__(self, window):
        Ui_MainWindow.__init__(self)    # Carrega o ficheiro da interface (parte dos desenhos)
        self.setupUi(window)
        self.custom_signals = CustomSignalsClass()
        SignalsConnection.__init__(self)
        self.custom_signals.update_value_in_label_trigger.emit("None")
        self.window = window

        init_plot.__init__(self)
        self.cameraacquisition_class = CameraAcquisition(stop_event_cam, camera_is_recording)
        self.cameraacquisition_class.imageReady.connect(self._update_camera_image)

    def start_acquisition(self):
        if self.pushButton.isChecked() == False:
            stop_event.set()
            stop_event_cam.set()
            self.cameraacquisition_class.stop()
            print('STOP')

        else:

            #AQUI criar pasta e diretorio da pasta
            #AQUI criar nome do ficheiro e entrar como argumento do ArduinoNewAcquisition e cameraacquisition_class
            self.arduino_acquisitionthread = ArduinoNewAcquisition(self.custom_signals, self.pushButton.isChecked())
            self.cameraacquisition_class.start()
            print('START')

    def update_values(self, string_input):
        self.label.setText(string_input)

    def _update_camera_image(self):
        self.label_image.setPixmap(QPixmap.fromImage(self.cameraacquisition_class.image))

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

class WorkingProcessor: #P2 - Acquire data from arduino
    def __init__(self, transferdata, stop_event, camera_is_recording):
        self.transferdata = transferdata
        self.stop_event = stop_event
        self.camera_is_recording = camera_is_recording
        self.name_serial_equipment = "Arduino Uno"
        self.serial_reading_process()

    def serial_reading_process(self):
        #Open Serial to comunicate with arduito
        ser = serial.Serial()
        port = self._check_connected_equipment()
        print(port)
        ser.baudrate  = 115200
        ser.port = port[0][0]
        ser.open()
        ser.flushInput()

        # Acquisition of data from arduino
        while self.stop_event.is_set() == False:
            x = []
            while len(x) != 3:
                ser_bytes = ser.readline()
                decoded_bytes = ser_bytes[0:len(ser_bytes) - 2].decode("utf-8")
                x = decoded_bytes.split(',')

            if self.camera_is_recording.is_set(): # Evento fica True quando recebemos o primeiro frame da camera
                with open(csvname, "a") as f:
                    f.write('%.2f,%d,%.2f \n' % (float(x[2]), float(x[0]), float(x[1])))

            datatosend = x
            print("P2 send {}".format(datatosend))
            self.transferdata.put(datatosend) # Sending raw data read from Arduino

        ser.close()

    def _check_connected_equipment(self):
        ports_available = list(list_ports.comports())
        fishy_port = []
        for port in ports_available:
            print(port[0], '\n', port[1], '\n', port[2], '\n -----------')
            if port[1].startswith(self.name_serial_equipment):
                fishy_port.append(port)
        return fishy_port

class Filter_ArduinoData:
    def __init__(self, data):
        self.data = data

    def filter_data(self):
        N = 2  # Filter order
        Wn = [0.008, 0.07]  # Cutoff frequency
        B, A = signal.butter(N, Wn, 'bandpass', output='ba')
        smooth_data = signal.filtfilt(B, A, self.data)
        return smooth_data

class Calculate_Heartbeat:
    def __init__(self, t, filtered):
        self.filtered = filtered
        self.t = t

    def findpeaks(self):
        peaks, _ = find_peaks(self.filtered, height = 0.4, distance = 20,
                                threshold = 0.005)  # Retorna os indices dos picos
        heart_beat = []
        for n in range(len(peaks) - 1):
            delta_t = self.t[peaks[n + 1]] - self.t[peaks[n]]
            if delta_t < 1.5:
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

    def start_acquisition2thread(self): # T2
        t = []
        a =[]
        heart_beat = []
        T = []

        transferdata = Queue()  # Communication channel between processes

        global process_reading_data_acquisition
        process_reading_data_acquisition = Process(target=WorkingProcessor,
                                                   args=( transferdata,stop_event, camera_is_recording))
        process_reading_data_acquisition.start()

        n = 0
        while stop_event.is_set() == False:
            # Receção de dados brutos
            datareceive = transferdata.get() # P2 data reception - arduino raw data
            n += 1
            t.append(float(datareceive[2]))     # Time
            a.append(float(datareceive[0]))     # Amplitude
            T.append(float(datareceive[1]))     # Temperature

            if len(t) > samples_10s:
                data_filter = Filter_ArduinoData(a[-samples_10s:]).filter_data()    # Arduino raw data filtering
                p = Calculate_Heartbeat(t[-samples_10s:], data_filter)              # Calculation of heart rate
                temperature = round(sum(T[-samples_10s:])/float(len(T[-samples_10s:])),2)# Mean of the last 200 temperature readings of the thermistor

                if n % int(0.25/ta) == 0:
                    data_filter = data_filter/max(data_filter)
                    self.custom_signals.trigger.emit(t[-samples_10s:], [data_filter]) # Sending data to init_plot function (T1 - interface)
                if n % int(2.5/ta) == 0: # de 2,5s em 2,5s o valor do batimento cardíaco e temperatura é atualizado
                    self.custom_signals.update_value_in_label_trigger.emit("{} bpm \n\n{} ºC".format(p.findpeaks(),temperature)) # Upadate the hear beat and temperature values in the GUI

        process_reading_data_acquisition.join()
        print("Finished arduino thread ")
        stop_event.clear()

class CustomSignalsClass(QObject):
    # Define new signals.
    update_value_in_label_trigger = pyqtSignal(str)
    trigger = pyqtSignal(list, list) # sinal para enviar dados filtrados para o init_plot

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
