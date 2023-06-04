from flask import Flask, render_template, Response
import picamera
import io
from threading import Condition
from threading import Thread

app = Flask(__name__)


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

@app.route('/')
def index():
    return render_template('index.html')

def gen_frames():
    while True:
        with output.condition:
            output.condition.wait()
            frame = output.frame
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def camera_stream():
    with picamera.PiCamera(resolution='1280x720', framerate=24) as camera:
        camera.start_recording(output, format='mjpeg')
        try:
            while True:
                camera.wait_recording(1)
        finally:
            camera.stop_recording()

if __name__ == '__main__':
    camera_thread = Thread(target=camera_stream)
    camera_thread.start()
    app.run(host='0.0.0.0', port=8000)
