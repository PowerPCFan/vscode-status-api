from flask import request, jsonify, Response
from modules.utils.logger import logger
from modules.utils.database import db
from modules.utils.request import remote_addr
from typing import Any

# expects a json payload like this:

# {
#     'appName': 'Visual Studio Code',
#     'details': 'Editing blueprint_tools.py',
#     'fileName': 'blueprint_tools.py',
#     'gitBranch': 'master',
#     'gitRepo': '',
#     'isDebugging': False,
#     'language': 'python',
#     'languageIcon': 'https://raw.githubusercontent.com/PowerPCFan/vscode-status-extension/refs/heads/main/assets/icons/python.png',
#     'timestamp': 1755863352174,
#     'userId': '8551517423728874',
#     'workspace': 'vscode-status-api'
# }

# it also needs "Bearer <token>" in the Authorization header

def route() -> tuple[Response, int]:
    try:
        logger.info(f"Incoming /update-status request from {remote_addr}")

        data: dict[str, Any] = request.get_json()

        if not data:
            logger.warning("No JSON data provided in request body.")
            return jsonify({'error': 'No JSON data provided'}), 400

        user_id = data.get('userId')
        auth_token = request.headers.get('Authorization')

        if not user_id:
            logger.warning("userId is missing from request data.")
            return jsonify({'error': 'userId is required'}), 400

        if not auth_token:
            logger.warning("Authorization header is missing.")
            return jsonify({'error': 'Authorization header is required'}), 401

        if auth_token.startswith('Bearer '):
            auth_token = auth_token[7:]

        status_data = {k: v for k, v in data.items() if k != 'userId'}

        success, message, is_new_user = db.update_status(user_id, auth_token, status_data)

        if success:
            logger.info(f"Status updated successfully for user {user_id}")
            return jsonify({'message': message, 'user_id': user_id}), 200
        else:
            logger.warning(f"Failed to update status for user {user_id}: {message}")
            if "Authentication failed" in message:
                return jsonify({'error': message}), 401
            elif "User not found" in message:
                return jsonify({'error': message}), 404
            else:
                return jsonify({'error': message}), 500

    except Exception as e:
        logger.error(f"Error in update_status route: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
