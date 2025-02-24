import { eventManager } from '../core/events.js';
import { gameState } from '../core/state.js';
import { socketManager } from '../core/socket.js';

/**
 * 對話系統組件
 */
class DialogueManager {
    constructor() {
        this.dialogueContainer = document.querySelector('.dialogue-container');
        this.choiceContainer = document.querySelector('.choice-container');
        this.messageQueue = [];
        this.isTyping = false;
        
        this.initEventListeners();
    }

    /**
     * 初始化事件監聽
     */
    initEventListeners() {
        // 初始化消息表單
        this.messageForm = document.getElementById('message-form');
        this.messageInput = document.getElementById('message-input');
        
        if (this.messageForm) {
            this.messageForm.addEventListener('submit', (e) => {
                e.preventDefault();
                const message = this.messageInput.value.trim();
                if (message) {
                    const currentCharacter = gameState.get('currentCharacter');
                    // 確保只發送角色ID而不是整個角色對象
                    socketManager.send('send_message', {
                        message: message,
                        character: currentCharacter?.name || currentCharacter
                    });
                    this.messageInput.value = '';
                }
            });
        }

        // 訂閱對話狀態變化
        gameState.subscribe('dialogue.messages', (messages) => {
            if (messages) {
                this.updateDialogueDisplay(messages);
            }
        });

        gameState.subscribe('dialogue.choices', (choices) => {
            this.updateChoices(choices);
        });

        // 處理來自伺服器的對話更新
        socketManager.on('receive_message', (data) => {
            if (data.status === 'success') {
                this.handleNewMessage({
                    type: 'text',
                    speaker: data.character.name,
                    speakerName: data.character.name,
                    content: data.message
                });
                if (data.choices && data.choices.length > 0) {
                    this.handleNewChoices(data.choices);
                }
            } else {
                console.error(data.message);
            }
        });

        // 處理選項選擇
        this.choiceContainer?.addEventListener('click', (e) => {
            const button = e.target.closest('.choice');
            if (button && !button.disabled) {
                const choiceId = button.dataset.choiceId;
                this.handleChoiceSelection(choiceId);
            }
        });
    }

    /**
     * 更新對話顯示
     * @param {Array} messages - 消息列表
     */
    updateDialogueDisplay(messages) {
        if (!this.dialogueContainer) return;

        // 清空現有內容
        this.dialogueContainer.innerHTML = '';

        // 重新顯示所有消息
        messages.forEach(async (messageData) => {
            const messageElement = this.createMessageElement(messageData);
            this.dialogueContainer.appendChild(messageElement);

            if (messageData.type === 'text') {
                const contentElement = messageElement.querySelector('.message-content');
                if (contentElement) {
                    contentElement.textContent = messageData.content;
                }
            }
        });

        // 滾動到底部
        this.scrollToBottom();
    }

    /**
     * 處理新消息
     * @param {Object} messageData - 消息資料
     */
    handleNewMessage(messageData) {
        this.messageQueue.push(messageData);
        if (!this.isTyping) {
            this.processMessageQueue();
        }
    }

    /**
     * 處理消息隊列
     */
    async processMessageQueue() {
        if (this.messageQueue.length === 0 || this.isTyping) {
            return;
        }

        this.isTyping = true;
        const messageData = this.messageQueue.shift();
        await this.displayMessage(messageData);
        this.isTyping = false;

        // 處理下一條消息
        if (this.messageQueue.length > 0) {
            this.processMessageQueue();
        }
    }

    /**
     * 顯示消息
     * @param {Object} messageData - 消息資料
     * @returns {Promise} 打字動畫完成的Promise
     */
    async displayMessage(messageData) {
        const messageElement = this.createMessageElement(messageData);
        this.dialogueContainer.appendChild(messageElement);
        
        // 添加到遊戲狀態
        const messages = gameState.get('dialogue.messages') || [];
        gameState.set('dialogue.messages', [...messages, messageData]);

        // 滾動到底部
        this.scrollToBottom();

        // 打字機效果
        if (messageData.type === 'text') {
            await this.typewriterEffect(messageElement, messageData.content);
        }
    }

    /**
     * 創建消息元素
     * @param {Object} messageData - 消息資料
     * @returns {HTMLElement} 消息元素
     */
    createMessageElement(messageData) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${messageData.type} ${messageData.speaker}`;
        
        if (messageData.type === 'text') {
            messageElement.innerHTML = `
                <div class="message-content"></div>
                <div class="message-info">
                    <span class="speaker">${messageData.speakerName || ''}</span>
                    <span class="timestamp">${new Date().toLocaleTimeString()}</span>
                </div>
            `;
        } else if (messageData.type === 'image') {
            messageElement.innerHTML = `
                <img src="${messageData.content}" alt="Story Image">
                <div class="message-info">
                    <span class="timestamp">${new Date().toLocaleTimeString()}</span>
                </div>
            `;
        }

        return messageElement;
    }

    /**
     * 打字機效果
     * @param {HTMLElement} element - 目標元素
     * @param {string} text - 要顯示的文字
     * @returns {Promise} 動畫完成的Promise
     */
    async typewriterEffect(element, text) {
        const contentElement = element.querySelector('.message-content');
        if (!contentElement) return Promise.resolve();

        const delay = 30; // 每個字符的延遲時間（毫秒）

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
     * 更新選項顯示
     * @param {Array} choices - 選項列表
     */
    updateChoices(choices) {
        if (!this.choiceContainer) return;

        if (!choices || choices.length === 0) {
            this.choiceContainer.innerHTML = '';
            return;
        }

        const choicesHtml = choices.map(choice => `
            <button class="choice" data-choice-id="${choice.id}">
                ${choice.text}
            </button>
        `).join('');

        this.choiceContainer.innerHTML = choicesHtml;
    }

    /**
     * 處理選項選擇
     * @param {string} choiceId - 選項ID
     */
    handleChoiceSelection(choiceId) {
        if (!this.choiceContainer) return;

        // 禁用所有選項按鈕
        const buttons = this.choiceContainer.querySelectorAll('.choice');
        buttons.forEach(button => {
            button.disabled = true;
            if (button.dataset.choiceId === choiceId) {
                button.classList.add('selected');
            }
        });

        // 發送選擇到服務器
        socketManager.send('send_message', { 
            message: choiceId,
            character: gameState.get('currentCharacter')?.name || gameState.get('currentCharacter')
        });
    }

    /**
     * 處理新的選項
     * @param {Array} choices - 選項列表
     */
    handleNewChoices(choices) {
        gameState.set('dialogue.choices', choices);
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
     * 清空對話內容
     */
    clearDialogue() {
        if (this.dialogueContainer) {
            this.dialogueContainer.innerHTML = '';
        }
        if (this.choiceContainer) {
            this.choiceContainer.innerHTML = '';
        }
        gameState.set('dialogue.messages', []);
        gameState.set('dialogue.choices', []);
    }
}

// 導出單例
export const dialogueManager = new DialogueManager();
