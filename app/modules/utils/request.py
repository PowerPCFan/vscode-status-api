from flask import request
from werkzeug.local import LocalProxy
from modules.utils.gv import CLOUDFLARE_TUNNEL
from modules.utils.logger import logger

def _get_client_ip() -> str:
    if CLOUDFLARE_TUNNEL:
        if "CF-Connecting-IP" in request.headers:
            return request.headers["CF-Connecting-IP"]
        else:
            logger.warning("Header 'CF-Connecting-IP' not found in request, but CLOUDFLARE_TUNNEL is enabled. This may lead to excessive rate limiting due to IP proxying.")
    return request.remote_addr or "127.0.0.1"

remote_addr = LocalProxy(_get_client_ip)
