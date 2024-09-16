from flask import Flask, Response, stream_with_context, request
from flask_cors import CORS
from flask_socketio import SocketIO
from laserharp.app import LaserHarpApp


def create_backend(laserharp: LaserHarpApp) -> tuple[Flask, callable]:
    app = Flask(__name__)
    socketio = SocketIO(app, cors_allowed_origins="*", path="/ws")
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # send app events via socket connection
    laserharp.on("state", lambda state: socketio.emit("app:state", state.name.lower()))
    laserharp.on("frame_rate", lambda frame_rate: socketio.emit("app:frame_rate", frame_rate))

    @socketio.on("connect")
    def on_connect():
        clientid = request.sid
        print(f"Client connected: {clientid}")

        socketio.emit("app:state", laserharp.state.name.lower())
        socketio.emit("app:config", laserharp.config)
        socketio.emit(
            "app:calibration",
            (laserharp.calibrator.calibration.to_dict() if laserharp.calibrator.calibration else None),
        )

        laserharp.processor.state.watch(
            lambda value: socketio.emit("app:processor", value, to=clientid),
            immediate=True,
        )
        laserharp.calibrator.state.watch(
            lambda value: socketio.emit("app:calibrator", value, to=clientid),
            immediate=True,
        )

    @socketio.on_error()
    def on_error(e):
        print("Socket error:", e)

    @socketio.on("app:calibrate")
    def on_calibrate(_data):
        laserharp.run_calibration()

    # will be set when calling run further down
    output = None

    @app.route("/api/stream.mjpg")
    def stream():
        @stream_with_context
        def generate():
            while True:
                with output.condition:
                    output.condition.wait()

                    frame = output.frame
                    if frame is None:
                        continue

                    yield b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"

        return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")

    def run(*kargs, **kwargs):
        # setup the streaming output
        nonlocal output
        output = laserharp.camera.start_debug_stream()

        # run the app with the socketio wrapper
        socketio.run(app, *kargs, **kwargs)

    return app, run
