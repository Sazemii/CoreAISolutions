import re
import logging
from sqlglot import exp

_logger = logging.getLogger(__name__)

def extract_tables_ast(statements):
    tables, cte_aliases = set(), set()
    for stmt in statements:
        for cte in stmt.find_all(exp.CTE):
            if cte.alias:
                cte_aliases.add(cte.alias.lower())
        for tbl in stmt.find_all(exp.Table):
            if tbl.name:
                tables.add(tbl.name.lower())
    return tables - cte_aliases

def check_query_permissions(env, statements, payload):
    """
    Check if the user has permissions to query all referenced Odoo models.
    Returns True if allowed, False otherwise.
    """
    extracted_tables = extract_tables_ast(statements)
    user = env.user

    table_to_model = {}

    for model_name in env.registry:
        try:
            model_cls = env.registry[model_name]

            if getattr(model_cls, '_table', False):
                table_to_model[model_cls._table] = model_name

            table_to_model[
                model_name.replace('.', '_')
            ] = model_name

        except Exception:
            continue 
    
    filters = payload.get('filters') or payload.get('filter') or payload if isinstance(payload, dict) else {}
    companies_filter = []
    if isinstance(filters, dict):
        companies_filter = filters.get('companies', [])
    elif isinstance(payload, dict):
        companies_filter = payload.get('companies', [])

    # If no filters / companies were provided in the payload, fetch them dynamically from Odoo
    if not companies_filter:
        try:
            user_config = env['datums.script'].get_user_companies_config()
            companies_filter = user_config.get('companies', [])
            _logger.debug("Fetched permissions dynamically from Odoo: %s", companies_filter)
        except Exception as e:
            _logger.error("Failed to fetch permissions dynamically from Odoo: %s", e)

    allowed_permissions = None

    if companies_filter:
        current_company_id = env.company.id
        for c in companies_filter:
            if isinstance(c, dict) and 'id' in c:
                try:
                    if int(c.get('id')) == int(current_company_id):
                        allowed_permissions = c.get('permissions')
                        break
                except (ValueError, TypeError):
                    continue
        
        # Fallback: if no match found for current_company_id, union all permissions from all companies in the payload
        if allowed_permissions is None:
            allowed_permissions = []
            for c in companies_filter:
                if isinstance(c, dict):
                    perms = c.get('permissions')
                    if perms == 'all_permission':
                        allowed_permissions = 'all_permission'
                        break
                    elif isinstance(perms, list):
                        allowed_permissions.extend(perms)
            if isinstance(allowed_permissions, list):
                allowed_permissions = list(set(allowed_permissions))

    for table in extracted_tables:
        model_name = table_to_model.get(table)
        if (
            not model_name
            and table.endswith('s')
            and table[:-1] in table_to_model
        ):
            model_name = table_to_model[table[:-1]]

        if not model_name:
            _logger.warning(
                "No model found for table %s",
                table
            )
            return {
                "allowed": False,
                "table": table,
                "message": f'Unknown table "{table}"'
            }

        model = env.registry.get(model_name)
        model_description = (
            getattr(model, '_description', None)
            or model_name
        ) if model is not None else model_name

        # Enforce payload-based permissions if they are provided
        if allowed_permissions is not None:
            is_allowed = False
            if allowed_permissions == 'all_permission':
                is_allowed = True
            elif isinstance(allowed_permissions, list):
                # Bypass payload permissions for base/framework models
                base_prefixes = ('mail.', 'base.', 'ir.', 'web.', 'res.users', 'res.company', 'res.currency', 'res.country', 'res.groups', 'res.lang')
                if model_name.startswith(base_prefixes) or model_name in allowed_permissions or (model_name + '.public') in allowed_permissions:
                    is_allowed = True
            
            if not is_allowed:
                _logger.warning(
                    "Access denied by payload permissions: User %s (%s) -> %s not in %s",
                    user.name,
                    user.id,
                    model_name,
                    allowed_permissions
                )
                return {
                    "allowed": False,
                    "model": model_name,
                    "table": table,
                    "message": f'You do not have permission to access "{model_description or table}"'
                }

        try:
            # Check model-level access rights
            try:
                env[model_name].check_access('read')
                has_access = True
            except Exception:
                has_access = False

            # Fallback for models with a public counterpart (e.g., hr.employee -> hr.employee.public)
            if not has_access and (model_name + '.public') in env.registry:
                try:
                    env[model_name + '.public'].check_access('read')
                    has_access = True
                except Exception:
                    has_access = False
                if has_access:
                    _logger.info(
                        "Access granted via public model fallback: User %s (%s) -> %s (via %s)",
                        user.name,
                        user.id,
                        model_name,
                        model_name + '.public'
                    )

            if not has_access:
                _logger.warning(
                    "Access denied: User %s (%s) -> %s",
                    user.name,
                    user.id,
                    model_name
                )
                return {
                    "allowed": False,
                    "model": model_name,
                    "table": table,
                    "message": f'You do not have permission to access "{model_description or table}"'
                }
        
        except Exception as e:
            _logger.error(
                "Permission check failed for %s: %s",
                model_name,
                str(e)
            )
            return {
                "allowed": False,
                "model": model_name,
                "table": table,
                "message": f'You do not have permission to access "{model_description or table}"'
            }

    return {"allowed": True}
