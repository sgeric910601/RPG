import { socketManager } from '../core/socket.js';
import { gameState } from '../core/state.js';
import { eventManager } from '../core/events.js';

class DialogueManager {
    constructor() {
        this.dialogueContainer = document.querySelector('.dialogue-container');
        this.choiceContainer = document.querySelector('.choice-container');
        this.messageForm = document.getElementById('message-form');
        this.messageInput = document.getElementById('message-input');
        
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

        socketManager.on('receive_message', (data) => {
            this.handleServerMessage(data);
        });
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
        socketManager.send('send_message', {
            message: message,
            character: character.id  // 使用角色ID
        });

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
        if (data.status === 'error') {
            this.showError(data.message);
            return;
        }

        if (data.message) {
            this.addMessage({
                content: data.message,
                sender: 'assistant',
                character: data.character,
                is_chunk: data.is_chunk
            });
        }
    }

    /**
     * 添加消息到對話界面
     * @param {Object} messageData - 消息數據
     */
    addMessage(messageData) {
        const { content, sender, character, is_chunk, is_typing } = messageData;
        
        // 如果是新的助手回覆，移除之前的"輸入中..."消息
        if (sender === 'assistant' && !is_chunk && !is_typing) {
            const lastMessage = this.dialogueContainer.lastElementChild;
            if (lastMessage && lastMessage.classList.contains('assistant-message') && 
                lastMessage.classList.contains('typing-message')) {
                lastMessage.remove();
            }
        }

        // 如果是流式回應的片段，更新現有消息而不是創建新消息
        if (sender === 'assistant' && is_chunk) {
            const lastMessage = this.dialogueContainer.lastElementChild;
            if (lastMessage && lastMessage.classList.contains('assistant-message')) {
                const contentElement = lastMessage.querySelector('.message-content');
                // 追加內容而不是替換
                contentElement.textContent += content;
                return;
            }
        }


        const messageElement = document.createElement('div');
        messageElement.className = `message ${sender}-message${is_typing ? ' typing-message' : ''}`;
        
        const contentElement = document.createElement('div');
        contentElement.className = 'message-content';
        contentElement.textContent = content;
        
        messageElement.appendChild(contentElement);
        
        // 如果是角色消息，添加角色信息
        if (sender === 'assistant' && character) {
            const nameElement = document.createElement('div');
            nameElement.className = 'message-sender';
            nameElement.textContent = character.name;
            messageElement.insertBefore(nameElement, contentElement);
        }
        
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
