import time
import threading
from dataclasses import asdict
from flask import Flask, Response, stream_with_context, request
from flask_cors import CORS
from flask_socketio import SocketIO
from perci import QueueWatcher, create_queue_watcher
from perci.changes import Change
from laserharp.app import LaserHarpApp


class Session:
    def __init__(self, socketio: SocketIO, clientid: str, laserharp: LaserHarpApp):
        self.socketio = socketio
        self.clientid = clientid
        self.laserharp = laserharp

        # send the initial state
        self.socketio.emit("app:global_state:init", laserharp.get_global_state().json())

        # create a new queue watcher
        self.watcher = create_queue_watcher(laserharp.get_global_state())

        # create a thread that watches for changes
        self.running = False
        self.thread = threading.Thread(target=self._run)

    def start(self):
        self.running = True
        self.thread.start()

    def stop(self):
        self.laserharp.get_global_state().get_namespace().remove_watcher(self.watcher)
        self.running = False

    def _run(self):
        while self.running:
            changes = [asdict(change) for change in self.watcher.get_changes()]

            if changes:
                self.socketio.emit("app:global_state:changes", changes, to=self.clientid)

            time.sleep(1 / 30)


def create_backend(laserharp: LaserHarpApp) -> tuple[Flask, callable]:
    app = Flask(__name__)
    socketio = SocketIO(app, cors_allowed_origins="*", path="/ws")
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    sessions: dict[str, Session] = {}

    @socketio.on("connect")
    def on_connect():
        clientid = request.sid
        print(f"Client connected: {clientid}")

        # create a new session
        session = Session(socketio, clientid, laserharp)
        session.start()
        sessions[clientid] = session

    @socketio.on("disconnect")
    def on_disconnect():
        clientid = request.sid
        print(f"Client disconnected: {clientid}")

        # remove and stop the session
        session = sessions.pop(clientid)
        session.stop()

    @socketio.on_error()
    def on_error(e):
        print("Socket error:", e)

    @socketio.on("app:setting:update")
    def on_setting_update(data):
        try:
            laserharp.get_settings().set(data["componentKey"], data["settingKey"], data["value"], role="client")
            return {
                "status": "ok",
                "value": laserharp.get_settings().get(data["componentKey"], data["settingKey"]).get_value(),
            }
        except Exception as e:
            print("Failed to update setting:", e)
            return {
                "status": "error",
                "error": str(e),
            }

    @socketio.on("app:calibrate")
    def on_calibrate(_data):
        laserharp.run_calibration()

    # will be set when calling run further down
    output = None

    @app.route("/api/stream.mjpg")
    def stream():
        if not laserharp.camera.enabled:
            return Response("Camera is not enabled", status=503)

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
