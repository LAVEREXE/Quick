import os
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--no-sandbox"

from flask import Flask, render_template, request, redirect, url_for, jsonify, session
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
# Папка для хранения файлов истории чатов
HISTORY_DIR = os.path.join(os.getcwd(), 'chat_history')
if not os.path.exists(HISTORY_DIR):
    os.makedirs(HISTORY_DIR)

def save_ip_to_history(ip):
    try:
        history = []
        ip_file = os.path.join(os.getcwd(), 'ip_history.json')
        if os.path.exists(ip_file):
            with open(ip_file, 'r') as f:
                history = json.load(f)
        
        if ip not in history:
            history.insert(0, ip)
            history = history[:5]  # Храним последние 5 IP
            
        with open(ip_file, 'w') as f:
            json.dump(history, f)
    except Exception as e:
        print(f"Error saving IP history: {e}")

def get_ip_history():
    try:
        ip_file = os.path.join(os.getcwd(), 'ip_history.json')
        if os.path.exists(ip_file):
            with open(ip_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading IP history: {e}")
    return []

# Функция для сохранения самопереписки (сообщения себе)
def save_self_message(username, text):
    try:
        filename = os.path.join(HISTORY_DIR, f'{username}SelfMG.json')
        messages = []
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                messages = json.load(f)
        messages.append({
            'text': text,
            'timestamp': datetime.now().strftime('%H:%M')
        })
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
        print(f"Самопереписка сохранена в {filename}")
    except Exception as e:
        print(f"Error saving self message: {e}")

# Функция для сохранения переписки между двумя пользователями
def save_chat_message(sender, recipient, text):
    try:
        # Если отправитель и получатель совпадают, вызываем функцию для самопереписки
        if sender == recipient:
            save_self_message(sender, text)
            return
        # Формирование имени файла, например: LaverChatDrakula.json
        filename = os.path.join(HISTORY_DIR, f"{sender}Chat{recipient}.json")
        messages = []
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                messages = json.load(f)
        new_message = {
            'sender': sender,
            'recipient': recipient,
            'text': text,
            'timestamp': datetime.now().strftime('%H:%M')
        }
        messages.append(new_message)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
        print(f"История чата {sender} -> {recipient} сохранена в {filename}")
    except Exception as e:
        print(f"Error saving chat message: {e}")

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

connected_clients = {}
# Обработка self_message через отдельный endpoint
@sock.route('/ws/chat')
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
            print("Client disconnected from /ws/chat")
            break
        except Exception as e:
            print(f"WebSocket error (/ws/chat): {e}")
            break

def handle_self_message(message):
    try:
        username = message.get('username')
        text = message.get('text')
        if not username or not text:
            return None
        # Сохраняем сообщение себе
        save_self_message(username, text)
        # Возвращаем ответ для отображения
        return {
            'type': 'self_message',
            'text': text,
            'timestamp': datetime.now().strftime('%H:%M')
        }
    except Exception as e:
        print(f"Error handling self_message: {e}")
        return None

# Обработка обычных сообщений (между пользователями)
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
            # Сохраняем историю переписки между пользователями
            save_chat_message(data['sender'], data['recipient'], data['text'])
            return {
                'type': 'message',
                'sender': data['sender'],
                'text': data['text'],
                'timestamp': datetime.now().strftime('%H:%M')
            }
        # Если вдруг self_message попадает сюда, обрабатываем отдельно
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

@sock.route('/ws')
def handle_websocket(ws):
    try:
        while True:
            data = ws.receive()
            if not data:
                continue
                
            message_data = json.loads(data)
            print(f"Received message on /ws: {message_data}")
            
            if 'timestamp' not in message_data:
                message_data['timestamp'] = datetime.now().strftime("%H:%M:%S")
            
            try:
                if message_data.get('type') == 'connect':
                    username = message_data.get('username')
                    if username:
                        connected_clients[username] = ws
                        print(f"User connected: {username}")
                elif message_data.get('type') in ['message', 'self_message']:
                    # Рассылка сообщения всем клиентам
                    for client in connected_clients.values():
                        try:
                            client.send(json.dumps(message_data))
                        except Exception as e:
                            print(f"Error sending to client: {e}")
            except Exception as e:
                print(f"Error processing message on /ws: {e}")
                ws.send(json.dumps({
                    'type': 'error',
                    'message': str(e)
                }))
                    
    except Exception as e:
        print(f"WebSocket error (/ws): {e}")
    finally:
        if ws in connected_clients.values():
            to_remove = [k for k, v in connected_clients.items() if v == ws]
            for k in to_remove:
                del connected_clients[k]

# Обработчики ошибок
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

# Обновлённый маршрут страницы чата, который загружает историю самопереписки
@app.route('/chat')
def chat():
    username = request.args.get('username', 'Anonymous')
    server_ip = request.args.get('server_ip', '127.0.0.1')
    # Попытка загрузить сохранённые сообщения для self-chat
    self_chat_file = os.path.join(HISTORY_DIR, f'{username}SelfMG.json')
    self_chat_messages = []
    if os.path.exists(self_chat_file):
        try:
            with open(self_chat_file, 'r', encoding='utf-8') as f:
                self_chat_messages = json.load(f)
        except Exception as e:
            print(f"Error loading self chat messages: {e}")
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
