"""處理提示詞相關的路由。"""

from flask import Blueprint, request, jsonify
from ..utils.prompt_manager import PromptManager

# 創建藍圖
prompt_bp = Blueprint('prompt', __name__)
prompt_manager = PromptManager()

@prompt_bp.route('/enhance', methods=['POST'])
def enhance_prompt():
    """處理提示詞增強請求。
    
    請求體格式：
    {
        "prompt": "要增強的提示詞",
        "options": {  # 可選
            "detailed_analysis": true  # 是否返回詳細分析
        }
    }
    
    返回格式：
    {
        "status": "success",
        "data": {
            "enhanced_prompt": "增強後的提示詞",
            "analysis": {  # 如果detailed_analysis為true
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
        detailed = options.get('detailed_analysis', False)
        
        # 使用提示詞管理器增強提示詞
        result = prompt_manager.enhance_prompt(prompt)
        
        # 如果不需要詳細分析，則只返回增強後的提示詞
        if not detailed:
            result.pop('analysis', None)
        
        return jsonify({
            'status': 'success',
            'data': result
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'處理提示詞時發生錯誤: {str(e)}'
        }), 500

@prompt_bp.route('/templates', methods=['GET'])
def list_templates():
    """獲取所有可用的提示詞模板。
    
    返回格式：
    {
        "status": "success",
        "data": {
            "templates": [
                {
                    "name": "模板名稱",
                    "description": "模板描述",
                    "metadata": {}
                }
            ]
        }
    }
    """
    try:
        templates = prompt_manager.list_templates()
        return jsonify({
            'status': 'success',
            'data': {
                'templates': templates
            }
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'獲取模板列表時發生錯誤: {str(e)}'
        }), 500