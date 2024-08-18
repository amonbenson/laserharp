from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
import base64
from laserharp.app import LaserHarpApp

def create_backend(laserharp: LaserHarpApp) -> tuple[Flask, callable]:
    app = Flask(__name__)
    socketio = SocketIO(app, cors_allowed_origins="*", path="/ws")
    CORS(app, resources={
        r"/api/*": {"origins": "*"}
    })

    # send app events via socket connection
    laserharp.on("state", lambda state: socketio.emit("app:state", state.name.lower()))
    laserharp.on("frame", lambda frame: socketio.emit("app:frame", base64.b64encode(frame).decode()))
    laserharp.on("frame_rate", lambda frame_rate: socketio.emit("app:frame_rate", frame_rate))
    laserharp.on("calibration", lambda calibration: socketio.emit("app:calibration", calibration.to_dict() if calibration else None))
    # laserharp.on("result", lambda result: socketio.emit("app:result", {
    #     "active": result.active.tolist(),
    #     "length": result.length.tolist(),
    #     "modulation": result.modulation.tolist()  
    # }))
    
    @socketio.on("connect")
    def on_connect():
        print("Socket connected")
        socketio.emit("app:state", laserharp.state.name.lower())
        socketio.emit("app:config", laserharp.config)
        socketio.emit("app:calibration", laserharp.calibrator.calibration.to_dict() if laserharp.calibrator.calibration else None)

    @socketio.on_error()
    def on_error(e):
        print("Socket error:", e)

    def run(*kargs, **kwargs):
        socketio.run(app, *kargs, **kwargs)

    return app, run
