from odoo import http
from odoo.http import request
import logging
from ..utils.query_security import check_query_permissions
from ..utils import is_ip_allowed
from odoo.api import Environment
import traceback

_logger = logging.getLogger(__name__)

class QueryAPI(http.Controller):


    @http.route('/api/query', type='http', auth='public', methods=['POST'], csrf=False)
    def query(self, **kwargs):
        import json
        import base64

        # Check IP access
        if not is_ip_allowed(request):
            return request.make_json_response({
                "success":1,
                "message": "Unauthorized Access",
                "data": [{"message": "Unauthorized Access"}]
            })

        # Read request body
        try:
            payload = json.loads(request.httprequest.data or '{}')
        except Exception:
            return request.make_json_response({
                "success": 0,
                "message": "Invalid JSON payload",
                "data": []
            })

        query = payload.get("query")
        access_key = payload.get("access_key")
        user_id = payload.get("user_id", None)

        if not query:
            return request.make_json_response({
                "success": 0,
                "message": "Query is required",
                "data": []
            })

        if not access_key:
            return request.make_json_response({
                "success": 0,
                "message": "Access key is required",
                "data": []
            })

        if user_id is None or user_id == '':
            return request.make_json_response({
                "success": 0,
                "message": "user_id is required",
                "data": []
            })

        try:
            target_user = request.env['res.users'].sudo().browse(int(user_id))
            if not target_user.exists():
                return request.make_json_response({
                    "success": 0,
                    "message": "Invalid user ID",
                    "data": []
                })

            env_user = Environment(
                request.env.cr,
                target_user.id,
                request.env.context
            )

        except Exception as e:
            _logger.error("Failed to resolve user: %s", e)
            _logger.error("Traceback: %s", traceback.format_exc())
            return request.make_json_response({
                "success": 0,
                "message": f"Invalid user ID: {str(e)}",
                "data": []
            })

        # Validate access_key
        config = request.env['datums.config'].sudo().search([], limit=1)
        stored_access_key = config.datums_access_key if config else None
        if access_key != stored_access_key:
            return request.make_json_response({
                "success": 0,
                "message": "Invalid access key",
                "data": []
            })

        # Decode base64 query
        try:
            query = base64.b64decode(query).decode("utf-8").strip()
        except Exception as e:
            _logger.error("Failed to decode base64 query: %s", e)
            return request.make_json_response({
                "success": 0,
                "message": f"Invalid base64 format: {str(e)}",
                "data": []
            })

        # AST-based check using sqlglot
        import sqlglot
        from sqlglot import exp

        disallowed_node_types = (
            exp.Insert,
            exp.Update,
            exp.Delete,
            exp.Merge,
            exp.Create,
            exp.Drop,
            exp.Alter,
            exp.TruncateTable,
            exp.Command,
            exp.Copy,
        )

        try:
            statements = sqlglot.parse(query)
        except Exception as parse_err:
            _logger.warning("SQL parsing failed: %s", parse_err)
            return request.make_json_response({
                "success": 0,
                "message": f"SQL syntax / parsing error: {str(parse_err)}",
                "data": []
            })

        if not statements:
            return request.make_json_response({
                "success": 0,
                "message": "No valid SQL statements found.",
                "data": []
            })

        for statement in statements:
            if not isinstance(statement, exp.Query):
                _logger.warning("API query blocked (disallowed statement type): %s", query)
                return request.make_json_response({
                    "success": 0,
                    "message": f"Only SELECT and WITH queries are allowed. Disallowed statement: {statement.__class__.__name__}",
                    "data": []
                })

            for node in statement.walk():
                if isinstance(node, disallowed_node_types):
                    _logger.warning("API query blocked (disallowed operation %s): %s", node.__class__.__name__, query)
                    return request.make_json_response({
                        "success": 0,
                        "message": f"Only read-only SELECT and WITH queries are allowed. Disallowed operation: {node.__class__.__name__}",
                        "data": []
                    })

        #Check permissions for target models/tables
        security_check = check_query_permissions(env_user, statements, payload)
        if isinstance(security_check, dict) and not security_check.get("allowed", True):
            model_name = security_check.get("model", "unknown")
            model = env_user[model_name] if model_name in env_user.registry else None
            model_description = (
                getattr(model, '_description', None)
                or model_name
            ) if model is not None else model_name
            denial_message = security_check.get(
                "message",
                f"You do not have permission to access '{model_description}' ({model_name})"
            )
            return request.make_json_response({
                "success": 1,
                "message": denial_message,
                "data": [{"message": denial_message}]
            })

        try:
            # Execute query
            request.env.cr.execute(query)
            rows = request.env.cr.fetchall()
            columns = [col[0] for col in request.env.cr.description]

            result = [dict(zip(columns, row)) for row in rows]

            return request.make_json_response({
                "success": 1,
                "message": "Query executed successfully",
                "data": result
            })

        except Exception as e:
            return request.make_json_response({
                "success": 0,
                "message": str(e),
                "data": []
            })
