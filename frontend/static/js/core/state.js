/**
 * 全局狀態管理模組
 */
class GameState {
    constructor() {
        this.state = {
            currentCharacter: null,
            dialogue: {
                messages: [],
                choices: []
            },
            settings: {
                aiModel: 'gpt4',
                themeColor: '#FF69B4'
            },
            worldSetting: {
                name: '',
                description: '',
                background: '',
                themes: []
            },
            gameProgress: {
                affectionLevel: 0,
                events: [],
                flags: new Set()
            }
        };
        this.listeners = new Map();
    }

    /**
     * 獲取狀態
     * @param {string} key - 狀態鍵
     * @returns {*} 狀態值
     */
    get(key) {
        return key.split('.').reduce((obj, k) => obj?.[k], this.state);
    }

    /**
     * 更新狀態
     * @param {string} key - 狀態鍵
     * @param {*} value - 新的狀態值
     */
    set(key, value) {
        const keys = key.split('.');
        const lastKey = keys.pop();
        const target = keys.reduce((obj, k) => obj[k] = obj[k] || {}, this.state);
        target[lastKey] = value;
        this.notify(key);
    }

    /**
     * 訂閱狀態變化
     * @param {string} key - 狀態鍵
     * @param {Function} callback - 回調函數
     */
    subscribe(key, callback) {
        if (!this.listeners.has(key)) {
            this.listeners.set(key, new Set());
        }
        this.listeners.get(key).add(callback);
    }

    /**
     * 取消訂閱
     * @param {string} key - 狀態鍵
     * @param {Function} callback - 回調函數
     */
    unsubscribe(key, callback) {
        const listeners = this.listeners.get(key);
        if (listeners) {
            listeners.delete(callback);
        }
    }

    /**
     * 通知訂閱者
     * @param {string} key - 狀態鍵
     */
    notify(key) {
        const value = this.get(key);
        const listeners = this.listeners.get(key);
        if (listeners) {
            listeners.forEach(callback => callback(value));
        }
    }

    /**
     * 保存遊戲狀態
     */
    saveToLocalStorage() {
        const saveData = {
            settings: this.state.settings,
            gameProgress: this.state.gameProgress,
            worldSetting: this.state.worldSetting
        };
        localStorage.setItem('gameState', JSON.stringify(saveData));
    }

    /**
     * 從本地存儲加載遊戲狀態
     */
    loadFromLocalStorage() {
        const savedData = localStorage.getItem('gameState');
        if (savedData) {
            const data = JSON.parse(savedData);
            this.state.settings = { ...this.state.settings, ...data.settings };
            this.state.gameProgress = { ...this.state.gameProgress, ...data.gameProgress };
            this.state.worldSetting = { ...this.state.worldSetting, ...data.worldSetting };
        }
    }
}

// 導出單例
export const gameState = new GameState();
