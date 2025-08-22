from flask import request, jsonify, Response
from modules.utils.logger import logger
from modules.utils.database import db
from modules.utils.request import remote_addr
from typing import Any

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
            if is_new_user:
                logger.info(f"New user {user_id} registered and status updated")
                return jsonify({'message': 'User registered and status updated successfully', 'user_id': user_id, 'new_user': True}), 201
            else:
                logger.info(f"Status updated successfully for existing user {user_id}")
                return jsonify({'message': message, 'user_id': user_id, 'new_user': False}), 200
        else:
            logger.warning(f"Failed to update status for user {user_id}: {message}")
            if "Authentication failed" in message:
                return jsonify({'error': message}), 401
            else:
                return jsonify({'error': message}), 500

    except Exception as e:
        logger.error(f"Error in update_status route: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
