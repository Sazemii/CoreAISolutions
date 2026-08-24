from odoo import http
from odoo.http import request
import json
import logging
import os
from ..utils.api_response import format_api_response, make_json_response
from ..utils import is_ip_allowed

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Load hard-allowlist from JSON (data/allowed_tables.json)
# ---------------------------------------------------------------------------
_JSON_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),  # datums/
    'data', 'allowed_tables.json'
)
try:
    with open(_JSON_PATH, 'r') as _f:
        _allowed_tables_data = json.load(_f).get('allowed_tables', [])
        _HARD_ALLOWLIST: set = set(_allowed_tables_data)
        _ALLOWED_TABLES_LIST: list = _allowed_tables_data
except Exception as _e:
    _logger.error("Failed to load allowed_tables.json: %s", _e)
    _HARD_ALLOWLIST: set = set()
    _ALLOWED_TABLES_LIST: list = []

# CONTROLLER
class DatabaseStructureAPI(http.Controller):

    @http.route(
        '/api/db_structure',
        type='http',
        auth='public',
        methods=['POST'],
        csrf=False
    )
    def db_structure(self):
        """
        DB Structure API

        - Allowed models → full structure
        - Related models → included EVEN IF excluded
        - Related models are marked with source="relation"
        """

        # Check IP access
        # if not is_ip_allowed(request):
        #     return make_json_response(format_api_response(
        #         success=False,
        #         message="Unauthorized Access"
        #     ))

        try:
            data = json.loads(request.httprequest.data or '{}')
        except Exception:
            return make_json_response(format_api_response(
                success=False,
                message="Invalid JSON payload"
            ))

        requested_model = data.get("model")
        env = request.env

        # Helper: build model structure + collect relations
        def get_model_structure(model_obj, model_name, related_models, m2m_tables=None):
            fields_info = {}
            
            # Initialize m2m_tables if not provided
            if m2m_tables is None:
                m2m_tables = set()

            for field_name, field_obj in model_obj._fields.items():
                if not field_obj.store:
                    continue
                field_data = {
                    "type": field_obj.type,
                    "required": field_obj.required,
                    "readonly": field_obj.readonly,
                    # Include additional metadata as needed
                }

                # MANY2ONE → real column
                if field_obj.type == "many2one":
                    related_models.add(field_obj.comodel_name)
                    field_data.update({
                        "type": "integer",  # Change type to integer for ID
                        "relation": {
                            "table": field_obj.comodel_name.replace('.', '_'),
                            "column": "id"
                        }
                    })

                # Skip one2many fields as they don't have a database column
                elif field_obj.type == "one2many":
                    continue

                # MANY2MANY → separate relation table
                elif field_obj.type == "many2many":
                    related_models.add(field_obj.comodel_name)

                    m2m_tables.add(field_obj.relation)

                    field_data.update({
                        "relation_model": field_obj.comodel_name,
                        "relation_table": field_obj.relation,
                        "column1": field_obj.column1,
                        "column2": field_obj.column2,
                        "virtual": True,
                    })

                # Selection values
                if field_obj.type == "selection":
                    field_data["selection"] = field_obj.selection

                fields_info[field_name] = field_data

            return {
                "model": model_name,
                "table": model_name.replace('.', '_'),
                "fields": fields_info,
            }

        # Helper: get database table structure directly from postgres catalog
        def get_db_table_structure(table_name, exists=True):
            fields_info = {}
            if exists:
                try:
                    request.cr.execute("""
                        SELECT 
                            column_name, 
                            data_type, 
                            is_nullable
                        FROM information_schema.columns
                        WHERE table_schema = 'public'
                          AND table_name = %s
                        ORDER BY ordinal_position
                    """, (table_name,))
                    columns = request.cr.fetchall()
                    
                    for col in columns:
                        col_name, data_type, is_nullable = col
                        
                        type_map = {
                            'integer': 'integer',
                            'bigint': 'integer',
                            'smallint': 'integer',
                            'character varying': 'char',
                            'character': 'char',
                            'text': 'text',
                            'boolean': 'boolean',
                            'numeric': 'float',
                            'real': 'float',
                            'double precision': 'float',
                            'timestamp without time zone': 'datetime',
                            'timestamp with time zone': 'datetime',
                            'date': 'date',
                        }
                        odoo_type = type_map.get(data_type, data_type)
                        
                        fields_info[col_name] = {
                            "type": odoo_type,
                            "required": (is_nullable == 'NO'),
                            "readonly": False,
                        }
                except Exception as e:
                    _logger.warning("Error fetching columns for table %s: %s", table_name, e)

            return {
                "model": table_name.replace('_', '.'),
                "table": table_name,
                "fields": fields_info,
                "type": "many2many",
                "source": "relation",
            }

        # SINGLE MODEL REQUEST
        if requested_model:
            if requested_model not in env:
                return make_json_response(format_api_response(
                    success=False,
                    message=f"Model '{requested_model}' not found in Odoo."
                ))

            model_obj = env[requested_model].sudo()
            model_table = model_obj._table
            
            # Check if the model's actual table or synthesized table or pluralized table is in allowlist
            model_synth_table = requested_model.replace('.', '_')
            allowed_candidates = [model_table, model_synth_table, f"{model_synth_table}s"]
            if not any(cand in _HARD_ALLOWLIST for cand in allowed_candidates):
                return make_json_response(format_api_response(
                    success=False,
                    message=f"Access to model '{requested_model}' is not allowed."
                ))

            related_models = set()
            m2m_tables = set()
            
            model_data = get_model_structure(
                model_obj,
                requested_model,
                related_models,
                m2m_tables
            )

            # Override table name to match the allowlist if necessary
            for cand in allowed_candidates:
                if cand in _HARD_ALLOWLIST:
                    model_data["table"] = cand
                    break

            related_data = []
            for rel in related_models:
                if rel not in env:
                    continue
                try:
                    rel_table = env[rel]._table
                    rel_synth_table = rel.replace('.', '_')
                    rel_candidates = [rel_table, rel_synth_table, f"{rel_synth_table}s"]
                    if not any(cand in _HARD_ALLOWLIST for cand in rel_candidates):
                        continue

                    rel_data = get_model_structure(env[rel].sudo(), rel, set(), set())
                    for cand in rel_candidates:
                        if cand in _HARD_ALLOWLIST:
                            rel_data["table"] = cand
                            break

                    related_data.append({
                        **rel_data,
                        "source": "relation",
                        "excluded": False,
                    })
                except Exception as e:
                    _logger.warning("Skipping related model %s: %s", rel, e)

            # MANY2MANY RELATION TABLES
            m2m_result = [
                get_db_table_structure(table, exists=True)
                for table in sorted(m2m_tables)
                if table in _HARD_ALLOWLIST
            ]
            
            return make_json_response(format_api_response(
                success=True,
                message="Model structure retrieved successfully",
                data=[model_data] + related_data + m2m_result
            ))

        # ALL MODELS (SYNC MODE)
        allowed_tables_list = _ALLOWED_TABLES_LIST

        # Find existing tables in the database
        request.cr.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
              AND table_type = 'BASE TABLE'
        """)
        existing_db_tables = {row[0] for row in request.cr.fetchall()}

        # Build table_name -> model_name map from registry
        table_to_model = {}
        for model_name in env.registry:
            try:
                model_cls = env.registry[model_name]
                if hasattr(model_cls, '_table') and model_cls._table:
                    # 1. Map actual table name to model name
                    table_to_model[model_cls._table] = model_name
                
                # 2. Map synthesized table name to model name
                synth_table = model_name.replace('.', '_')
                table_to_model[synth_table] = model_name
            except Exception:
                pass

        result = []
        m2m_result = []
        skipped = 0

        for table_name in allowed_tables_list:
            if not table_name:
                continue

            # Determine the model name using our lookup mapping
            lookup_key = table_name
            if lookup_key not in table_to_model and lookup_key.endswith('s'):
                if lookup_key[:-1] in table_to_model:
                    lookup_key = lookup_key[:-1]

            model_name = table_to_model.get(lookup_key)

            # Check if model exists and has a table in DB
            has_db_table = False
            if model_name:
                try:
                    actual_table = env[model_name]._table
                    has_db_table = actual_table in existing_db_tables
                except Exception:
                    pass

            if model_name and has_db_table:
                try:
                    # Retrieve the model structure
                    model_data = get_model_structure(
                        env[model_name].sudo(),
                        model_name,
                        set(),
                        set()
                    )
                    # Override the table name to match the allowlist table name exactly
                    model_data["table"] = table_name
                    result.append(model_data)
                except Exception as e:
                    _logger.warning("Skipping model %s due to error: %s", model_name, e)
                    # Fallback to relation format if we couldn't load the structure
                    m2m_result.append(get_db_table_structure(table_name, exists=True))
            else:
                db_exists = table_name in existing_db_tables
                m2m_result.append(get_db_table_structure(table_name, exists=db_exists))

        final_result = result + m2m_result

        return make_json_response(format_api_response(
            success=True,
            message="Database structure retrieved successfully",
            data=final_result,
            meta={
                "total": len(final_result),
                "main_tables": len(result),
                "related_tables": 0,
                "m2m_relation_tables": len(m2m_result),
                "skipped": skipped,
            }
        ))
