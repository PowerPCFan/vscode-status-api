from flask import Blueprint
from flask_limiter import Limiter
from .blueprints import update_status, get_status, healthcheck, trigger_rate_limit, register_user, delete_user, check_if_user_exists

def create_blueprints(limiter: Limiter | None) -> list[Blueprint | None]:
    if limiter:
        hc_blueprint = Blueprint('health_check', __name__)
        hc_blueprint.route('/', methods=['GET'])(limiter.limit("60 per minute")(healthcheck.route))

        us_blueprint = Blueprint('update_status', __name__)
        us_blueprint.route('/update-status', methods=['POST'])(limiter.limit("30 per minute")(update_status.route))

        gs_blueprint = Blueprint('get_status', __name__)
        gs_blueprint.route('/get-status', methods=['GET'])(limiter.limit("45 per minute")(get_status.route))

        ru_blueprint = Blueprint('register_user', __name__)
        ru_blueprint.route('/register-user', methods=['POST'])(limiter.limit("5 per day")(register_user.route))

        du_blueprint = Blueprint('delete_user', __name__)
        du_blueprint.route('/delete-user', methods=['DELETE'])(limiter.limit("10 per day")(delete_user.route))

        ciue_blueprint = Blueprint('check_if_user_exists', __name__)
        ciue_blueprint.route('/check-if-user-exists', methods=['GET'])(limiter.limit("45 per minute")(check_if_user_exists.route))

        trl_blueprint = Blueprint('trigger_rate_limit', __name__)
        trl_blueprint.route('/trigger-rate-limit', methods=['GET'])(limiter.limit("1 per minute")(trigger_rate_limit.route))

    else:
        hc_blueprint = Blueprint('health_check', __name__)
        hc_blueprint.route('/', methods=['GET'])(healthcheck.route)

        us_blueprint = Blueprint('update_status', __name__)
        us_blueprint.route('/update-status', methods=['POST'])(update_status.route)

        gs_blueprint = Blueprint('get_status', __name__)
        gs_blueprint.route('/get-status', methods=['GET'])(get_status.route)

        ru_blueprint = Blueprint('register_user', __name__)
        ru_blueprint.route('/register-user', methods=['POST'])(register_user.route)

        du_blueprint = Blueprint('delete_user', __name__)
        du_blueprint.route('/delete-user', methods=['DELETE'])(delete_user.route)

        ciue_blueprint = Blueprint('check_if_user_exists', __name__)
        ciue_blueprint.route('/check-if-user-exists', methods=['GET'])(check_if_user_exists.route)

        trl_blueprint = None  # useless if rate limiting is off

    return [
        hc_blueprint,
        us_blueprint,
        gs_blueprint,
        ru_blueprint,
        du_blueprint,
        ciue_blueprint,
        trl_blueprint
    ]
