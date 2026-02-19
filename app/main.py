import sys
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.errors import RateLimitExceeded
from flask import Flask, jsonify, request, Response
from modules.utils.logger import logger
from modules.utils.telemetry_db import db
from modules.utils.telemetry import start_telemetry
from modules.blueprint_tools import create_blueprints
from modules.utils.request import _get_client_ip, remote_addr
from modules.utils.gv import RATE_LIMITING, TELEMETRY_DISCORD_WEBHOOK_URL

app = Flask(__name__)
CORS(app)

# this will only start if the URL provided is not None,
# and TELEMETRY_DISCORD_WEBHOOK_URL is None if not provided
start_telemetry(TELEMETRY_DISCORD_WEBHOOK_URL)


@app.after_request
def telemetry_logger(response: Response) -> Response:
    ip: str = str(remote_addr)
    endpoint: str = request.path
    method: str = request.method
    status: int = response.status_code

    if "favicon.ico" not in endpoint:
        db.log_request(ip=ip, endpoint=endpoint, method=method, status=status)

    return response


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
    match i:
        case "0":
            sys.exit(0)
        case "1":
            app.run(host='127.0.0.1', port=5000, debug=False)
        case _:
            print("Invalid input")
            sys.exit(0)
