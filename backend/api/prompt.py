"""提示詞API模組，提供提示詞相關的HTTP接口。"""

from flask import Blueprint, request, jsonify
from ..core.prompt import PromptManager
from ..utils.error import ValidationError, NotFoundError, ServiceError, handle_error

# 創建藍圖
prompt_bp = Blueprint('prompt', __name__)
prompt_manager = PromptManager()

@prompt_bp.route('/', methods=['GET'])
def get_all_prompts():
    """獲取所有提示詞。"""
    try:
        prompts = prompt_manager.get_all_prompts()
        return jsonify({
            'status': 'success',
            'data': {
                'prompts': [prompt.to_dict() for prompt in prompts]
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': '獲取提示詞列表時發生錯誤', 'details': str(e)}), 500

@prompt_bp.route('/<prompt_id>', methods=['GET'])
def get_prompt(prompt_id):
    """獲取指定ID的提示詞。"""
    try:
        prompt = prompt_manager.get_prompt(prompt_id)
        return jsonify({
            'status': 'success',
            'data': {
                'prompt': prompt.to_dict()
            }
        })
    except NotFoundError as e:
        return jsonify(handle_error(e))
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'獲取提示詞 {prompt_id} 時發生錯誤', 'details': str(e)}), 500

@prompt_bp.route('/', methods=['POST'])
def create_prompt():
    """創建新提示詞。"""
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
        return jsonify(handle_error(e))
    except Exception as e:
        return jsonify({'status': 'error', 'message': '創建提示詞時發生錯誤', 'details': str(e)}), 500

@prompt_bp.route('/<prompt_id>', methods=['PUT'])
def update_prompt(prompt_id):
    """更新提示詞。"""
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
        return jsonify(handle_error(e))
    except ValidationError as e:
        return jsonify(handle_error(e))
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'更新提示詞 {prompt_id} 時發生錯誤', 'details': str(e)}), 500

@prompt_bp.route('/<prompt_id>', methods=['DELETE'])
def delete_prompt(prompt_id):
    """刪除提示詞。"""
    try:
        prompt_manager.delete_prompt(prompt_id)
        return jsonify({
            'status': 'success',
            'message': f'提示詞 {prompt_id} 已刪除'
        })
    except NotFoundError as e:
        return jsonify(handle_error(e))
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'刪除提示詞 {prompt_id} 時發生錯誤', 'details': str(e)}), 500

@prompt_bp.route('/templates', methods=['GET'])
def get_all_templates():
    """獲取所有提示詞模板。"""
    try:
        templates = prompt_manager.get_all_templates()
        return jsonify({
            'status': 'success',
            'data': {
                'templates': templates
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': '獲取提示詞模板列表時發生錯誤', 'details': str(e)}), 500

@prompt_bp.route('/templates/<template_name>', methods=['GET'])
def get_template(template_name):
    """獲取指定名稱的提示詞模板。"""
    try:
        template = prompt_manager.get_template(template_name)
        return jsonify({
            'status': 'success',
            'data': {
                'template': template.to_dict()
            }
        })
    except NotFoundError as e:
        return jsonify(handle_error(e))
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'獲取提示詞模板 {template_name} 時發生錯誤', 'details': str(e)}), 500

@prompt_bp.route('/templates', methods=['POST'])
def create_template():
    """創建新提示詞模板。"""
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
        return jsonify(handle_error(e))
    except Exception as e:
        return jsonify({'status': 'error', 'message': '創建提示詞模板時發生錯誤', 'details': str(e)}), 500

@prompt_bp.route('/templates/<template_name>', methods=['PUT'])
def update_template(template_name):
    """更新提示詞模板。"""
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
        return jsonify(handle_error(e))
    except ValidationError as e:
        return jsonify(handle_error(e))
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'更新提示詞模板 {template_name} 時發生錯誤', 'details': str(e)}), 500

@prompt_bp.route('/templates/<template_name>', methods=['DELETE'])
def delete_template(template_name):
    """刪除提示詞模板。"""
    try:
        prompt_manager.delete_template(template_name)
        return jsonify({
            'status': 'success',
            'message': f'提示詞模板 {template_name} 已刪除'
        })
    except NotFoundError as e:
        return jsonify(handle_error(e))
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'刪除提示詞模板 {template_name} 時發生錯誤', 'details': str(e)}), 500

@prompt_bp.route('/templates/<template_name>/render', methods=['POST'])
def render_template(template_name):
    """渲染提示詞模板。"""
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
        return jsonify(handle_error(e))
    except ValidationError as e:
        return jsonify(handle_error(e))
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'渲染提示詞模板 {template_name} 時發生錯誤', 'details': str(e)}), 500

@prompt_bp.route('/enhance', methods=['POST'])
def enhance_prompt():
    """增強提示詞。"""
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
        return jsonify(handle_error(e))
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'處理提示詞時發生錯誤', 'details': str(e)}), 500