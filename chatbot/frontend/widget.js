// =====================
// CHATBOT WIDGET CON RENDERIZADOR DE MARKDOWN MEJORADO
// =====================

(function() {
    // Configuración
    const CONFIG = {
        apiUrl: window.CHATBOT_API_URL || 'http://localhost:8000',
        businessId: window.CHATBOT_BUSINESS_ID || 1,
        position: window.CHATBOT_POSITION || 'bottom-right', // 'bottom-right', 'bottom-left', 'top-right', 'top-left'
        primaryColor: window.CHATBOT_PRIMARY_COLOR || '#6366f1',
        sessionIdPrefix: 'chatbot-session-'
    };

    // Generar ID de sesión único
    function generateSessionId() {
        return CONFIG.sessionIdPrefix + Math.random().toString(36).substr(2, 9) + '-' + Date.now();
    }

    // Obtener o crear session ID
    function getSessionId() {
        let sessionId = localStorage.getItem('chatbot_session_id');
        if (!sessionId) {
            sessionId = generateSessionId();
            localStorage.setItem('chatbot_session_id', sessionId);
        }
        return sessionId;
    }

    // =====================
    // RENDERIZADOR DE MARKDOWN MEJORADO
    // =====================
    function convertTableToHtml(lines) {
        try {
            if (lines.length < 2) return null;

            lines = lines.filter(l => l.trim());
            if (lines.length < 2) return null;

            let separatorIdx = -1;
            for (let i = 0; i < lines.length; i++) {
                if (lines[i].includes('---')) {
                    separatorIdx = i;
                    break;
                }
            }

            if (separatorIdx === -1 || separatorIdx === 0) return null;

            const headerLines = lines.slice(0, separatorIdx);
            const dataLines = lines.slice(separatorIdx + 1);

            const headerCells = [];
            headerLines.forEach(line => {
                const cells = line.split('|')
                    .map(c => c.trim())
                    .filter(c => c && !c.match(/^[\-:]+$/));
                headerCells.push(...cells);
            });

            if (headerCells.length === 0) return null;

            const dataRows = dataLines
                .filter(line => line.includes('|'))
                .map(line => {
                    return line.split('|')
                        .map(c => c.trim())
                        .filter(c => c);
                })
                .filter(row => row.length > 0);

            if (dataRows.length === 0) return null;

            let tableHtml = '<table class="chatbot-markdown-table">';
            
            tableHtml += '<thead><tr>';
            headerCells.forEach(cell => {
                tableHtml += `<th>${cell}</th>`;
            });
            tableHtml += '</tr></thead>';

            tableHtml += '<tbody>';
            dataRows.forEach((row, idx) => {
                tableHtml += '<tr>';
                row.forEach((cell, cellIdx) => {
                    if (cellIdx < headerCells.length) {
                        tableHtml += `<td>${cell}</td>`;
                    }
                });
                tableHtml += '</tr>';
            });
            tableHtml += '</tbody></table>';

            return tableHtml;
        } catch (e) {
            console.error('Error converting table:', e);
            return null;
        }
    }

    function renderMarkdown(text) {
        let html = text;

        html = html.replace(/■/g, '-');
        html = html.replace(/�/g, '');
        
        const tables = [];
        const lines = html.split('\n');
        let inTable = false;
        let tableLines = [];
        let result = [];

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            
            if (line.includes('|')) {
                if (!inTable) {
                    inTable = true;
                    tableLines = [];
                }
                tableLines.push(line);
            } else {
                if (inTable && tableLines.length > 0) {
                    const tableHtml = convertTableToHtml(tableLines);
                    if (tableHtml) {
                        const placeholder = `__TABLE_${tables.length}__`;
                        tables.push(tableHtml);
                        result.push(placeholder);
                    } else {
                        result.push(...tableLines);
                    }
                    tableLines = [];
                    inTable = false;
                }
                result.push(line);
            }
        }

        if (inTable && tableLines.length > 0) {
            const tableHtml = convertTableToHtml(tableLines);
            if (tableHtml) {
                const placeholder = `__TABLE_${tables.length}__`;
                tables.push(tableHtml);
                result.push(placeholder);
            } else {
                result.push(...tableLines);
            }
        }

        html = result.join('\n');

        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/^[\*\-] (.+)$/gm, '<li>$1</li>');
        html = html.replace(/((?:<li[^>]*>.*?<\/li>\s*)+)/g, '<ul>$1</ul>');
        html = html.replace(/\n/g, '<br>');

        tables.forEach((table, idx) => {
            html = html.replace(`__TABLE_${idx}__`, table);
        });

        return html;
    }

    // =====================
    // ESTILOS CSS
    // =====================
    const styles = `
        .chatbot-markdown-table {
            width: 100%;
            border-collapse: collapse;
            margin: 12px 0;
            font-size: 0.75em;
            background: white;
            border-radius: 6px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            display: block;
            overflow-x: auto;
            max-width: 100%;
        }
        .chatbot-markdown-table thead tr {
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: white;
            text-align: left;
            font-weight: 600;
        }
        .chatbot-markdown-table th {
            padding: 8px 10px;
            border-bottom: 2px solid rgba(255,255,255,0.3);
            font-size: 0.9em;
            white-space: nowrap;
        }
        .chatbot-markdown-table td {
            padding: 8px 10px;
            border-bottom: 1px solid rgba(0,0,0,0.06);
            color: #333;
            font-size: 0.95em;
            vertical-align: top;
        }
        .chatbot-markdown-table tbody tr:nth-child(even) {
            background: rgba(99,102,241,0.04);
        }
        .chatbot-markdown-table tbody tr:hover {
            background: rgba(99,102,241,0.12);
            transition: background 0.15s;
        }
        .chatbot-message-bubble ul {
            margin: 8px 0;
            padding-left: 20px;
            list-style-type: disc;
        }
        .chatbot-message-bubble li {
            margin: 4px 0;
            line-height: 1.5;
        }
        .chatbot-message-bubble strong {
            color: #6366f1;
            font-weight: 600;
        }
        .chatbot-message-bubble a {
            color: #6366f1;
            text-decoration: underline;
        }
        .chatbot-widget-container {
            position: fixed;
            ${CONFIG.position.includes('bottom') ? 'bottom: 20px' : 'top: 20px'};
            ${CONFIG.position.includes('right') ? 'right: 20px' : 'left: 20px'};
            z-index: 10000;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        .chatbot-toggle-button {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, ${CONFIG.primaryColor}, #8b5cf6);
            border: none;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.3s;
        }
        .chatbot-toggle-button:hover {
            transform: scale(1.1);
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.6);
        }
        .chatbot-toggle-button svg {
            width: 30px;
            height: 30px;
            fill: white;
        }
        .chatbot-window {
            position: absolute;
            ${CONFIG.position.includes('bottom') ? 'bottom: 80px' : 'top: 80px'};
            ${CONFIG.position.includes('right') ? 'right: 0' : 'left: 0'};
            width: 380px;
            height: 550px;
            background: white;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            display: none;
            flex-direction: column;
            overflow: hidden;
            animation: slideUp 0.3s;
        }
        .chatbot-window.open {
            display: flex;
        }
        @keyframes slideUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .chatbot-header {
            background: linear-gradient(135deg, ${CONFIG.primaryColor}, #8b5cf6);
            color: white;
            padding: 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .chatbot-header-title {
            font-size: 18px;
            font-weight: 600;
        }
        .chatbot-close-button {
            background: none;
            border: none;
            color: white;
            font-size: 24px;
            cursor: pointer;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            transition: background 0.2s;
        }
        .chatbot-close-button:hover {
            background: rgba(255, 255, 255, 0.2);
        }
        .chatbot-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f8f9fa;
        }
        .chatbot-message {
            margin-bottom: 16px;
            display: flex;
        }
        .chatbot-message.user {
            justify-content: flex-end;
            flex-direction: column;
            align-items: flex-end;
        }
        .chatbot-message.bot {
            justify-content: flex-start;
        }
        .chatbot-message-bubble {
            max-width: 85%;
            padding: 12px 16px;
            border-radius: 16px;
            word-wrap: break-word;
            line-height: 1.5;
            overflow-x: auto;
        }
        .chatbot-message.user .chatbot-message-bubble {
            background: ${CONFIG.primaryColor};
            color: white;
            border-bottom-right-radius: 4px;
        }
        .chatbot-message.bot .chatbot-message-bubble {
            background: white;
            color: #333;
            border-bottom-left-radius: 4px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        .message-status {
            font-size: 0.7rem;
            margin-top: 2px;
            margin-right: 4px;
            opacity: 0.7;
        }
        .status-icon {
            display: inline-block;
            transition: all 0.3s ease;
        }
        .status-icon.sending {
            color: #94a3b8;
        }
        .status-icon.delivered {
            color: #64748b;
        }
        .status-icon.read {
            color: #3b82f6;
            font-weight: bold;
        }
        .chatbot-typing {
            display: none;
            padding: 12px 16px;
            background: white;
            border-radius: 16px;
            border-bottom-left-radius: 4px;
            max-width: 75%;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        .chatbot-typing.active {
            display: flex;
            gap: 4px;
        }
        .chatbot-typing-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #ccc;
            animation: typing 1.4s infinite;
        }
        .chatbot-typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .chatbot-typing-dot:nth-child(3) { animation-delay: 0.4s; }
        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-10px); }
        }
        .chatbot-input-container {
            padding: 16px;
            background: white;
            border-top: 1px solid #e5e7eb;
            display: flex;
            gap: 8px;
        }
        .chatbot-input {
            flex: 1;
            padding: 12px;
            border: 1px solid #e5e7eb;
            border-radius: 24px;
            outline: none;
            font-size: 14px;
            transition: border-color 0.2s;
        }
        .chatbot-input:focus {
            border-color: ${CONFIG.primaryColor};
        }
        .chatbot-send-button {
            width: 44px;
            height: 44px;
            border-radius: 50%;
            background: ${CONFIG.primaryColor};
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.2s;
        }
        .chatbot-send-button:hover:not(:disabled) {
            background: #5558e3;
        }
        .chatbot-send-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .chatbot-send-button svg {
            width: 20px;
            height: 20px;
            fill: white;
        }
        @media (max-width: 480px) {
            .chatbot-window {
                width: calc(100vw - 40px);
                height: calc(100vh - 100px);
            }
        }
    `;

    // =====================
    // WIDGET CLASS
    // =====================
    class ChatbotWidget {
        constructor() {
            this.sessionId = getSessionId();
            this.isOpen = false;
            this.isTyping = false;
            this.init();
        }

        init() {
            this.injectStyles();
            this.createWidget();
            this.attachEventListeners();
        }

        injectStyles() {
            const style = document.createElement('style');
            style.textContent = styles;
            document.head.appendChild(style);
        }

        createWidget() {
            const container = document.createElement('div');
            container.className = 'chatbot-widget-container';
            container.innerHTML = `
                <button class="chatbot-toggle-button" id="chatbot-toggle">
                    <svg viewBox="0 0 24 24">
                        <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
                    </svg>
                </button>
                <div class="chatbot-window" id="chatbot-window">
                    <div class="chatbot-header">
                        <div class="chatbot-header-title">💬 Chat</div>
                        <button class="chatbot-close-button" id="chatbot-close">×</button>
                    </div>
                    <div class="chatbot-messages" id="chatbot-messages">
                        <div class="chatbot-message bot">
                            <div class="chatbot-message-bubble">¡Hola! 👋 ¿En qué puedo ayudarte?</div>
                        </div>
                        <div class="chatbot-typing" id="chatbot-typing">
                            <div class="chatbot-typing-dot"></div>
                            <div class="chatbot-typing-dot"></div>
                            <div class="chatbot-typing-dot"></div>
                        </div>
                    </div>
                    <div class="chatbot-input-container">
                        <input type="text" class="chatbot-input" id="chatbot-input" placeholder="Escribe tu mensaje..." autocomplete="off"/>
                        <button class="chatbot-send-button" id="chatbot-send">
                            <svg viewBox="0 0 24 24">
                                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                            </svg>
                        </button>
                    </div>
                </div>
            `;
            document.body.appendChild(container);
        }

        attachEventListeners() {
            document.getElementById('chatbot-toggle').addEventListener('click', () => this.toggleWidget());
            document.getElementById('chatbot-close').addEventListener('click', () => this.closeWidget());
            document.getElementById('chatbot-send').addEventListener('click', () => this.sendMessage());
            document.getElementById('chatbot-input').addEventListener('keypress', (e) => {
                if (e.key === 'Enter') this.sendMessage();
            });
        }

        toggleWidget() {
            this.isOpen = !this.isOpen;
            document.getElementById('chatbot-window').classList.toggle('open');
            if (this.isOpen) {
                document.getElementById('chatbot-input').focus();
            }
        }

        closeWidget() {
            this.isOpen = false;
            document.getElementById('chatbot-window').classList.remove('open');
        }

        addMessage(message, isUser = false) {
            const messagesContainer = document.getElementById('chatbot-messages');
            const typingIndicator = document.getElementById('chatbot-typing');
            
            const messageDiv = document.createElement('div');
            messageDiv.className = `chatbot-message ${isUser ? 'user' : 'bot'}`;
            
            const bubble = document.createElement('div');
            bubble.className = 'chatbot-message-bubble';
            
            if (!isUser) {
                // Renderizar markdown primero
                const renderedContent = renderMarkdown(message);
                
                // Detectar si el mensaje contiene tablas o contenido complejo
                const hasTable = message.includes('|') && message.includes('---');
                const isLongContent = message.length > 500;
                
                messageDiv.appendChild(bubble);
                messagesContainer.insertBefore(messageDiv, typingIndicator);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
                
                // Si tiene tabla o es muy largo, mostrar directamente sin efecto de escritura
                if (hasTable || isLongContent) {
                    bubble.innerHTML = renderedContent;
                    messagesContainer.scrollTop = messagesContainer.scrollHeight;
                } else {
                    // Efecto de escritura solo para mensajes cortos y simples
                    bubble.innerHTML = '';
                    
                    // Crear un div temporal para obtener el texto plano
                    const tempDiv = document.createElement('div');
                    tempDiv.innerHTML = renderedContent;
                    const plainText = tempDiv.textContent || tempDiv.innerText || '';
                    
                    let index = 0;
                    const speed = 20; // milliseconds por caracter
                    
                    const typeWriter = () => {
                        if (index < plainText.length) {
                            bubble.textContent = plainText.substring(0, index + 1);
                            index++;
                            messagesContainer.scrollTop = messagesContainer.scrollHeight;
                            setTimeout(typeWriter, speed);
                        } else {
                            // Una vez terminado, mostrar el contenido completo con formato
                            bubble.innerHTML = renderedContent;
                            messagesContainer.scrollTop = messagesContainer.scrollHeight;
                        }
                    };
                    
                    typeWriter();
                }
            } else {
                // Mensaje del usuario con indicador de leído
                bubble.textContent = message;
                
                // Agregar indicador de estado
                const statusDiv = document.createElement('div');
                statusDiv.className = 'message-status';
                statusDiv.innerHTML = '<span class="status-icon sending">⏱</span>';
                messageDiv.appendChild(bubble);
                messageDiv.appendChild(statusDiv);
                messagesContainer.insertBefore(messageDiv, typingIndicator);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
                
                // Simular estados: enviando → entregado → leído
                setTimeout(() => {
                    statusDiv.innerHTML = '<span class="status-icon delivered">✓</span>';
                }, 300);
                
                setTimeout(() => {
                    statusDiv.innerHTML = '<span class="status-icon read">✓✓</span>';
                }, 1000);
            }
        }

        setTyping(isTyping) {
            this.isTyping = isTyping;
            const typingIndicator = document.getElementById('chatbot-typing');
            const sendBtn = document.getElementById('chatbot-send');
            const input = document.getElementById('chatbot-input');
            
            if (isTyping) {
                typingIndicator.classList.add('active');
                sendBtn.disabled = true;
                input.disabled = true;
            } else {
                typingIndicator.classList.remove('active');
                sendBtn.disabled = false;
                input.disabled = false;
            }
            document.getElementById('chatbot-messages').scrollTop = document.getElementById('chatbot-messages').scrollHeight;
        }

        // Burbuja vacía del bot que se va rellenando mientras llega la respuesta en streaming
        addStreamingBubble() {
            const messagesContainer = document.getElementById('chatbot-messages');
            const typingIndicator = document.getElementById('chatbot-typing');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'chatbot-message bot';
            const bubble = document.createElement('div');
            bubble.className = 'chatbot-message-bubble';
            messageDiv.appendChild(bubble);
            messagesContainer.insertBefore(messageDiv, typingIndicator);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
            return bubble;
        }

        async sendMessage() {
            const input = document.getElementById('chatbot-input');
            const message = input.value.trim();

            if (!message || this.isTyping) return;

            this.addMessage(message, true);
            input.value = '';
            this.setTyping(true);

            const payload = {
                message: message,
                session_id: this.sessionId,
                business_id: CONFIG.businessId
            };

            try {
                await this.streamReply(payload);
            } catch (error) {
                console.error('Error:', error);
                this.addMessage('Lo siento, ha ocurrido un error. Por favor intenta de nuevo.');
            } finally {
                this.setTyping(false);
            }
        }

        // Respuesta en streaming (SSE). Si el servidor no lo soporta, usa /chat.
        async streamReply(payload) {
            const response = await fetch(`${CONFIG.apiUrl}/chat/stream`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (response.status === 404 || response.status === 405) {
                return this.replyWithoutStreaming(payload);
            }
            if (!response.ok || !response.body) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            const messagesContainer = document.getElementById('chatbot-messages');
            let buffer = '';
            let raw = '';
            let finalText = null;
            let bubble = null;

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });

                let end;
                while ((end = buffer.indexOf('\n\n')) >= 0) {
                    const line = buffer.slice(0, end).trim();
                    buffer = buffer.slice(end + 2);
                    if (!line.startsWith('data:')) continue;
                    const event = JSON.parse(line.slice(5));

                    if (event.delta) {
                        raw += event.delta;
                        if (!bubble) {
                            document.getElementById('chatbot-typing').classList.remove('active');
                            bubble = this.addStreamingBubble();
                        }
                        bubble.textContent = raw;
                        messagesContainer.scrollTop = messagesContainer.scrollHeight;
                    }
                    if (typeof event.final === 'string') finalText = event.final;
                }
            }

            const text = finalText !== null ? finalText : raw;
            if (!text) throw new Error('Respuesta vacía');

            if (bubble) {
                // Sustituye el texto en bruto por la versión limpia y con formato
                bubble.innerHTML = renderMarkdown(text);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            } else {
                this.addMessage(text);
            }
        }

        async replyWithoutStreaming(payload) {
            const response = await fetch(`${CONFIG.apiUrl}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            this.addMessage(data.response);
        }
    }

    // =====================
    // INICIALIZACIÓN
    // =====================
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.chatbotWidget = new ChatbotWidget();
        });
    } else {
        window.chatbotWidget = new ChatbotWidget();
    }
})();
