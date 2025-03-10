import { socketManager } from '../core/socket.js';
import { gameState } from '../core/state.js';
import { eventManager } from '../core/events.js';

class DialogueManager {
    constructor() {
        this.dialogueContainer = document.querySelector('.dialogue-container');
        this.choiceContainer = document.querySelector('.choice-container');
        this.messageForm = document.getElementById('message-form');
        this.messageInput = document.getElementById('message-input');
        this.currentStreamMessage = null;
        
        this.initEventListeners();
    }

    /**
     * 初始化事件監聽
     */
    initEventListeners() {
        if (this.messageForm) {
            this.messageForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.sendMessage();
            });
        }

        // 監聽一般消息
        socketManager.on('receive_message', (data) => {
            console.log('[DialogueManager] 收到消息:', data);
            this.handleServerMessage(data);
        });

        // 監聽流式回應開始
        socketManager.on('stream_start', (data) => {
            console.log('[DialogueManager] 流式響應開始:', data);
            this.handleStreamStart(data);
        });

        // 監聽流式數據片段
        socketManager.on('stream_data', (data) => {
            console.log('[DialogueManager] 流式數據片段:', data);
            this.handleStreamData(data);
        });

        // 監聽流式回應結束
        socketManager.on('stream_end', (data) => {
            console.log('[DialogueManager] 流式響應結束:', data);
            this.handleStreamEnd(data);
        });
    }

    /**
     * 處理流式回應開始
     * @param {Object} data - 開始數據
     */
    handleStreamStart(data) {
        // 移除之前的"輸入中..."消息
        const lastMessage = this.dialogueContainer.lastElementChild;
        if (lastMessage && lastMessage.classList.contains('typing-message')) {
            lastMessage.remove();
        }

        // 創建新的消息元素用於流式內容
        this.currentStreamMessage = this.createMessageElement({
            content: '',
            sender: 'assistant',
            character: data.character
        });
        this.dialogueContainer.appendChild(this.currentStreamMessage);
    }

    /**
     * 處理流式數據片段
     * @param {Object} data - 數據片段
     */
    handleStreamData(data) {
        if (!this.currentStreamMessage) {
            return;
        }

        const contentElement = this.currentStreamMessage.querySelector('.message-content');
        if (contentElement) {
            contentElement.textContent += data.content;
            this.scrollToBottom();
        }
    }

    /**
     * 處理流式回應結束
     * @param {Object} data - 結束數據
     */
    handleStreamEnd(data) {
        this.currentStreamMessage = null;
    }

    /**
     * 發送消息到服務器
     */
    sendMessage() {
        const message = this.messageInput.value.trim();
        
        if (!message) {
            return;
        }

        const character = gameState.get('currentCharacter');
        if (!character || !character.id) {
            this.showError('請先選擇一個角色');
            return;
        }
        
        // 發送消息到服務器
        socketManager.sendMessage(message, character.id);

        // 添加用戶消息到界面
        this.addMessage({
            content: message,
            sender: 'user'
        });

        // 添加"輸入中..."的臨時消息
        this.addMessage({
            content: '輸入中...',
            sender: 'assistant',
            character: character,
            is_typing: true
        });

        // 清空輸入框
        this.messageInput.value = '';
    }

    /**
     * 處理服務器返回的消息
     * @param {Object} data - 消息數據
     */
    handleServerMessage(data) {
        console.log('[DialogueManager] 處理消息:', { type: data.type, isChunk: data.is_chunk });
        
        if (data.status === 'error') {
            this.showError(data.message);
            return;
        }

        if (data.message) {
            // 如果不是流式響應，則直接添加消息
            if (!data.is_chunk) {
                this.addMessage({
                    content: data.message,
                    sender: 'assistant',
                    character: data.character
                });
            }
        }
    }

    /**
     * 創建消息元素
     * @param {Object} messageData - 消息數據
     * @returns {HTMLElement} 消息元素
     */
    createMessageElement(messageData) {
        const { content, sender, character, is_typing } = messageData;
        
        const messageElement = document.createElement('div');
        messageElement.className = `message ${sender}-message${is_typing ? ' typing-message' : ''}`;
        
        // 如果是角色消息，添加角色信息
        if (sender === 'assistant' && character) {
            const nameElement = document.createElement('div');
            nameElement.className = 'message-sender';
            nameElement.textContent = character.name;
            messageElement.appendChild(nameElement);
        }
        
        const contentElement = document.createElement('div');
        contentElement.className = 'message-content';
        contentElement.textContent = content;
        messageElement.appendChild(contentElement);
        
        return messageElement;
    }

    /**
     * 添加消息到對話界面
     * @param {Object} messageData - 消息數據
     */
    addMessage(messageData) {
        const { is_typing } = messageData;
        
        // 如果是新的助手回覆，移除之前的"輸入中..."消息
        if (messageData.sender === 'assistant' && !is_typing) {
            const lastMessage = this.dialogueContainer.lastElementChild;
            if (lastMessage && lastMessage.classList.contains('typing-message')) {
                lastMessage.remove();
            }
        }

        const messageElement = this.createMessageElement(messageData);
        this.dialogueContainer.appendChild(messageElement);
        this.scrollToBottom();
    }

    /**
     * 滾動到對話底部
     */
    scrollToBottom() {
        if (this.dialogueContainer) {
            this.dialogueContainer.scrollTop = this.dialogueContainer.scrollHeight;
        }
    }

    /**
     * 顯示錯誤消息
     * @param {string} message - 錯誤信息
     */
    showError(message) {
        const event = new CustomEvent('system-message', {
            detail: {
                message,
                type: 'error',
                duration: 5000
            }
        });
        document.dispatchEvent(event);
    }
}

// 導出單例
export const dialogueManager = new DialogueManager();
