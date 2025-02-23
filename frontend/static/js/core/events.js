/**
 * 事件管理模組
 */
class EventManager {
    constructor() {
        this.events = new Map();
        this.domListeners = new Map();
    }

    /**
     * 註冊事件監聽器
     * @param {string} eventName - 事件名稱
     * @param {Function} handler - 處理函數
     * @param {string} [id] - 可選的處理器ID，用於後續移除
     */
    on(eventName, handler, id = null) {
        if (!this.events.has(eventName)) {
            this.events.set(eventName, new Map());
        }
        const handlers = this.events.get(eventName);
        handlers.set(id || handler, handler);
    }

    /**
     * 移除事件監聽器
     * @param {string} eventName - 事件名稱
     * @param {Function|string} handlerOrId - 處理函數或ID
     */
    off(eventName, handlerOrId) {
        const handlers = this.events.get(eventName);
        if (handlers) {
            handlers.delete(handlerOrId);
        }
    }

    /**
     * 觸發事件
     * @param {string} eventName - 事件名稱
     * @param {*} data - 事件數據
     */
    emit(eventName, data) {
        const handlers = this.events.get(eventName);
        if (handlers) {
            handlers.forEach(handler => handler(data));
        }
    }

    /**
     * 為DOM元素添加事件監聽器
     * @param {string} selector - CSS選擇器
     * @param {string} eventType - 事件類型
     * @param {Function} handler - 處理函數
     * @param {Object} options - addEventListener的選項
     */
    addDOMListener(selector, eventType, handler, options = {}) {
        const elements = document.querySelectorAll(selector);
        const key = `${selector}-${eventType}`;
        
        if (!this.domListeners.has(key)) {
            this.domListeners.set(key, new Set());
        }

        elements.forEach(element => {
            const wrappedHandler = (event) => handler(event, element);
            element.addEventListener(eventType, wrappedHandler, options);
            this.domListeners.get(key).add({
                element,
                handler: wrappedHandler
            });
        });
    }

    /**
     * 移除DOM事件監聽器
     * @param {string} selector - CSS選擇器
     * @param {string} eventType - 事件類型
     */
    removeDOMListener(selector, eventType) {
        const key = `${selector}-${eventType}`;
        const listeners = this.domListeners.get(key);
        
        if (listeners) {
            listeners.forEach(({ element, handler }) => {
                element.removeEventListener(eventType, handler);
            });
            this.domListeners.delete(key);
        }
    }

    /**
     * 初始化遊戲相關的DOM事件監聽
     */
    initGameEvents() {
        // 角色選擇
        this.addDOMListener('#createCharacter', 'click', () => {
            this.emit('character:create');
        });

        // 對話選項
        this.addDOMListener('.choice-container .choice', 'click', (event, element) => {
            const choiceId = element.dataset.choiceId;
            this.emit('dialogue:choice', { choiceId });
        });

        // 設定保存
        this.addDOMListener('#saveSettings', 'click', () => {
            const settings = {
                aiModel: document.querySelector('#modelSelect').value,
                themeColor: document.querySelector('#themeColor').value
            };
            this.emit('settings:save', settings);
        });

        // 世界觀設定保存
        this.addDOMListener('#saveWorldSetting', 'click', () => {
            const worldSetting = {
                name: document.querySelector('#worldName').value,
                description: document.querySelector('#worldDescription').value,
                background: document.querySelector('#storyBackground').value,
                themes: document.querySelector('#storyThemes').value.split(',').map(t => t.trim())
            };
            this.emit('world:save', worldSetting);
        });
    }
}

// 導出單例
export const eventManager = new EventManager();
