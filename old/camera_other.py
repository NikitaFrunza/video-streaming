from flask import Flask, render_template, Response, request
import cv2
import datetime, time
import os, sys
import numpy as np
from threading import Thread
import netifaces as ni
import picamera
import io
from threading import Condition

global capture, camera
capture = 0

#make pictures directory to save pics
try:
    os.mkdir('./shots')
except OSError as error:
    pass

#### GET IP Address on network interfaces ###
ip_eth0 = ni.ifaddresses('eth0')[ni.AF_INET][0]['addr']
# ip_wlan0 = ni.ifaddresses('wlan0')[ni.AF_INET][0]['addr']

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


class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)

output = StreamingOutput()


### Conifuring Pi camera ###
def gen_frames():  # generate frame by frame from camera
    try:  
        while True:
            with output.condition:
                output.condition.wait()
                frame = output.frame
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    except Exception as e:
        pass

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

    # elif request.method == 'GET':
    #     return render_template('index.html')
    
    # capture_photo()  # Call the capture_photo function on each request
    return render_template('index.html')

def camera_stream():
    with picamera.PiCamera(resolution='1280x720', framerate=24) as camera:
        camera.start_recording(output, format='mjpeg')
        try:
            while True:
                camera.wait_recording(1)
        finally:
            camera.stop_recording()

### Run Web-Server ###
if __name__ == '__main__':
    camera_thread = Thread(target=camera_stream)
    camera_thread.start()
    app.run(host = ip_eth0, port = 8000)
