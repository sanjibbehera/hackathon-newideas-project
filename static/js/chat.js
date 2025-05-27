const STATE = {
    NORMAL: 'normal',
    AWS_HELP: 'aws_help',
    SERVICE_SPECIFIC: 'service_specific',
    INITIAL_GREETING: 'initial_greeting'  // New state for handling greetings
};
let conversationState = STATE.INITIAL_GREETING;
let currentService = null;

document.addEventListener('DOMContentLoaded', function() {
    const userInput = document.getElementById('userInput');
    const sendButton = document.getElementById('sendButton');
    const attachButton = document.getElementById('attachButton');
    const fileUpload = document.getElementById('fileUpload');
    const fileName = document.getElementById('fileName');
    const messageContainer = document.getElementById('messageContainer');

    // Track if it's the first user message
    let isFirstInteraction = true;
    let hasShownInitialGreeting = false;

    // Add this function to display approved services
    function displayApprovedServices(services) {
        const messageGroup = document.createElement('div');
        messageGroup.className = 'message-group bot-message-group dynamic-message';
        
        const avatar = document.createElement('img');
        avatar.className = 'avatar';
        avatar.src = '/static/images/bot.png';
        avatar.alt = 'Bot avatar';
        messageGroup.appendChild(avatar);
        
        const messagesContainer = document.createElement('div');
        messagesContainer.className = 'messages-container';
        
        const messageBubble = document.createElement('div');
        messageBubble.className = 'message bot-message';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        const title = document.createElement('div');
        title.className = 'message-text';
        title.textContent = 'I can help you with the below AWS services:';
        messageContent.appendChild(title);
        
        const list = document.createElement('ul');
        list.className = 'services-ul';
        
        services.forEach(service => {
            const item = document.createElement('li');
            item.className = 'service-item';
            item.textContent = service;
            list.appendChild(item);
        });
        
        messageContent.appendChild(list);
        messageBubble.appendChild(messageContent);
        messagesContainer.appendChild(messageBubble);
        messageGroup.appendChild(messagesContainer);
        
        messageContainer.appendChild(messageGroup);
        messageContainer.scrollTop = messageContainer.scrollHeight;
    }
    
    // Handle text messages
    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => e.key === 'Enter' && sendMessage());
    
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

        addMessage(message, 'user');
        userInput.value = '';

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    message: message,
                    current_state: conversationState,
                    current_service: currentService,
                    is_first_interaction: isFirstInteraction
                })
            });

            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

            const data = await response.json();

            // Update state and service
            if (data.new_state) conversationState = data.new_state;
            if (data.service) currentService = data.service;

            // Mark first interaction as complete
            if (isFirstInteraction) isFirstInteraction = false;            
            
            // Handle different response types
            if (data.response_type === 'approved_services') {
                if (data.approval_link) {
                    addMessage(`${data.response}`, 'bot');
                    displayApprovedServices(data.services);
                    addMessage(
                        'So let me know, how I can help you with AWS IAM.',
                        'bot'
                    );
                } else {
                    addMessage(data.response.replace(/\n/g, '<br>'), 'bot');
                }
            } else if (data.response_type === 'multiple_services') {
                // Handle case where multiple services were detected
                addMessage(data.response, 'bot');
                if (data.services_info) {
                    data.services_info.forEach(serviceInfo => {
                        addMessage(serviceInfo.message, 'bot');
                        if (serviceInfo.services) {
                            displayApprovedServices(serviceInfo.services);
                        }
                    });
                }
            } else {
                console.log("SANJIB SAYDSSSSS inside else:::::", data);
                console.log("STATES SAYDSSSSS inside else WAATTTTA STATE:::::", STATE);
                let formattedResponse = data.response;
                // Add follow-up prompts based on state
                if (conversationState === STATE.INITIAL_GREETING) {
                    formattedResponse += '\nHow can I help you with AWS IAM today?';
                } 
                else if (conversationState === STATE.AWS_HELP) {
                    formattedResponse += '\nPlease share the specific issue you\'re facing with AWS so that I can help you better.';
                }
                else {
                    console.log("SANJIB IS HERE IN THE ELSE ELSE CODN!!!", data);
                    console.log("STATES inside else ELSE WAATTTTA STATE:::::", STATE);
                }
                console.log("RESPRESP inside else:::::", formattedResponse);
                
                addMessage(formattedResponse, 'bot');
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

        // Add avatar
        const avatar = document.createElement('img');
        avatar.className = 'avatar';
        avatar.src = type === 'bot' ? '/static/images/bot.png' : '/static/images/user.png';
        avatar.alt = `${type} avatar`;

        // Create messages container (same as initial messages)
        const messagesContainer = document.createElement('div');
        messagesContainer.className = 'messages-container';

        // Create message bubble with proper structure
        const messageBubble = document.createElement('div');
        messageBubble.className = `message ${type}-message`;

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        // Handle rich content formatting
        let formattedContent = content;
        if (typeof content === 'string' && content.includes('**')) {
            formattedContent = content
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\📝(.*?)\n/g, '<div class="error-detail">$1</div>')
                .replace(/\🛠️(.*?)(\n|$)/g, '<div class="fix-header">$1</div>')
                .replace(/\- (.*?)(\n|$)/g, '<li>$1</li>')
                .replace(/\📖(.*?)(\n|$)/g, '<a href="$1" class="doc-link">View AWS Documentation</a>')
                .replace(/\n/g, '<br>');
        }

        // Add formatted content
        messageContent.innerHTML = formattedContent;
        messageBubble.appendChild(messageContent);
        messagesContainer.appendChild(messageBubble);

        // messagesContainer.appendChild(messageBubble);

        // Parse rich content
        // if (typeof content === 'string' && content.includes('**')) {
        //     const formattedContent = content
        //         .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        //         .replace(/\📝(.*?)\n/g, '<div class="error-detail">$1</div>')
        //         .replace(/\🛠️(.*?)(\n|$)/g, '<div class="fix-header">$1</div>')
        //         .replace(/\- (.*?)(\n|$)/g, '<li>$1</li>')
        //         .replace(/\📖(.*?)(\n|$)/g, '<a href="$1" class="doc-link">View AWS Documentation</a>')
        //         .replace(/\n/g, '<br>');
            
        //     messageGroup.innerHTML = formattedContent;
        // } else {
        //     // Regular message handling
        //     const messageText = document.createElement('div');
        //     messageText.className = 'message-text';
        //     messageText.textContent = content;
        //     messageGroup.appendChild(messageText);
        // }


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

        if (type === 'bot') {
            messageGroup.appendChild(avatar);  // Avatar first for bot
            messageGroup.appendChild(messagesContainer);
        } else {
            messageGroup.appendChild(messagesContainer);  // Text first for user
            messageGroup.appendChild(avatar);
        }
        
        // Final assembly
        messageContainer.appendChild(messageGroup);

        // Scroll to bottom
        messageContainer.scrollTop = messageContainer.scrollHeight;
    }
});