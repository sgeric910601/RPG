"""故事API模組，提供故事相關的HTTP接口。"""

from flask import Blueprint, request, jsonify
from ..core.story import StoryManager
from ..utils.error import ValidationError, NotFoundError, handle_error

# 創建藍圖
story_bp = Blueprint('story', __name__)
story_manager = StoryManager()

@story_bp.route('/', methods=['GET'])
def get_all_stories():
    """獲取所有故事的摘要信息。
    
    返回格式：
    {
        "status": "success",
        "data": {
            "stories": [
                {
                    "id": "故事ID",
                    "title": "故事標題",
                    "world_type": "世界類型",
                    "setting": "設定",
                    "character_count": 角色數量,
                    "created_at": "創建時間",
                    "updated_at": "更新時間"
                }
            ]
        }
    }
    """
    try:
        stories = story_manager.get_all_stories()
        return jsonify({
            'status': 'success',
            'data': {
                'stories': stories
            }
        })
    except Exception as e:
        return handle_error(e, '獲取故事列表時發生錯誤')

@story_bp.route('/<story_id>', methods=['GET'])
def get_story(story_id):
    """獲取指定ID的故事。
    
    路徑參數：
    - story_id: 故事ID
    
    返回格式：
    {
        "status": "success",
        "data": {
            "story": {
                "id": "故事ID",
                "title": "故事標題",
                "world_type": "世界類型",
                "setting": "設定",
                "background": "背景",
                "characters": {
                    "角色名稱": {
                        "name": "角色名稱",
                        "personality": "角色性格",
                        ...
                    }
                },
                "current_scene": "當前場景",
                "adult_content": true/false,
                "themes": ["主題1", "主題2"],
                "custom_rules": {"規則名稱": "規則內容"},
                "events": [{"type": "事件類型", "description": "事件描述", ...}],
                "created_at": "創建時間",
                "updated_at": "更新時間"
            }
        }
    }
    """
    try:
        story = story_manager.get_story(story_id)
        return jsonify({
            'status': 'success',
            'data': {
                'story': story
            }
        })
    except NotFoundError as e:
        return handle_error(e, f'找不到故事: {story_id}')
    except Exception as e:
        return handle_error(e, f'獲取故事 {story_id} 時發生錯誤')

@story_bp.route('/', methods=['POST'])
def create_story():
    """創建新故事。
    
    請求體格式：
    {
        "title": "故事標題",
        "world_type": "世界類型",  // fantasy, scifi, modern, custom
        "setting": "設定",
        "background": "背景",
        "current_scene": "當前場景",
        "adult_content": true/false,
        "themes": ["主題1", "主題2"],  // 可選
        "custom_rules": {"規則名稱": "規則內容"},  // 可選
        "characters": {  // 可選
            "角色名稱": {
                "name": "角色名稱",
                "personality": "角色性格",
                ...
            }
        }
    }
    
    返回格式：
    {
        "status": "success",
        "data": {
            "story": {
                "id": "故事ID",
                "title": "故事標題",
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
        
        story = story_manager.create_story(data)
        return jsonify({
            'status': 'success',
            'data': {
                'story': story
            }
        }), 201
    except ValidationError as e:
        return handle_error(e, '創建故事時驗證失敗')
    except Exception as e:
        return handle_error(e, '創建故事時發生錯誤')

@story_bp.route('/<story_id>', methods=['PUT'])
def update_story(story_id):
    """更新故事。
    
    路徑參數：
    - story_id: 故事ID
    
    請求體格式：
    {
        "title": "故事標題",
        "world_type": "世界類型",
        "setting": "設定",
        "background": "背景",
        "current_scene": "當前場景",
        "adult_content": true/false,
        "themes": ["主題1", "主題2"],
        "custom_rules": {"規則名稱": "規則內容"},
        "characters": {
            "角色名稱": {
                "name": "角色名稱",
                "personality": "角色性格",
                ...
            }
        }
    }
    
    返回格式：
    {
        "status": "success",
        "data": {
            "story": {
                "id": "故事ID",
                "title": "故事標題",
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
        
        story = story_manager.update_story(story_id, data)
        return jsonify({
            'status': 'success',
            'data': {
                'story': story
            }
        })
    except NotFoundError as e:
        return handle_error(e, f'找不到故事: {story_id}')
    except ValidationError as e:
        return handle_error(e, '更新故事時驗證失敗')
    except Exception as e:
        return handle_error(e, f'更新故事 {story_id} 時發生錯誤')

@story_bp.route('/<story_id>', methods=['DELETE'])
def delete_story(story_id):
    """刪除故事。
    
    路徑參數：
    - story_id: 故事ID
    
    返回格式：
    {
        "status": "success",
        "message": "故事已刪除"
    }
    """
    try:
        story_manager.delete_story(story_id)
        return jsonify({
            'status': 'success',
            'message': f'故事 {story_id} 已刪除'
        })
    except NotFoundError as e:
        return handle_error(e, f'找不到故事: {story_id}')
    except Exception as e:
        return handle_error(e, f'刪除故事 {story_id} 時發生錯誤')

@story_bp.route('/<story_id>/characters', methods=['POST'])
def add_character_to_story(story_id):
    """添加角色到故事中。
    
    路徑參數：
    - story_id: 故事ID
    
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
            "story": {
                "id": "故事ID",
                "title": "故事標題",
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
        
        story = story_manager.add_character_to_story(story_id, data)
        return jsonify({
            'status': 'success',
            'data': {
                'story': story
            }
        })
    except NotFoundError as e:
        return handle_error(e, f'找不到故事: {story_id}')
    except ValidationError as e:
        return handle_error(e, '添加角色時驗證失敗')
    except Exception as e:
        return handle_error(e, f'添加角色到故事 {story_id} 時發生錯誤')

@story_bp.route('/<story_id>/events', methods=['POST'])
def add_event_to_story(story_id):
    """添加事件到故事中。
    
    路徑參數：
    - story_id: 故事ID
    
    請求體格式：
    {
        "type": "事件類型",
        "description": "事件描述",
        "characters": ["角色名稱1", "角色名稱2"]
    }
    
    返回格式：
    {
        "status": "success",
        "data": {
            "story": {
                "id": "故事ID",
                "title": "故事標題",
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
        
        story = story_manager.add_event_to_story(story_id, data)
        return jsonify({
            'status': 'success',
            'data': {
                'story': story
            }
        })
    except NotFoundError as e:
        return handle_error(e, f'找不到故事: {story_id}')
    except ValidationError as e:
        return handle_error(e, '添加事件時驗證失敗')
    except Exception as e:
        return handle_error(e, f'添加事件到故事 {story_id} 時發生錯誤')

@story_bp.route('/<story_id>/scene', methods=['PUT'])
def update_scene(story_id):
    """更新故事的當前場景。
    
    路徑參數：
    - story_id: 故事ID
    
    請求體格式：
    {
        "scene": "新場景描述"
    }
    
    返回格式：
    {
        "status": "success",
        "data": {
            "story": {
                "id": "故事ID",
                "title": "故事標題",
                ...
            }
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'scene' not in data:
            return jsonify({
                'status': 'error',
                'message': '缺少場景描述'
            }), 400
        
        story = story_manager.update_scene(story_id, data['scene'])
        return jsonify({
            'status': 'success',
            'data': {
                'story': story
            }
        })
    except NotFoundError as e:
        return handle_error(e, f'找不到故事: {story_id}')
    except Exception as e:
        return handle_error(e, f'更新故事 {story_id} 的場景時發生錯誤')

@story_bp.route('/default', methods=['POST'])
def create_default_story():
    """創建默認故事。
    
    返回格式：
    {
        "status": "success",
        "data": {
            "story": {
                "id": "故事ID",
                "title": "故事標題",
                ...
            }
        }
    }
    """
    try:
        story = story_manager.create_default_story()
        return jsonify({
            'status': 'success',
            'data': {
                'story': story
            }
        }), 201
    except Exception as e:
        return handle_error(e, '創建默認故事時發生錯誤')