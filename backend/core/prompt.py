"""提示詞核心邏輯模組，提供提示詞相關的業務邏輯。"""

import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict

from ..services.storage import StorageServiceFactory
from ..services.ai import AIServiceFactory
from ..utils.validation import Validator
from ..utils.error import ValidationError, NotFoundError, ServiceError


@dataclass
class Prompt:
    """提示詞數據類，表示AI提示詞。"""
    
    content: str
    type: str
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """將提示詞轉換為字典格式。
        
        Returns:
            提示詞的字典表示
        """
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Prompt':
        """從字典創建提示詞實例。
        
        Args:
            data: 提示詞數據字典
            
        Returns:
            創建的提示詞實例
        """
        return cls(
            content=data['content'],
            type=data['type'],
            tags=data.get('tags', []),
            metadata=data.get('metadata', {})
        )


class PromptTemplate:
    """提示詞模板類，表示可重用的提示詞模板。"""
    
    def __init__(self, name: str, template: str, description: str = "", 
                 variables: List[str] = None, tags: List[str] = None, 
                 metadata: Dict[str, Any] = None):
        """初始化提示詞模板。
        
        Args:
            name: 模板名稱
            template: 模板內容，可包含變量佔位符，如 {variable_name}
            description: 模板描述
            variables: 模板變量列表
            tags: 模板標籤列表
            metadata: 模板元數據
        """
        self.name = name
        self.template = template
        self.description = description
        self.variables = variables or []
        self.tags = tags or []
        self.metadata = metadata or {}
        
        # 解析模板中的變量
        if not self.variables:
            import re
            self.variables = re.findall(r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}', template)
    
    def render(self, variables: Dict[str, str]) -> str:
        """渲染模板，將變量替換為實際值。
        
        Args:
            variables: 變量字典，鍵為變量名，值為變量值
            
        Returns:
            渲染後的提示詞
            
        Raises:
            ValidationError: 如果缺少必要的變量
        """
        # 檢查是否提供了所有必要的變量
        missing_vars = [var for var in self.variables if var not in variables]
        if missing_vars:
            raise ValidationError(f"缺少必要的變量: {', '.join(missing_vars)}")
        
        # 渲染模板
        result = self.template
        for var_name, var_value in variables.items():
            result = result.replace(f"{{{var_name}}}", var_value)
        
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """將模板轉換為字典格式。
        
        Returns:
            模板的字典表示
        """
        return {
            'name': self.name,
            'template': self.template,
            'description': self.description,
            'variables': self.variables,
            'tags': self.tags,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptTemplate':
        """從字典創建模板實例。
        
        Args:
            data: 模板數據字典
            
        Returns:
            創建的模板實例
        """
        return cls(
            name=data['name'],
            template=data['template'],
            description=data.get('description', ''),
            variables=data.get('variables', []),
            tags=data.get('tags', []),
            metadata=data.get('metadata', {})
        )


class PromptService:
    """提示詞服務類，提供提示詞相關的業務邏輯。"""
    
    def __init__(self, prompts_path=None, templates_path=None):
        """初始化提示詞服務。"""
        # 獲取存儲服務
        self.storage = StorageServiceFactory.get_service()
        
        # 獲取AI服務
        self.ai_service = AIServiceFactory.get_service()
        
        # 提示詞數據存儲路徑
        self.prompts_path = prompts_path or "prompts"
        self.templates_path = templates_path or "prompt_templates"
        
        # 確保提示詞數據目錄存在
        self.storage.ensure_directory(self.prompts_path)
        self.storage.ensure_directory(self.templates_path)
        
        # 提示詞驗證器
        self.validator = Validator()
        
        # 載入提示詞模板
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, PromptTemplate]:
        """載入提示詞模板。
        
        Returns:
            提示詞模板字典，鍵為模板名稱，值為模板實例
        """
        templates = {}
        
        # 獲取模板目錄中的所有文件
        files = self.storage.list_files(self.templates_path)
        
        # 過濾出JSON文件
        template_files = [f for f in files if f.endswith('.json')]
        
        # 讀取每個模板文件
        for file_name in template_files:
            file_path = os.path.join(self.templates_path, file_name)
            try:
                data = json.loads(self.storage.read_file(file_path))
                template = PromptTemplate.from_dict(data)
                templates[template.name] = template
            except Exception as e:
                print(f"讀取模板文件 {file_path} 時出錯: {str(e)}")
        
        return templates
    
    def get_all_prompts(self) -> List[Prompt]:
        """獲取所有提示詞。
        
        Returns:
            提示詞列表
        """
        # 獲取提示詞目錄中的所有文件
        files = self.storage.list_files(self.prompts_path)
        
        # 過濾出JSON文件
        prompt_files = [f for f in files if f.endswith('.json')]
        
        # 讀取每個提示詞文件
        prompts = []
        for file_name in prompt_files:
            file_path = os.path.join(self.prompts_path, file_name)
            try:
                data = json.loads(self.storage.read_file(file_path))
                prompts.append(Prompt.from_dict(data))
            except Exception as e:
                print(f"讀取提示詞文件 {file_path} 時出錯: {str(e)}")
        
        return prompts
    
    def get_prompt(self, prompt_id: str) -> Prompt:
        """獲取指定ID的提示詞。
        
        Args:
            prompt_id: 提示詞ID
            
        Returns:
            提示詞實例
            
        Raises:
            NotFoundError: 如果找不到指定ID的提示詞
        """
        file_path = os.path.join(self.prompts_path, f"{prompt_id}.json")
        
        try:
            data = json.loads(self.storage.read_file(file_path))
            return Prompt.from_dict(data)
        except Exception as e:
            raise NotFoundError(f"找不到提示詞: {prompt_id}")
    
    def create_prompt(self, prompt_data: Dict[str, Any]) -> Prompt:
        """創建新提示詞。
        
        Args:
            prompt_data: 提示詞數據字典
            
        Returns:
            創建的提示詞實例
            
        Raises:
            ValidationError: 如果提示詞數據無效
        """
        # 驗證提示詞數據
        self._validate_prompt_data(prompt_data)
        
        # 創建提示詞實例
        prompt = Prompt.from_dict(prompt_data)
        
        # 生成提示詞ID
        prompt_id = self._generate_prompt_id()
        
        # 保存提示詞數據
        file_path = os.path.join(self.prompts_path, f"{prompt_id}.json")
        self.storage.write_file(file_path, json.dumps(prompt.to_dict(), ensure_ascii=False, indent=2))
        
        return prompt
    
    def update_prompt(self, prompt_id: str, prompt_data: Dict[str, Any]) -> Prompt:
        """更新提示詞。
        
        Args:
            prompt_id: 提示詞ID
            prompt_data: 提示詞數據字典
            
        Returns:
            更新後的提示詞實例
            
        Raises:
            NotFoundError: 如果找不到指定ID的提示詞
            ValidationError: 如果提示詞數據無效
        """
        # 檢查提示詞是否存在
        self.get_prompt(prompt_id)
        
        # 驗證提示詞數據
        self._validate_prompt_data(prompt_data)
        
        # 創建更新後的提示詞實例
        prompt = Prompt.from_dict(prompt_data)
        
        # 保存提示詞數據
        file_path = os.path.join(self.prompts_path, f"{prompt_id}.json")
        self.storage.write_file(file_path, json.dumps(prompt.to_dict(), ensure_ascii=False, indent=2))
        
        return prompt
    
    def delete_prompt(self, prompt_id: str) -> None:
        """刪除提示詞。
        
        Args:
            prompt_id: 提示詞ID
            
        Raises:
            NotFoundError: 如果找不到指定ID的提示詞
        """
        # 檢查提示詞是否存在
        self.get_prompt(prompt_id)
        
        # 刪除提示詞文件
        file_path = os.path.join(self.prompts_path, f"{prompt_id}.json")
        self.storage.delete_file(file_path)
    
    def get_all_templates(self) -> List[Dict[str, Any]]:
        """獲取所有提示詞模板。
        
        Returns:
            提示詞模板列表
        """
        return [template.to_dict() for template in self.templates.values()]
    
    def get_template(self, template_name: str) -> PromptTemplate:
        """獲取指定名稱的提示詞模板。
        
        Args:
            template_name: 模板名稱
            
        Returns:
            提示詞模板實例
            
        Raises:
            NotFoundError: 如果找不到指定名稱的提示詞模板
        """
        if template_name not in self.templates:
            raise NotFoundError(f"找不到提示詞模板: {template_name}")
        
        return self.templates[template_name]
    
    def create_template(self, template_data: Dict[str, Any]) -> PromptTemplate:
        """創建新提示詞模板。
        
        Args:
            template_data: 模板數據字典
            
        Returns:
            創建的提示詞模板實例
            
        Raises:
            ValidationError: 如果模板數據無效
        """
        # 驗證模板數據
        self._validate_template_data(template_data)
        
        # 創建模板實例
        template = PromptTemplate.from_dict(template_data)
        
        # 保存模板數據
        file_path = os.path.join(self.templates_path, f"{template.name}.json")
        self.storage.write_file(file_path, json.dumps(template.to_dict(), ensure_ascii=False, indent=2))
        
        # 更新模板緩存
        self.templates[template.name] = template
        
        return template
    
    def update_template(self, template_name: str, template_data: Dict[str, Any]) -> PromptTemplate:
        """更新提示詞模板。
        
        Args:
            template_name: 模板名稱
            template_data: 模板數據字典
            
        Returns:
            更新後的提示詞模板實例
            
        Raises:
            NotFoundError: 如果找不到指定名稱的提示詞模板
            ValidationError: 如果模板數據無效
        """
        # 檢查模板是否存在
        if template_name not in self.templates:
            raise NotFoundError(f"找不到提示詞模板: {template_name}")
        
        # 驗證模板數據
        self._validate_template_data(template_data)
        
        # 創建更新後的模板實例
        template = PromptTemplate.from_dict(template_data)
        
        # 保存模板數據
        file_path = os.path.join(self.templates_path, f"{template.name}.json")
        self.storage.write_file(file_path, json.dumps(template.to_dict(), ensure_ascii=False, indent=2))
        
        # 更新模板緩存
        self.templates[template.name] = template
        
        return template
    
    def delete_template(self, template_name: str) -> None:
        """刪除提示詞模板。
        
        Args:
            template_name: 模板名稱
            
        Raises:
            NotFoundError: 如果找不到指定名稱的提示詞模板
        """
        # 檢查模板是否存在
        if template_name not in self.templates:
            raise NotFoundError(f"找不到提示詞模板: {template_name}")
        
        # 刪除模板文件
        file_path = os.path.join(self.templates_path, f"{template_name}.json")
        self.storage.delete_file(file_path)
        
        # 更新模板緩存
        del self.templates[template_name]
    
    def render_template(self, template_name: str, variables: Dict[str, str]) -> str:
        """渲染提示詞模板。
        
        Args:
            template_name: 模板名稱
            variables: 變量字典，鍵為變量名，值為變量值
            
        Returns:
            渲染後的提示詞
            
        Raises:
            NotFoundError: 如果找不到指定名稱的提示詞模板
            ValidationError: 如果缺少必要的變量
        """
        # 獲取模板
        template = self.get_template(template_name)
        
        # 渲染模板
        return template.render(variables)
    
    def enhance_prompt(self, prompt: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """增強提示詞。
        
        Args:
            prompt: 原始提示詞
            options: 增強選項
            
        Returns:
            增強結果，包含增強後的提示詞和分析信息
            
        Raises:
            ServiceError: 如果增強提示詞時出錯
        """
        options = options or {}
        
        try:
            # 構建增強提示詞
            enhancement_prompt = f"""請分析並增強以下提示詞，使其更加清晰、具體和有效：

原始提示詞：
{prompt}

請提供以下內容：
1. 增強後的提示詞
2. 分析（清晰度、上下文、具體性、結構）
3. 改進建議

請以JSON格式返回結果，包含以下字段：
- enhanced_prompt: 增強後的提示詞
- analysis: 包含各項分析得分的對象
- suggestions: 改進建議列表
"""
            
            # 調用AI服務
            response = self.ai_service.generate_text(enhancement_prompt)
            
            # 解析JSON響應
            try:
                result = json.loads(response)
            except json.JSONDecodeError:
                # 如果無法解析JSON，嘗試從文本中提取JSON部分
                import re
                json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(1))
                else:
                    # 如果仍然無法提取JSON，則創建一個基本結果
                    result = {
                        "enhanced_prompt": response,
                        "analysis": {
                            "clarity_score": 0.0,
                            "context_score": 0.0,
                            "specificity_score": 0.0,
                            "structure_score": 0.0,
                            "overall_score": 0.0
                        },
                        "suggestions": ["無法解析AI回應為JSON格式"]
                    }
            
            # 如果不需要詳細分析，則移除分析部分
            if not options.get('detailed_analysis', True):
                result.pop('analysis', None)
            
            return result
        except Exception as e:
            raise ServiceError("ai", f"增強提示詞時出錯: {str(e)}")
    
    def _generate_prompt_id(self) -> str:
        """生成唯一的提示詞ID。
        
        Returns:
            提示詞ID
        """
        import uuid
        return str(uuid.uuid4())
    
    def _validate_prompt_data(self, data: Dict[str, Any]) -> None:
        """驗證提示詞數據。
        
        Args:
            data: 提示詞數據字典
            
        Raises:
            ValidationError: 如果提示詞數據無效
        """
        # 檢查必填字段
        required_fields = ['content', 'type']
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"缺少必填字段: {field}")
        
        # 驗證標籤列表
        if 'tags' in data and data['tags'] is not None:
            if not isinstance(data['tags'], list):
                raise ValidationError("標籤必須是列表")
        
        # 驗證元數據字典
        if 'metadata' in data and data['metadata'] is not None:
            if not isinstance(data['metadata'], dict):
                raise ValidationError("元數據必須是字典")
    
    def _validate_template_data(self, data: Dict[str, Any]) -> None:
        """驗證模板數據。
        
        Args:
            data: 模板數據字典
            
        Raises:
            ValidationError: 如果模板數據無效
        """
        # 檢查必填字段
        required_fields = ['name', 'template']
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"缺少必填字段: {field}")
        
        # 驗證變量列表
        if 'variables' in data and data['variables'] is not None:
            if not isinstance(data['variables'], list):
                raise ValidationError("變量必須是列表")
        
        # 驗證標籤列表
        if 'tags' in data and data['tags'] is not None:
            if not isinstance(data['tags'], list):
                raise ValidationError("標籤必須是列表")
        
        # 驗證元數據字典
        if 'metadata' in data and data['metadata'] is not None:
            if not isinstance(data['metadata'], dict):
                raise ValidationError("元數據必須是字典")


class PromptManager:
    """提示詞管理器類，提供提示詞管理功能。"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """創建提示詞管理器單例。"""
        if cls._instance is None:
            cls._instance = super(PromptManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, prompts_path=None):
        """初始化提示詞管理器。"""
        if self._initialized:
            return
        
        self.prompt_service = PromptService(prompts_path=prompts_path)
        self.enhancer = None
        self._initialized = True
    
    def get_all_prompts(self) -> List[Prompt]:
        """獲取所有提示詞。
        
        Returns:
            提示詞列表
        """
        return self.prompt_service.get_all_prompts()
    
    def get_prompt(self, prompt_id: str) -> Prompt:
        """獲取指定ID的提示詞。
        
        Args:
            prompt_id: 提示詞ID
            
        Returns:
            提示詞實例
            
        Raises:
            NotFoundError: 如果找不到指定ID的提示詞
        """
        return self.prompt_service.get_prompt(prompt_id)
    
    def create_prompt(self, prompt_data: Dict[str, Any]) -> Prompt:
        """創建新提示詞。
        
        Args:
            prompt_data: 提示詞數據字典
            
        Returns:
            創建的提示詞實例
            
        Raises:
            ValidationError: 如果提示詞數據無效
        """
        return self.prompt_service.create_prompt(prompt_data)
    
    def update_prompt(self, prompt_id: str, prompt_data: Dict[str, Any]) -> Prompt:
        """更新提示詞。
        
        Args:
            prompt_id: 提示詞ID
            prompt_data: 提示詞數據字典
            
        Returns:
            更新後的提示詞實例
            
        Raises:
            NotFoundError: 如果找不到指定ID的提示詞
            ValidationError: 如果提示詞數據無效
        """
        return self.prompt_service.update_prompt(prompt_id, prompt_data)
    
    def delete_prompt(self, prompt_id: str) -> None:
        """刪除提示詞。
        
        Args:
            prompt_id: 提示詞ID
            
        Raises:
            NotFoundError: 如果找不到指定ID的提示詞
        """
        self.prompt_service.delete_prompt(prompt_id)
    
    def get_all_templates(self) -> List[Dict[str, Any]]:
        """獲取所有提示詞模板。
        
        Returns:
            提示詞模板列表
        """
        return self.prompt_service.get_all_templates()
    
    def get_template(self, template_name: str) -> PromptTemplate:
        """獲取指定名稱的提示詞模板。
        
        Args:
            template_name: 模板名稱
            
        Returns:
            提示詞模板實例
            
        Raises:
            NotFoundError: 如果找不到指定名稱的提示詞模板
        """
        return self.prompt_service.get_template(template_name)
    
    def create_template(self, template_data: Dict[str, Any]) -> PromptTemplate:
        """創建新提示詞模板。
        
        Args:
            template_data: 模板數據字典
            
        Returns:
            創建的提示詞模板實例
            
        Raises:
            ValidationError: 如果模板數據無效
        """
        return self.prompt_service.create_template(template_data)
    
    def update_template(self, template_name: str, template_data: Dict[str, Any]) -> PromptTemplate:
        """更新提示詞模板。
        
        Args:
            template_name: 模板名稱
            template_data: 模板數據字典
            
        Returns:
            更新後的提示詞模板實例
            
        Raises:
            NotFoundError: 如果找不到指定名稱的提示詞模板
            ValidationError: 如果模板數據無效
        """
        return self.prompt_service.update_template(template_name, template_data)
    
    def delete_template(self, template_name: str) -> None:
        """刪除提示詞模板。
        
        Args:
            template_name: 模板名稱
            
        Raises:
            NotFoundError: 如果找不到指定名稱的提示詞模板
        """
        self.prompt_service.delete_template(template_name)
    
    def render_template(self, template_name: str, variables: Dict[str, str]) -> str:
        """渲染提示詞模板。
        
        Args:
            template_name: 模板名稱
            variables: 變量字典，鍵為變量名，值為變量值
            
        Returns:
            渲染後的提示詞
            
        Raises:
            NotFoundError: 如果找不到指定名稱的提示詞模板
            ValidationError: 如果缺少必要的變量
        """
        return self.prompt_service.render_template(template_name, variables)
    
    def enhance_prompt(self, prompt: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """增強提示詞。
        
        Args:
            prompt: 原始提示詞
            options: 增強選項
            
        Returns:
            增強結果，包含增強後的提示詞和分析信息
            
        Raises:
            ServiceError: 如果增強提示詞時出錯
        """
        return self.prompt_service.enhance_prompt(prompt, options)

    def set_enhancer(self, enhancer):
        """設置提示詞增強器。
        
        Args:
            enhancer: 提示詞增強器實例
        """
        self.enhancer = enhancer
        # 如果提示詞增強器不為空，則將其AI服務設置為提示詞服務的AI服務
        if self.enhancer:
            self.prompt_service.ai_service = self.enhancer.ai_service

class PromptEnhancer:
    """提示詞增強器類，提供提示詞增強功能。"""
    
    def __init__(self, ai_service):
        """初始化提示詞增強器。
        
        Args:
            ai_service: AI服務實例
        """
        self.ai_service = ai_service
    
    def enhance(self, prompt: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """增強提示詞。
        
        Args:
            prompt: 原始提示詞
            options: 增強選項
            
        Returns:
            增強結果，包含增強後的提示詞和分析信息
            
        Raises:
            ServiceError: 如果增強提示詞時出錯
        """
        try:
            # 創建一個臨時的 PromptService 實例
            prompt_service = PromptService()
            # 替換 AI 服務
            prompt_service.ai_service = self.ai_service
            return prompt_service.enhance_prompt(prompt, options)
        except Exception as e:
            raise ServiceError("ai", f"增強提示詞時出錯: {str(e)}")