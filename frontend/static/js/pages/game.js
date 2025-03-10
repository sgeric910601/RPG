import { socketManager } from '../core/socket.js';
import { characterManager } from '../components/character.js';
import { eventManager } from '../core/events.js';
import { gameState } from '../core/state.js';

class Game {
    constructor() {
        this.init();
    }

    init() {
        this.initSocketConnection();
        this.initEventListeners();
        this.showCharacterSelection();
    }

    /**
     * 初始化Socket連接
     */
    initSocketConnection() {
        socketManager.init();
    }

    /**
     * 初始化事件監聽器
     */
    initEventListeners() {
        // 監聽表單提交
        const messageForm = document.getElementById('message-form');
        if (messageForm) {
            messageForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleMessageSubmit();
            });
        }

        // 監聽按鈕點擊
        document.addEventListener('click', (e) => {
            const target = e.target.closest('[data-action]');
            if (target) {
                const action = target.dataset.action;
                if (typeof this[action] === 'function') {
                    this[action](e);
                }
            }
        });

        // 監聽角色選擇
        eventManager.on('character:selected', (character) => {
            this.handleCharacterSelected(character);
            // 關閉模態框
            const characterModal = document.getElementById('characterModal');
            const modal = bootstrap.Modal.getInstance(characterModal);
            if (modal) {
                modal.hide();
            }
        });
    }

    /**
     * 顯示角色選擇模態框
     */
    showCharacterSelection() {
        console.log('顯示角色選擇模態框');  // 調試日誌
        const characterModal = document.getElementById('characterModal');
        if (characterModal) {
            const modal = new bootstrap.Modal(characterModal);
            modal.show();

            // 在模態框顯示時載入角色列表
            characterModal.addEventListener('shown.bs.modal', async () => {
                try {
                    console.log('開始載入角色列表');  // 調試日誌
                    const response = await fetch('/api/characters/');
                    const data = await response.json();
                    console.log('收到角色數據:', data);  // 調試日誌
                    
                    if (data.status === 'success') {
                        characterManager.updateCharacterList(data);
                    } else {
                        console.error('載入角色列表失敗:', data.message);
                    }
                } catch (error) {
                    console.error('載入角色列表時出錯:', error);
                }
            });
        }
    }

    /**
     * 處理角色選擇
     * @param {Object} character - 選擇的角色數據
     */
    handleCharacterSelected(character) {
        console.log('選擇角色:', character);  // 調試日誌
        gameState.set('currentCharacter', character);
    }

    /**
     * 處理消息提交
     */
    handleMessageSubmit() {
        const input = document.getElementById('message-input');
        if (!input || !input.value.trim()) return;

        const currentCharacter = gameState.get('currentCharacter');
        if (!currentCharacter) {
            alert('請先選擇一個角色');
            return;
        }

        socketManager.send('send_message', {
            message: input.value.trim(),
            character: currentCharacter
        });

        input.value = '';
    }

    /**
     * 處理設定保存
     * @param {Event} e - 事件對象
     */
    handleSettingsSave(e) {
        e.preventDefault();
        const form = e.target.closest('form');
        if (!form) return;

        const formData = new FormData(form);
        const settings = Object.fromEntries(formData.entries());
        
        gameState.set('settings', settings);
        gameState.saveToLocalStorage();

        // 關閉模態框
        const modal = bootstrap.Modal.getInstance(form.closest('.modal'));
        if (modal) {
            modal.hide();
        }
    }

    /**
     * 處理世界設定保存
     * @param {Event} e - 事件對象
     */
    handleWorldSettingSave(e) {
        e.preventDefault();
        const form = e.target.closest('form');
        if (!form) return;

        const formData = new FormData(form);
        const settings = {
            name: formData.get('name'),
            description: formData.get('description'),
            background: formData.get('background'),
            themes: formData.get('themes').split(',').map(t => t.trim())
        };

        socketManager.send('world:save', settings);

        // 關閉模態框
        const modal = bootstrap.Modal.getInstance(form.closest('.modal'));
        if (modal) {
            modal.hide();
        }
    }
}

// 當DOM加載完成後初始化遊戲
document.addEventListener('DOMContentLoaded', () => {
    console.log('初始化遊戲頁面');  // 調試日誌
    new Game();
});
