from flask import request, jsonify, Response
from modules.utils.logger import logger
from modules.utils.database import db

def route() -> tuple[Response, int]:
    try:
        logger.info(f"Incoming /get-status request from {request.remote_addr}")

        user_id = request.args.get('userId')

        if not user_id:
            return jsonify({'error': '`userId` URL parameter is required'}), 400

        status_data = db.get_status(user_id)

        if status_data is None:
            logger.info(f"User not found: {user_id}")
            return jsonify({'error': 'User not found'}), 404

        logger.info(f"Status retrieved successfully for user {user_id}")
        return jsonify(status_data), 200

    except Exception as e:
        logger.error(f"Error in get_status route: {e}")
        return jsonify({'error': 'Internal server error'}), 500
