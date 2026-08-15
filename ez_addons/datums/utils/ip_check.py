import logging
from odoo.http import request

_logger = logging.getLogger(__name__)

def is_ip_allowed(env):
    """
    Check if the client IP is allowed based on the system parameter 'datums.allowed_ips'.
    """
    client_ip = request.httprequest.remote_addr
    _logger.info("client_ip (remote_addr): %s", client_ip)

    if hasattr(env, 'env'):
        env = env.env
    allowed_ips_str = env['ir.config_parameter'].sudo().get_param(
        'datums.allowed_ips', '')
    allowed_ips = [ip.strip() for ip in allowed_ips_str.split(',') if ip.strip()]
    if not allowed_ips:
        return False   # empty means deny all

    if not client_ip or client_ip not in allowed_ips:
        _logger.warning("Unauthorized Access: Request from IP %s is not in the allowed list %s", client_ip, allowed_ips)
        return False
    return True
