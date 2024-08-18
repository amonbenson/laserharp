from flask import Flask
from flask_cors import CORS
from laserharp.app import LaserHarpApp

def create_backend(laserharp: LaserHarpApp):
    app = Flask(__name__)
    CORS(app, resources={
        r"/api/*": {"origins": "*"}
    })

    @app.get("/api/camera/frame")
    def get_camera_frame():
        # capture a black/white frame from the camera
        frame = laserharp.camera.capture()
        print(frame.shape)

        # send it as binary data
        return frame.tobytes()

    return app
