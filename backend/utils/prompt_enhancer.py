"""提示詞增強器模組，提供提示詞分析和優化功能。"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class PromptAnalysis:
    """提示詞分析結果數據類。"""
    clarity_score: float
    context_score: float
    specificity_score: float
    structure_score: float
    overall_score: float
    suggestions: List[str]

class PromptEnhancer:
    """提示詞增強器，負責分析和改進提示詞。"""
    
    ENHANCEMENT_TEMPLATE = """分析以下提示詞並提供改進建議：

原始提示詞：
{original_prompt}

請從以下方面提供改進：
1. 清晰度和具體性
2. 上下文信息
3. 目標和預期結果
4. 格式和結構
5. 可能的限制或約束

同時提供一個優化後的版本。"""

    def __init__(self, ai_handler=None):
        """初始化提示詞增強器。
        
        Args:
            ai_handler: AI處理器實例，用於生成優化建議
        """
        self.ai_handler = ai_handler
        
    def analyze_prompt(self, prompt: str) -> PromptAnalysis:
        """分析提示詞的品質和特徵。
        
        Args:
            prompt: 要分析的提示詞
            
        Returns:
            提示詞分析結果
        """
        # 基本指標評分
        clarity_score = self._evaluate_clarity(prompt)
        context_score = self._evaluate_context(prompt)
        specificity_score = self._evaluate_specificity(prompt)
        structure_score = self._evaluate_structure(prompt)
        
        # 計算總體評分
        overall_score = (clarity_score + context_score + 
                        specificity_score + structure_score) / 4
        
        # 生成改進建議
        suggestions = self._generate_suggestions(prompt)
        
        return PromptAnalysis(
            clarity_score=clarity_score,
            context_score=context_score,
            specificity_score=specificity_score,
            structure_score=structure_score,
            overall_score=overall_score,
            suggestions=suggestions
        )
    
    def enhance_prompt(self, prompt: str) -> str:
        """生成增強後的提示詞。
        
        Args:
            prompt: 原始提示詞
            
        Returns:
            優化後的提示詞
        """
        # 預處理提示詞
        cleaned_prompt = self._preprocess_prompt(prompt)
        
        # 使用模板生成增強版本
        enhancement_prompt = self.ENHANCEMENT_TEMPLATE.format(
            original_prompt=cleaned_prompt
        )
        
        # 如果有AI處理器，使用它來生成優化版本
        if self.ai_handler:
            try:
                response = self.ai_handler.generate_response(enhancement_prompt)
                if response:
                    return response
            except Exception as e:
                print(f"AI生成優化提示詞失敗: {str(e)}")
        
        # 如果AI處理失敗或沒有AI處理器，返回原始提示詞
        return cleaned_prompt
    
    def _evaluate_clarity(self, prompt: str) -> float:
        """評估提示詞的清晰度。"""
        score = 0.0
        
        # 檢查是否有明確的指令
        if any(word in prompt.lower() for word in ['請', '使用', '創建', '生成']):
            score += 0.2
            
        # 檢查句子完整性
        if prompt.strip().endswith(('。', '？', '!')):
            score += 0.2
            
        # 檢查長度適中
        length = len(prompt)
        if 10 <= length <= 200:
            score += 0.2
            
        # 檢查是否有多個句子
        sentences = [s for s in prompt.split('。') if s.strip()]
        if 1 <= len(sentences) <= 5:
            score += 0.2
            
        # 檢查是否有關鍵詞
        if any(word in prompt.lower() for word in ['如何', '什麼', '為什麼', '目標', '需求']):
            score += 0.2
            
        return min(score, 1.0)
        
    def _evaluate_context(self, prompt: str) -> float:
        """評估提示詞的上下文豐富度。"""
        score = 0.0
        
        # 檢查是否提供了背景信息
        if any(word in prompt.lower() for word in ['因為', '由於', '基於', '考慮到']):
            score += 0.25
            
        # 檢查是否指定了場景
        if any(word in prompt.lower() for word in ['在', '當', '情況下', '環境']):
            score += 0.25
            
        # 檢查是否有條件或限制
        if any(word in prompt.lower() for word in ['如果', '假設', '條件', '限制']):
            score += 0.25
            
        # 檢查是否有示例
        if any(word in prompt.lower() for word in ['例如', '比如', '舉例', '示例']):
            score += 0.25
            
        return score
        
    def _evaluate_specificity(self, prompt: str) -> float:
        """評估提示詞的具體性。"""
        score = 0.0
        
        # 檢查是否有具體的數字或量化指標
        if any(c.isdigit() for c in prompt):
            score += 0.2
            
        # 檢查是否有具體的描述詞
        specific_words = ['具體', '詳細', '精確', '準確', '明確']
        if any(word in prompt.lower() for word in specific_words):
            score += 0.2
            
        # 檢查是否有格式要求
        format_words = ['格式', '樣式', '形式', '結構', '排版']
        if any(word in prompt.lower() for word in format_words):
            score += 0.2
            
        # 檢查是否有時間相關信息
        time_words = ['分鐘', '小時', '天', '月', '年']
        if any(word in prompt for word in time_words):
            score += 0.2
            
        # 檢查是否有單位或度量
        measure_words = ['個', '份', '次', '米', '公斤']
        if any(word in prompt for word in measure_words):
            score += 0.2
            
        return score
        
    def _evaluate_structure(self, prompt: str) -> float:
        """評估提示詞的結構。"""
        score = 0.0
        
        # 檢查是否有明確的段落分隔
        paragraphs = [p for p in prompt.split('\n\n') if p.strip()]
        if len(paragraphs) > 1:
            score += 0.25
            
        # 檢查是否有標點符號的正確使用
        if all(mark in prompt for mark in ['，', '。']):
            score += 0.25
            
        # 檢查是否有列表或編號
        if any(line.strip().startswith(('1.', '•', '-', '第')) for line in prompt.split('\n')):
            score += 0.25
            
        # 檢查是否有邏輯連接詞
        logic_words = ['首先', '其次', '然後', '最後', '因此']
        if any(word in prompt for word in logic_words):
            score += 0.25
            
        return score
        
    def _generate_suggestions(self, prompt: str) -> List[str]:
        """生成改進建議。"""
        suggestions = []
        
        # 基於清晰度評分生成建議
        clarity_score = self._evaluate_clarity(prompt)
        if clarity_score < 0.6:
            suggestions.append("建議添加明確的指令和目標")
            
        # 基於上下文評分生成建議
        context_score = self._evaluate_context(prompt)
        if context_score < 0.6:
            suggestions.append("可以添加更多背景信息和場景描述")
            
        # 基於具體性評分生成建議
        specificity_score = self._evaluate_specificity(prompt)
        if specificity_score < 0.6:
            suggestions.append("建議使用更具體的描述和量化指標")
            
        # 基於結構評分生成建議
        structure_score = self._evaluate_structure(prompt)
        if structure_score < 0.6:
            suggestions.append("可以改善文本結構，使用段落和列表")
            
        # 如果沒有任何建議，添加一個正面評價
        if not suggestions:
            suggestions.append("提示詞結構良好，無需重大改進")
            
        return suggestions
        
    def _preprocess_prompt(self, prompt: str) -> str:
        """預處理提示詞。"""
        # 去除多餘空白
        cleaned = " ".join(prompt.split())
        return cleaned