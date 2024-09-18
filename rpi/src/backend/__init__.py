from dataclasses import asdict
from flask import Flask, Response, stream_with_context, request
from flask_cors import CORS
from flask_socketio import SocketIO
from perci import Watcher, watch
from perci.changes import Change
from laserharp.app import LaserHarpApp


def create_backend(laserharp: LaserHarpApp) -> tuple[Flask, callable]:
    app = Flask(__name__)
    socketio = SocketIO(app, cors_allowed_origins="*", path="/ws")
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    watchers: dict[str, Watcher] = {}

    @socketio.on("connect")
    def on_connect():
        clientid = request.sid
        print(f"Client connected: {clientid}")

        # send the initial state
        socketio.emit("app:state", laserharp.get_global_state().json())

        # watch any changes and send them to the client
        watchers[clientid] = watch(laserharp.get_global_state(), lambda change: socketio.emit("app:state", asdict(change), to=clientid))

    @socketio.on("disconnect")
    def on_disconnect():
        clientid = request.sid
        print(f"Client disconnected: {clientid}")

        # remove the session's watcher
        watcher = watchers.pop(clientid)
        laserharp.get_global_state().get_namespace().remove_watcher(watcher)

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
