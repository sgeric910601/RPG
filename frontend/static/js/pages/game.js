import { socketManager } from '../core/socket.js';
import { gameState } from '../core/state.js';
import { eventManager } from '../core/events.js';
import { characterManager } from '../components/character.js';
import { dialogueManager } from '../components/dialogue.js';
import { modalManager } from '../components/modals.js';

/**
 * 遊戲頁面初始化
 */
class GamePage {
    constructor() {
        this.init();
    }

    /**
     * 初始化遊戲頁面
     */
    async init() {
        try {
            // 初始化 WebSocket 連接
            socketManager.init();

            // 從本地存儲加載遊戲狀態
            gameState.loadFromLocalStorage();

            // 初始化事件監聽
            this.initEventListeners();

            // 加載上一次的遊戲狀態（如果有）
            await this.loadLastGameState();

            // 顯示加載完成的視覺反饋
            this.showLoadedState();
        } catch (error) {
            console.error('遊戲初始化失敗:', error);
            this.showErrorMessage('遊戲初始化失敗，請重新整理頁面');
        }
    }

    /**
     * 初始化事件監聽器
     */
    initEventListeners() {
        // 頁面關閉前保存
        window.addEventListener('beforeunload', () => {
            gameState.saveToLocalStorage();
        });

        // 監聽主題變化
        gameState.subscribe('settings', (settings) => {
            if (settings?.themeColor) {
                document.documentElement.style.setProperty('--theme-color', settings.themeColor);
            }
        });
    }

    /**
     * 加載上一次的遊戲狀態
     */
    async loadLastGameState() {
        try {
            const response = await fetch('/api/load_story');
            const data = await response.json();
            
            if (data.status === 'success' && data.dialogue_history) {
                // 首先設置對話歷史
                const parsedHistory = Array.isArray(data.dialogue_history) 
                    ? data.dialogue_history 
                    : [];
                gameState.set('dialogue.messages', parsedHistory);

                // 然後設置角色信息
                if (data.story?.current_character) {
                    gameState.set('currentCharacter', data.story.current_character);
                }
            }
        } catch (error) {
            console.warn('無法加載上一次的遊戲狀態:', error);
        }
    }

    /**
     * 顯示加載完成的視覺反饋
     */
    showLoadedState() {
        const gameContainer = document.querySelector('.game-container');
        if (gameContainer) {
            gameContainer.classList.add('loaded');
        }
    }

    /**
     * 顯示錯誤信息
     * @param {string} message - 錯誤信息
     */
    showErrorMessage(message) {
        const errorElement = document.createElement('div');
        errorElement.className = 'error-message';
        errorElement.textContent = message;
        document.body.appendChild(errorElement);

        // 5秒後自動移除錯誤信息
        setTimeout(() => {
            errorElement.remove();
        }, 5000);
    }
}

// 當 DOM 加載完成後初始化遊戲頁面
document.addEventListener('DOMContentLoaded', () => {
    new GamePage();
});
