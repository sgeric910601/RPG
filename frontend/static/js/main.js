// 導入依賴
import { gameState } from './core/state.js';
import { characterManager } from './components/character.js';

/**
 * 初始化通用功能
 */
class App {
    constructor() {
        this.init();
    }

    async init() {
        this.initTooltips();
        this.initResizeHandler();
        this.initMessageHandler();
        this.initModals();
        await this.loadCharacterList();
    }

    /**
     * 載入角色列表
     */
    async loadCharacterList() {
        try {
            console.log('開始載入角色列表');  // 調試日誌
            const response = await fetch('/api/characters/');
            const data = await response.json();
            console.log('收到角色數據:', data);  // 調試日誌
            
            if (data.status === 'success') {
                characterManager.updateCharacterList(data);
            } else {
                console.error('載入角色列表失敗:', data.message);
                this.showSystemMessage({ 
                    message: '載入角色列表失敗', 
                    type: 'error' 
                });
            }
        } catch (error) {
            console.error('載入角色列表時出錯:', error);
            this.showSystemMessage({ 
                message: '載入角色列表時發生錯誤', 
                type: 'error' 
            });
        }
    }

    /**
     * 初始化所有模態框
     */
    initModals() {
        const modalIds = [
            'settingsModal',
            'characterModal',
            'chatHistoryModal',
            'worldSettingModal'
        ];

        modalIds.forEach(id => {
            const modalElement = document.getElementById(id);
            if (modalElement) {
                // 確保每個模態框只初始化一次
                if (!bootstrap.Modal.getInstance(modalElement)) {
                    new bootstrap.Modal(modalElement, {
                        backdrop: 'static',
                        keyboard: false
                    });
                }
            }
        });
    }

    /**
     * 初始化工具提示
     */
    initTooltips() {
        const tooltips = document.querySelectorAll('[data-toggle="tooltip"]');
        tooltips.forEach(element => {
            new bootstrap.Tooltip(element);
        });
    }

    /**
     * 初始化視窗大小處理
     */
    initResizeHandler() {
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                const gameArea = document.querySelector('.game-area');
                if (gameArea) {
                    const navHeight = document.querySelector('.navbar')?.offsetHeight || 0;
                    gameArea.style.height = `calc(100vh - ${navHeight}px)`;
                }
            }, 250);
        });
    }

    /**
     * 初始化系統消息處理
     */
    initMessageHandler() {
        document.addEventListener('system-message', (event) => {
            this.showSystemMessage(event.detail);
        });
    }

    /**
     * 顯示系統消息
     * @param {Object} detail - 消息詳情
     */
    showSystemMessage({ message, type = 'info', duration = 5000 }) {
        const messageElement = document.createElement('div');
        messageElement.className = `system-message ${type}`;
        messageElement.textContent = message;
        
        document.body.appendChild(messageElement);
        
        setTimeout(() => {
            messageElement.classList.add('fade-out');
            setTimeout(() => messageElement.remove(), 500);
        }, duration);
    }
}

// 當 DOM 加載完成後初始化應用
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM 加載完成，初始化應用');  // 調試日誌
    new App();
});
