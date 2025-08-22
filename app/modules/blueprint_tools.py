from flask import Blueprint
from flask_limiter import Limiter
from .blueprints import update_status, get_status, healthcheck, register_user

def create_blueprints(limiter: Limiter | None) -> list[Blueprint]:
    if limiter:
        hc_blueprint = Blueprint('health_check', __name__)
        hc_blueprint.route('/', methods=['GET'])(limiter.limit("60 per minute")(healthcheck.route))

        us_blueprint = Blueprint('update_status', __name__)
        us_blueprint.route('/update-status', methods=['POST'])(limiter.limit("30 per minute")(update_status.route))

        gs_blueprint = Blueprint('get_status', __name__)
        gs_blueprint.route('/get-status', methods=['GET'])(limiter.limit("45 per minute")(get_status.route))

        # ru_blueprint = Blueprint('register_user', __name__)
        # ru_blueprint.route('/register-user', methods=['POST'])(limiter.limit("5 per hour")(register_user.route))
    else:
        hc_blueprint = Blueprint('health_check', __name__)
        hc_blueprint.route('/', methods=['GET'])(healthcheck.route)

        us_blueprint = Blueprint('update_status', __name__)
        us_blueprint.route('/update-status', methods=['POST'])(update_status.route)

        gs_blueprint = Blueprint('get_status', __name__)
        gs_blueprint.route('/get-status', methods=['GET'])(get_status.route)

        # ru_blueprint = Blueprint('register_user', __name__)
        # ru_blueprint.route('/register-user', methods=['POST'])(register_user.route)

    return [
        hc_blueprint,
        us_blueprint,
        gs_blueprint,
        # ru_blueprint
    ]
