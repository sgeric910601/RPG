"""AI模型管理器，用於管理和選擇不同的AI模型."""

from typing import Dict, List, Optional

class ModelManager:
    """AI模型管理類，提供可用模型信息和建議."""
    
    # OpenAI 模型
    OPENAI_MODELS = {
        "gpt-4o": {
            "description": "最新的GPT-4多模態模型，能力全面且高效",
            "tokens_limit": 128000,
            "cost_per_1k": "$5.00 / $15.00",  # 輸入/輸出
            "recommended": True
        },
        "gpt-4-turbo": {
            "description": "更新的GPT-4版本，知識庫至2023年4月",
            "tokens_limit": 128000,
            "cost_per_1k": "$10.00 / $30.00",
            "recommended": False
        },
        "gpt-3.5-turbo": {
            "description": "價格更實惠的GPT模型，適合簡單任務",
            "tokens_limit": 16000,
            "cost_per_1k": "$0.50 / $1.50",
            "recommended": True
        }
    }
    
    # Claude 模型
    CLAUDE_MODELS = {
        "claude-3.7-sonnet": {
            "description": "最新的 Claude 3.7 Sonnet 模型，具有更高的性能和能力",
            "tokens_limit": 400000,
            "cost_per_1k": "$3.00 / $15.00",  # 輸入/輸出
            "recommended": True,
            "supports_vision": True
        },
        "claude-3-opus-20240229": {
            "description": "Claude 3系列中高性能的模型，適合複雜任務",
            "tokens_limit": 200000,
            "cost_per_1k": "$15.00 / $75.00",
            "recommended": True,
            "supports_vision": True
        },
        "claude-3-sonnet-20240229": {
            "description": "平衡性能和成本的Claude 3模型",
            "tokens_limit": 200000,
            "cost_per_1k": "$3.00 / $15.00",
            "recommended": False,
            "supports_vision": True
        },
        "claude-3-haiku-20240307": {
            "description": "速度最快、成本最低的Claude模型",
            "tokens_limit": 200000,
            "cost_per_1k": "$0.25 / $1.25",
            "recommended": True,
            "supports_vision": True
        },
        "claude-2.1": {
            "description": "Claude 2系列更新版本",
            "tokens_limit": 200000,
            "cost_per_1k": "$8.00 / $24.00",
            "recommended": False,
            "supports_vision": False
        }
    }
    
    def get_all_models(self) -> Dict:
        """獲取所有模型及其詳細信息."""
        return {
            "openai": self.OPENAI_MODELS,
            "claude": self.CLAUDE_MODELS
        }
    
    def get_model_names(self) -> Dict[str, List[str]]:
        """獲取所有可用模型名稱列表."""
        return {
            "openai": list(self.OPENAI_MODELS.keys()),
            "claude": list(self.CLAUDE_MODELS.keys())
        }
    
    def get_recommended_models(self) -> Dict[str, List[str]]:
        """獲取推薦模型列表."""
        return {
            "openai": [k for k, v in self.OPENAI_MODELS.items() if v.get("recommended", False)],
            "claude": [k for k, v in self.CLAUDE_MODELS.items() if v.get("recommended", False)]
        }
    
    def get_model_info(self, model_name: str) -> Optional[Dict]:
        """獲取特定模型的詳細信息."""
        if model_name in self.OPENAI_MODELS:
            return {"provider": "openai", **self.OPENAI_MODELS[model_name]}
        elif model_name in self.CLAUDE_MODELS:
            return {"provider": "claude", **self.CLAUDE_MODELS[model_name]}
        return None
    
    def suggest_model(self, task_type: str, budget_sensitive: bool = False) -> str:
        """根據任務類型和預算敏感度推薦模型."""
        if task_type == "roleplay" and not budget_sensitive:
            return "claude-3.7-sonnet"  # 更新為最新推薦模型
        elif task_type == "roleplay" and budget_sensitive:
            return "claude-3-haiku-20240307"
        elif task_type == "story_generation" and not budget_sensitive:
            return "claude-3.7-sonnet"  # 更新為最新推薦模型
        elif task_type == "story_generation" and budget_sensitive:
            return "gpt-3.5-turbo"
        else:
            return "claude-3.7-sonnet"  # 預設推薦
