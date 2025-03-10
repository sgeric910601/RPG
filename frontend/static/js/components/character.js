import { eventManager } from '../core/events.js';
import { gameState } from '../core/state.js';
import { socketManager } from '../core/socket.js';

/**
 * 角色管理組件
 */
class CharacterManager {
    constructor() {
        this.characterImageElement = document.querySelector('.character-image');
        this.characterNameElement = document.querySelector('.character-name');
        this.characterStatsElement = document.querySelector('.character-stats');
        this.characterListElement = document.querySelector('.character-list');
        
        this.initEventListeners();
    }

    /**
     * 初始化事件監聽
     */
    initEventListeners() {
        // 訂閱角色狀態變化
        gameState.subscribe('currentCharacter', (character) => {
            this.updateCharacterDisplay(character);
        });

        // 監聽角色創建事件
        eventManager.on('character:create', () => {
            this.showCharacterCreationModal();
        });

        // 處理來自伺服器的角色更新
        socketManager.on('character:update', (data) => {
            this.handleCharacterUpdate(data);
        });
    }

    /**
     * 更新角色顯示
     * @param {Object} character - 角色資料
     */
    updateCharacterDisplay(character) {
        if (!character) return;

        // 更新立繪
        if (character.image) {
            this.characterImageElement.style.backgroundImage = `url(${character.image})`;
        }
        
        // 更新名稱
        this.characterNameElement.textContent = character.name;

        // 更新好感度顯示
        this.updateAffectionDisplay(character.affection);

        // 更新角色狀態面板
        this.updateCharacterStats(character);
    }

    /**
     * 更新好感度顯示
     * @param {number} affection - 好感度數值
     */
    updateAffectionDisplay(affection) {
        const hearts = document.querySelectorAll('.hearts .fa-heart');
        const filledHearts = Math.floor(affection / 20); // 每20點填充一顆心

        hearts.forEach((heart, index) => {
            if (index < filledHearts) {
                heart.classList.add('filled');
            } else {
                heart.classList.remove('filled');
            }
        });
    }

    /**
     * 更新角色狀態面板
     * @param {Object} character - 角色資料
     */
    updateCharacterStats(character) {
        const statsHtml = `
            <h4>角色資料</h4>
            <div class="stat-item">
                <label>性格：</label>
                <span>${character.personality}</span>
            </div>
            <div class="stat-item">
                <label>說話風格：</label>
                <span>${character.dialogue_style}</span>
            </div>
            <div class="stat-item">
                <label>好感度：</label>
                <span>${character.affection || 0}</span>
            </div>
            ${character.traits ? `
            <div class="stat-item">
                <label>特質：</label>
                <span>${character.traits.join(', ')}</span>
            </div>
            ` : ''}
            ${character.orientation ? `
            <div class="stat-item">
                <label>性向：</label>
                <span>${character.orientation}</span>
            </div>
            ` : ''}
        `;
        this.characterStatsElement.innerHTML = statsHtml;
    }

    /**
     * 顯示角色創建模態框
     */
    showCharacterCreationModal() {
        // TODO: 實作角色創建介面
        console.log('Show character creation modal');
    }

    /**
     * 處理來自伺服器的角色更新
     * @param {Object} data - 更新的角色資料
     */
    handleCharacterUpdate(data) {
        gameState.set('currentCharacter', data);
    }

    /**
     * 更新角色列表
     * @param {Object} charactersData - 角色列表數據
     */
    updateCharacterList(charactersData) {
        if (!this.characterListElement) return;
        console.log('更新角色列表，收到數據:', charactersData);  // 調試日誌

        if (!charactersData || !charactersData.data || !charactersData.data.characters) {
            console.error('無效的角色數據格式');
            return;
        }

        const characters = charactersData.data.characters;
        console.log('處理角色數據:', characters);  // 調試日誌

        const characterListHtml = Object.entries(characters).map(([id, char]) => {
            console.log('處理角色:', id, char);  // 調試日誌
            return `
                <div class="character-card" data-character-id="${id}">
                    <div class="character-avatar" style="background-image: url(${char.image})"></div>
                    <div class="character-info">
                        <h5>${char.name}</h5>
                        <p>${char.personality}</p>
                    </div>
                </div>
            `;
        }).join('');

        console.log('生成的HTML:', characterListHtml);  // 調試日誌
        this.characterListElement.innerHTML = characterListHtml;

        // 添加點擊事件監聽
        this.characterListElement.querySelectorAll('.character-card').forEach(card => {
            card.addEventListener('click', () => {
                const characterId = card.dataset.characterId;
                console.log('選擇角色:', characterId);  // 調試日誌
                this.selectCharacter(characterId);
            });
        });
    }

    /**
     * 選擇角色
     * @param {string} characterId - 角色ID
     */
    async selectCharacter(characterId) {
        try {
            console.log('正在請求角色數據:', characterId);  // 調試日誌
            const response = await fetch(`/api/characters/${characterId}`);
            const data = await response.json();
            
            if (data.status === 'success') {
                const character = data.data.character;
                console.log('收到角色數據:', character);  // 調試日誌
                gameState.set('currentCharacter', character);
                eventManager.emit('character:selected', character);
            } else {
                console.error('選擇角色失敗:', data.message);
            }
        } catch (error) {
            console.error('選擇角色時發生錯誤:', error);
        }
    }
}

// 導出單例
export const characterManager = new CharacterManager();
