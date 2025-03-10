"""角色API模組，提供角色相關的HTTP接口。"""

from flask import Blueprint, request, jsonify
from ..core.character import CharacterManager
from ..utils.error import ValidationError, NotFoundError, handle_error

# 創建藍圖
character_bp = Blueprint('character', __name__)
character_manager = CharacterManager()

@character_bp.route('/', methods=['GET'])
def get_all_characters():
    """獲取所有角色。"""
    try:
        # 獲取所有角色
        characters = character_manager.get_all_characters()
        
        # 轉換為以ID為鍵的字典格式
        character_dict = {char.id: char.to_dict() for char in characters}
        
        return jsonify({
            'status': 'success',
            'data': {
                'characters': character_dict
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': '獲取角色列表時發生錯誤', 'details': str(e)}), 500

@character_bp.route('/<character_id>', methods=['GET'])
def get_character(character_id):
    """獲取指定ID的角色。"""
    try:
        character = character_manager.get_character(character_id)
        return jsonify({
            'status': 'success',
            'data': {
                'character': character.to_dict()
            }
        })
    except NotFoundError as e:
        return jsonify(handle_error(e))
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'獲取角色 {character_id} 時發生錯誤', 'details': str(e)}), 500

@character_bp.route('/', methods=['POST'])
def create_character():
    """創建新角色。"""
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
        return jsonify(handle_error(e))
    except Exception as e:
        return jsonify({'status': 'error', 'message': '創建角色時發生錯誤', 'details': str(e)}), 500

@character_bp.route('/<character_id>', methods=['PUT'])
def update_character(character_id):
    """更新角色。"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': '缺少請求體'
            }), 400
        
        character = character_manager.update_character(character_id, data)
        return jsonify({
            'status': 'success',
            'data': {
                'character': character.to_dict()
            }
        })
    except NotFoundError as e:
        return jsonify(handle_error(e))
    except ValidationError as e:
        return jsonify(handle_error(e))
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'更新角色 {character_id} 時發生錯誤', 'details': str(e)}), 500

@character_bp.route('/<character_id>', methods=['DELETE'])
def delete_character(character_id):
    """刪除角色。"""
    try:
        character_manager.delete_character(character_id)
        return jsonify({
            'status': 'success',
            'message': f'角色 {character_id} 已刪除'
        })
    except NotFoundError as e:
        return jsonify(handle_error(e))
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'刪除角色 {character_id} 時發生錯誤', 'details': str(e)}), 500

@character_bp.route('/default', methods=['POST'])
def load_default_characters():
    """載入預設角色。"""
    try:
        characters = character_manager.load_default_characters()
        return jsonify({
            'status': 'success',
            'data': {
                'characters': [char.to_dict() for char in characters]
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': '載入預設角色時發生錯誤', 'details': str(e)}), 500