import { eventManager } from './events.js';

class SocketManager {
    constructor() {
        this.socket = null;
        this.eventHandlers = {};
        this.pendingHandlers = [];
        this.init();
    }

    /**
     * 初始化Socket.IO連接
     */
    init() {
        console.log('[SocketManager] 初始化WebSocket連接');
        this.socket = io({
            path: '/socket.io',
            reconnection: true,
            reconnectionAttempts: 5,
            reconnectionDelay: 1000
        });

        // 監聽連接事件
        this.socket.on('connect', () => {
            console.log('[SocketManager] WebSocket已連接');
            this.registerPendingHandlers();
        });

        // 監聽斷開連接事件
        this.socket.on('disconnect', () => {
            console.log('[SocketManager] WebSocket已斷開連接');
        });

        // 監聽錯誤事件
        this.socket.on('error', (error) => {
            console.error('[SocketManager] WebSocket錯誤:', error);
        });

        // 監聽重連事件
        this.socket.on('reconnect_attempt', () => {
            console.log('[SocketManager] 嘗試重新連接...');
        });
    }

    /**
     * 發送消息到服務器
     * @param {string} event - 事件名稱
     * @param {Object} data - 消息數據
     */
    send(event, data) {
        if (!this.socket || !this.socket.connected) {
            console.error('[SocketManager] WebSocket未連接，無法發送消息');
            return;
        }
        console.log(`[SocketManager] 發送事件 ${event}:`, data);
        this.socket.emit(event, data);
    }

    /**
     * 發送消息到指定角色
     * @param {string} message - 消息內容
     * @param {string} characterId - 角色ID
     */
    sendMessage(message, characterId) {
        this.send('send_message', {
            message: message,
            character: characterId
        });
    }

    /**
     * 註冊事件監聽器
     * @param {string} event - 事件名稱
     * @param {Function} handler - 處理函數
     */
    on(event, handler) {
        // 如果socket還未連接，將處理器加入待處理隊列
        if (!this.socket || !this.socket.connected) {
            console.log(`[SocketManager] 添加待處理事件: ${event}`);
            this.pendingHandlers.push({ event, handler });
            return;
        }
        this.socket.on(event, handler);
        this.eventHandlers[event] = handler;
        console.log(`[SocketManager] 註冊事件處理器: ${event}`);
    }

    /**
     * 註冊所有待處理的事件處理器
     */
    registerPendingHandlers() {
        console.log(`[SocketManager] 開始註冊待處理事件，數量: ${this.pendingHandlers.length}`);
        this.pendingHandlers.forEach(({ event, handler }) => {
            if (this.socket && this.socket.connected) {
                this.socket.on(event, handler);
                this.eventHandlers[event] = handler;
                console.log(`[SocketManager] 註冊待處理事件: ${event}`);
            }
        });
        this.pendingHandlers = [];
    }

    /**
     * 移除事件監聽器
     * @param {string} event - 事件名稱
     */
    off(event) {
        if (!this.socket || !this.eventHandlers[event]) {
            return;
        }
        this.socket.off(event, this.eventHandlers[event]);
        delete this.eventHandlers[event];
        console.log(`[SocketManager] 移除事件處理器: ${event}`);
    }
}

// 導出單例
export const socketManager = new SocketManager();
