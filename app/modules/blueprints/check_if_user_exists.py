from flask import request, jsonify, Response
from modules.utils.logger import logger
from modules.utils.database import db
from modules.utils.request import remote_addr
from typing import Any

def route() -> tuple[Response, int]:
    try:
        logger.info(f"Incoming /check-if-user-exists request from {remote_addr}")

        user_id = request.args.get('userId')

        if not user_id:
            return jsonify({'error': 'userId is required'}), 400

        success, message = db.check_if_user_exists(user_id)

        if success:
            logger.info(f"User {user_id} exists.")
            return jsonify({'exists': True}), 200
        else:
            logger.warning(f"Failed to check if user {user_id} exists: {message}")
            if message == "User does not exist":
                return jsonify({'exists': False}), 404
            else:
                return jsonify({'error': message}), 500
    except Exception as e:
        logger.error(f"Error in check-if-user-exists endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500
