import os
import json
import logging
import time
import threading
from datetime import datetime
from typing import List, Dict, Any

from flask import Flask, render_template, request, redirect, url_for, session
from flask_sock import Sock
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QUrl, Qt, QCoreApplication
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
from simple_websocket import ConnectionClosed

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass

# Constants
PORT = 12345
HISTORY_DIR = os.path.join(os.getcwd(), 'chat_history')

# Ensure history directory exists
if not os.path.exists(HISTORY_DIR):
    os.makedirs(HISTORY_DIR)

def save_ip_to_history(ip: str) -> None:
    """Saves the IP address to the IP history file."""
    try:
        ip_file = os.path.join(os.getcwd(), 'ip_history.json')
        history: List[str] = []
        if os.path.exists(ip_file):
            with open(ip_file, 'r') as f:
                history = json.load(f)

        if ip not in history:
            history.insert(0, ip)
            history = history[:5]  # Keep only the last 5 IPs

        with open(ip_file, 'w') as f:
            json.dump(history, f)
        logger.info(f"IP address {ip} saved to history.")
    except Exception as e:
        logger.error(f"Error saving IP history: {e}", exc_info=True)

def get_ip_history() -> List[str]:
    """Retrieves the IP history from the IP history file."""
    try:
        ip_file = os.path.join(os.getcwd(), 'ip_history.json')
        if os.path.exists(ip_file):
            with open(ip_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading IP history: {e}", exc_info=True)
        return []

def save_self_message(username: str, text: str) -> None:
    """Saves a self-message to the user's self-chat history file."""
    try:
        filename = os.path.join(HISTORY_DIR, f'{username}SelfMG.json')
        messages: List[Dict[str, str]] = []
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                messages = json.load(f)

        messages.append({
            'text': text,
            'timestamp': datetime.now().strftime('%H:%M')
        })

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
        logger.info(f"Self-message saved to {filename}")
    except Exception as e:
        logger.error(f"Error saving self-message: {e}", exc_info=True)

def save_chat_message(sender: str, recipient: str, text: str) -> None:
    """Saves a chat message between two users to the appropriate history file."""
    try:
        if sender == recipient:
            save_self_message(sender, text)
            return

        filename = os.path.join(HISTORY_DIR, f"{sender}Chat{recipient}.json")
        messages: List[Dict[str, str]] = []
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
        logger.info(f"Chat history {sender} -> {recipient} saved to {filename}")
    except Exception as e:
        logger.error(f"Error saving chat message: {e}", exc_info=True)

# Flask app setup
app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a strong, randomly generated key
sock = Sock(app)

# WebSocket route for handling chat messages
@sock.route('/ws')
def echo(ws):
    """Handles WebSocket connections for chat."""
    username = None
    try:
        while True:
            data = ws.receive()
            if data is None:
                break  # Connection closed

            message = json.loads(data)
            message_type = message.get('type')

            if message_type == 'connect':
                username = message.get('username')
                logger.info(f"User {username} connected.")
                # In a real application, you would likely store the username
                # and WebSocket connection in a data structure to track
                # connected users.

            elif message_type == 'message':
                sender = message.get('sender')
                text = message.get('text')
                recipient = message.get('recipient')
                timestamp = message.get('timestamp')

                if not all([sender, text, recipient, timestamp]):
                    raise ValidationError("Missing required fields in message.")

                save_chat_message(sender, recipient, text)

                # Broadcast the message to the recipient (and sender)
                broadcast_message(sender, recipient, text, timestamp)

            elif message_type == 'self_message':
                sender = message.get('sender')
                text = message.get('text')
                timestamp = message.get('timestamp')

                if not all([sender, text, timestamp]):
                    raise ValidationError("Missing required fields in self_message.")

                save_self_message(sender, text)

                # Broadcast the self-message to the sender
                broadcast_message(sender, sender, text, timestamp)

            else:
                logger.warning(f"Unknown message type: {message_type}")

    except ConnectionClosed:
        logger.info(f"Connection closed for user {username}.")
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
    except Exception as e:
        logger.error(f"Error handling WebSocket message: {e}", exc_info=True)

def broadcast_message(sender: str, recipient: str, text: str, timestamp: str) -> None:
    """Broadcasts a message to the specified recipient (and sender)."""
    # In a real application, you would iterate over the connected users
    # and send the message to the appropriate recipients based on
    # your user tracking data structure.
    # This is a placeholder for that logic.
    logger.info(f"Broadcasting message from {sender} to {recipient}.")
    # Replace this with your actual broadcasting logic.
    pass

# Flask routes
@app.route('/', methods=['GET', 'POST'])
def login():
    """Handles user login."""
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        server_ip = request.form.get('server_ip')

        if not username or not server_ip:
            error = "Username and IP are required."
        else:
            save_ip_to_history(server_ip)
            # Store login information in session
            session['username'] = username
            session['server_ip'] = server_ip
            return redirect(url_for('chat'))

    ip_history = get_ip_history()
    return render_template('login.html', ip_history=ip_history, error=error)

@app.route('/chat')
def chat():
    """Renders the chat interface."""
    if 'username' in session and 'server_ip' in session:
        username = session['username']
        return render_template('chat.html', username=username)
    else:
        return redirect(url_for('login'))

def run_qt():
    """Runs the Qt application."""
    logger.info("Starting Qt application...")
    QCoreApplication.setAttribute(Qt.AA_UseSoftwareOpenGL)
    qt_app = QApplication([])  # Use empty list instead of sys.argv
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
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--no-sandbox"
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=lambda: app.run(debug=False, use_reloader=False))
    flask_thread.daemon = True
    flask_thread.start()

    # Run the Qt application in the main thread
    qt_app_return_code = run_qt()
    logger.info(f"Qt application exited with code: {qt_app_return_code}")


