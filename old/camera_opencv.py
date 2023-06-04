from flask import Flask, render_template, Response, request
import cv2
import datetime, time
import os, sys
import numpy as np
from threading import Thread
import netifaces as ni
import picamera
import io

global capture, camera
capture = 0

#make pictures directory to save pics
try:
    os.mkdir('./shots')
except OSError as error:
    pass

#### GET IP Address on network interfaces ###
ip_eth0 = ni.ifaddresses('eth0')[ni.AF_INET][0]['addr']
ip_wlan0 = ni.ifaddresses('wlan0')[ni.AF_INET][0]['addr']

### Initiate Flask ###
app = Flask(__name__, template_folder='templates')


### Initiate PiCamera ###
camera = picamera.PiCamera()


def func_capture(frame):
    global capture
    if (capture): 
        capture=0
        now = datetime.datetime.now()
        path = os.path.sep.join(['shots', "shot_{}.png".format(str(now).replace(":",''))])
        cv2.imwrite(path, frame)

### Conifuring Pi camera ###
def gen_frames():  # generate frame by frame from camera
    stream = io.BytesIO()
    for _ in camera.capture_continuous(stream, format='jpeg', use_video_port=True):
        stream.seek(0)

        ### Converting to OpenCV ###
        frame = cv2.imdecode(np.frombuffer(stream.getvalue(), dtype=np.uint8), cv2.IMREAD_COLOR)
        func_capture(frame)

        try:
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + stream.read() + b'\r\n')
            stream.seek(0)
            stream.truncate()
        except Exception as e :
            pass


### Flask Routing ###
@app.route('/')
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
    
    elif request.method == 'GET':
        return render_template('index.html')
    
    return render_template('index.html')


### Run Web-Server ###
app.run(host = ip_eth0, port = 8000)
