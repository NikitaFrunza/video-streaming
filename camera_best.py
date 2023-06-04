from flask import Flask, render_template, Response, request
import cv2
import datetime, time
import os, sys
import numpy as np
from threading import Thread
import netifaces as ni
import picamera
import io

global capture, camera, record
capture = 0
record = 0

#make pictures directory to save pics
try:
    os.mkdir('./shots')
except OSError as error:
    pass

try:
    os.mkdir('./videos')
except OSError as error:
    pass

#### GET IP Address on network interfaces ###
ip_eth0 = ni.ifaddresses('eth0')[ni.AF_INET][0]['addr']
ip_wlan0 = ni.ifaddresses('wlan0')[ni.AF_INET][0]['addr']
ip_wg0 = ni.ifaddresses('wg0')[ni.AF_INET][0]['addr']
ip_usb0 = ni.ifaddresses('usb0')[ni.AF_INET][0]['addr']

### Initiate Flask ###
app = Flask(__name__, template_folder='templates')


### Initiate PiCamera ###
camera = picamera.PiCamera()


# Capture photo function
def capture_photo():
    global capture
    if capture == 1:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        image_path = f"./shots/{timestamp}.jpg"
        camera.capture(image_path)
        capture = 0

def record_video():
    global record
    if record == 1:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        image_path = f"./videos/{timestamp}.h264"
        camera.start_recording(image_path)
        camera.wait_recording(5)
        camera.stop_recording()
        record = 0



### Conifuring Pi camera ###
def gen_frames():  # generate frame by frame from camera
    stream = io.BytesIO()
    for _ in camera.capture_continuous(stream, format='jpeg', use_video_port=True):
        stream.seek(0)
        
        try:
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + stream.read() + b'\r\n')
            stream.seek(0)
            stream.truncate()
        except Exception as e :
            pass

        if (capture):
            break
        if (record):
            break

### Flask Routing ###
@app.route('/')
def root():    
    return render_template('index.html')

@app.route('/index.html')
def index():    
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/requests', methods = ['POST', 'GET'])
def tasks():
    if request.method == 'POST':    
        if request.form.get('capture') == 'Capture':
            global capture
            capture = 1
            capture_photo()
        if request.form.get('rec') == 'Record':
            global record
            record = 1
            record_video()


    # elif request.method == 'GET':
    #     return render_template('index.html')
    
    # capture_photo()  # Call the capture_photo function on each request
    return render_template('index.html')


### Run Web-Server ###
app.run(host = ip_wg0, port = 8000)
