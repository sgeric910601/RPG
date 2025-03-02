"""對話API模組，提供對話相關的HTTP接口。"""

from flask import Blueprint, request, jsonify
from ..core.dialogue import DialogueManager
from ..utils.error import ValidationError, NotFoundError, ServiceError, handle_error

# 創建藍圖
dialogue_bp = Blueprint('dialogue', __name__)
dialogue_manager = DialogueManager()

@dialogue_bp.route('/', methods=['GET'])
def get_all_dialogue_sessions():
    """獲取所有對話會話的摘要信息。
    
    返回格式：
    {
        "status": "success",
        "data": {
            "sessions": [
                {
                    "id": "會話ID",
                    "character_name": "角色名稱",
                    "story_id": "故事ID",
                    "message_count": 消息數量,
                    "created_at": "創建時間",
                    "updated_at": "更新時間"
                }
            ]
        }
    }
    """
    try:
        sessions = dialogue_manager.get_all_dialogue_sessions()
        return jsonify({
            'status': 'success',
            'data': {
                'sessions': sessions
            }
        })
    except Exception as e:
        return handle_error(e, '獲取對話會話列表時發生錯誤')

@dialogue_bp.route('/<session_id>', methods=['GET'])
def get_dialogue_session(session_id):
    """獲取指定ID的對話會話。
    
    路徑參數：
    - session_id: 對話會話ID
    
    返回格式：
    {
        "status": "success",
        "data": {
            "session": {
                "id": "會話ID",
                "character_name": "角色名稱",
                "story_id": "故事ID",
                "messages": [
                    {
                        "role": "user/assistant/system",
                        "content": "消息內容",
                        "timestamp": "時間戳"
                    }
                ],
                "created_at": "創建時間",
                "updated_at": "更新時間"
            }
        }
    }
    """
    try:
        session = dialogue_manager.get_dialogue_session(session_id)
        return jsonify({
            'status': 'success',
            'data': {
                'session': session
            }
        })
    except NotFoundError as e:
        return handle_error(e, f'找不到對話會話: {session_id}')
    except Exception as e:
        return handle_error(e, f'獲取對話會話 {session_id} 時發生錯誤')

@dialogue_bp.route('/', methods=['POST'])
def create_dialogue_session():
    """創建新的對話會話。
    
    請求體格式：
    {
        "character_name": "角色名稱",
        "story_id": "故事ID"
    }
    
    返回格式：
    {
        "status": "success",
        "data": {
            "session": {
                "id": "會話ID",
                "character_name": "角色名稱",
                "story_id": "故事ID",
                "messages": [],
                "created_at": "創建時間",
                "updated_at": "更新時間"
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
        
        if 'character_name' not in data:
            return jsonify({
                'status': 'error',
                'message': '缺少角色名稱'
            }), 400
        
        if 'story_id' not in data:
            return jsonify({
                'status': 'error',
                'message': '缺少故事ID'
            }), 400
        
        session = dialogue_manager.create_dialogue_session(
            data['character_name'],
            data['story_id']
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'session': session
            }
        }), 201
    except NotFoundError as e:
        return handle_error(e, '創建對話會話時找不到角色或故事')
    except Exception as e:
        return handle_error(e, '創建對話會話時發生錯誤')

@dialogue_bp.route('/<session_id>/messages', methods=['POST'])
def add_message(session_id):
    """添加消息到對話會話中。
    
    路徑參數：
    - session_id: 對話會話ID
    
    請求體格式：
    {
        "role": "user/assistant/system",
        "content": "消息內容"
    }
    
    返回格式：
    {
        "status": "success",
        "data": {
            "session": {
                "id": "會話ID",
                "character_name": "角色名稱",
                "story_id": "故事ID",
                "messages": [
                    {
                        "role": "user/assistant/system",
                        "content": "消息內容",
                        "timestamp": "時間戳"
                    }
                ],
                "created_at": "創建時間",
                "updated_at": "更新時間"
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
        
        session = dialogue_manager.add_message(session_id, data)
        return jsonify({
            'status': 'success',
            'data': {
                'session': session
            }
        })
    except NotFoundError as e:
        return handle_error(e, f'找不到對話會話: {session_id}')
    except ValidationError as e:
        return handle_error(e, '添加消息時驗證失敗')
    except Exception as e:
        return handle_error(e, f'添加消息到對話會話 {session_id} 時發生錯誤')

@dialogue_bp.route('/<session_id>/generate', methods=['POST'])
def generate_response(session_id):
    """生成AI回應。
    
    路徑參數：
    - session_id: 對話會話ID
    
    請求體格式：
    {
        "message": "用戶消息"
    }
    
    返回格式：
    {
        "status": "success",
        "data": {
            "session": {
                "id": "會話ID",
                "character_name": "角色名稱",
                "story_id": "故事ID",
                "messages": [
                    {
                        "role": "user/assistant/system",
                        "content": "消息內容",
                        "timestamp": "時間戳"
                    }
                ],
                "created_at": "創建時間",
                "updated_at": "更新時間"
            },
            "response": "AI回應"
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                'status': 'error',
                'message': '缺少用戶消息'
            }), 400
        
        session, response = dialogue_manager.generate_response(
            session_id,
            data['message']
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'session': session,
                'response': response
            }
        })
    except NotFoundError as e:
        return handle_error(e, f'找不到對話會話: {session_id}')
    except ServiceError as e:
        return handle_error(e, '生成回應時發生服務錯誤')
    except Exception as e:
        return handle_error(e, f'生成回應時發生錯誤: {str(e)}')

@dialogue_bp.route('/<session_id>', methods=['DELETE'])
def delete_dialogue_session(session_id):
    """刪除對話會話。
    
    路徑參數：
    - session_id: 對話會話ID
    
    返回格式：
    {
        "status": "success",
        "message": "對話會話已刪除"
    }
    """
    try:
        dialogue_manager.delete_dialogue_session(session_id)
        return jsonify({
            'status': 'success',
            'message': f'對話會話 {session_id} 已刪除'
        })
    except NotFoundError as e:
        return handle_error(e, f'找不到對話會話: {session_id}')
    except Exception as e:
        return handle_error(e, f'刪除對話會話 {session_id} 時發生錯誤')

@dialogue_bp.route('/start', methods=['POST'])
def start_new_conversation():
    """開始新的對話。
    
    請求體格式：
    {
        "character_name": "角色名稱",  // 可選
        "story_id": "故事ID"  // 可選
    }
    
    返回格式：
    {
        "status": "success",
        "data": {
            "session": {
                "id": "會話ID",
                "character_name": "角色名稱",
                "story_id": "故事ID",
                "messages": [],
                "created_at": "創建時間",
                "updated_at": "更新時間"
            }
        }
    }
    """
    try:
        data = request.get_json() or {}
        
        character_name = data.get('character_name')
        story_id = data.get('story_id')
        
        session = dialogue_manager.start_new_conversation(
            character_name,
            story_id
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'session': session
            }
        }), 201
    except NotFoundError as e:
        return handle_error(e, '開始新對話時找不到角色或故事')
    except Exception as e:
        return handle_error(e, f'開始新對話時發生錯誤: {str(e)}')