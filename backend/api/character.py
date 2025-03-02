"""角色API模組，提供角色相關的HTTP接口。"""

from flask import Blueprint, request, jsonify
from ..core.character import CharacterManager
from ..utils.error import ValidationError, NotFoundError, handle_error

# 創建藍圖
character_bp = Blueprint('character', __name__)
character_manager = CharacterManager()

@character_bp.route('/', methods=['GET'])
def get_all_characters():
    """獲取所有角色。
    
    返回格式：
    {
        "status": "success",
        "data": {
            "characters": [
                {
                    "name": "角色名稱",
                    "personality": "角色性格",
                    "dialogue_style": "對話風格",
                    "image": "圖片路徑",
                    ...
                }
            ]
        }
    }
    """
    try:
        characters = character_manager.get_all_characters()
        return jsonify({
            'status': 'success',
            'data': {
                'characters': [char.to_dict() for char in characters]
            }
        })
    except Exception as e:
        return handle_error(e, '獲取角色列表時發生錯誤')

@character_bp.route('/<name>', methods=['GET'])
def get_character(name):
    """獲取指定名稱的角色。
    
    路徑參數：
    - name: 角色名稱
    
    返回格式：
    {
        "status": "success",
        "data": {
            "character": {
                "name": "角色名稱",
                "personality": "角色性格",
                "dialogue_style": "對話風格",
                "image": "圖片路徑",
                ...
            }
        }
    }
    """
    try:
        character = character_manager.get_character(name)
        return jsonify({
            'status': 'success',
            'data': {
                'character': character.to_dict()
            }
        })
    except NotFoundError as e:
        return handle_error(e, f'找不到角色: {name}')
    except Exception as e:
        return handle_error(e, f'獲取角色 {name} 時發生錯誤')

@character_bp.route('/', methods=['POST'])
def create_character():
    """創建新角色。
    
    請求體格式：
    {
        "name": "角色名稱",
        "personality": "角色性格",
        "dialogue_style": "對話風格",
        "image": "圖片路徑",  // 可選
        "background": "背景故事",  // 可選
        "traits": ["特質1", "特質2"],  // 可選
        "relationships": {"角色名稱": 關係值},  // 可選
        "orientation": "性取向"  // 可選
    }
    
    返回格式：
    {
        "status": "success",
        "data": {
            "character": {
                "name": "角色名稱",
                "personality": "角色性格",
                "dialogue_style": "對話風格",
                "image": "圖片路徑",
                ...
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
        
        character = character_manager.create_character(data)
        return jsonify({
            'status': 'success',
            'data': {
                'character': character.to_dict()
            }
        }), 201
    except ValidationError as e:
        return handle_error(e, '創建角色時驗證失敗')
    except Exception as e:
        return handle_error(e, '創建角色時發生錯誤')

@character_bp.route('/<name>', methods=['PUT'])
def update_character(name):
    """更新角色。
    
    路徑參數：
    - name: 角色名稱
    
    請求體格式：
    {
        "name": "角色名稱",
        "personality": "角色性格",
        "dialogue_style": "對話風格",
        "image": "圖片路徑",  // 可選
        "background": "背景故事",  // 可選
        "traits": ["特質1", "特質2"],  // 可選
        "relationships": {"角色名稱": 關係值},  // 可選
        "orientation": "性取向"  // 可選
    }
    
    返回格式：
    {
        "status": "success",
        "data": {
            "character": {
                "name": "角色名稱",
                "personality": "角色性格",
                "dialogue_style": "對話風格",
                "image": "圖片路徑",
                ...
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
        
        character = character_manager.update_character(name, data)
        return jsonify({
            'status': 'success',
            'data': {
                'character': character.to_dict()
            }
        })
    except NotFoundError as e:
        return handle_error(e, f'找不到角色: {name}')
    except ValidationError as e:
        return handle_error(e, '更新角色時驗證失敗')
    except Exception as e:
        return handle_error(e, f'更新角色 {name} 時發生錯誤')

@character_bp.route('/<name>', methods=['DELETE'])
def delete_character(name):
    """刪除角色。
    
    路徑參數：
    - name: 角色名稱
    
    返回格式：
    {
        "status": "success",
        "message": "角色已刪除"
    }
    """
    try:
        character_manager.delete_character(name)
        return jsonify({
            'status': 'success',
            'message': f'角色 {name} 已刪除'
        })
    except NotFoundError as e:
        return handle_error(e, f'找不到角色: {name}')
    except Exception as e:
        return handle_error(e, f'刪除角色 {name} 時發生錯誤')

@character_bp.route('/default', methods=['POST'])
def load_default_characters():
    """載入預設角色。
    
    返回格式：
    {
        "status": "success",
        "data": {
            "characters": [
                {
                    "name": "角色名稱",
                    "personality": "角色性格",
                    "dialogue_style": "對話風格",
                    "image": "圖片路徑",
                    ...
                }
            ]
        }
    }
    """
    try:
        characters = character_manager.load_default_characters()
        return jsonify({
            'status': 'success',
            'data': {
                'characters': [char.to_dict() for char in characters]
            }
        })
    except Exception as e:
        return handle_error(e, '載入預設角色時發生錯誤')