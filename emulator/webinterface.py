import os
import logging
import subprocess
from typing import Optional
import threading
import multiprocessing
import queue
from flask import Flask, Response, send_from_directory
from flask_cors import CORS
from waitress import serve

logger = logging.getLogger("webinterface")

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "frontend"))
FRONTEND_DIST_DIR = os.path.join(FRONTEND_DIR, "dist")

app_process: Optional[multiprocessing.Process] = None
app_send_queue: Optional[multiprocessing.Queue] = None
app_recv_queue: Optional[multiprocessing.Queue] = None

class SSE:
    def __init__(self, pub_queue: multiprocessing.Queue):
        self.listeners: list[queue.Queue] = []
        self.pub_queue = pub_queue
        
        self.forward_thread = threading.Thread(target=self.forward_thread_run, daemon=True)
        self.forward_thread.start()

    def forward_thread_run(self):
        while True:
            try:
                msg = self.pub_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            self.send(msg)

    def listen(self):
        q = queue.Queue(maxsize=5)
        self.listeners.append(q)
        return q

    def send(self, msg):
        for i in reversed(range(len(self.listeners))):
            try:
                self.listeners[i].put_nowait(msg)
            except queue.Full:
                del self.listeners[i]

def run(host, port, send_queue, recv_queue):
    app = Flask("laserharp emulator webinterface")
    CORS(app, resources="/api/*")

    sse = SSE(send_queue)

    @app.route("/")
    def serve_frontend_root():
        return send_from_directory(FRONTEND_DIST_DIR, "index.html")

    @app.route("/<path:path>")
    def serve_frontend(path):
        return send_from_directory(FRONTEND_DIST_DIR, path)

    @app.route("/api/stream")
    def sse_stream():
        def stream():
            messages = sse.listen()
            while True:
                msg = messages.get()
                yield msg

        return Response(stream(), mimetype="text/event-stream")

    serve(app, host=host, port=port)

def build_web_interface(api_endpoint):
    # run linter
    # logger.info("Linting frontend...")
    # subprocess.check_call(
    #     args=["deno", "run", "lint"],
    #     cwd=FRONTEND_DIR,
    # )

    # run build process
    logger.info("Building frontend...")
    subprocess.check_call(
        args=["deno", "run", "build", "--outDir", "dist"],
        cwd=FRONTEND_DIR,
        env={
            **os.environ,
            "VITE_API_ENDPOINT": api_endpoint,
        },)

def start_web_interface(host, port, build=True):
    global app_process, app_send_queue, app_recv_queue

    if build:
        build_web_interface(api_endpoint=f"http://{host}:{port}/api")

    # create send and receive queue
    app_send_queue = multiprocessing.Queue(maxsize=50)
    app_recv_queue = multiprocessing.Queue(maxsize=50)

    # run the app process
    logger.info("Starting server...")
    app_process = multiprocessing.Process(target=run, args=(host, port, app_send_queue, app_recv_queue), daemon=True)
    app_process.start()

def stop_web_interface():
    global app_process

    if app_process is None:
        raise ValueError("Web interface was not started.")

    logger.info("Stopping server...")
    app_process.terminate()

def send_event(msg):
    global app_send_queue

    app_send_queue.put_nowait(msg)
