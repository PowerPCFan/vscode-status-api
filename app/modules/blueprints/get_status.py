from flask import request, jsonify, Response
from modules.utils.logger import logger
from modules.utils.database import db
from modules.utils.request import remote_addr
from modules.utils.language_image import get as get_language_image
from typing import Any  # me when im mad at type checking:

def route() -> tuple[Response, int]:
    try:
        logger.info(f"Incoming /get-status request from {remote_addr}")

        user_id = request.args.get('userId')

        if not user_id:
            return jsonify({'error': '`userId` URL parameter is required'}), 400

        status_data = db.get_status(user_id)

        if status_data is None:
            logger.info(f"User not found: {user_id}")
            return jsonify({'error': 'User not found'}), 404

        status_data_status: dict[str, Any] = status_data.get("status", {})

        language: str = status_data_status.get("language", "")
        filename: str = status_data_status.get("fileName", "")
        idling: bool = status_data_status.get("isIdling", False)
        language_image = get_language_image(language, filename, idling)

        new_data: dict[str, str | dict[str, str | bool]] = {
            "created_at": status_data.get("created_at", ""),
            "last_updated": status_data.get("last_updated", ""),
            "status": {
                "appName": status_data_status.get("appName", ""),
                "details": status_data_status.get("details", ""),
                "fileName": filename,
                "gitBranch": status_data_status.get("gitBranch", ""),
                "gitRepo": status_data_status.get("gitRepo", ""),
                "isDebugging": status_data_status.get("isDebugging", ""),
                "isIdling": idling,
                "language": language,
                "languageIcon": language_image,
                "timestamp": status_data_status.get("timestamp", ""),
                "workspace": status_data_status.get("workspace", ""),
            },
            "user_id": status_data.get("user_id", ""),
        }

        logger.info(f"Status retrieved successfully for user {user_id}")
        return jsonify(new_data), 200

    except Exception as e:
        logger.error(f"Error in get_status route: {e}")
        return jsonify({'error': 'Internal server error'}), 500
