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
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        if (type === 'bot') {
            const avatar = document.createElement('img');
            avatar.className = 'avatar';
            avatar.src = '/static/images/bot.png';
            avatar.alt = 'Bot avatar';
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-text';
            contentDiv.textContent = content;
            
            messageDiv.appendChild(avatar);
            messageDiv.appendChild(contentDiv);
        } else {
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-text';
            contentDiv.textContent = content;
            
            const avatar = document.createElement('img');
            avatar.className = 'avatar';
            avatar.src = '/static/images/user.png';
            avatar.alt = 'User avatar';
            
            messageDiv.appendChild(contentDiv);
            messageDiv.appendChild(avatar);
        }
        
        messageContainer.appendChild(messageDiv);
        messageContainer.scrollTop = messageContainer.scrollHeight;
    }
});