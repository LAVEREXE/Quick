document.addEventListener('DOMContentLoaded', function() {
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-message');
    const messagesContainer = document.getElementById('messages');
    
    function createMessage(data) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${data.is_mine ? 'mine' : 'other'}`;
        
        let html = '';
        if (!data.is_mine) {
            html += `<div class="sender">${data.sender}</div>`;
        }
        
        if (data.reply_to) {
            html += `<div class="reply">${data.reply_to}</div>`;
        }
        
        html += `<div class="content">${data.text}</div>`;
        html += `<div class="timestamp">${data.timestamp}</div>`;
        
        messageDiv.innerHTML = html;
        return messageDiv;
    }
    
    let ws = null;

    function connectWebSocket(username) {
        ws = new WebSocket(`ws://${window.location.host}/ws`);
        
        ws.onopen = function() {
            console.log('WebSocket connected');
            document.getElementById('connection-status').textContent = 'Connected';
            document.getElementById('connection-status').classList.remove('text-red-500');
            document.getElementById('connection-status').classList.add('text-green-500');
        };

        ws.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                appendMessage(data.username, data.message, data.timestamp);
            } catch (error) {
                console.error('Error parsing message:', error);
            }
        };

        ws.onclose = function() {
            document.getElementById('connection-status').textContent = 'Disconnected';
            document.getElementById('connection-status').classList.remove('text-green-500');
            document.getElementById('connection-status').classList.add('text-red-500');
            // Try to reconnect after 5 seconds
            setTimeout(() => connectWebSocket(username), 5000);
        };

        ws.onerror = function(error) {
            console.error('WebSocket error:', error);
        };
    }

    function sendMessage() {
        const messageInput = document.getElementById('message-input');
        const message = messageInput.value.trim();
        
        if (!message) return;
        
        if (ws && ws.readyState === WebSocket.OPEN) {
            const messageData = {
                username: document.getElementById('username').value,
                message: message
            };
            
            try {
                ws.send(JSON.stringify(messageData));
                messageInput.value = '';
            } catch (error) {
                console.error('Error sending message:', error);
                alert('Failed to send message. Please try again.');
            }
        } else {
            alert('Not connected to server. Attempting to reconnect...');
            connectWebSocket(document.getElementById('username').value);
        }
    }

    function appendMessage(username, message, timestamp) {
        const chatMessages = document.getElementById('chat-messages');
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', 'mb-4', 'p-2', 'rounded');
        
        const isCurrentUser = username === document.getElementById('username').value;
        messageElement.classList.add(isCurrentUser ? 'bg-blue-100' : 'bg-gray-100');
        
        messageElement.innerHTML = `
            <div class="flex justify-between items-start">
                <span class="font-bold">${username}</span>
                <span class="text-xs text-gray-500">${timestamp}</span>
            </div>
            <div class="mt-1">${escapeHtml(message)}</div>
        `;
        
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // Event listeners
    document.getElementById('message-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    document.getElementById('send-button').addEventListener('click', sendMessage);
});