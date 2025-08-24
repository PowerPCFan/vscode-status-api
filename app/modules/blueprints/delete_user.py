from flask import request, jsonify, Response
from modules.utils.logger import logger
from modules.utils.database import db
from modules.utils.request import remote_addr
from typing import Any

def route() -> tuple[Response, int]:
    try:
        logger.info(f"Incoming /delete-user request from {remote_addr}")

        data: dict[str, Any] = request.get_json()

        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        user_id = data.get('userId')
        auth_token = request.headers.get('Authorization')

        if not user_id:
            return jsonify({'error': 'userId is required'}), 400

        if not auth_token:
            return jsonify({'error': 'Authorization header is required'}), 401

        auth_token = auth_token[7:] if auth_token.startswith('Bearer ') else auth_token

        success, message = db.delete_user(user_id, auth_token)

        if success:
            logger.info(f"User {user_id} deleted successfully.")
            return jsonify({'message': message}), 200
        else:
            logger.warning(f"Failed to delete user {user_id}: {message}")
            if message == "User does not exist":
                return jsonify({'error': message}), 404
            elif "Authentication failed" in message:
                return jsonify({'error': message}), 401
            else:
                return jsonify({'error': message}), 500
    except Exception as e:
        logger.error(f"Error in delete-user endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500
