from flask import request, jsonify, Response
from modules.utils.logger import logger
from modules.utils.database import db
from typing import Any

def route() -> tuple[Response, int]:
    try:
        logger.info(f"Incoming /register-user request from {request.remote_addr}")

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

        success, message = db.register_user(user_id, auth_token)

        if success:
            logger.info(f"User {user_id} registered successfully.")
            return jsonify({'message': message, 'user_id': user_id}), 201
        else:
            logger.warning(f"Failed to register user {user_id}: {message}")
            if message == "User registered successfully":
                return jsonify({'error': message}), 409
            else:
                return jsonify({'error': message}), 500

    except Exception as e:
        logger.error(f"Error in register_user route: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
