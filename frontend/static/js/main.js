// 建立WebSocket連接
const socket = io();

// 全局變量
let currentCharacter = null;
let currentModel = 'gpt4';
let dialogueHistory = [];

// DOM元素
const dialogueContainer = document.querySelector('.dialogue-container');
const choiceContainer = document.querySelector('.choice-container');
const characterImage = document.querySelector('.character-image');
const characterName = document.querySelector('.character-name');
const modelSelect = document.getElementById('modelSelect');
const themeColor = document.getElementById('themeColor');

// 全局狀態
let worldTemplate = null;

// 初始化函數
async function initGame() {
    try {
        // 載入故事模板
        const storyTemplates = await loadStoryTemplates();
        
        // 設定事件監聽器
        setupEventListeners();
        
        // 檢查是否有已保存的故事
        const savedStory = await loadSavedStory();
        if (savedStory) {
            await loadGameState(savedStory);
        } else {
            // 顯示初始化對話
            showInitialDialog();
        }
    } catch (error) {
        console.error('初始化遊戲失敗:', error);
        showError('遊戲初始化失敗，請重新載入頁面');
    }
}

// 載入已保存的故事
async function loadSavedStory() {
    try {
        const response = await fetch('/api/load_story');
        if (response.ok) {
            const data = await response.json();
            return data.story;
        }
        return null;
    } catch (error) {
        console.error('載入故事失敗:', error);
        return null;
    }
}

// 載入故事模板
async function loadStoryTemplates() {
    try {
        const response = await fetch('/api/templates');
        return await response.json();
    } catch (error) {
        console.error('載入故事模板失敗:', error);
        throw error;
    }
}

// 載入遊戲狀態
async function loadGameState(story = null) {
    try {
        if (story) {
            worldTemplate = story.world_type;
        }
        
        // 載入角色
        const response = await fetch('/api/characters');
        const data = await response.json();
        
        if (data.status === 'new_game') {
            showInitialDialog();
            return;
        }
        
        // 更新角色列表
        if (data.status === 'success' && data.characters) {
            const characters = Object.values(data.characters);
            if (characters.length > 0) {
                currentCharacter = characters[0];
                updateCharacter(currentCharacter);
                showCharacterSelection(characters);
            }
        }
        
        // 載入並顯示歷史對話
        dialogueHistory = [];  // 清空當前對話歷史
        const storyResponse = await fetch('/api/load_story');
        const storyData = await storyResponse.json();
        
        if (storyData.status === 'success' && storyData.dialogue_history) {
            // 顯示所有歷史對話
            storyData.dialogue_history.forEach(entry => {
                showMessage(entry.content, entry.speaker !== 'user');
            });
            dialogueHistory = storyData.dialogue_history;
        }
    } catch (error) {
        console.error('載入遊戲狀態失敗:', error);
        showError('載入遊戲狀態失敗');
    }
}

// 設定事件監聽器
function setupEventListeners() {
    // 模型選擇
    modelSelect.addEventListener('change', (e) => {
        currentModel = e.target.value;
    });

    // 主題顏色
    themeColor.addEventListener('change', (e) => {
        document.documentElement.style.setProperty('--primary-color', e.target.value);
    });

    // WebSocket事件
    socket.on('receive_message', handleReceivedMessage);
}

// 顯示初始對話
function showInitialDialog() {
    const initialChoices = [
        {
            text: '創建奇幻世界觀',
            value: 'fantasy'
        },
        {
            text: '創建科幻世界觀',
            value: 'scifi'
        },
        {
            text: '創建現代世界觀',
            value: 'modern'
        },
        {
            text: '自訂世界觀',
            value: 'custom'
        }
    ];

    showChoices(initialChoices, '請選擇遊戲世界觀');
}

    // 顯示對話氣泡
function showMessage(message, isCharacter = false) {
    const bubble = document.createElement('div');
    bubble.className = `dialogue-bubble ${isCharacter ? 'character' : 'player'}`;
    bubble.textContent = message;
    dialogueContainer.appendChild(bubble);
    
    // 自動滾動到底部
    dialogueContainer.scrollTop = dialogueContainer.scrollHeight;
    
    // 保存對話歷史
    const historyEntry = {
        speaker: isCharacter ? currentCharacter?.name : 'user',
        content: message
    };
    dialogueHistory.push(historyEntry);

    // 保存並顯示狀態
    saveGameState();
}

// 保存遊戲狀態
async function saveGameState() {
    const saveIndicator = document.querySelector('.save-indicator');
    saveIndicator.classList.add('visible');

    try {
        const response = await fetch('/api/save_story', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error('保存失敗');
        }

        setTimeout(() => {
            saveIndicator.classList.remove('visible');
        }, 2000);
    } catch (error) {
        console.error('保存遊戲狀態失敗:', error);
        showError('保存對話失敗');
        saveIndicator.classList.remove('visible');
    }
}

// 顯示選項
function showChoices(choices, prompt = null) {
    // 清空現有選項
    choiceContainer.innerHTML = '';
    
    // 顯示提示文字
    if (prompt) {
        const promptDiv = document.createElement('div');
        promptDiv.className = 'choice-prompt';
        promptDiv.textContent = prompt;
        choiceContainer.appendChild(promptDiv);
    }
    
    // 添加選項按鈕
    choices.forEach(choice => {
        const button = document.createElement('button');
        button.className = 'choice-button';
        button.textContent = choice.text;
        button.addEventListener('click', () => handleChoice(choice));
        choiceContainer.appendChild(button);
    });
}

// 處理選項選擇
async function handleChoice(choice) {
    showMessage(choice.text);
    
    if (choice.value === 'custom') {
        // 處理自訂世界觀
        showCustomWorldDialog();
        return;
    }
    
    if (!worldTemplate) {
        // 選擇世界觀
        try {
            const response = await fetch('/api/init_story', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    world_type: choice.value,
                    setting: choice.text,
                    background: '',  // 將從模板中獲取
                    adult_content: false  // 可以通過設置更改
                })
            });
            
            const data = await response.json();
            if (data.status === 'success') {
                worldTemplate = choice.value;
                await loadGameState(data.story);
                showCharacterSelection();
            } else {
                showError('創建故事失敗');
            }
        } catch (error) {
            console.error('處理選擇失敗:', error);
            showError('處理選擇時發生錯誤');
        }
    } else {
        // 一般對話選擇
        socket.emit('send_message', {
            message: choice.text,
            character: currentCharacter?.name
        });
    }
}

// 顯示自訂世界觀對話框
function showCustomWorldDialog() {
    const dialogContent = `
        <div class="custom-world-form">
            <div class="form-group">
                <label>世界觀設定</label>
                <textarea id="worldSetting" class="form-control" rows="3"></textarea>
            </div>
            <div class="form-group">
                <label>故事背景</label>
                <textarea id="storyBackground" class="form-control" rows="3"></textarea>
            </div>
            <div class="form-check">
                <input type="checkbox" class="form-check-input" id="adultContent">
                <label class="form-check-label">包含限制級內容</label>
            </div>
        </div>
    `;
    
    showDialog('創建自訂世界', dialogContent, async () => {
        const setting = document.getElementById('worldSetting').value;
        const background = document.getElementById('storyBackground').value;
        const adultContent = document.getElementById('adultContent').checked;
        
        if (!setting || !background) {
            showError('請填寫所有必要欄位');
            return;
        }
        
        try {
            const response = await fetch('/api/init_story', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    world_type: 'custom',
                    setting,
                    background,
                    adult_content: adultContent
                })
            });
            
            const data = await response.json();
            if (data.status === 'success') {
                worldTemplate = 'custom';
                await loadGameState(data.story);
                showCharacterSelection();
            } else {
                showError('創建故事失敗');
            }
        } catch (error) {
            console.error('創建自訂世界失敗:', error);
            showError('創建自訂世界時發生錯誤');
        }
    });
}

// 顯示角色選擇介面
function showCharacterSelection(characters = []) {
    if (!characters || characters.length === 0) {
        showError('沒有可用的角色');
        return;
    }
    const choiceButtons = characters.map(char => ({
        text: `與 ${char.name} 對話`,
        value: char.name
    }));
    
    showChoices(choiceButtons, '請選擇要互動的角色');
}

// 顯示錯誤訊息
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    document.body.appendChild(errorDiv);
    
    setTimeout(() => {
        errorDiv.remove();
    }, 3000);
}

// 顯示對話框
function showDialog(title, content, onConfirm) {
    const modal = document.createElement('div');
    modal.className = 'modal fade show';
    modal.style.display = 'block';
    modal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">${title}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    ${content}
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                    <button type="button" class="btn btn-primary confirm-btn">確認</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    const confirmBtn = modal.querySelector('.confirm-btn');
    const closeBtn = modal.querySelector('.btn-close');
    const cancelBtn = modal.querySelector('.btn-secondary');
    
    confirmBtn.addEventListener('click', () => {
        onConfirm();
        modal.remove();
    });
    
    [closeBtn, cancelBtn].forEach(btn => {
        btn.addEventListener('click', () => {
            modal.remove();
        });
    });
}

// 處理收到的消息
function handleReceivedMessage(data) {
    if (data.status === 'error') {
        showError(data.message);
        return;
    }
    
    showMessage(data.message, true);
    
    // 更新角色狀態
    if (data.character) {
        updateCharacter(data.character);
    }
    
    // 如果有新的選項，顯示它們
    if (data.choices) {
        showChoices(data.choices);
    }
}

// 更新角色信息
function updateCharacter(character) {
    currentCharacter = character;
    characterName.textContent = character.name;
    
    // 更新立繪
    if (character.image) {
        characterImage.style.backgroundImage = `url(${character.image})`;
    }
    
    // 更新好感度
    updateAffection(character.affection);
}

// 更新好感度顯示
function updateAffection(level) {
    const hearts = document.querySelector('.hearts');
    hearts.innerHTML = '';
    
    for (let i = 0; i < 5; i++) {
        const heart = document.createElement('i');
        heart.className = `fas fa-heart ${i < level ? 'active' : ''}`;
        hearts.appendChild(heart);
    }
}

// 添加特效
function addEffect(type) {
    switch(type) {
        case 'heart':
            const heart = document.createElement('div');
            heart.className = 'floating-heart';
            document.body.appendChild(heart);
            setTimeout(() => heart.remove(), 1000);
            break;
            
        case 'sparkle':
            // 添加閃耀特效
            break;
    }
}

// 初始化遊戲
document.addEventListener('DOMContentLoaded', initGame);
