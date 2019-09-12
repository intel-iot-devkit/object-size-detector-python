"""Object Size Detector"""
"""
* Copyright (c) 2018 Intel Corporation.
*
* Permission is hereby granted, free of charge, to any person obtaining
* a copy of this software and associated documentation files (the
* "Software"), to deal in the Software without restriction, including
* without limitation the rights to use, copy, modify, merge, publish,
* distribute, sublicense, and/or sell copies of the Software, and to
* permit persons to whom the Software is furnished to do so, subject to
* the following conditions:
*
* The above copyright notice and this permission notice shall be
* included in all copies or substantial portions of the Software.
*
* THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
* EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
* MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
* NONINFRINGEMENT. IN NO EVEN
T SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
* LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
* OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
* WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

from argparse import ArgumentParser
from collections import namedtuple
import json
import math
import numpy as np
import paho.mqtt.client as mqtt
import signal
import sys
import cv2
import os
import time
import datetime

# GLOBAL Variables
CONFIG_FILE = '../resources/config.json'

# OpenCV-related variables
delay = 5
frame = None

# Assembly part and defect areas
frame_ok_count = 0
frame_defect_count = 0
max_width = 0
min_width = 0
min_length = 0
max_length = 0
nextimage = list()
prev_seen = False
prev_defect = False
total_parts = 0
total_defect = 0
one_pixel_length = 0
diagonal_length_of_image_plane = 0

# Define mqtt variables
topic = "defects/counter"
host = "localhost"
port = 1883
alive = 45

# AssemblyInfo contains information about assembly line defects
AssemblyInfo = namedtuple("AssemblyInfo", "inc_total, defect, area, length, width, show, rects")
info2 = AssemblyInfo(inc_total="false", defect="false", area="0", length="0", width="0", show="false", rects=[])


# Parse the command line arguments
def build_argparser():
    parser = ArgumentParser()
    parser.add_argument("-maxl", "--maxlength1", help="Maximum length of assembly object", default=None, required=True)
    parser.add_argument("-minl", "--minlength1", help="Minimum length of assembly object", default=None, required=True)
    parser.add_argument("-maxw", "--maxwidth1", help="Maximum width of assembly object", default=None, required=True)
    parser.add_argument("-minw", "--minwidth1", help="Minimum width of assembly object", default=None, required=True)
    parser.add_argument("-d", "--distance", help="Distance between camera and object in millimeters", default=None,
                        required=False, type=float)
    parser.add_argument("-fv", "--fieldofview", help="Field of view of camera", default=None, required=False,
                        type=float)

    return parser


# Updates the current AssemblyInfo for the application to the latest detected values
def update_info(info1):
    global total_parts
    global total_defect
    global info2
    info2 = AssemblyInfo(inc_total=info1.inc_total, defect=info1.defect, area=info1.area, length=info1.length,
                         width=info1.width, show=info1.show, rects=info1.rects)
    if info1.inc_total:
        total_parts += 1
    if info1.defect:
        total_defect += 1


# Returns the most-recent AssemblyInfo for the application
def getcurrent_info():
    current = info2
    return current


# Returns the next image from the list
def nextimage_available():
    rtn = None
    if nextimage:
        rtn = nextimage.pop(0)
    return rtn


# Adds an image to the list
def add_image(img):
    global nextimage
    if not nextimage:
        nextimage.append(img)


# Publish MQTT message with a JSON payload
def messageRunner():
    info3 = getcurrent_info()
    client.publish(topic, payload=json.dumps({"defect": info3.defect}))


# Signal handler
def signal_handler(sig, frame):
    cv2.destroyAllWindows()
    client.disconnect()
    sys.exit(0)


# Function process the next available video frame
def frameRunner():
    next = nextimage_available()
    if next is not None:
        global frame_defect_count
        global frame_ok_count
        global prev_seen
        global prev_defect
        global args

        rect = []
        defect = False
        frame_defect = False
        inc_total = False
        max_blob_area = 0
        maxlength = 0
        maxwidth = 0
        kernel = np.ones((5, 5), np.uint8)

        img = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

        # Blur the image to smooth it
        img = cv2.GaussianBlur(img, (3, 3), 0)

        # Morphology: OPEN -> CLOSE -> OPEN
        img = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
        img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel)
        img = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)

        # Threshold the image to emphasize assembly part
        ret, img = cv2.threshold(img, 200, 255, cv2.THRESH_BINARY)

        # Find the contours of assembly part
        contours, hierarchy = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        # Pick detected objects with largest size
        for cnt in contours:
            x, y, width, height = cv2.boundingRect(cnt)
            wide = math.ceil(width * one_pixel_length) * 10
            length = math.ceil(height * one_pixel_length) * 10

            part_area = wide * length
            if part_area > max_blob_area and x > 0 and x + width < img.shape[1] and width > 30:
                max_blob_area = part_area
                maxwidth = wide
                maxlength = length
                x1, y1, width1, height1 = cv2.boundingRect(cnt)
                rect = [x1, y1, width1, height1]
        part_area = max_blob_area
        wide = maxwidth
        length = maxlength

        # If no object is detected we dont do anything
        if part_area != 0:

            # Increment ok or defect counts
            if wide > max_width or wide < min_width or length > max_length or length < min_length:
                frame_defect = True
                frame_defect_count += 1
            else:
                frame_ok_count = frame_ok_count + 1

            # If the part wasn't seen before it's a new part
            if not prev_seen:
                prev_seen = True
                inc_total = True

            # If the previously seen object has no defect detected in 10 previous consecutive frames
            if frame_defect is False and frame_ok_count > 10:
                frame_defect_count = 0

            # If previously seen object has a defect detected in 10 previous consecutive frames
            if frame_defect is True and frame_defect_count > 10:
                if prev_defect == False:
                    prev_defect = True
                    defect = True
                frame_ok_count = 0
        else:
            # Reset values if no defected part is detected
            prev_seen = False
            inc_total = False
            prev_defect = False
            frame_defect_count = 0
            frame_ok_count = 0
        assembly = AssemblyInfo(inc_total=inc_total, defect=defect, area=part_area, length=maxlength, width=maxwidth,
                                show=prev_defect, rects=rect)
        update_info(assembly)


def main():
    global delay
    global frame
    global max_length
    global min_length
    global max_width
    global min_width
    global total_parts
    global total_defect
    global one_pixel_length
    global diagonal_length_of_image_plane
    global args
    global CONFIG_FILE
    # Parsing the arguments
    args = build_argparser().parse_args()

    try:
        max_length = int(args.maxlength1)
    except ValueError:
        print("\nInvalid Argument for -maxl!\n")
        sys.exit(0)

    try:
        min_length = int(args.minlength1)
    except ValueError:
        print("\nInvalid Argument for -minl!\n")
        sys.exit(0)

    try:
        max_width = int(args.maxwidth1)
    except ValueError:
        print("\nInvalid Argument for -maxw!\n")
        sys.exit(0)

    try:
        min_width = int(args.minwidth1)
    except ValueError:
        print("\nInvalid Argument for -minw!\n")
        sys.exit(0)

    assert os.path.isfile(CONFIG_FILE), "{} file doesn't exist".format(CONFIG_FILE)
    config = json.loads(open(CONFIG_FILE).read())

    for idx, item in enumerate(config['inputs']):
        if item['video'].isdigit():
            input_stream = int(item['video'])
            capture = cv2.VideoCapture(input_stream)
            if not capture.isOpened():
                print("\nCamera not plugged in... Exiting...\n")
                sys.exit(0)
            fps = capture.get(cv2.CAP_PROP_FPS)
            delay = int(1000 / fps)
        else:
            input_stream = item['video']
            capture = cv2.VideoCapture(input_stream)
            if not capture.isOpened():
                print("\nUnable to open video file... Exiting...\n")
                sys.exit(0)
            fps = capture.get(cv2.CAP_PROP_FPS)
            delay = int(1000 / fps)

    if args.distance and args.fieldofview:
        width_of_video = capture.get(3)
        height_of_video = capture.get(4)
        radians = (args.fieldofview / 2) * 0.0174533  # Convert degrees to radians
        diagonal_length_of_image_plane = abs(2 * (args.distance / 10) * math.tan(radians))
        diagonal_length_in_pixel = math.sqrt(math.pow(width_of_video, 2) + math.pow(height_of_video, 2))
        one_pixel_length = (diagonal_length_of_image_plane / diagonal_length_in_pixel)
    else:
        one_pixel_length = 0.0264583333

    signal.signal(signal.SIGINT, signal_handler)

    if max_length < min_length:
        print("\nInvalid Arguments: Max length of the object is less then Min length!\n")
        sys.exit(0)

    if max_width < min_width:
        print("\nInvalid Arguments: Max width of the object is less then Min width!\n")
        sys.exit(0)

    # Read video input data
    while capture.isOpened():
        ret, frame = capture.read()
        if not ret:
            break
        # frame = cv2.resize(frame, (960, 540))
        displayFrame = frame.copy()
        add_image(frame)
        frameRunner()
        assemble_line = getcurrent_info()
        length = str("Expected length (mm): = [{} - {}]".format(min_length, max_length))
        width = str("Expected width (mm): = [{} - {}]".format(min_width, max_width))
        Measurement = "Area (mm * mm) : {}".format(assemble_line.area)
        Length = "Length (mm) : {}".format(assemble_line.length)
        Width = "Width (mm)  : {}".format(assemble_line.width)
        total_part = "Total_parts : {}".format(total_parts)
        total_defects = "Total_defects : {}".format(total_defect)
        defects = "Defect : {}".format("False")

        if assemble_line.show is True:
            cv2.rectangle(displayFrame, (assemble_line.rects[0], assemble_line.rects[1]), (
            assemble_line.rects[0] + assemble_line.rects[2], assemble_line.rects[1] + assemble_line.rects[3]),
                          (0, 0, 255), 2)
            defects = "Defect : {}".format("True")
            cv2.putText(displayFrame, defects, (5, 170), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)
        else:
            if assemble_line.rects:
                cv2.rectangle(displayFrame, (assemble_line.rects[0], assemble_line.rects[1]), (
                assemble_line.rects[0] + assemble_line.rects[2], assemble_line.rects[1] + assemble_line.rects[3]),
                              (0, 255, 0), 2)
                defects = "Defect : {}".format("False")
                cv2.putText(displayFrame, defects, (5, 170), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)

        cv2.putText(displayFrame, Measurement, (5, 100), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(displayFrame, length, (5, 200), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(displayFrame, width, (5, 220), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(displayFrame, Length, (5, 120), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(displayFrame, Width, (5, 140), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(displayFrame, total_part, (5, 50), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(displayFrame, total_defects, (5, 70), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(displayFrame, defects, (5, 170), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)
        cv2.imshow("Object size detector", displayFrame)
        messageRunner()
        if cv2.waitKey(delay) > 0:
            break

    capture.release()

    # Destroy all the windows
    cv2.destroyAllWindows()


if __name__ == '__main__':
    # Create a new instance
    client = mqtt.Client("object_size_detector")
    # Connect to broker
    client.connect(host, port, alive)
    main()
    # Disconnect MQTT messaging
    client.disconnect()
