import { eventManager } from '../core/events.js';
import { gameState } from '../core/state.js';
import { socketManager } from '../core/socket.js';

/**
 * 模態框管理組件
 */
class ModalManager {
    constructor() {
        this.modals = {};
        this.observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.classList && node.classList.contains('modal-backdrop')) {
                        node.remove();
                    }
                });
            });
        });
        
        // 開始監視body元素的變化
        this.observer.observe(document.body, {
            childList: true,
            subtree: false
        });
        
        this.initModals();
        this.initEventListeners();
    }

    /**
     * 初始化所有模態框
     */
    initModals() {
        // 定義所有模態框的ID
        const modalIds = [
            'settingsModal',
            'characterModal',
            'chatHistoryModal',
            'worldSettingModal'
        ];

        // 初始化每個模態框
        modalIds.forEach(id => {
            const element = document.querySelector(`#${id}`);
            if (element) {
                // 如果模態框已經存在，先銷毀
                const existingModal = bootstrap.Modal.getInstance(element);
                if (existingModal) {
                    existingModal.dispose();
                }

                // 創建新的模態框實例
                this.modals[id] = new bootstrap.Modal(element, {
                    keyboard: true,
                    backdrop: false, // 完全禁用Bootstrap的backdrop
                    focus: true
                });

                // 監聽模態框事件
                element.addEventListener('show.bs.modal', (event) => {
                    // 阻止其他模態框的事件
                    event.stopPropagation();
                    
                    // 清理任何存在的backdrop
                    document.querySelectorAll('.modal-backdrop, .custom-backdrop').forEach(backdrop => {
                        backdrop.remove();
                    });
                    
                    // 創建自定義backdrop
                    const customBackdrop = document.createElement('div');
                    customBackdrop.className = 'custom-backdrop';
                    document.body.appendChild(customBackdrop);
                    
                    this.onModalShow(id);
                });

                // 監聽模態框關閉事件
                element.addEventListener('hide.bs.modal', () => {
                    // 移除自定義backdrop
                    const customBackdrop = document.querySelector('.custom-backdrop');
                    if (customBackdrop) {
                        customBackdrop.remove();
                    }
                });

                element.addEventListener('shown.bs.modal', () => {
                    // 確保模態框內的表單控件可以獲得焦點
                    const firstInput = element.querySelector('input, select, textarea');
                    if (firstInput) {
                        firstInput.focus();
                    }

                    // 添加表單鍵盤事件監聽
                    const form = element.querySelector('form');
                    if (form) {
                        form.addEventListener('keypress', (e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                const submitButton = form.querySelector('button[type="submit"]');
                                if (submitButton) {
                                    e.preventDefault();
                                    submitButton.click();
                                }
                            }
                        });
                    }
                });

                element.addEventListener('hide.bs.modal', () => {
                    // 重置表單驗證狀態
                    const form = element.querySelector('form');
                    if (form) {
                        form.classList.remove('was-validated');
                        form.reset();
                    }
                });

                element.addEventListener('hidden.bs.modal', () => {
                    // 確保所有backdrop和相關元素被清理
                    document.querySelectorAll('.modal-backdrop, .custom-backdrop').forEach(backdrop => {
                        backdrop.remove();
                    });
                    document.body.classList.remove('modal-open');
                    document.body.style.removeProperty('padding-right');
                    // 重置任何可能的樣式
                    document.body.style.overflow = '';
                });

                // 設置按鈕和表單處理
                this.setupModalButtons(element, id);
            }
        });
    }

    /**
     * 設置模態框按鈕
     * @param {HTMLElement} element - 模態框元素
     * @param {string} id - 模態框ID
     */
    setupModalButtons(element, id) {
        // 設置表單提交處理
        const form = element.querySelector('form');
        if (form) {
            // 添加表單驗證樣式
            form.classList.add('needs-validation');
            form.noValidate = true;

            // 表單提交處理
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                if (!form.checkValidity()) {
                    e.stopPropagation();
                    form.classList.add('was-validated');
                    return;
                }

                const formData = new FormData(form);
                const data = Object.fromEntries(formData.entries());
                
                switch (id) {
                    case 'settingsModal':
                        this.handleSettingsSave(data);
                        break;
                    case 'worldSettingModal':
                        // 處理主題標籤
                        if (data.themes) {
                            data.themes = data.themes.split(',').map(tag => tag.trim());
                        }
                        this.handleWorldSettingSave(data);
                        break;
                }
            });
        }

        // 設置動作按鈕處理
        const actionButtons = element.querySelectorAll('[data-action]');
        actionButtons.forEach(button => {
            button.addEventListener('click', (event) => {
                event.preventDefault();
                event.stopPropagation();

                const action = button.dataset.action;
                switch (action) {
                    case 'handleSettingsSave':
                    case 'handleWorldSettingSave':
                        const formId = action === 'handleSettingsSave' ? 'settingsForm' : 'worldSettingForm';
                        const targetForm = document.getElementById(formId);
                        if (targetForm) {
                            targetForm.dispatchEvent(new Event('submit', {
                                cancelable: true,
                                bubbles: true
                            }));
                        }
                        break;
                    case 'createCharacter':
                        this.createCharacter();
                        break;
                    case 'hideModal':
                        this.closeModal(id);
                        break;
                }
            });
        });

        // 設置模態框關閉按鈕
        element.querySelectorAll('[data-bs-dismiss="modal"]').forEach(button => {
            button.addEventListener('click', (event) => {
                event.preventDefault();
                this.closeModal(id);
            });
        });
    }

    /**
     * 加載角色列表
     */
    async loadCharacterList() {
        try {
            const response = await fetch('/api/characters/');
            const data = await response.json();
            
            if (data.status === 'success' && data.data && data.data.characters) {
                const characterList = document.querySelector('.character-list');
                if (characterList) {
                    const charactersHtml = data.data.characters.map(char => `
                        <div class="character-card" data-character-id="${char.name.toLowerCase()}">
                            <div class="character-avatar" style="background-image: url(${char.image || ''})"></div>
                            <div class="character-info">
                                <h5>${char.name}</h5>
                                <p>${char.personality || ''}</p>
                            </div>
                        </div>
                    `).join('');
                    
                    characterList.innerHTML = charactersHtml || '<div class="no-data">沒有角色數據</div>';

                    // 添加點擊事件
                    characterList.querySelectorAll('.character-card').forEach(card => {
                        card.addEventListener('click', () => {
                            const characterId = card.dataset.characterId;
                            this.selectCharacter(characterId);
                        });
                    });
                }
            } else {
                console.error('角色數據格式不正確:', data);
                const characterList = document.querySelector('.character-list');
                if (characterList) {
                    characterList.innerHTML = '<div class="no-data">無法加載角色數據</div>';
                }
            }
        } catch (error) {
            console.error('加載角色列表失敗:', error);
            eventManager.emit('system-message', {
                type: 'error',
                message: '無法加載角色列表'
            });
        }
    }

    /**
     * 選擇角色
     * @param {string} characterId - 角色ID
     */
    async selectCharacter(characterId) {
        try {
            const response = await fetch(`/api/characters/${characterId}`);
            const data = await response.json();
            
            if (data.status === 'success' && data.data && data.data.character) {
                // 更新遊戲狀態
                gameState.set('currentCharacter', data.data.character);
                
                // 關閉模態框
                this.closeModal('characterModal');
                
                // 通知服務器
                socketManager.send('character:select', { characterId });

                // 發出事件通知
                eventManager.emit('character:selected', data.data.character);
            } else {
                console.error('角色數據格式不正確:', data);
                eventManager.emit('system-message', {
                    type: 'error',
                    message: '無法選擇角色：數據格式不正確'
                });
            }
        } catch (error) {
            console.error('選擇角色失敗:', error);
            eventManager.emit('system-message', {
                type: 'error',
                message: '無法選擇角色'
            });
        }
    }

    /**
     * 創建新角色
     */
    async createCharacter() {
        try {
            // 獲取當前世界設定
            const worldSetting = gameState.get('worldSetting');
            if (!worldSetting) {
                throw new Error('請先設置世界觀');
            }

            // 發送創建角色請求
            const response = await fetch('/api/characters/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    worldSetting: worldSetting
                })
            });

            const data = await response.json();
            if (data.status === 'success') {
                // 更新角色列表
                this.loadCharacterList();
            } else {
                throw new Error(data.message || '創建角色失敗');
            }
        } catch (error) {
            console.error('創建角色失敗:', error);
            // 顯示錯誤消息
            eventManager.emit('system-message', {
                type: 'error',
                message: error.message
            });
        }
    }

    /**
     * 加載聊天歷史記錄
     */
    async loadChatHistory() {
        try {
            const response = await fetch('/api/dialogues/');
            const data = await response.json();
            
            if (data.status === 'success') {
                const chatHistoryContainer = document.querySelector('.chat-sessions');
                if (chatHistoryContainer) {
                    if (data.data && data.data.sessions && data.data.sessions.length > 0) {
                        const historyHtml = data.data.sessions.map(session => `
                            <div class="chat-session" data-session-id="${session.id}">
                                <div class="session-header">
                                    <h6>${session.title}</h6>
                                    <span class="date">${new Date(session.timestamp).toLocaleDateString()}</span>
                                </div>
                                <p class="preview">${session.preview}</p>
                            </div>
                        `).join('');
                        
                        chatHistoryContainer.innerHTML = historyHtml;

                        // 添加點擊事件處理
                        chatHistoryContainer.querySelectorAll('.chat-session').forEach(session => {
                            session.addEventListener('click', () => {
                                const sessionId = session.dataset.sessionId;
                                this.loadChatSession(sessionId);
                            });
                        });
                    } else {
                        chatHistoryContainer.innerHTML = '<div class="no-data">沒有聊天記錄</div>';
                    }
                }
            } else {
                console.error('聊天記錄數據格式不正確:', data);
                const chatHistoryContainer = document.querySelector('.chat-sessions');
                if (chatHistoryContainer) {
                    chatHistoryContainer.innerHTML = '<div class="no-data">無法加載聊天記錄</div>';
                }
            }
        } catch (error) {
            console.error('加載聊天歷史失敗:', error);
            eventManager.emit('system-message', {
                type: 'error',
                message: '無法加載聊天歷史'
            });
        }
    }

    /**
     * 加載指定的聊天會話
     * @param {string} sessionId - 會話ID
     */
    async loadChatSession(sessionId) {
        try {
            const response = await fetch(`/api/dialogues/${sessionId}`);
            const data = await response.json();
            
            if (data.status === 'success' && data.data && data.data.session) {
                // 更新遊戲狀態
                gameState.set('currentSession', data.data.session);
                
                // 關閉模態框
                this.closeModal('chatHistoryModal');
                
                // 通知伺服器加載此會話
                socketManager.send('chat:load', { sessionId });
            } else {
                console.error('聊天會話數據格式不正確:', data);
                eventManager.emit('system-message', {
                    type: 'error',
                    message: '無法加載聊天會話：數據格式不正確'
                });
            }
        } catch (error) {
            console.error('加載聊天會話失敗:', error);
            eventManager.emit('system-message', {
                type: 'error',
                message: '無法加載聊天會話'
            });
        }
    }

    /**
     * 處理模態框顯示事件
     * @param {string} modalId - 模態框ID
     */
    onModalShow(modalId) {
        switch (modalId) {
            case 'characterModal':
                this.loadCharacterList();
                break;
            case 'settingsModal':
                this.loadModelList();
                break;
            case 'chatHistoryModal':
                this.loadChatHistory();
                break;
            case 'worldSettingModal':
                this.loadWorldTemplates();
                break;
        }
    }

    /**
     * 加載模型列表
     */
    async loadModelList() {
        try {
            const response = await fetch('/api/models');
            const data = await response.json();
            
            if (data.status === 'success' && data.data && data.data.models) {
                const modelSelect = document.querySelector('#modelSelect');
                if (modelSelect) {
                    // 清空現有選項
                    modelSelect.innerHTML = '';
                    
                    // 自動處理所有API提供者的模型
                    const models = data.data.models;
                    
                    // 獲取所有API提供者
                    const providers = Object.keys(models);
                    
                    // 為每個提供者創建一個選項組
                    providers.forEach(provider => {
                        if (models[provider] && models[provider].length > 0) {
                            const optgroup = document.createElement('optgroup');
                            
                            // 格式化提供者名稱 (首字母大寫)
                            const providerName = provider.charAt(0).toUpperCase() + provider.slice(1);
                            optgroup.label = `${providerName} 模型`;
                            
                            // 添加該提供者的所有模型
                            models[provider].forEach(model => {
                                const option = document.createElement('option');
                                option.value = model.id;
                                option.textContent = model.display || model.id;
                                optgroup.appendChild(option);
                            });
                            
                            modelSelect.appendChild(optgroup);
                        }
                    });
                    
                    // 設置當前選中的模型
                    const currentSettings = gameState.get('settings');
                    if (currentSettings && currentSettings.aiModel) {
                        modelSelect.value = currentSettings.aiModel;
                    }
                }
            } else {
                console.error('模型數據格式不正確:', data);
                const modelSelect = document.querySelector('#modelSelect');
                if (modelSelect) {
                    modelSelect.innerHTML = '<option value="">無法加載模型</option>';
                }
            }
        } catch (error) {
            console.error('加載模型列表失敗:', error);
            eventManager.emit('system-message', {
                type: 'error',
                message: '無法加載模型列表'
            });
        }
    }

    /**
     * 初始化事件監聽
     */
    initEventListeners() {
        // 設定保存
        eventManager.on('settings:save', (settings) => {
            this.handleSettingsSave(settings);
        });

        // 世界觀設定保存
        eventManager.on('world:save', (worldSetting) => {
            this.handleWorldSettingSave(worldSetting);
        });

        // 訂閱設定狀態變化
        gameState.subscribe('settings', (settings) => {
            this.updateSettingsDisplay(settings);
        });

        // 訂閱世界觀設定變化
        gameState.subscribe('worldSetting', (worldSetting) => {
            this.updateWorldSettingDisplay(worldSetting);
        });
    }

    /**
     * 處理設定保存
     * @param {Object} settings - 設定資料
     */
    handleSettingsSave(settings) {
        // 更新本地狀態
        gameState.set('settings', settings);
        // 保存到本地存儲
        gameState.saveToLocalStorage();
        // 發送到服務器
        
        // 設置AI模型
        if (settings.aiModel) {
            fetch('/api/set_model', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ model: settings.aiModel })
            }).catch(err => console.error('設置模型失敗:', err));
        }
        socketManager.send('settings:save', settings);
        // 關閉模態框
        this.closeModal('settingsModal');
    }

    /**
     * 處理世界觀設定保存
     * @param {Object} worldSetting - 世界觀設定資料
     */
    handleWorldSettingSave(worldSetting) {
        // 更新本地狀態
        gameState.set('worldSetting', worldSetting);
        // 保存到本地存儲
        gameState.saveToLocalStorage();
        // 發送到服務器
        socketManager.send('world:save', worldSetting);
        // 關閉模態框
        this.closeModal('worldSettingModal');
    }

    /**
     * 更新設定顯示
     * @param {Object} settings - 設定資料
     */
    updateSettingsDisplay(settings) {
        if (!settings) return;

        const modelSelect = document.querySelector('#modelSelect');
        const themeColor = document.querySelector('#themeColor');

        if (modelSelect) {
            modelSelect.value = settings.aiModel;
        }
        if (themeColor) {
            themeColor.value = settings.themeColor;
        }
    }

    /**
     * 加載世界設定模板
     */
    async loadWorldTemplates() {
        try {
            const response = await fetch('/api/stories/templates');
            const data = await response.json();
            
            if (data.status === 'success' && data.data && data.data.templates) {
                const templateList = document.querySelector('.template-list');
                if (templateList) {
                    const templatesHtml = data.data.templates.map(template => `
                        <div class="world-template" data-template-id="${template.id}">
                            <h6>${template.name}</h6>
                            <p class="description">${template.description}</p>
                            <div class="tags">
                                ${template.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                            </div>
                        </div>
                    `).join('');
                    
                    templateList.innerHTML = templatesHtml || '<div class="no-data">沒有世界模板</div>';

                    // 添加點擊事件
                    templateList.querySelectorAll('.world-template').forEach(template => {
                        template.addEventListener('click', () => {
                            const templateId = template.dataset.templateId;
                            this.selectWorldTemplate(templateId, data.data.templates);
                        });
                    });
                }
            } else {
                console.error('世界模板數據格式不正確:', data);
                const templateList = document.querySelector('.template-list');
                if (templateList) {
                    templateList.innerHTML = '<div class="no-data">無法加載世界模板</div>';
                }
            }
        } catch (error) {
            console.error('加載世界模板失敗:', error);
            eventManager.emit('system-message', {
                type: 'error',
                message: '無法加載世界模板'
            });
        }
    }

    /**
     * 選擇世界模板
     * @param {string} templateId - 模板ID
     * @param {Array} templates - 所有模板列表
     */
    selectWorldTemplate(templateId, templates) {
        // 移除其他模板的選中狀態
        const templateElements = document.querySelectorAll('.world-template');
        templateElements.forEach(el => el.classList.remove('selected'));

        // 添加選中狀態到當前模板
        const selectedElement = document.querySelector(`[data-template-id="${templateId}"]`);
        if (selectedElement) {
            selectedElement.classList.add('selected');
        }

        // 找到選中的模板數據
        const selectedTemplate = templates.find(t => t.id === templateId);
        if (selectedTemplate) {
            // 填充表單
            this.fillWorldSettingForm(selectedTemplate);
        }
    }

    /**
     * 填充世界設定表單
     * @param {Object} template - 世界模板數據
     */
    fillWorldSettingForm(template) {
        const worldName = document.querySelector('#worldName');
        const worldDescription = document.querySelector('#worldDescription');
        const storyBackground = document.querySelector('#storyBackground');
        const storyThemes = document.querySelector('#storyThemes');

        if (worldName) worldName.value = template.name || '';
        if (worldDescription) worldDescription.value = template.description || '';
        if (storyBackground) storyBackground.value = template.background || template.description || '';
        if (storyThemes) storyThemes.value = (template.tags || []).join(', ');

        // 觸發表單驗證
        const form = document.getElementById('worldSettingForm');
        if (form) {
            form.classList.add('was-validated');
        }
    }

    /**
     * 更新世界觀設定顯示
     * @param {Object} worldSetting - 世界觀設定資料
     */
    updateWorldSettingDisplay(worldSetting) {
        if (!worldSetting) return;

        const worldName = document.querySelector('#worldName');
        const worldDescription = document.querySelector('#worldDescription');
        const storyBackground = document.querySelector('#storyBackground');
        const storyThemes = document.querySelector('#storyThemes');

        if (worldName) {
            worldName.value = worldSetting.name;
        }
        if (worldDescription) {
            worldDescription.value = worldSetting.description;
        }
        if (storyBackground) {
            storyBackground.value = worldSetting.background;
        }
        if (storyThemes) {
            storyThemes.value = worldSetting.themes.join(', ');
        }
    }

    /**
     * 打開模態框
     * @param {string} modalId - 模態框ID
     */
    openModal(modalId) {
        if (this.modals[modalId]) {
            this.modals[modalId].show();
        }
    }

    /**
     * 關閉模態框
     * @param {string} modalId - 模態框ID
     */
    closeModal(modalId) {
        if (this.modals[modalId]) {
            this.modals[modalId].hide();
            // 手動移除backdrop
            const backdrop = document.querySelector('.modal-backdrop');
            if (backdrop) {
                backdrop.remove();
            }
            // 移除body上的modal-open class
            document.body.classList.remove('modal-open');
            // 移除body的padding-right
            document.body.style.removeProperty('padding-right');
        }
    }

    /**
     * 清理資源
     */
    destroy() {
        // 停止觀察
        if (this.observer) {
            this.observer.disconnect();
        }
        
        // 清理所有模態框實例
        Object.values(this.modals).forEach(modal => {
            if (modal) {
                modal.dispose();
            }
        });
        
        // 移除所有backdrop
        document.querySelectorAll('.modal-backdrop, .custom-backdrop').forEach(backdrop => {
            backdrop.remove();
        });
        
        // 移除body上的類和樣式
        document.body.classList.remove('modal-open');
        document.body.style.removeProperty('padding-right');
    }
}

// 導出單例
export const modalManager = new ModalManager();

// 在頁面卸載時清理資源
window.addEventListener('unload', () => {
    modalManager.destroy();
});
