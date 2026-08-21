const conversationInput = document.getElementById("conversation_id");
const connectButton = document.getElementById("connect_button");
const messages = document.getElementById("messages");
const messageInput = document.getElementById("message_input");
const sendButton = document.getElementById("send_button");
const connectionStatus = document.getElementById("connection_status");

const setMessagingEnabled = (enabled) => {
    sendButton.disabled = !enabled;
    messageInput.disabled = !enabled;
};

let websocket = null;
let historyLoading = false;
let pendingMessages = [];
let connectionVersion = 0;
const displayedMessageIds = new Set();
setMessagingEnabled(false);

const handleConnect = () => {
    const conversationId = Number(conversationInput.value);
    if (
        !Number.isInteger(conversationId) || 
        conversationId <= 0
    ) {
        addMessage("Invalid conversation ID");
        return;
    }
    
    connectionStatus.textContent = "Connecting...";
    setMessagingEnabled(false);
    
    if (
        websocket !== null && 
        (
            websocket.readyState === WebSocket.OPEN ||
            websocket.readyState === WebSocket.CONNECTING
        )
    ) {
        websocket.close();
    }

    connectionVersion += 1;
    const version = connectionVersion;
    websocket = new WebSocket(
        `ws://${window.location.host}/ws/${conversationId}`
    );
    
    websocket.addEventListener("open", (event) => handleWebSocketOpen(event, conversationId, version));
    websocket.addEventListener("message", handleWebSocketMessage);
    websocket.addEventListener("close", handleWebSocketClose);
    websocket.addEventListener("error", handleWebSocketError);
};

const handleWebSocketOpen = (event, conversationId, version) => {
    if (event.target !== websocket) {
        return;
    }
    messages.textContent = "";
    displayedMessageIds.clear();
    loadMessages(conversationId, version);
    setMessagingEnabled(true);
    connectionStatus.textContent = "Connected";
};

const handleWebSocketClose = (event) => {
    if (event.target === websocket) {
        setMessagingEnabled(false);
        addMessage("Disconnected");
        websocket = null;
        connectionStatus.textContent = "Disconnected";
    }
};

const handleWebSocketMessage = (event) => {
    if (event.target !== websocket) {
        return;
    }

    let data;
    
    try {
        data = JSON.parse(event.data);
    } catch (error) {
        addMessage("Invalid server message");
        return;
    }
    
    if (data.type === "connected") {
        addMessage(`Connected: ${data.connection_id}`);
    } else if (data.type === "member_joined") {
        addMessage(`Member joined: ${data.connection_id}`);
    } else if (data.type === "message") {
        if (historyLoading) {
            pendingMessages.push(data);
            return;
        }
        if (displayedMessageIds.has(data.message_id)) {
            return;
        }
        displayedMessageIds.add(data.message_id);
        addMessage(`${data.sender_id}: ${data.text}`);
    } else if (data.type === "member_left") {
        addMessage(`Member left: ${data.connection_id}`);
    } else if (data.type === "error") {
        addMessage(`Error: ${data.detail}`);
    }
    
};

const addMessage = (text) => {
    const element = document.createElement("div");
    element.textContent = text;
    messages.appendChild(element);
};

const handleSend = () => {
    if (websocket === null || websocket.readyState !== WebSocket.OPEN) {
        return;
    }

    const text = messageInput.value.trim();
    if (text === "") {
        return;
    }

    const message = {"type": "message", "text": text};
    websocket.send(JSON.stringify(message));
    messageInput.value = "";
    
};

const handleMessageKeyDown = (event) => {
    if (event.key === "Enter") {
        handleSend();
    }
};

const loadMessages = async (conversationId, version) => {
    try {
        historyLoading = true;
        pendingMessages = [];

        const response = await fetch(
            `/conversations/${conversationId}/messages`
        );
        if (version !== connectionVersion) {
            return;
        }
        if (!response.ok) {
            addMessage("Failed to load messages");
            return;
        }
        const data = await response.json();
        if (version !== connectionVersion) {
            return;
        }
        for (const message of data) {
            displayedMessageIds.add(message.id);
            addMessage(message.text);
            
        }
    } catch (error) {
        if (version === connectionVersion) {
            addMessage("Network error");
        }
    } finally {
        if (version === connectionVersion) {
            historyLoading = false;
            for (const message of pendingMessages) {
                if (displayedMessageIds.has(message.message_id)) {
                    continue;
                }
                displayedMessageIds.add(message.message_id);
                addMessage(`${message.sender_id}: ${message.text}`);
            }
            pendingMessages = [];
        }
    }
};

const handleWebSocketError = (event) => {
    if (event.target !== websocket) {
        return;
    }
    connectionStatus.textContent = "Connection error";
    addMessage("WebSocket error");
};

connectButton.addEventListener("click", handleConnect);
sendButton.addEventListener("click", handleSend);
messageInput.addEventListener("keydown", handleMessageKeyDown);
