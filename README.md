# Dissertation - Biomedical Engineering 2020/2021
### Author 
Ana Catarina Monteiro Magalhães

# Organization 
This repository are available all the data acquire by the monitoring system and also the code of the monitoring system. Besides, it contains the code of the posterior data analysis.

The videos acquired during the trial 2 and 3 are available in the following link ().

### Data_bioterium
The Data_bioterium directory has the data of the trials 1, 2 and 3, that corresponds to the zebrafish vital signs and water temperature measurenments. 

### Arduino_code
The Arduino_code directory has the file **sensors.ino** that makes the comunitcation between the hardware and the software of the developed monitoring system. 

### Python_code
The Python_code directory has the software developed to built the monitoring system. In more detail the directory has 4 files. 
The file **mainwindow.ui** corresponds to the design of interface in a Qt environment. 
The file **mainwindow.py** is responsible for establish the communication between the Qt environment and the Python environemnt.
The script **init_interface.py** has the code to update the interface with the new information that arroves from the Arduino and from the webcam. Also the serial comunication between the Arduino and the Python software is established and the calculation of the heart rate are made in this portion of code.
The script **cameraacquisition.py** is reponsible for grabbing the frames of the webcam and process them in a way that can be displayed in the Qt interface.

### Computer_vision_code
In the Computer_vision_code, we have the script **video_analysis.py** that calaculates the zebrafish heart rate based on the change of intensity of the region of interest, the heart region. 
Besides, there are two files Trial 2 and Trial 3 that have the .txt file resulting from the analysis of several sections of the zebrafish videos from trial 2 and 3.

### Analysis_code

