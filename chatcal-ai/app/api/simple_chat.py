"""Simple chat interface for ChatCal.ai."""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/simple-chat", response_class=HTMLResponse)
async def simple_chat():
    """Simple working chat interface."""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>ChatCal.ai</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            max-width: 800px; 
            margin: 50px auto; 
            padding: 20px;
            background: #f5f5f5;
        }
        .chat-box { 
            background: white; 
            border-radius: 10px; 
            padding: 20px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .messages { 
            height: 400px; 
            overflow-y: auto; 
            border: 1px solid #ddd; 
            padding: 15px; 
            margin-bottom: 20px;
            background: #fafafa;
            border-radius: 5px;
        }
        .message { 
            margin: 10px 0; 
            padding: 10px;
            border-radius: 5px;
        }
        .user { 
            background: #007bff; 
            color: white; 
            text-align: right;
            margin-left: 20%;
        }
        .assistant { 
            background: #e9ecef; 
            margin-right: 20%;
        }
        .input-group { 
            display: flex; 
            gap: 10px;
        }
        input { 
            flex: 1; 
            padding: 10px; 
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
        }
        button { 
            padding: 10px 20px; 
            background: #28a745; 
            color: white; 
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover { background: #218838; }
        button:disabled { 
            background: #ccc; 
            cursor: not-allowed;
        }
        .loading { 
            text-align: center; 
            color: #666; 
            padding: 10px;
            display: none;
        }
        .error { 
            color: red; 
            padding: 10px;
            background: #fee;
            border-radius: 5px;
            margin: 10px 0;
        }
        h1 { 
            text-align: center; 
            color: #333;
        }
        .subtitle { 
            text-align: center; 
            color: #666; 
            margin-bottom: 30px;
        }
    </style>
</head>
<body>
    <div class="chat-box">
        <h1>🌟 ChatCal.ai</h1>
        <p class="subtitle">Your AI Calendar Assistant</p>
        
        <div class="messages" id="messages">
            <div class="message assistant">
                👋 Hi! I'm ChatCal, your friendly calendar assistant. I can help you:
                <ul>
                    <li>Check your calendar</li>
                    <li>Schedule meetings</li>
                    <li>Find available time slots</li>
                </ul>
                Just ask me anything about your schedule!
            </div>
        </div>
        
        <div class="loading" id="loading">ChatCal is thinking...</div>
        
        <div class="input-group">
            <input 
                type="text" 
                id="input" 
                placeholder="Type your message here..."
                onkeypress="if(event.key==='Enter') send()"
            >
            <button onclick="send()" id="sendBtn">Send</button>
        </div>
    </div>

    <script>
        let sessionId = null;
        let busy = false;
        
        // Get elements
        const input = document.getElementById('input');
        const messages = document.getElementById('messages');
        const loading = document.getElementById('loading');
        const sendBtn = document.getElementById('sendBtn');
        
        // Initialize session
        fetch('/sessions', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({})
        })
        .then(r => r.json())
        .then(data => {
            sessionId = data.session_id;
            console.log('Session:', sessionId);
        })
        .catch(err => {
            showMessage('Error: Could not start session', 'error');
            console.error(err);
        });
        
        function showMessage(text, type='assistant') {
            const div = document.createElement('div');
            div.className = 'message ' + type;
            div.textContent = text;
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
        }
        
        async function send() {
            const text = input.value.trim();
            if (!text || busy || !sessionId) return;
            
            // Show user message
            showMessage(text, 'user');
            input.value = '';
            
            // Disable while sending
            busy = true;
            sendBtn.disabled = true;
            loading.style.display = 'block';
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        message: text,
                        session_id: sessionId
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    showMessage(data.response, 'assistant');
                } else {
                    showMessage('Error: ' + (data.message || 'Something went wrong'), 'error');
                }
            } catch (err) {
                showMessage('Error: Connection failed', 'error');
                console.error(err);
            } finally {
                busy = false;
                sendBtn.disabled = false;
                loading.style.display = 'none';
                input.focus();
            }
        }
    </script>
</body>
</html>
"""