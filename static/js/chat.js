document.addEventListener('DOMContentLoaded', function() {
    const userInput = document.getElementById('userInput');
    const sendButton = document.getElementById('sendButton');
    const attachButton = document.getElementById('attachButton');
    const fileUpload = document.getElementById('fileUpload');
    const fileName = document.getElementById('fileName');
    const messageContainer = document.getElementById('messageContainer');
    
    // Handle text messages
    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Handle file attachment button click
    attachButton.addEventListener('click', function() {
        fileUpload.click();
    });
    
    // Handle file selection
    fileUpload.addEventListener('change', function() {
        if (this.files.length > 0) {
            fileName.textContent = this.files[0].name;
        } else {
            fileName.textContent = 'No file selected';
        }
    });
    
    async function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        addMessage('user', message);
        document.getElementById('userInput').value = '';
        // addMessage('bot', data.response.replace(/\n/g, '<br>'));

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            addMessage('bot', data.response.replace(/\n/g, '<br>'));
            // Format the response better if it's about unapproved services
            if (data.response.includes('not currently approved') || 
                data.response.includes('I specialize only')) {
                addMessage('bot', data.response.replace(/\n/g, '<br>'));
            } else {
                addMessage('bot', data.response);
            }
        } catch (error) {
            console.error('Error:', error);
            addMessage('bot', 'Sorry, there was an error processing your request.');
        }
    }
    
    function addMessage(content, type) {

        // Create the complete message group structure
        const messageGroup = document.createElement('div');
        messageGroup.className = `message-group ${type}-message-group dynamic-message`;

        // Create messages container (same as initial messages)
        const messagesContainer = document.createElement('div');
        messagesContainer.className = 'messages-container';

        // Create message bubble with proper structure
        const messageBubble = document.createElement('div');
        messageBubble.className = `message ${type}-message`;

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        const messageText = document.createElement('div');
        messageText.className = 'message-text';
        messageText.textContent = content;

        // Add avatar
        const avatar = document.createElement('img');
        avatar.className = 'avatar';
        avatar.src = type === 'bot' ? '/static/images/bot.png' : '/static/images/user.png';
        avatar.alt = `${type} avatar`;

        // Assemble message - DIFFERENT ORDER FOR USER/BOT
        messageContent.appendChild(messageText);
        messageBubble.appendChild(messageContent);

        if (type === 'bot') {
            messageGroup.appendChild(avatar);  // Avatar first for bot
            messageGroup.appendChild(messagesContainer);
        } else {
            messageGroup.appendChild(messagesContainer);  // Text first for user
            messageGroup.appendChild(avatar);
        }

        messagesContainer.appendChild(messageBubble);


        // Add timestamp
        const timestamp = document.createElement('div');
        timestamp.className = 'message-time';

        // Create custom formatted date string
        const now = new Date();
        const day = now.getDate();
        const month = now.toLocaleString('default', { month: 'short' });
        const year = now.getFullYear();
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');

        timestamp.textContent = `${day} ${month} ${year} ${hours}:${minutes}`;
        messagesContainer.appendChild(timestamp);
        
        // Final assembly
        messageContainer.appendChild(messageGroup);

        // Scroll to bottom
        messageContainer.scrollTop = messageContainer.scrollHeight;
    }
});