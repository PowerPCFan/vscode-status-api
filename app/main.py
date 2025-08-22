# stdlib
import sys
# 3rd party
from flask import Flask, request
from flask_cors import CORS
import flask_limiter
# local
from modules.blueprint_tools import create_blueprints
from modules.utils.gv import RATE_LIMITING
from modules.utils.request import _get_client_ip

app = Flask(__name__)
CORS(app)

limiter = None
if RATE_LIMITING:
    limiter = flask_limiter.Limiter(
        app=app,
        key_func=_get_client_ip,
        storage_uri="memcached://localhost:11211",
    )

for bp in create_blueprints(limiter):
    app.register_blueprint(bp)

if __name__ == '__main__':
    i = input("Type 1 to start development server, 0 to cancel: ")
    app.run(host='127.0.0.1', port=5000, debug=False) if i == '1' else sys.exit(0)
