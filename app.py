from flask import Flask, jsonify, render_template
from flask_socketio import SocketIO
from flask_cors import CORS
import psutil
import time
import threading
import os

app = Flask(__name__)

# Konfigurasi CORS untuk Flask dan Socket.IO
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Flag untuk mengontrol thread
monitoring_active = False
monitoring_lock = threading.Lock()

# Fungsi untuk mengirimkan data performa ke frontend
def send_performance_data():
    global monitoring_active
    
    print("Monitoring thread started")
    
    while monitoring_active:
        try:
            cpu_usage = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            memory_usage = memory_info.percent
            
            # Kirim data ke semua client yang terhubung
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

# Route untuk halaman utama
@app.route('/')
def index():
    return render_template('index.html')

# API untuk mendapatkan penggunaan CPU
@app.route('/cpu')
def get_cpu_usage():
    cpu_percent = psutil.cpu_percent(interval=1)
    return jsonify({"cpu_usage": cpu_percent})

# API untuk mendapatkan penggunaan memori
@app.route('/memory')
def get_memory_usage():
    memory_info = psutil.virtual_memory()
    return jsonify({"memory_usage": memory_info.percent})

# Event ketika client terhubung
@socketio.on('connect')
def handle_connect():
    global monitoring_active
    
    print("Client connected!")
    
    # Mulai monitoring hanya jika belum berjalan
    with monitoring_lock:
        if not monitoring_active:
            monitoring_active = True
            thread = threading.Thread(target=send_performance_data, daemon=True)
            thread.start()
            print("Started monitoring thread")

# Event ketika client terputus
@socketio.on('disconnect')
def handle_disconnect():
    global monitoring_active
    
    print("Client disconnected!")

if __name__ == '__main__':
    # Ambil PORT dari environment variable (untuk Render)
    # Fallback ke 5000 untuk development lokal
    port = int(os.environ.get('PORT', 5000))
    
    # Jalankan dengan host 0.0.0.0 agar bisa diakses dari luar
    # Debug=False untuk production
    socketio.run(app, host='0.0.0.0', port=port, debug=False)