/**
 * 對話系統組件
 */
import { eventManager } from '../core/events.js';
import { gameState } from '../core/state.js';
import { socketManager } from '../core/socket.js';

class DialogueManager {
    constructor() {
        console.log('[對話系統] 初始化');
        this.dialogueContainer = document.querySelector('.dialogue-container');
        
        if (!this.dialogueContainer) {
            console.error('[對話系統] 錯誤: 找不到對話容器元素 .dialogue-container');
            return;
        }

        // 初始化表單元素
        this.messageForm = document.getElementById('message-form');
        this.messageInput = document.getElementById('message-input');
        
        if (!this.messageForm || !this.messageInput) {
            console.error('[對話系統] 錯誤: 找不到消息表單元素');
            return;
        }

        this.initEventListeners();
    }

    /**
     * 初始化事件監聽器
     */
    initEventListeners() {
        // 處理消息發送
        this.messageForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const message = this.messageInput.value.trim();
            if (message) {
                console.log('[對話系統] 發送消息:', message);
                const currentCharacter = gameState.get('currentCharacter');
                
                // 立即顯示用戶消息
                this.displayMessage({
                    type: 'text',
                    speaker: 'user',
                    content: message,
                    speakerName: '你'
                });

                // 發送到服務器
                socketManager.send('send_message', {
                    message: message,
                    character: currentCharacter?.name || currentCharacter
                });
                
                this.messageInput.value = '';
            }
        });

        // 處理來自服務器的消息
        socketManager.on('receive_message', (data) => {
            console.log('[對話系統] 收到服務器消息:', data);
            
            if (data.status === 'success' && data.message) {
                this.displayMessage({
                    type: 'text',
                    speaker: data.character.name,
                    content: data.message,
                    speakerName: data.character.name
                });
            } else {
                console.error('[對話系統] 錯誤:', data.message || '未知錯誤');
            }
        });
    }

    /**
     * 顯示消息
     * @param {Object} messageData - 消息數據
     */
    async displayMessage(messageData) {
        console.log('[對話系統] 顯示消息:', messageData);
        
        if (!this.dialogueContainer) {
            console.error('[對話系統] 錯誤: 對話容器不存在');
            return;
        }

        const messageElement = this.createMessageElement(messageData);
        this.dialogueContainer.appendChild(messageElement);

        // 更新狀態
        const messages = gameState.get('dialogue.messages') || [];
        gameState.set('dialogue.messages', [...messages, messageData]);

        // 滾動到底部
        this.scrollToBottom();

        // 如果是文本消息且不是用戶消息，使用打字機效果
        if (messageData.type === 'text' && messageData.speaker !== 'user') {
            await this.typewriterEffect(messageElement, messageData.content);
        }
    }

    /**
     * 創建消息元素
     */
    createMessageElement(messageData) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${messageData.type} ${messageData.speaker}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        // 如果是用戶消息，直接顯示內容
        if (messageData.speaker === 'user') {
            messageContent.textContent = messageData.content;
        }
        
        const messageInfo = document.createElement('div');
        messageInfo.className = 'message-info';
        messageInfo.innerHTML = `
            <span class="speaker">${messageData.speakerName || ''}</span>
            <span class="timestamp">${new Date().toLocaleTimeString()}</span>
        `;
        
        messageElement.appendChild(messageContent);
        messageElement.appendChild(messageInfo);
        
        return messageElement;
    }

    /**
     * 打字機效果
     */
    async typewriterEffect(element, text) {
        const contentElement = element.querySelector('.message-content');
        if (!contentElement) return Promise.resolve();

        const delay = 30;
        contentElement.textContent = '';
        
        return new Promise(resolve => {
            let index = 0;
            function type() {
                if (index < text.length) {
                    contentElement.textContent += text[index];
                    index++;
                    setTimeout(type, delay);
                } else {
                    resolve();
                }
            }
            type();
        });
    }

    /**
     * 滾動到對話底部
     */
    scrollToBottom() {
        if (this.dialogueContainer) {
            this.dialogueContainer.scrollTop = this.dialogueContainer.scrollHeight;
        }
    }
}

// 導出單例
export const dialogueManager = new DialogueManager();
console.log('[對話系統] 初始化完成');
