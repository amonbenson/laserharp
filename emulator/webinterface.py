from flask import Flask
from flask_socketio import SocketIO

app = Flask("laserharp-emulator-webinterface")
socketio = SocketIO(app)

@app.route("/")
def root():
    return
