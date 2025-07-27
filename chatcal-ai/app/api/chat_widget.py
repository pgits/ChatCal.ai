"""Chat widget HTML interface for ChatCal.ai."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/chat-widget", response_class=HTMLResponse)
async def chat_widget(request: Request):
    """Embeddable chat widget."""
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ChatCal.ai - Calendar Assistant</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }}
            
            .chat-container {{
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                width: 100%;
                max-width: 800px;
                height: 600px;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }}
            
            .chat-header {{
                background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
                color: white;
                padding: 20px;
                text-align: center;
                position: relative;
            }}
            
            .chat-header h1 {{
                font-size: 24px;
                margin-bottom: 5px;
            }}
            
            .chat-header p {{
                opacity: 0.9;
                font-size: 14px;
            }}
            
            .status-indicator {{
                position: absolute;
                top: 20px;
                right: 20px;
                width: 12px;
                height: 12px;
                background: #4CAF50;
                border-radius: 50%;
                border: 2px solid white;
                animation: pulse 2s infinite;
            }}
            
            @keyframes pulse {{
                0% {{ opacity: 1; }}
                50% {{ opacity: 0.5; }}
                100% {{ opacity: 1; }}
            }}
            
            .chat-messages {{
                flex: 1;
                padding: 20px;
                overflow-y: auto;
                background: #f8f9fa;
            }}
            
            .message {{
                margin-bottom: 15px;
                display: flex;
                align-items: flex-start;
                gap: 10px;
            }}
            
            .message.user {{
                flex-direction: row-reverse;
            }}
            
            .message-avatar {{
                width: 36px;
                height: 36px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 16px;
                flex-shrink: 0;
            }}
            
            .message.user .message-avatar {{
                background: #2196F3;
                color: white;
            }}
            
            .message.assistant .message-avatar {{
                background: #4CAF50;
                color: white;
            }}
            
            .message-content {{
                max-width: 70%;
                padding: 12px 16px;
                border-radius: 18px;
                line-height: 1.4;
                white-space: pre-wrap;
            }}
            
            .message.user .message-content {{
                background: #2196F3;
                color: white;
                border-bottom-right-radius: 4px;
            }}
            
            .message.assistant .message-content {{
                background: white;
                color: #333;
                border: 1px solid #e0e0e0;
                border-bottom-left-radius: 4px;
            }}
            
            .chat-input {{
                padding: 20px;
                background: white;
                border-top: 1px solid #e0e0e0;
                display: flex;
                gap: 10px;
                align-items: center;
            }}
            
            .chat-input input {{
                flex: 1;
                padding: 12px 16px;
                border: 2px solid #e0e0e0;
                border-radius: 25px;
                outline: none;
                font-size: 14px;
                transition: border-color 0.3s;
            }}
            
            .chat-input input:focus {{
                border-color: #4CAF50;
            }}
            
            .chat-input button {{
                width: 40px;
                height: 40px;
                border: none;
                background: #4CAF50;
                color: white;
                border-radius: 50%;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: background-color 0.3s;
            }}
            
            .chat-input button:hover {{
                background: #45a049;
            }}
            
            .chat-input button:disabled {{
                background: #ccc;
                cursor: not-allowed;
            }}
            
            .typing-indicator {{
                display: none;
                padding: 12px 16px;
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 18px;
                border-bottom-left-radius: 4px;
                max-width: 70%;
                margin-bottom: 15px;
            }}
            
            .typing-dots {{
                display: flex;
                gap: 4px;
            }}
            
            .typing-dots span {{
                width: 8px;
                height: 8px;
                background: #999;
                border-radius: 50%;
                animation: typing 1.4s infinite;
            }}
            
            .typing-dots span:nth-child(2) {{
                animation-delay: 0.2s;
            }}
            
            .typing-dots span:nth-child(3) {{
                animation-delay: 0.4s;
            }}
            
            @keyframes typing {{
                0%, 60%, 100% {{
                    transform: translateY(0);
                    opacity: 0.4;
                }}
                30% {{
                    transform: translateY(-10px);
                    opacity: 1;
                }}
            }}
            
            .welcome-message {{
                text-align: center;
                color: #666;
                font-style: italic;
                margin: 20px 0;
            }}
            
            .quick-actions {{
                display: flex;
                gap: 10px;
                margin: 10px 0;
                flex-wrap: wrap;
            }}
            
            .quick-action {{
                background: #f0f0f0;
                color: #555;
                padding: 8px 12px;
                border-radius: 15px;
                border: none;
                cursor: pointer;
                font-size: 12px;
                transition: background-color 0.3s;
            }}
            
            .quick-action:hover {{
                background: #e0e0e0;
            }}
        </style>
    </head>
    <body>
        <div class="chat-container">
            <div class="chat-header">
                <div class="status-indicator"></div>
                <h1>🌟 ChatCal.ai</h1>
                <p>Your friendly AI calendar assistant</p>
            </div>
            
            <div class="chat-messages" id="chatMessages">
                <div class="welcome-message">
                    👋 Welcome! I'm ChatCal, your friendly calendar assistant.<br>
                    Try saying: "Schedule a meeting next Tuesday at 2pm" or "Check my availability tomorrow"
                </div>
                
                <div class="quick-actions">
                    <button class="quick-action" onclick="sendQuickMessage('Check my availability for tomorrow')">📅 Check availability</button>
                    <button class="quick-action" onclick="sendQuickMessage('What meetings do I have this week?')">📋 View schedule</button>
                    <button class="quick-action" onclick="sendQuickMessage('/help')">❓ Help</button>
                </div>
            </div>
            
            <div class="typing-indicator" id="typingIndicator">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
            
            <div class="chat-input">
                <input 
                    type="text" 
                    id="messageInput" 
                    placeholder="Ask me to schedule a meeting, check availability, or manage your calendar..."
                    maxlength="1000"
                />
                <button id="sendButton" onclick="sendMessage()">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                    </svg>
                </button>
            </div>
        </div>
        
        <script>
            let sessionId = null;
            let isLoading = false;
            
            const chatMessages = document.getElementById('chatMessages');
            const messageInput = document.getElementById('messageInput');
            const sendButton = document.getElementById('sendButton');
            const typingIndicator = document.getElementById('typingIndicator');
            
            // Initialize session
            async function initializeSession() {{
                try {{
                    const response = await fetch('{base_url}/sessions', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{}})
                    }});
                    
                    if (response.ok) {{
                        const data = await response.json();
                        sessionId = data.session_id;
                        console.log('Session initialized:', sessionId);
                    }}
                }} catch (error) {{
                    console.error('Failed to initialize session:', error);
                }}
            }}
            
            function addMessage(content, isUser = false) {{
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${{isUser ? 'user' : 'assistant'}}`;
                
                const avatar = document.createElement('div');
                avatar.className = 'message-avatar';
                avatar.textContent = isUser ? '👤' : '🤖';
                
                const messageContent = document.createElement('div');
                messageContent.className = 'message-content';
                messageContent.textContent = content;
                
                messageDiv.appendChild(avatar);
                messageDiv.appendChild(messageContent);
                
                // Insert before typing indicator
                chatMessages.insertBefore(messageDiv, typingIndicator);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }}
            
            function showTyping() {{
                typingIndicator.style.display = 'block';
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }}
            
            function hideTyping() {{
                typingIndicator.style.display = 'none';
            }}
            
            async function sendMessage(message = null) {{
                const text = message || messageInput.value.trim();
                if (!text || isLoading) return;
                
                // Add user message
                addMessage(text, true);
                messageInput.value = '';
                
                // Show loading state
                isLoading = true;
                sendButton.disabled = true;
                showTyping();
                
                try {{
                    const response = await fetch('{base_url}/chat', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{
                            message: text,
                            session_id: sessionId
                        }})
                    }});
                    
                    if (response.ok) {{
                        const data = await response.json();
                        sessionId = data.session_id; // Update session ID
                        addMessage(data.response);
                    }} else {{
                        const error = await response.json();
                        addMessage(`Sorry, I encountered an error: ${{error.message || 'Unknown error'}}`);
                    }}
                }} catch (error) {{
                    console.error('Chat error:', error);
                    addMessage('Sorry, I had trouble connecting. Please try again!');
                }} finally {{
                    isLoading = false;
                    sendButton.disabled = false;
                    hideTyping();
                }}
            }}
            
            function sendQuickMessage(message) {{
                messageInput.value = message;
                sendMessage();
            }}
            
            // Event listeners
            messageInput.addEventListener('keypress', function(e) {{
                if (e.key === 'Enter' && !e.shiftKey) {{
                    e.preventDefault();
                    sendMessage();
                }}
            }});
            
            // Initialize when page loads
            window.addEventListener('load', initializeSession);
        </script>
    </body>
    </html>
    """


@router.get("/widget", response_class=HTMLResponse)
async def embeddable_widget():
    """Minimal embeddable widget for other websites."""
    return """
    <div id="chatcal-widget" style="
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 400px;
        height: 500px;
        background: white;
        border-radius: 10px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        z-index: 9999;
        display: none;
    ">
        <iframe 
            src="/chat-widget" 
            width="100%" 
            height="100%" 
            frameborder="0"
            style="border-radius: 10px;">
        </iframe>
    </div>
    
    <button id="chatcal-toggle" style="
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 60px;
        height: 60px;
        background: #4CAF50;
        color: white;
        border: none;
        border-radius: 50%;
        cursor: pointer;
        font-size: 24px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        z-index: 10000;
    ">💬</button>
    
    <script>
        document.getElementById('chatcal-toggle').onclick = function() {
            const widget = document.getElementById('chatcal-widget');
            const toggle = document.getElementById('chatcal-toggle');
            
            if (widget.style.display === 'none') {
                widget.style.display = 'block';
                toggle.textContent = '✕';
            } else {
                widget.style.display = 'none';
                toggle.textContent = '💬';
            }
        };
    </script>
    """