# Object Size Detector

| Details            |              |
|-----------------------|---------------|
| Target OS:            |  Ubuntu\* 16.04 LTS   |
| Programming Language: |  Python* 3.5 |
| Time to Complete:     |  45 min     |

![Defect](./docs/images/defect.png)

## What it does
This application demonstrates how to use CV to detect and measure the approximate size of assembly line parts. It is designed to work with an assembly line camera mounted above the assembly line belt. The application monitors mechanical parts as they are moving down the assembly line and raises an alert if it detects a part on the belt outside a specified size range.

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
  
* Intel® Distribution of OpenVINO™ toolkit 2019 R2 release toolkit

## How It works

This object size detector works with a video source, such as a camera. The application captures video frames and processes the frame data with OpenCV algorithms. It detects objects on the assembly line and calculates the length and width of the objects. If the calculated length and width is not within a predefined range, the application raises an alert to notify the assembly line operator. Optionally, the application sends data to a message queuing telemetry transport (MQTT) machine, or machine messaging server, as a part of an assembly line data analytics system.

![app image](./docs/images/architectural_diagram.png)
**Architectural Diagram**

## Setup

### Get the code

Steps to clone the reference implementation: (object-size-detector-python)

    sudo apt-get update && sudo apt-get install git
    git clone https://github.com/intel-iot-devkit/object-size-detector-python.git
    
### Install Intel® Distribution of OpenVINO™ toolkit
Before running the application, install the Intel® Distribution of OpenVINO™ toolkit. For details, see [Installing the Intel® Distribution of OpenVINO™ toolkit for Linux*](https://software.intel.com/en-us/openvino-toolkit/choose-download/free-download-linux)

### Other dependencies
#### Mosquitto*
Mosquitto is an open source message broker that implements the MQTT protocol. The MQTT protocol provides a lightweight method of carrying out messaging using a publish/subscribe model.

To install the dependencies of the RI, run the below command:
   ```
   cd <path_to_the_object-size-detector-python_directory>
   ./setup.sh
   ```
### The Config File

The _resources/config.json_ contains the path to the videos that will be used by the application.
The _config.json_ file is of the form name/value pair, `video: <path/to/video>`   

Example of the _config.json_ file:

```
{

    "inputs": [
	    {
            "video": "videos/video1.mp4"
        }
    ]
}
```

### Which Input video to use

The application works with any input video. Find sample videos for object detection [here](https://github.com/intel-iot-devkit/sample-videos/).  

For first-use, we recommend using the [bolt-multi-size-detection](https://github.com/intel-iot-devkit/sample-videos/blob/master/bolt-multi-size-detection.mp4) video.The video is automatically downloaded to the `resources/` folder.
For example: <br>
The config.json would be:

```
{

    "inputs": [
	    {
            "video": "sample-videos/bolt-multi-size-detection.mp4"
        }
    ]
}
```
To use any other video, specify the path in config.json file

### Using the Camera instead of video

Replace the path/to/video in the _resources/config.json_  file with the camera ID, where the ID is taken from the video device (the number X in /dev/videoX).   

On Ubuntu, list all available video devices with the following command:

```
ls /dev/video*
```

For example, if the output of above command is /dev/video0, then config.json would be::

```
{

    "inputs": [
	    {
            "video": "0"
        }
    ]
}
```

### Setup the Environment

Configure the environment to use the Intel® Distribution of OpenVINO™ toolkit once per session by running the **source** command on the command line:
```
source /opt/intel/openvino/bin/setupvars.sh -pyver 3.5
```
__Note__: This command needs to be executed only once in the terminal where the application will be executed. If the terminal is closed, the command needs to be executed again.

## Run the Application

Change the current directory to the git-cloned application code location on your system:
```
cd <path-to-object-size-detector-python>/application
```

To see a list of the various options, invoke the help output of this application with the help parameter:
```
python3.5 object_size_detector.py -h
```

Run the application using the below command if field of view and distance between the object and camera in millimeters are not known. 

Using input as videofile:
```
python3.5 object_size_detector.py -minl=228 -minw=28 -maxl=250 -maxw=45
``` 
Run the application using the below command if field of view and distance between the object and camera in millimeters are known. 

Using input as videofile:
```
python3.5 object_size_detector.py -minl=228 -minw=28 -maxl=250 -maxw=45 -fv=60 -d=370
``` 
**Note:**<br>
User can get field of view from camera specifications. The minl, minw, maxl and maxw parameters set the values for the minimum and maximum values for length and width. If a part’s length and width is not within this range, the application issues an alert.

### Subscribe the data

Open a new terminal and execute the below commands:

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

