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
    
    function sendMessage() {
        const message = userInput.value.trim();
        if (message) {
            addMessage(message, 'user');
            userInput.value = '';
            
            // Here you would typically send the message to your backend
            // For now, we'll just simulate a response
            setTimeout(() => {
                addMessage("Thanks for your message! How can I assist you with AWS IAM?", 'bot');
            }, 1000);
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
        timestamp.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        messagesContainer.appendChild(timestamp);
        
        // Final assembly
        messageContainer.appendChild(messageGroup);

        // Scroll to bottom
        messageContainer.scrollTop = messageContainer.scrollHeight;
    }
});