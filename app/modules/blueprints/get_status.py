from flask import request, jsonify, Response
from modules.utils.logger import logger
from modules.utils.database import db
from modules.utils.request import remote_addr

# Returns something like this:

# {
#   "created_at": "2025-08-22T11:49:09.125405",
#   "last_updated": "2025-08-22T08:55:42.766476",
#   "status": {
#     "appName": "Visual Studio Code",
#     "details": "Editing file.py",
#     "fileName": "file.py",
#     "gitBranch": "master",
#     "gitRepo": "",
#     "isDebugging": false,
#     "language": "python",
#     "languageIcon": "https://raw.githubusercontent.com/PowerPCFan/vscode-status-extension/refs/heads/master/assets/icons/python.png",
#     "timestamp": 1755863352174,
#     "workspace": "vscode-workspace-name"
#   },
#   "user_id": "1234567890123456"
# }

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

        new_data = {
            "created_at": status_data.get("created_at", ""),
            "last_updated": status_data.get("last_updated", ""),
            "status": {
                "appName": status_data.get("appName", ""),
                "details": status_data.get("details", ""),
                "fileName": status_data.get("fileName", ""),
                "gitBranch": status_data.get("gitBranch", ""),
                "gitRepo": status_data.get("gitRepo", ""),
                "isDebugging": status_data.get("isDebugging", ""),
                "language": status_data.get("language", ""),
                "languageIcon": status_data.get("languageIcon", ""),
                "timestamp": status_data.get("timestamp", ""),
                "workspace": status_data.get("workspace", ""),
            },
            "user_id": status_data.get("user_id", ""),
        }

        logger.info(f"Status retrieved successfully for user {user_id}")
        return jsonify(new_data), 200

    except Exception as e:
        logger.error(f"Error in get_status route: {e}")
        return jsonify({'error': 'Internal server error'}), 500
