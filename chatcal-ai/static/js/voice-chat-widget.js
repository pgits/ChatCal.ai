/**
 * Voice-enabled chat widget for ChatCal.ai
 * Integrates audio recording with existing text chat functionality
 */

class VoiceChatWidget {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.sessionId = options.sessionId || null;
        this.baseUrl = options.baseUrl || window.location.origin;
        
        // Audio recorder instance
        this.audioRecorder = null;
        
        // UI state
        this.isVoiceMode = false;
        this.isListening = false;
        this.isSpeaking = false;
        
        // Initialize UI
        this.createUI();
        this.setupEventListeners();
        
        // Initialize session with backend (async)
        this.initializeSession().then(() => {
            console.log('Widget ready with session:', this.sessionId);
        }).catch(error => {
            console.error('Widget initialization failed:', error);
        });
    }
    
    async initializeSession() {
        if (this.sessionId) return; // Already have a session
        
        try {
            const response = await fetch(`${this.baseUrl}/sessions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ user_data: {} })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.sessionId = data.session_id;
                console.log('Session initialized:', this.sessionId);
            } else {
                console.error('Failed to initialize session:', response.status);
                this.addMessage('assistant', '❌ Failed to initialize session. Please refresh the page.');
            }
        } catch (error) {
            console.error('Session initialization error:', error);
            this.addMessage('assistant', `❌ Session error: ${error.message}. Please refresh the page.`);
        }
    }
    
    generateSessionId() {
        return 'session_' + Math.random().toString(36).substr(2, 9) + Date.now().toString(36);
    }
    
    createUI() {
        this.container.innerHTML = `
            <div class="voice-chat-container">
                <div class="chat-header">
                    <div class="header-content">
                        <h2>🗓️ ChatCal.ai</h2>
                        <p>Your AI Calendar Assistant</p>
                    </div>
                    <div class="voice-toggle">
                        <button id="voice-toggle-btn" class="voice-btn" title="Enable voice chat">
                            🎙️
                        </button>
                    </div>
                </div>
                
                <div class="chat-messages" id="chat-messages">
                    <div class="message assistant">
                        <div class="message-content">
                            <p>👋 Hi! I'm your AI calendar assistant. I can help you schedule meetings with Peter Michael Gits.</p>
                            <p>You can type your message or click the microphone button to speak!</p>
                        </div>
                    </div>
                </div>
                
                <div class="voice-status" id="voice-status" style="display: none;">
                    <div class="status-indicator">
                        <div class="pulse-ring"></div>
                        <div class="pulse-ring-2"></div>
                        <span class="status-text">Ready to listen...</span>
                    </div>
                    <div class="transcription" id="live-transcription"></div>
                </div>
                
                <div class="chat-input-container">
                    <div class="input-group">
                        <input type="text" id="chat-input" placeholder="Type your message or use voice..." />
                        <div class="button-group">
                            <button id="record-btn" class="record-btn" style="display: none;" title="Hold to speak">
                                🎤
                            </button>
                            <button id="send-btn" class="send-btn" title="Send message">
                                ➤
                            </button>
                        </div>
                    </div>
                </div>
                
                <div class="audio-controls" id="audio-controls" style="display: none;">
                    <button id="stop-recording-btn" class="control-btn">Stop Recording</button>
                    <button id="cancel-recording-btn" class="control-btn secondary">Cancel</button>
                </div>
            </div>
        `;
        
        this.addStyles();
    }
    
    addStyles() {
        const styleSheet = document.createElement('style');
        styleSheet.textContent = `
            .voice-chat-container {
                max-width: 600px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                overflow: hidden;
                height: 500px;
                display: flex;
                flex-direction: column;
            }
            
            .chat-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 16px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .header-content h2 {
                margin: 0;
                font-size: 1.4em;
            }
            
            .header-content p {
                margin: 4px 0 0 0;
                opacity: 0.9;
                font-size: 0.9em;
            }
            
            .voice-toggle .voice-btn {
                background: rgba(255,255,255,0.2);
                border: 2px solid rgba(255,255,255,0.3);
                color: white;
                border-radius: 50%;
                width: 44px;
                height: 44px;
                cursor: pointer;
                font-size: 1.2em;
                transition: all 0.3s ease;
            }
            
            .voice-btn:hover {
                background: rgba(255,255,255,0.3);
                transform: scale(1.05);
            }
            
            .voice-btn.active {
                background: #4CAF50;
                border-color: #4CAF50;
                box-shadow: 0 0 12px rgba(76, 175, 80, 0.5);
            }
            
            .chat-messages {
                flex: 1;
                overflow-y: auto;
                padding: 16px;
                display: flex;
                flex-direction: column;
                gap: 12px;
            }
            
            .message {
                display: flex;
                align-items: flex-start;
                gap: 8px;
            }
            
            .message.user {
                flex-direction: row-reverse;
            }
            
            .message-content {
                background: #f5f5f5;
                padding: 12px 16px;
                border-radius: 18px;
                max-width: 80%;
                word-wrap: break-word;
            }
            
            .message.user .message-content {
                background: #667eea;
                color: white;
            }
            
            .message.assistant .message-content {
                background: #e3f2fd;
            }
            
            .voice-status {
                background: #f8f9fa;
                border-top: 1px solid #e9ecef;
                padding: 16px;
                text-align: center;
            }
            
            .status-indicator {
                position: relative;
                display: inline-flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 8px;
            }
            
            .pulse-ring, .pulse-ring-2 {
                position: absolute;
                left: 50%;
                top: 50%;
                transform: translate(-50%, -50%);
                width: 24px;
                height: 24px;
                border: 2px solid #4CAF50;
                border-radius: 50%;
                animation: pulse 2s infinite;
            }
            
            .pulse-ring-2 {
                animation-delay: 1s;
            }
            
            @keyframes pulse {
                0% { transform: translate(-50%, -50%) scale(1); opacity: 1; }
                100% { transform: translate(-50%, -50%) scale(2); opacity: 0; }
            }
            
            .status-text {
                font-weight: 500;
                color: #4CAF50;
                padding-left: 32px;
            }
            
            .transcription {
                font-style: italic;
                color: #666;
                min-height: 20px;
            }
            
            .chat-input-container {
                border-top: 1px solid #e9ecef;
                padding: 16px;
            }
            
            .input-group {
                display: flex;
                gap: 8px;
                align-items: center;
            }
            
            #chat-input {
                flex: 1;
                padding: 12px 16px;
                border: 2px solid #e9ecef;
                border-radius: 24px;
                outline: none;
                font-size: 14px;
            }
            
            #chat-input:focus {
                border-color: #667eea;
            }
            
            .button-group {
                display: flex;
                gap: 4px;
            }
            
            .record-btn, .send-btn {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                border: none;
                cursor: pointer;
                font-size: 1.1em;
                transition: all 0.2s ease;
            }
            
            .send-btn {
                background: #667eea;
                color: white;
            }
            
            .send-btn:hover {
                background: #5a67d8;
                transform: scale(1.05);
            }
            
            .record-btn {
                background: #4CAF50;
                color: white;
            }
            
            .record-btn:hover {
                background: #45a049;
                transform: scale(1.05);
            }
            
            .record-btn.recording {
                background: #f44336;
                animation: recordPulse 1s infinite;
            }
            
            @keyframes recordPulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.7; }
            }
            
            .audio-controls {
                background: #fff3e0;
                border-top: 1px solid #ffcc02;
                padding: 12px;
                display: flex;
                gap: 8px;
                justify-content: center;
            }
            
            .control-btn {
                padding: 8px 16px;
                border: 1px solid #ddd;
                border-radius: 20px;
                background: white;
                cursor: pointer;
                font-size: 14px;
                transition: all 0.2s ease;
            }
            
            .control-btn:hover {
                background: #f5f5f5;
            }
            
            .control-btn.secondary {
                color: #666;
            }
            
            /* Ensure HTML content within messages is properly styled */
            .message-content strong {
                font-weight: bold;
            }
            
            .message-content em {
                font-style: italic;
            }
            
            .message-content code {
                background: #e0e0e0;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: monospace;
                font-size: 0.9em;
            }
            
            .message-content div[style*="background"] {
                display: block !important;
                margin: 8px 0 !important;
                padding: 12px !important;
                border-radius: 8px !important;
            }
            
            .message-content div[style*="border-left"] {
                border-left-width: 4px !important;
                border-left-style: solid !important;
            }
        `;
        document.head.appendChild(styleSheet);
    }
    
    setupEventListeners() {
        // Voice toggle button
        const voiceToggleBtn = document.getElementById('voice-toggle-btn');
        voiceToggleBtn.addEventListener('click', () => this.toggleVoiceMode());
        
        // Record button (push-to-talk)
        const recordBtn = document.getElementById('record-btn');
        recordBtn.addEventListener('mousedown', () => this.startRecording());
        recordBtn.addEventListener('mouseup', () => this.stopRecording());
        recordBtn.addEventListener('mouseleave', () => this.stopRecording());
        
        // Touch support for mobile
        recordBtn.addEventListener('touchstart', (e) => {
            e.preventDefault();
            this.startRecording();
        });
        recordBtn.addEventListener('touchend', (e) => {
            e.preventDefault();
            this.stopRecording();
        });
        
        // Text input and send
        const chatInput = document.getElementById('chat-input');
        const sendBtn = document.getElementById('send-btn');
        
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendTextMessage();
            }
        });
        
        sendBtn.addEventListener('click', () => this.sendTextMessage());
        
        // Audio controls
        const stopRecordingBtn = document.getElementById('stop-recording-btn');
        const cancelRecordingBtn = document.getElementById('cancel-recording-btn');
        
        stopRecordingBtn.addEventListener('click', () => this.stopRecording());
        cancelRecordingBtn.addEventListener('click', () => this.cancelRecording());
    }
    
    async toggleVoiceMode() {
        const voiceToggleBtn = document.getElementById('voice-toggle-btn');
        const recordBtn = document.getElementById('record-btn');
        const voiceStatus = document.getElementById('voice-status');
        
        if (!this.isVoiceMode) {
            // Enable voice mode
            try {
                this.audioRecorder = new AudioRecorder({
                    sessionId: this.sessionId,
                    websocketUrl: `ws://${window.location.host}/ws/audio/${this.sessionId}`,
                    onTranscription: (text, isFinal) => this.handleTranscription(text, isFinal),
                    onSpeechStart: (text) => this.handleSpeechStart(text),
                    onSpeechEnd: () => this.handleSpeechEnd(),
                    onError: (error) => this.handleAudioError(error),
                    onStatusChange: (status) => this.handleStatusChange(status)
                });
                
                const initialized = await this.audioRecorder.initialize();
                if (!initialized) {
                    return;
                }
                
                await this.audioRecorder.connect();
                
                this.isVoiceMode = true;
                voiceToggleBtn.classList.add('active');
                voiceToggleBtn.title = 'Disable voice chat';
                recordBtn.style.display = 'block';
                voiceStatus.style.display = 'block';
                
                this.addMessage('assistant', '🎤 Voice mode enabled! Hold the microphone button to speak.');
                
            } catch (error) {
                console.error('Failed to enable voice mode:', error);
                this.addMessage('assistant', '❌ Failed to enable voice mode. Please check your microphone permissions.');
            }
            
        } else {
            // Disable voice mode
            if (this.audioRecorder) {
                await this.audioRecorder.disconnect();
                this.audioRecorder = null;
            }
            
            this.isVoiceMode = false;
            voiceToggleBtn.classList.remove('active');
            voiceToggleBtn.title = 'Enable voice chat';
            recordBtn.style.display = 'none';
            voiceStatus.style.display = 'none';
            
            this.addMessage('assistant', '📝 Voice mode disabled. You can now type your messages.');
        }
    }
    
    async startRecording() {
        if (!this.audioRecorder || this.isListening) {
            return;
        }
        
        const recordBtn = document.getElementById('record-btn');
        const audioControls = document.getElementById('audio-controls');
        const statusText = document.querySelector('.status-text');
        
        this.isListening = true;
        recordBtn.classList.add('recording');
        audioControls.style.display = 'flex';
        statusText.textContent = 'Listening...';
        
        await this.audioRecorder.startRecording();
    }
    
    async stopRecording() {
        if (!this.audioRecorder || !this.isListening) {
            return;
        }
        
        const recordBtn = document.getElementById('record-btn');
        const audioControls = document.getElementById('audio-controls');
        const statusText = document.querySelector('.status-text');
        
        this.isListening = false;
        recordBtn.classList.remove('recording');
        audioControls.style.display = 'none';
        statusText.textContent = 'Processing...';
        
        this.audioRecorder.stopRecording();
    }
    
    cancelRecording() {
        // Stop recording without processing
        this.stopRecording();
        
        const statusText = document.querySelector('.status-text');
        const transcription = document.getElementById('live-transcription');
        
        statusText.textContent = 'Ready to listen...';
        transcription.textContent = '';
    }
    
    handleTranscription(text, isFinal) {
        const transcription = document.getElementById('live-transcription');
        
        if (isFinal) {
            // Add final transcription as user message
            this.addMessage('user', text);
            transcription.textContent = '';
            
            const statusText = document.querySelector('.status-text');
            statusText.textContent = 'Ready to listen...';
        } else {
            // Show partial transcription
            transcription.textContent = text + '...';
        }
    }
    
    handleSpeechStart(text) {
        this.isSpeaking = true;
        const statusText = document.querySelector('.status-text');
        statusText.textContent = 'Speaking...';
    }
    
    handleSpeechEnd() {
        this.isSpeaking = false;
        const statusText = document.querySelector('.status-text');
        statusText.textContent = 'Ready to listen...';
    }
    
    handleAudioError(error) {
        console.error('Audio error:', error);
        this.addMessage('assistant', `❌ Audio error: ${error}`);
        
        // Reset UI state
        this.isListening = false;
        const recordBtn = document.getElementById('record-btn');
        const audioControls = document.getElementById('audio-controls');
        
        if (recordBtn) recordBtn.classList.remove('recording');
        if (audioControls) audioControls.style.display = 'none';
    }
    
    handleStatusChange(status) {
        console.log('Audio status:', status);
        
        const statusText = document.querySelector('.status-text');
        if (statusText) {
            switch (status) {
                case 'connected':
                    statusText.textContent = 'Ready to listen...';
                    break;
                case 'recording':
                    statusText.textContent = 'Listening...';
                    break;
                case 'processing':
                    statusText.textContent = 'Processing...';
                    break;
                case 'disconnected':
                    statusText.textContent = 'Disconnected';
                    break;
            }
        }
    }
    
    async sendTextMessage() {
        const chatInput = document.getElementById('chat-input');
        const message = chatInput.value.trim();
        
        if (!message) return;
        
        // Ensure we have a session
        if (!this.sessionId) {
            await this.initializeSession();
            if (!this.sessionId) {
                this.addMessage('assistant', '❌ Unable to establish session. Please refresh the page.');
                return;
            }
        }
        
        // Add user message to chat
        this.addMessage('user', message);
        chatInput.value = '';
        
        // Send to chat API
        try {
            const response = await fetch(`${this.baseUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('Chat API response:', data);
                // Add assistant response
                this.addMessage('assistant', data.response || 'No response received');
            } else {
                const errorData = await response.json();
                console.error('Chat API error:', errorData);
                this.addMessage('assistant', `❌ Sorry, I encountered an error: ${errorData.message || 'Unknown error'}`);
            }
            
        } catch (error) {
            console.error('Failed to send message:', error);
            this.addMessage('assistant', `❌ Network error: ${error.message}. Please check your connection and try again.`);
        }
    }
    
    addMessage(sender, content) {
        const messagesContainer = document.getElementById('chat-messages');
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Handle HTML content (for formatted responses)
        if (content && typeof content === 'string' && (content.includes('<') || content.includes('&'))) {
            contentDiv.innerHTML = content;
        } else {
            contentDiv.textContent = content || 'Empty response';
        }
        
        messageDiv.appendChild(contentDiv);
        messagesContainer.appendChild(messageDiv);
        
        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if we have a container element
    const container = document.getElementById('voice-chat-widget');
    if (container) {
        new VoiceChatWidget('voice-chat-widget');
    }
});