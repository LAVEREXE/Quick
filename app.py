import os
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--no-sandbox"

from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sock import Sock
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
import sys
import threading
import time
import json
import socket
from datetime import datetime
import traceback
from simple_websocket import ConnectionClosed

class ValidationError(Exception):
    pass

# Constants
PORT = 12345

def save_ip_to_history(ip):
    try:
        history = []
        if os.path.exists('ip_history.json'):
            with open('ip_history.json', 'r') as f:
                history = json.load(f)
        
        if ip not in history:
            history.insert(0, ip)
            history = history[:5]  # Keep only last 5 IPs
            
        with open('ip_history.json', 'w') as f:
            json.dump(history, f)
    except Exception as e:
        print(f"Error saving IP history: {e}")

def get_ip_history():
    try:
        if os.path.exists('ip_history.json'):
            with open('ip_history.json', 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading IP history: {e}")
    return []

def save_self_message(username, text):
    filename = f'self_chat_{username}.json'
    messages = []
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                messages = json.load(f)
        messages.append({
            'text': text,
            'timestamp': datetime.now().strftime('%H:%M')
        })
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving self message: {e}")

class ServerThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.server = None
        self.clients = []

    def run(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(('0.0.0.0', PORT))
        self.server.listen(5)
        print(f"Server listening on 0.0.0.0:{PORT}")

        while True:
            try:
                client, address = self.server.accept()
                print(f"New connection from {address}")
                self.clients.append(client)
            except:
                break

    def stop(self):
        if self.server:
            self.server.close()
        for client in self.clients:
            try:
                client.close()
            except:
                pass

app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = 'your_secret_key'
sock = Sock(app)

connected_users = {}

@sock.route('/ws/chat')  # Changed route to avoid conflict
def ws_chat(ws):
    while True:
        try:
            data = ws.receive()
            if not data:
                continue
            
            message = json.loads(data)
            if message.get('type') == 'self_message':
                response = handle_self_message(message)
                if response:
                    ws.send(json.dumps(response))
        except ConnectionClosed:
            print("Client disconnected")
            break
        except Exception as e:
            print(f"WebSocket error: {e}")
            break

def handle_self_message(message):
    try:
        username = message.get('username')
        text = message.get('text')
        timestamp = datetime.now().strftime('%H:%M')
        
        if not username or not text:
            return None
            
        chat_file = f'self_chat_{username}.json'
        messages = []
        
        if os.path.exists(chat_file):
            with open(chat_file, 'r', encoding='utf-8') as f:
                messages = json.load(f)
        
        new_message = {
            'text': text,
            'timestamp': timestamp
        }
        messages.append(new_message)
        
        with open(chat_file, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
        
        return {
            'type': 'self_message',
            'text': text,
            'timestamp': timestamp
        }
    except Exception as e:
        print(f"Error handling message: {e}")
        return None

@sock.route('/chat')
def chat_socket(ws):
    try:
        while True:
            raw_data = ws.receive()
            if not raw_data:
                continue
                
            data = json.loads(raw_data)
            response = handle_message(data)
            
            if response:
                ws.send(json.dumps(response))
    except Exception as e:
        error_response = {
            'type': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }
        try:
            ws.send(json.dumps(error_response))
        except:
            print(f"Failed to send error message: {error_response}")

def handle_message(data):
    try:
        if data['type'] == 'message':
            return {
                'type': 'message',
                'sender': data['sender'],
                'text': data['text'],
                'timestamp': datetime.now().strftime('%H:%M')
            }
        elif data['type'] == 'self_message':
            save_self_message(data['username'], data['text'])
            return {
                'type': 'self_message',
                'text': data['text'],
                'timestamp': datetime.now().strftime('%H:%M')
            }
    except Exception as e:
        return {
            'type': 'error',
            'message': str(e)
        }

# Добавим обработчик ошибок
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# Страница входа
@app.route('/')
def login():
    ip_history = get_ip_history()
    last_login = None
    
    try:
        if os.path.exists('last_login.json'):
            with open('last_login.json', 'r', encoding='utf-8') as f:
                last_login = json.load(f)
    except Exception as e:
        print(f"Error loading last login: {e}")
    
    return render_template('login.html', 
                         ip_history=ip_history, 
                         last_login=last_login)

# Страница чата
@app.route('/chat')
def chat():
    username = request.args.get('username')
    server_ip = request.args.get('server_ip')
    
    if not username or not server_ip:
        return redirect(url_for('login'))
    
    chat_file = f'self_chat_{username}.json'
    
    # Initialize self-chat file if it doesn't exist
    if not os.path.exists(chat_file):
        with open(chat_file, 'w', encoding='utf-8') as f:
            json.dump([], f)
    
    try:
        with open(chat_file, 'r', encoding='utf-8') as f:
            self_chat_messages = json.load(f)
    except:
        self_chat_messages = []
    
    return render_template('chat.html', 
                         username=username, 
                         server_ip=server_ip,
                         self_chat_messages=self_chat_messages)

@app.route('/hello/<name>')
def hello(name):
    return jsonify({
        'message': f'Hello {name}!',
        'status': 'success'
    })

def run_flask():
    print("Starting Flask server...")
    app.run(debug=False, port=5000, host='127.0.0.1')

def run_qt():
    print("Starting Qt application...")
    qt_app = QApplication(sys.argv)
    
    # Create profile and page
    profile = QWebEngineProfile()
    profile.setHttpCacheType(QWebEngineProfile.MemoryHttpCache)
    
    web = QWebEngineView()
    page = QWebEnginePage(profile)
    web.setPage(page)
    
    web.setWindowTitle('Quick Chat')
    web.resize(1200, 800)
    
    time.sleep(2)
    url = QUrl('http://127.0.0.1:5000')
    web.load(url)
    web.show()
    
    return qt_app.exec()

if __name__ == '__main__':
    try:
        flask_thread = threading.Thread(target=run_flask)
        flask_thread.daemon = True
        flask_thread.start()
        
        server_thread = ServerThread()
        server_thread.start()
        
        print("Waiting for servers to start...")
        time.sleep(2)
        
        sys.exit(run_qt())
    except Exception as e:
        print(f"Error occurred: {e}")
