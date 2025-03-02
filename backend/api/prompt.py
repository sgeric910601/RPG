"""提示詞API模組，提供提示詞相關的HTTP接口。"""

from flask import Blueprint, request, jsonify
from ..core.prompt import PromptManager
from ..utils.error import ValidationError, NotFoundError, ServiceError, handle_error

# 創建藍圖
prompt_bp = Blueprint('prompt', __name__)
prompt_manager = PromptManager()

@prompt_bp.route('/', methods=['GET'])
def get_all_prompts():
    """獲取所有提示詞。
    
    返回格式：
    {
        "status": "success",
        "data": {
            "prompts": [
                {
                    "content": "提示詞內容",
                    "type": "提示詞類型",
                    "tags": ["標籤1", "標籤2"],
                    "metadata": {}
                }
            ]
        }
    }
    """
    try:
        prompts = prompt_manager.get_all_prompts()
        return jsonify({
            'status': 'success',
            'data': {
                'prompts': [prompt.to_dict() for prompt in prompts]
            }
        })
    except Exception as e:
        return handle_error(e, '獲取提示詞列表時發生錯誤')

@prompt_bp.route('/<prompt_id>', methods=['GET'])
def get_prompt(prompt_id):
    """獲取指定ID的提示詞。
    
    路徑參數：
    - prompt_id: 提示詞ID
    
    返回格式：
    {
        "status": "success",
        "data": {
            "prompt": {
                "content": "提示詞內容",
                "type": "提示詞類型",
                "tags": ["標籤1", "標籤2"],
                "metadata": {}
            }
        }
    }
    """
    try:
        prompt = prompt_manager.get_prompt(prompt_id)
        return jsonify({
            'status': 'success',
            'data': {
                'prompt': prompt.to_dict()
            }
        })
    except NotFoundError as e:
        return handle_error(e, f'找不到提示詞: {prompt_id}')
    except Exception as e:
        return handle_error(e, f'獲取提示詞 {prompt_id} 時發生錯誤')

@prompt_bp.route('/', methods=['POST'])
def create_prompt():
    """創建新提示詞。
    
    請求體格式：
    {
        "content": "提示詞內容",
        "type": "提示詞類型",
        "tags": ["標籤1", "標籤2"],  // 可選
        "metadata": {}  // 可選
    }
    
    返回格式：
    {
        "status": "success",
        "data": {
            "prompt": {
                "content": "提示詞內容",
                "type": "提示詞類型",
                "tags": ["標籤1", "標籤2"],
                "metadata": {}
            }
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': '缺少請求體'
            }), 400
        
        prompt = prompt_manager.create_prompt(data)
        return jsonify({
            'status': 'success',
            'data': {
                'prompt': prompt.to_dict()
            }
        }), 201
    except ValidationError as e:
        return handle_error(e, '創建提示詞時驗證失敗')
    except Exception as e:
        return handle_error(e, '創建提示詞時發生錯誤')

@prompt_bp.route('/<prompt_id>', methods=['PUT'])
def update_prompt(prompt_id):
    """更新提示詞。
    
    路徑參數：
    - prompt_id: 提示詞ID
    
    請求體格式：
    {
        "content": "提示詞內容",
        "type": "提示詞類型",
        "tags": ["標籤1", "標籤2"],  // 可選
        "metadata": {}  // 可選
    }
    
    返回格式：
    {
        "status": "success",
        "data": {
            "prompt": {
                "content": "提示詞內容",
                "type": "提示詞類型",
                "tags": ["標籤1", "標籤2"],
                "metadata": {}
            }
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': '缺少請求體'
            }), 400
        
        prompt = prompt_manager.update_prompt(prompt_id, data)
        return jsonify({
            'status': 'success',
            'data': {
                'prompt': prompt.to_dict()
            }
        })
    except NotFoundError as e:
        return handle_error(e, f'找不到提示詞: {prompt_id}')
    except ValidationError as e:
        return handle_error(e, '更新提示詞時驗證失敗')
    except Exception as e:
        return handle_error(e, f'更新提示詞 {prompt_id} 時發生錯誤')

@prompt_bp.route('/<prompt_id>', methods=['DELETE'])
def delete_prompt(prompt_id):
    """刪除提示詞。
    
    路徑參數：
    - prompt_id: 提示詞ID
    
    返回格式：
    {
        "status": "success",
        "message": "提示詞已刪除"
    }
    """
    try:
        prompt_manager.delete_prompt(prompt_id)
        return jsonify({
            'status': 'success',
            'message': f'提示詞 {prompt_id} 已刪除'
        })
    except NotFoundError as e:
        return handle_error(e, f'找不到提示詞: {prompt_id}')
    except Exception as e:
        return handle_error(e, f'刪除提示詞 {prompt_id} 時發生錯誤')

@prompt_bp.route('/templates', methods=['GET'])
def get_all_templates():
    """獲取所有提示詞模板。
    
    返回格式：
    {
        "status": "success",
        "data": {
            "templates": [
                {
                    "name": "模板名稱",
                    "template": "模板內容",
                    "description": "模板描述",
                    "variables": ["變量1", "變量2"],
                    "tags": ["標籤1", "標籤2"],
                    "metadata": {}
                }
            ]
        }
    }
    """
    try:
        templates = prompt_manager.get_all_templates()
        return jsonify({
            'status': 'success',
            'data': {
                'templates': templates
            }
        })
    except Exception as e:
        return handle_error(e, '獲取提示詞模板列表時發生錯誤')

@prompt_bp.route('/templates/<template_name>', methods=['GET'])
def get_template(template_name):
    """獲取指定名稱的提示詞模板。
    
    路徑參數：
    - template_name: 模板名稱
    
    返回格式：
    {
        "status": "success",
        "data": {
            "template": {
                "name": "模板名稱",
                "template": "模板內容",
                "description": "模板描述",
                "variables": ["變量1", "變量2"],
                "tags": ["標籤1", "標籤2"],
                "metadata": {}
            }
        }
    }
    """
    try:
        template = prompt_manager.get_template(template_name)
        return jsonify({
            'status': 'success',
            'data': {
                'template': template.to_dict()
            }
        })
    except NotFoundError as e:
        return handle_error(e, f'找不到提示詞模板: {template_name}')
    except Exception as e:
        return handle_error(e, f'獲取提示詞模板 {template_name} 時發生錯誤')

@prompt_bp.route('/templates', methods=['POST'])
def create_template():
    """創建新提示詞模板。
    
    請求體格式：
    {
        "name": "模板名稱",
        "template": "模板內容",
        "description": "模板描述",  // 可選
        "variables": ["變量1", "變量2"],  // 可選
        "tags": ["標籤1", "標籤2"],  // 可選
        "metadata": {}  // 可選
    }
    
    返回格式：
    {
        "status": "success",
        "data": {
            "template": {
                "name": "模板名稱",
                "template": "模板內容",
                "description": "模板描述",
                "variables": ["變量1", "變量2"],
                "tags": ["標籤1", "標籤2"],
                "metadata": {}
            }
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': '缺少請求體'
            }), 400
        
        template = prompt_manager.create_template(data)
        return jsonify({
            'status': 'success',
            'data': {
                'template': template.to_dict()
            }
        }), 201
    except ValidationError as e:
        return handle_error(e, '創建提示詞模板時驗證失敗')
    except Exception as e:
        return handle_error(e, '創建提示詞模板時發生錯誤')

@prompt_bp.route('/templates/<template_name>', methods=['PUT'])
def update_template(template_name):
    """更新提示詞模板。
    
    路徑參數：
    - template_name: 模板名稱
    
    請求體格式：
    {
        "name": "模板名稱",
        "template": "模板內容",
        "description": "模板描述",  // 可選
        "variables": ["變量1", "變量2"],  // 可選
        "tags": ["標籤1", "標籤2"],  // 可選
        "metadata": {}  // 可選
    }
    
    返回格式：
    {
        "status": "success",
        "data": {
            "template": {
                "name": "模板名稱",
                "template": "模板內容",
                "description": "模板描述",
                "variables": ["變量1", "變量2"],
                "tags": ["標籤1", "標籤2"],
                "metadata": {}
            }
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': '缺少請求體'
            }), 400
        
        template = prompt_manager.update_template(template_name, data)
        return jsonify({
            'status': 'success',
            'data': {
                'template': template.to_dict()
            }
        })
    except NotFoundError as e:
        return handle_error(e, f'找不到提示詞模板: {template_name}')
    except ValidationError as e:
        return handle_error(e, '更新提示詞模板時驗證失敗')
    except Exception as e:
        return handle_error(e, f'更新提示詞模板 {template_name} 時發生錯誤')

@prompt_bp.route('/templates/<template_name>', methods=['DELETE'])
def delete_template(template_name):
    """刪除提示詞模板。
    
    路徑參數：
    - template_name: 模板名稱
    
    返回格式：
    {
        "status": "success",
        "message": "提示詞模板已刪除"
    }
    """
    try:
        prompt_manager.delete_template(template_name)
        return jsonify({
            'status': 'success',
            'message': f'提示詞模板 {template_name} 已刪除'
        })
    except NotFoundError as e:
        return handle_error(e, f'找不到提示詞模板: {template_name}')
    except Exception as e:
        return handle_error(e, f'刪除提示詞模板 {template_name} 時發生錯誤')

@prompt_bp.route('/templates/<template_name>/render', methods=['POST'])
def render_template(template_name):
    """渲染提示詞模板。
    
    路徑參數：
    - template_name: 模板名稱
    
    請求體格式：
    {
        "variables": {
            "變量1": "值1",
            "變量2": "值2"
        }
    }
    
    返回格式：
    {
        "status": "success",
        "data": {
            "rendered_prompt": "渲染後的提示詞"
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'variables' not in data:
            return jsonify({
                'status': 'error',
                'message': '缺少變量數據'
            }), 400
        
        rendered_prompt = prompt_manager.render_template(template_name, data['variables'])
        return jsonify({
            'status': 'success',
            'data': {
                'rendered_prompt': rendered_prompt
            }
        })
    except NotFoundError as e:
        return handle_error(e, f'找不到提示詞模板: {template_name}')
    except ValidationError as e:
        return handle_error(e, '渲染提示詞模板時驗證失敗')
    except Exception as e:
        return handle_error(e, f'渲染提示詞模板 {template_name} 時發生錯誤')

@prompt_bp.route('/enhance', methods=['POST'])
def enhance_prompt():
    """增強提示詞。
    
    請求體格式：
    {
        "prompt": "要增強的提示詞",
        "options": {  // 可選
            "detailed_analysis": true  // 是否返回詳細分析
        }
    }
    
    返回格式：
    {
        "status": "success",
        "data": {
            "enhanced_prompt": "增強後的提示詞",
            "analysis": {  // 如果detailed_analysis為true
                "clarity_score": 0.8,
                "context_score": 0.7,
                "specificity_score": 0.9,
                "structure_score": 0.85,
                "overall_score": 0.81
            },
            "suggestions": [
                "建議1",
                "建議2"
            ]
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'prompt' not in data:
            return jsonify({
                'status': 'error',
                'message': '缺少必要的提示詞參數'
            }), 400
            
        prompt = data['prompt']
        options = data.get('options', {})
        
        # 使用提示詞管理器增強提示詞
        result = prompt_manager.enhance_prompt(prompt, options)
        
        return jsonify({
            'status': 'success',
            'data': result
        })
    
    except ServiceError as e:
        return handle_error(e, '增強提示詞時發生服務錯誤')
    except Exception as e:
        return handle_error(e, f'處理提示詞時發生錯誤: {str(e)}')