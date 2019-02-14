# Object Size Detector

| Details            |              |
|-----------------------|---------------|
| Target OS:            |  Ubuntu\* 16.04 LTS   |
| Programming Language: |  Python* 3.5 |
| Time to Complete:     |  45 min     |

![Defect](./images/defect.png)

## Introduction

This object size detector application is one of a series of computer vision (CV) reference implementations using the Intel® Distribution of OpenVINO™ toolkit. This application demonstrates how to use CV to detect and measure the approximate length, width and size of assembly line parts. It is designed to work with an assembly line camera mounted above the assembly line belt. The application monitors mechanical parts as they are moving down the assembly line and raises an alert if it detects a part on the belt outside a specified size range.

## Requirements

### Hardware
* 6th to 8th generation Intel® Core™ processor with Iris® Pro graphics or Intel® HD Graphics

### Software
* [Ubuntu\* 16.04 LTS](http://releases.ubuntu.com/16.04/)<br>
   NOTE: Use kernel versions 4.14+ with this software.<br> 
    Determine the kernel version with the below uname command. 
    ```
    uname -a
    ```
  
* Intel® Distribution of OpenVINO™ toolkit 2018 R5 release toolkit
* Jupyter* Notebook v5.7.0

## How it works

This object size detector works with a video source, such as a camera. The application captures video frames and processes the frame data with OpenCV algorithms. It detects objects on the assembly line and calculates the length and width of the objects. If the calculated length and width is not within a predefined range, the application raises an alert to notify the assembly line operator. Optionally, the application sends data to a message queuing telemetry transport (MQTT) machine, or machine messaging server, as a part of an assembly line data analytics system.

![app image](./images/object_size.png)

 ## Pre-requisites

### Install Intel® Distribution of OpenVINO™ toolkit
Before running the application, install the Intel® Distribution of OpenVINO™ toolkit. For details, see [Installing the Intel® Distribution of OpenVINO™ toolkit for Linux*](https://software.intel.com/en-us/openvino-toolkit/choose-download/free-download-linux)

## Setting the build environment

### Install Python* Dependencies
```
sudo apt-get update
sudo apt-get install python3-pip
sudo apt-get install python3-numpy
```
### Machine-to-Machine Messaging with MQTT

**Install mosquitto**
```
sudo apt-get update
sudo apt-get install mosquitto mosquitto-clients
```
**Install paho-mqtt-python**
```
sudo pip3 install paho-mqtt
```
**To run the mosquitto server**
```
mosquitto
```

**Note:** If the output of the above command is
```
1543918812: mosquitto version 1.4.8 (build date Wed, 05 Sep 2018 15:51:27 -0300) starting
1543918812: Using default config.
1543918812: Opening ipv4 listen socket on port 1883.
1543918812: Error: Address already in use
```
It means mosquitto server is already running in the background.<br>

**To Subscribe the data**
```
mosquitto_sub -h localhost -t defects/counter
```

## Run the code

Open a new terminal. Configure the environment to use the Intel® Distribution of OpenVINO™ toolkit once per session by running the **source** command on the command line:
```
source /opt/intel/computer_vision_sdk_2018.5.445/bin/setupvars.sh -pyver 3.5
```

Go to object-size-detector-python directory
```
cd <path-to-object-size-detector-python>
```

To see a list of the various options, invoke the help output of this application with the help parameter:
```
python3.5  main.py -h
```

Run the application using the below command if field of view and distance between the object and camera in millimeters are not known. 

Using input as videofile:
```
python3.5 main.py -minl=228 -minw=28 -maxl=250 -maxw=45 -i=./resources/bolt-multi-size-detection.mp4
``` 
Using input as camera:
```
python3.5 main.py -minl=228 -minw=28 -maxl=250 -maxw=45 -i=CAM
```
Run the application using the below command if field of view and distance between the object and camera in millimeters are known. 

Using input as videofile:
```
python3.5 main.py -minl=228 -minw=28 -maxl=250 -maxw=45 -i=./resources/bolt-multi-size-detection.mp4 -fv=60 -d=370
``` 
Using input as camera:
```
python3.5 main.py -minl=228 -minw=28 -maxl=250 -maxw=45 -i=CAM -fv=60 -d=370 
```
**Note:**<br>
User can get field of view from camera specifications. The minl, minw, maxl and maxw parameters set the values for the minimum and maximum values for length and width. If a part’s length and width is not within this range, the application issues an alert.


