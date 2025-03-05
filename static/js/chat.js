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
    
    function sendMessage() {
        const text = messageInput.value.trim();
        if (!text) return;
        
        // Add to UI immediately
        const data = {
            sender: '{{ username }}',
            text: text,
            timestamp: new Date().toLocaleTimeString(),
            is_mine: true
        };
        
        messagesContainer.appendChild(createMessage(data));
        messageInput.value = '';
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        // Send to server
        // TODO: Implement WebSocket or other real-time communication
    }
    
    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
});