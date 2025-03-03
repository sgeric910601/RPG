/**
 * 提示詞增強組件，提供提示詞分析和優化功能。
 */

class PromptEnhancer {
    constructor() {
        this.setupEventListeners();
    }

    /**
     * 設置事件監聽器。
     */
    setupEventListeners() {
        // 監聽增強按鈕點擊
        document.querySelectorAll('.enhance-prompt-btn').forEach(button => {
            button.addEventListener('click', this.handleEnhanceClick.bind(this));
        });

        // 監聽切換詳細分析顯示
        document.querySelectorAll('.toggle-analysis-btn').forEach(button => {
            button.addEventListener('click', this.toggleAnalysis.bind(this));
        });
    }

    /**
     * 處理提示詞增強按鈕點擊。
     * @param {Event} event - 點擊事件
     */
    async handleEnhanceClick(event) {
        const button = event.target;
        const promptInput = button.closest('.prompt-container').querySelector('.prompt-input');
        const resultContainer = button.closest('.prompt-container').querySelector('.enhancement-result');
        
        if (!promptInput || !promptInput.value.trim()) {
            this.showError('請輸入提示詞');
            return;
        }

        try {
            button.disabled = true;
            button.innerHTML = '增強中...';

            const result = await this.enhancePrompt(promptInput.value);
            this.displayEnhancementResult(resultContainer, result);
        } catch (error) {
            this.showError('提示詞增強失敗：' + error.message);
        } finally {
            button.disabled = false;
            button.innerHTML = '增強提示詞';
        }
    }

    /**
     * 發送提示詞增強請求。
     * @param {string} prompt - 原始提示詞
     * @returns {Promise<Object>} 增強結果
     */
    async enhancePrompt(prompt) {
        const response = await fetch('/api/prompts/enhance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                prompt,
                options: {
                    detailed_analysis: true
                }
            })
        });

        if (!response.ok) {
            throw new Error(`請求失敗：${response.statusText}`);
        }

        const data = await response.json();
        if (data.status === 'error') {
            throw new Error(data.message);
        }

        return data.data;
    }

    /**
     * 顯示增強結果。
     * @param {HTMLElement} container - 結果容器元素
     * @param {Object} result - 增強結果數據
     */
    displayEnhancementResult(container, result) {
        const { enhanced_prompt, analysis, suggestions } = result;

        container.innerHTML = `
            <div class="enhancement-content">
                <h4>增強後的提示詞：</h4>
                <div class="enhanced-prompt">
                    ${this.escapeHtml(enhanced_prompt)}
                </div>
                
                <div class="analysis-section" style="display: none;">
                    <h4>提示詞分析：</h4>
                    <div class="analysis-scores">
                        <div class="score-item">
                            <label>清晰度：</label>
                            <div class="score-bar">
                                <div class="score-fill" style="width: ${analysis.clarity_score * 100}%"></div>
                            </div>
                            <span>${(analysis.clarity_score * 100).toFixed(0)}%</span>
                        </div>
                        <div class="score-item">
                            <label>上下文：</label>
                            <div class="score-bar">
                                <div class="score-fill" style="width: ${analysis.context_score * 100}%"></div>
                            </div>
                            <span>${(analysis.context_score * 100).toFixed(0)}%</span>
                        </div>
                        <div class="score-item">
                            <label>具體性：</label>
                            <div class="score-bar">
                                <div class="score-fill" style="width: ${analysis.specificity_score * 100}%"></div>
                            </div>
                            <span>${(analysis.specificity_score * 100).toFixed(0)}%</span>
                        </div>
                        <div class="score-item">
                            <label>結構：</label>
                            <div class="score-bar">
                                <div class="score-fill" style="width: ${analysis.structure_score * 100}%"></div>
                            </div>
                            <span>${(analysis.structure_score * 100).toFixed(0)}%</span>
                        </div>
                    </div>
                </div>
                
                <div class="suggestions-section">
                    <h4>改進建議：</h4>
                    <ul class="suggestions-list">
                        ${suggestions.map(suggestion => `<li>${this.escapeHtml(suggestion)}</li>`).join('')}
                    </ul>
                </div>
                
                <div class="actions">
                    <button class="toggle-analysis-btn">顯示分析</button>
                    <button class="copy-prompt-btn">複製提示詞</button>
                </div>
            </div>
        `;

        // 添加複製按鈕事件監聽
        container.querySelector('.copy-prompt-btn').addEventListener('click', () => {
            this.copyToClipboard(enhanced_prompt);
        });

        // 添加顯示分析按鈕事件監聽
        container.querySelector('.toggle-analysis-btn').addEventListener('click', () => {
            this.toggleAnalysis(container);
        });
    }

    /**
     * 切換分析詳情顯示。
     * @param {HTMLElement} container - 結果容器元素
     */
    toggleAnalysis(container) {
        const analysisSection = container.querySelector('.analysis-section');
        const button = container.querySelector('.toggle-analysis-btn');
        
        if (analysisSection.style.display === 'none') {
            analysisSection.style.display = 'block';
            button.textContent = '隱藏分析';
        } else {
            analysisSection.style.display = 'none';
            button.textContent = '顯示分析';
        }
    }

    /**
     * 複製文本到剪貼板。
     * @param {string} text - 要複製的文本
     */
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showMessage('提示詞已複製到剪貼板');
        } catch (error) {
            this.showError('複製失敗');
        }
    }

    /**
     * 顯示錯誤消息。
     * @param {string} message - 錯誤消息
     */
    showError(message) {
        // TODO: 實現錯誤提示UI
        console.error(message);
    }

    /**
     * 顯示提示消息。
     * @param {string} message - 提示消息
     */
    showMessage(message) {
        // TODO: 實現提示消息UI
        console.log(message);
    }

    /**
     * HTML轉義。
     * @param {string} text - 要轉義的文本
     * @returns {string} 轉義後的文本
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// 初始化提示詞增強器
document.addEventListener('DOMContentLoaded', () => {
    window.promptEnhancer = new PromptEnhancer();
});