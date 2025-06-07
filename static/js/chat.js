document.addEventListener('DOMContentLoaded', function() {
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    const messagesContainer = document.getElementById('messagesContainer');
    const username = "{{ username }}"; // Get username from template
    let ws = null;
    let isSelfChat = false;
    let currentRecipient = null;
    const sentMessageIds = new Set();

    // Function to generate WebSocket URL dynamically
    function getWebSocketURL() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        return `${protocol}//${window.location.host}/ws`;
    }

    function connectWebSocket() {
        const wsURL = getWebSocketURL();
        ws = new WebSocket(wsURL);

        ws.onopen = () => {
            console.log('WebSocket connected');
            updateConnectionStatus(true);
            ws.send(JSON.stringify({ type: 'connect', username: username }));
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('Received message:', data);

                if (data.type === 'user_list' && data.users) {
                    updateUsersList(data.users);
                    return;
                }

                if (data.id && sentMessageIds.has(data.id)) {
                    sentMessageIds.delete(data.id);
                    return;
                }

                if (data.type === 'message' || (data.type === 'self_message' && isSelfChat)) {
                    addMessage(data);
                }
            } catch (error) {
                console.error('Ошибка обработки сообщения:', error);
            }
        };

        ws.onclose = () => {
            console.log('WebSocket disconnected');
            updateConnectionStatus(false);
            setTimeout(connectWebSocket, 2000);
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }

    function updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            statusElement.textContent = connected ? 'Connected' : 'Disconnected';
            statusElement.className = connected ? 'text-green-500' : 'text-red-500';
        }
    }

    function addMessage(message) {
        const messagesContainer = document.getElementById('messagesContainer');
        if (!messagesContainer) return;

        const isMine = message.sender === username;
        const messageClass = isMine ? 'message-mine' : 'message-other';

        const container = document.createElement('div');
        container.className = `message-container ${messageClass}`;

        const escapedText = escapeHtml(message.text || message.message);

        container.innerHTML = `
            <div class="message-bubble">
                ${message.sender && !isSelfChat ? `<p class="message-text font-bold">${escapeHtml(message.sender)}</p>` : ''}
                <p class="message-text">${escapedText}</p>
                <div class="message-time">${message.timestamp || new Date().toLocaleTimeString()}</div>
            </div>
        `;

        messagesContainer.appendChild(container);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function sendMessage() {
        const text = messageInput.value.trim();
        if (!text || !ws || ws.readyState !== WebSocket.OPEN) return;

        const id = `${new Date().getTime()}-${Math.random().toString(36).substr(2, 9)}`;
        const timestamp = new Date().toLocaleTimeString();

        const messageData = {
            type: isSelfChat ? 'self_message' : 'message',
            sender: username,
            text: text,
            timestamp: timestamp,
            recipient: isSelfChat ? username : currentRecipient,
            id: id
        };

        sentMessageIds.add(id);
        ws.send(JSON.stringify(messageData));
        addMessage(messageData);
        messageInput.value = '';
    }

    function updateUsersList(users) {
        const usersListEl = document.getElementById('users-list');
        if (!usersListEl) return;

        // Create a document fragment to minimize DOM manipulations
        const fragment = document.createDocumentFragment();

        users.forEach(user => {
            if (user === username) return;

            const userEl = document.createElement('div');
            userEl.className = 'user-item';
            userEl.textContent = user;
            userEl.addEventListener('click', () => selectUser(user));
            fragment.appendChild(userEl);
        });

        // Replace the entire user list with the new fragment
        usersListEl.innerHTML = '';
        usersListEl.appendChild(fragment);
    }

    function selectUser(user) {
        isSelfChat = false;
        currentRecipient = user;
        document.getElementById('recipientName').textContent = user;
        document.getElementById('lastSeen').textContent = '';
        document.getElementById('messagesContainer').innerHTML = '';
    }

    function selectSelfChat() {
        isSelfChat = true;
        currentRecipient = username;
        document.getElementById('recipientName').textContent = 'Заметки';
        document.getElementById('lastSeen').textContent = 'Личные сообщения';
        document.getElementById('messagesContainer').innerHTML = '';
    }

    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    document.addEventListener('DOMContentLoaded', () => {
        connectWebSocket();

        sendButton.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        document.getElementById('self-chat-option').addEventListener('click', selectSelfChat);
    });
});