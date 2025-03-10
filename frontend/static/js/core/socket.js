import { eventManager } from './events.js';

class SocketManager {
    constructor() {
        this.socket = null;
        this.eventHandlers = {};
    }

    /**
     * 初始化Socket.IO連接
     */
    init() {
        this.socket = io({
            path: '/socket.io'
        });

        // 監聽連接事件
        this.socket.on('connect', () => {
            console.log('WebSocket已連接');
        });

        // 監聽斷開連接事件
        this.socket.on('disconnect', () => {
            console.log('WebSocket已斷開連接');
        });

        // 監聽錯誤事件
        this.socket.on('error', (error) => {
            console.error('WebSocket錯誤:', error);
        });
    }

    /**
     * 發送消息到服務器
     * @param {string} event - 事件名稱
     * @param {Object} data - 消息數據
     */
    send(event, data) {
        if (!this.socket) {
            console.error('WebSocket未初始化');
            return;
        }
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
            character: characterId  // 直接使用角色ID
        });
    }

    /**
     * 註冊事件監聽器
     * @param {string} event - 事件名稱
     * @param {Function} handler - 處理函數
     */
    on(event, handler) {
        if (!this.socket) {
            console.error('WebSocket未初始化');
            return;
        }
        this.socket.on(event, handler);
        this.eventHandlers[event] = handler;
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
    }
}

// 導出單例
export const socketManager = new SocketManager();
