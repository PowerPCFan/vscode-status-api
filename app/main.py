# stdlib
import sys
# 3rd party
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.errors import RateLimitExceeded
# local
from modules.blueprint_tools import create_blueprints
from modules.utils.gv import RATE_LIMITING
from modules.utils.request import _get_client_ip, remote_addr
from modules.utils.logger import logger

app = Flask(__name__)
CORS(app)

limiter = None
if RATE_LIMITING:
    limiter = Limiter(
        app=app,
        key_func=_get_client_ip,
        storage_uri="memcached://localhost:11211",
    )

    @app.errorhandler(RateLimitExceeded)
    def ratelimit_handler(e: RateLimitExceeded):
        logger.warning(f"User {remote_addr} has exceeded rate limit of \"{e.description}\" for endpoint {request.path}")
        return jsonify({
            "error": "rate_limit_exceeded",
            "message": str(e.description)
        }), 429

for bp in create_blueprints(limiter):
    if bp is not None:
        app.register_blueprint(bp)

if __name__ == '__main__':
    i = input("Type 1 to start development server, 0 to cancel (default 1): ")
    sys.exit(0) if i == '0' else app.run(host='127.0.0.1', port=5000, debug=False)
