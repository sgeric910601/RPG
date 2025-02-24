/**
 * WebSocket 連接管理模組
 */
class SocketManager {
    constructor() {
        this.socket = null;
        this.messageHandlers = new Map();
    }

    /**
     * 初始化 WebSocket 連接
     */
    init() {
        const protocol = window.location.protocol;
        const { host, port } = window.SERVER_CONFIG;
        const url = `${protocol}//${host}:${port}`;
        this.socket = io(url, {
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionAttempts: 5,
            reconnectionDelay: 1000,
            timeout: 10000,
            autoConnect: true,
            withCredentials: true
        });
        this.setupEventListeners();

        // 添加重連事件監聽
        this.socket.on('connect_error', (error) => {
            console.error('WebSocket連接錯誤:', error);
            this.showConnectionError();
        });

        this.socket.on('reconnect', (attemptNumber) => {
            console.log(`WebSocket重新連接成功，嘗試次數: ${attemptNumber}`);
            this.hideConnectionError();
        });

        this.socket.on('reconnect_failed', () => {
            console.error('WebSocket重連失敗');
            this.showConnectionError(true);
        });
    }

    /**
     * 顯示連接錯誤信息
     * @param {boolean} permanent - 是否為永久錯誤
     */
    showConnectionError(permanent = false) {
        const message = permanent 
            ? '無法連接到伺服器，請檢查網絡連接後重新整理頁面'
            : '正在嘗試重新連接到伺服器...';

        let errorDiv = document.getElementById('connection-error');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.id = 'connection-error';
            errorDiv.style.cssText = `
                position: fixed;
                top: 20px;
                left: 50%;
                transform: translateX(-50%);
                background-color: #ff4444;
                color: white;
                padding: 1rem 2rem;
                border-radius: 10px;
                z-index: 9999;
            `;
            document.body.appendChild(errorDiv);
        }
        errorDiv.textContent = message;
    }

    /**
     * 隱藏連接錯誤信息
     */
    hideConnectionError() {
        const errorDiv = document.getElementById('connection-error');
        if (errorDiv) {
            errorDiv.remove();
        }
    }

    /**
     * 設置基本事件監聽器
     */
    setupEventListeners() {
        this.socket.on('connect', () => {
            console.log('Connected to server');
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
        });

        this.socket.on('message', (data) => {
            this.handleMessage(data);
        });
    }

    /**
     * 發送消息到服務器
     * @param {string} type - 消息類型
     * @param {Object} data - 消息數據
     */
    send(type, data) {
        this.socket.emit(type, data);
    }

    /**
     * 註冊消息處理器
     * @param {string} type - 消息類型
     * @param {Function} handler - 處理函數
     */
    on(type, handler) {
        this.messageHandlers.set(type, handler);
    }

    /**
     * 處理接收到的消息
     * @param {Object} data - 消息數據
     */
    handleMessage(data) {
        const handler = this.messageHandlers.get(data.type);
        if (handler) {
            handler(data.payload);
        }
    }
}

// 導出單例
export const socketManager = new SocketManager();
