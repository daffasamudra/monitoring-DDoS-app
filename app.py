from flask import Flask, jsonify, render_template
from flask_socketio import SocketIO
from flask_cors import CORS
import psutil
import time
import threading
import os

app = Flask(__name__)

# Konfigurasi CORS
CORS(app, resources={r"/*": {"origins": "*"}})

# PENTING: Gunakan eventlet untuk PythonAnywhere
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    async_mode='eventlet',  # ← Penting!
    logger=True,
    engineio_logger=True
)

# Flag untuk mengontrol thread
monitoring_active = False
monitoring_lock = threading.Lock()

def send_performance_data():
    global monitoring_active
    print("Monitoring thread started")
    
    while monitoring_active:
        try:
            cpu_usage = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            memory_usage = memory_info.percent
            
            socketio.emit('performance_data', {
                'cpu_usage': cpu_usage, 
                'memory_usage': memory_usage
            })
            
            print(f"Sent data - CPU: {cpu_usage}%, Memory: {memory_usage}%")
            
        except Exception as e:
            print(f"Error in monitoring thread: {e}")
            break
        
        time.sleep(1)
    
    print("Monitoring thread stopped")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cpu')
def get_cpu_usage():
    cpu_percent = psutil.cpu_percent(interval=1)
    return jsonify({"cpu_usage": cpu_percent})

@app.route('/memory')
def get_memory_usage():
    memory_info = psutil.virtual_memory()
    return jsonify({"memory_usage": memory_info.percent})

@socketio.on('connect')
def handle_connect():
    global monitoring_active
    print("Client connected!")
    
    with monitoring_lock:
        if not monitoring_active:
            monitoring_active = True
            thread = threading.Thread(target=send_performance_data, daemon=True)
            thread.start()
            print("Started monitoring thread")

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected!")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
