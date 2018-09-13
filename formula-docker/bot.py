#!env python
#
# Auto-driving Bot
#
# Revision:      v1.2
# Released Date: Aug 20, 2018
#
#coding=UTF-8

from io   import BytesIO
import os
import numpy as np
import base64
from PIL  import Image
from utils.log import Log
from utils.data_handler import FileModifier, TrainingDataCollector
from utils.image_handler import ImageProcessor
from model.pid import PID
import cv2


def logit(msg):
    print("%s" % msg)

class AutoDrive(object):
    #Two PID controllers (steer and throttle controller)
    STEERING_PID_Kp = 0.2 #0.3-0.06(0.2)
    STEERING_PID_Ki = 0.008 #0.01-0.003(0.008)
    STEERING_PID_Kd = 0.08 #0.1-0.03 (0.08)
    STEERING_PID_max_integral = 40
    THROTTLE_PID_Kp = 0.02
    THROTTLE_PID_Ki = 0.005
    THROTTLE_PID_Kd = 0.02
    THROTTLE_PID_max_integral = 0.5
    MAX_STEERING_HISTORY = 3
    MAX_THROTTLE_HISTORY = 3
    DEFAULT_SPEED = 0.5

    debug = True

    def __init__(self, car,car_training_data_collector, record_folder = None):
        self._record_folder    = record_folder
        self._steering_pid     = PID("wheel",Kp=self.STEERING_PID_Kp  , Ki=self.STEERING_PID_Ki  , Kd=self.STEERING_PID_Kd  , max_integral=self.STEERING_PID_max_integral)
        self._throttle_pid     = PID("throttle",Kp=self.THROTTLE_PID_Kp  , Ki=self.THROTTLE_PID_Ki  , Kd=self.THROTTLE_PID_Kd  , max_integral=self.THROTTLE_PID_max_integral)
        self._throttle_pid.assign_set_point(self.DEFAULT_SPEED)
        self.car_training_data_collector=car_training_data_collector
        #Historical data
        self._steering_history = []
        self._throttle_history = []
        #Register card to auto driving
        self._car = car
        self._car.register(self)
        self.current_lap=1

    def on_dashboard(self, src_img, last_steering_angle, speed, throttle, info):
        track_img     = ImageProcessor.preprocess(src_img) # crop 55% upper image  and sharpen the color
        #cur_radian, line_results = self.m_twQTeamImageProcessor.findSteeringAngle(src_img, proc_img)
       
        current_angle = ImageProcessor.find_steering_angle_by_color(track_img, last_steering_angle, debug = self.debug)
        #current_angle = ImageProcessor.find_steering_angle_by_line(track_img, last_steering_angle, debug = self.debug)
        steering_angle,Kp,Ki,Kd = self._steering_pid.update(-current_angle,-current_angle) #Current angle
        throttle,_,_,_       = self._throttle_pid.update(-current_angle,speed) #current speed
        message=str(info["lap"])+","+str(steering_angle)+","+str(Kp)+","+str(Ki)+","+str(Kd)+","
        message+=str(throttle)
        if info["lap"]>self.current_lap:
            self.current_lap=info["lap"]
            self._steering_pid.pid_reset()
            self._throttle_pid.pid_reset()
            #throttle=0.3
            #steering_angle=0.0
        total_time = info["time"].split(":") if "time" in info else []  # spend time
        seconds = float(total_time.pop()) if len(total_time) > 0 else 0.0
        minutes = int(total_time.pop()) if len(total_time) > 0 else 0
        hours = int(total_time.pop()) if len(total_time) > 0 else 0
        elapsed = ((hours * 60) + minutes) * 60 + seconds
        # if hours==0 and minutes==0 and seconds==0:
        #     ImageProcessor.switch_color(ImageProcessor.AUTO_DETECT)
        #     ImageProcessor.ALREADY_TRANSED=False
        #     ImageProcessor.current_step = 0
        #     ImageProcessor.is_translating = False
        self.car_training_data_collector.save_data_direct(message)
        #debug and save captured images
        if self.debug:
            ImageProcessor.show_image(src_img, "source")
            ImageProcessor.show_image(track_img, "track")
            logit("steering PID: %0.2f (%0.2f) => %0.2f (%0.2f)" % (current_angle, ImageProcessor.rad2deg(current_angle), steering_angle, ImageProcessor.rad2deg(steering_angle)))
            logit("throttle PID: %0.4f => %0.4f" % (speed, throttle))
            logit("info: %s" % repr(info))

        if self._record_folder:
            suffix = "-deg%0.3f" % (ImageProcessor.rad2deg(steering_angle))
            ImageProcessor.save_image(self._record_folder, src_img  , prefix = "cam", suffix = suffix)
            ImageProcessor.save_image(self._record_folder, track_img, prefix = "trk", suffix = suffix)

        #smooth the control signals
        self._steering_history.append(steering_angle)
        self._steering_history = self._steering_history[-self.MAX_STEERING_HISTORY:]
        self._throttle_history.append(throttle)
        self._throttle_history = self._throttle_history[-self.MAX_THROTTLE_HISTORY:]

        self._car.control(sum(self._steering_history)/self.MAX_STEERING_HISTORY, sum(self._throttle_history)/self.MAX_THROTTLE_HISTORY)

class Car(object):
    MAX_STEERING_ANGLE = 40.0

    def __init__(self, control_function):
        self._driver = None
        self._control_function = control_function


    def register(self, driver):
        self._driver = driver

    # payload
    def on_dashboard(self, dashboard):
        # dashboard-> {'steering_angle': '2.2865', 'throttle': '0.0264', 'brakes': '0.0000', 'speed': '0.7527', 'image':'', 'lap': '1', 'time': '12.760', 'status': '0'}
        last_steering_angle = np.pi/2 - float(dashboard["steering_angle"]) / 180.0 * np.pi # rest of steel wheel radian
        throttle            = float(dashboard["throttle"]) #speed control
        speed               = float(dashboard["speed"]) # current speed
        img                 = ImageProcessor.bgr2rgb(np.asarray(Image.open(BytesIO(base64.b64decode(dashboard["image"]))))) # current image

        total_time = dashboard["time"].split(":") if "time" in dashboard else [] # spend time
        seconds    = float(total_time.pop()) if len(total_time) > 0 else 0.0
        minutes    = int(total_time.pop())   if len(total_time) > 0 else 0
        hours      = int(total_time.pop())   if len(total_time) > 0 else 0
        elapsed    = ((hours * 60) + minutes) * 60 + seconds

        info = {
            "lap"    : int(dashboard["lap"]) if "lap" in dashboard else 0,
            "elapsed": elapsed,
            "status" : int(dashboard["status"]) if "status" in dashboard else 0,
        }
        self._driver.on_dashboard(img, last_steering_angle, speed, throttle, info)

    def control(self, steering_angle, throttle):
        #convert the values with proper units
        steering_angle = min(max(ImageProcessor.rad2deg(steering_angle), -Car.MAX_STEERING_ANGLE), Car.MAX_STEERING_ANGLE)
        self._control_function(steering_angle, throttle)

if __name__ == "__main__":
    import shutil
    import argparse
    from datetime import datetime

    import socketio
    import eventlet
    import eventlet.wsgi
    from flask import Flask

    parser = argparse.ArgumentParser(description='AutoDriveBot')
    parser.add_argument(
            'record',
            type=str,
            nargs='?',
            default='',
            help='Path to image folder to record the images.'
    )
    track_name="Track_5"
    text_file_path = "./log/car_training_data_" + track_name + ".txt"
    car_training_data_collector=TrainingDataCollector(text_file_path)
    message = "lap,steering_angle,Kp,Ki,Kd,throttle"
    car_training_data_collector.save_data_direct(message)
    args = parser.parse_args()
    ImageProcessor.switch_color(ImageProcessor.AUTO_DETECT) # sharpen it
    #Input arguments
    if args.record:
        if not os.path.exists(args.record):
            os.makedirs(args.record)
        logit("Start recording images to %s..." % args.record)
    sio = socketio.Server()

    def send_control(steering_angle, throttle):
        sio.emit(
            "steer",
            data={
                'steering_angle': str(steering_angle),
                'throttle': str(throttle)
            },
            skip_sid=True)
    car = Car(control_function = send_control)
    drive = AutoDrive(car,car_training_data_collector, args.record)

    @sio.on('telemetry')
    def telemetry(sid, dashboard):
        if dashboard:
            car.on_dashboard(dashboard)
        else:
            sio.emit('manual', data={}, skip_sid=True)

    @sio.on('connect')
    def connect(sid, environ):
        car.control(0, 0)
    
    app = socketio.Middleware(sio, Flask(__name__))
    eventlet.wsgi.server(eventlet.listen(('', 4567)), app)

# vim: set sw=4 ts=4 et :

