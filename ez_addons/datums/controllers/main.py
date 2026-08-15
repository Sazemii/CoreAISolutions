import json
import urllib.request
import urllib.error
import logging
import os
from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)
# API URL is parameterized. Retrieved via ir.config_parameter key 'datums.api_url'


class DatumsButtonController(http.Controller):

    def _get_api_credentials(self):
        config = request.env['datums.config'].sudo().search([], limit=1)
        if config:
            return config.datums_access_key or '', config.datums_secret_key or ''
        return '', ''

    @http.route('/datums/get_expected_origin', type='json', auth='user', methods=['POST'], csrf=False)
    def get_expected_origin(self):
        """ Returns the expected origin derived from datums.api_url """
        base_url = request.env['ir.config_parameter'].sudo().get_param('datums.api_url')
        if base_url:
            from urllib.parse import urlparse
            parsed = urlparse(base_url)
            return f"{parsed.scheme}://{parsed.netloc}"
        return ""

    # ------------------------------------------------------------------ #
    #  NEW: Proxy – Chatbot embed script                                  #
    # ------------------------------------------------------------------ #
    @http.route(['/datums/get_chatbot_script', '/datums_dashboard/get_chatbot_script'], type='http',
                auth='user', methods=['POST'], csrf=False, cors='*')
    def get_chatbot_script(self, **kwargs):
        """
        Proxy for:
          POST https://panel-api.datums.ai/api/company/get-embedded-script
               Body: { access_key, secret_key, filter }

        Returns JSON:  { success: true, script_content: "<script …>" }
        """
        try:
            access_key, secret_key = self._get_api_credentials()
            
            # Chatbot is always enabled
            chatbot_enabled = True

            if not access_key or not secret_key:
                return Response(
                    json.dumps({
                        'success': False,
                        'error': 'Missing API keys. Configure Access Key and Secret Key in Settings first.',
                    }),
                    headers={'Content-Type': 'application/json'},
                    status=200
                )

            filter_val = None
            if request.httprequest.headers.get('Content-Type') == 'application/json':
                try:
                    req_data = json.loads(request.httprequest.data.decode('utf-8'))
                    filter_val = req_data.get('filters') or req_data.get('filter')
                except Exception:
                    pass
            
            if not filter_val:
                filter_val = kwargs.get('filters') or kwargs.get('filter')

            if not filter_val:
                try:
                    filter_val = request.env['datums.script'].get_user_companies_config()
                except Exception:
                    pass

            # Inject user email into the filters structure if it's a dict and missing
            if isinstance(filter_val, dict) and 'user' in filter_val and isinstance(filter_val['user'], dict):
                if 'email' not in filter_val['user']:
                    filter_val['user']['email'] = request.env.user.email or ''

            payload = {
                'access_key': access_key,
                'secret_key': secret_key,
            }
            if filter_val:
                if isinstance(filter_val, dict):
                    payload['filters'] = filter_val
                elif isinstance(filter_val, str):
                    try:
                        parsed_val = json.loads(filter_val)
                        if isinstance(parsed_val, dict) and 'user' in parsed_val and isinstance(parsed_val['user'], dict):
                            if 'email' not in parsed_val['user']:
                                parsed_val['user']['email'] = request.env.user.email or ''
                        payload['filters'] = parsed_val
                    except Exception:
                        payload['filters'] = filter_val
                else:
                    payload['filters'] = filter_val

            base_url = request.env['ir.config_parameter'].sudo().get_param('datums.api_url')
            url = f"{base_url}/get-embedded-script"
            body = json.dumps(payload).encode('utf-8')

            req = urllib.request.Request(url, data=body, method='POST')
            req.add_header('Content-Type', 'application/json')
            req.add_header('Accept', 'application/json')
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

            with urllib.request.urlopen(req, timeout=10) as resp:
                raw = resp.read().decode('utf-8')

            # Forward the API response as-is to the browser
            api_data = json.loads(raw)
            # Check for maintenance status in the API's own settings object
            api_status = api_data.get('settings', {}).get('status')
            if api_status and api_status != 200:
                return Response(
                    json.dumps({'success': False, 'maintenance': True, 'error': api_data.get('settings', {}).get('message', 'Under Maintenance')}),
                    headers={'Content-Type': 'application/json'},
                    status=200 # Return 200 so the frontend receives the JSON
                )

            # API response shape:
            # { data: { embedded_code: "<script …>" }, settings: { … } }
            script_content = (
                (api_data.get('data') or {}).get('embedded_code')
                or (api_data.get('data') or {}).get('embed_code')
                or (api_data.get('data') or {}).get('script')
                or api_data.get('embedded_code')
                or api_data.get('script_content')
                or api_data.get('embed_code')
                or ''
            )

            user = request.env.user
            res_data = {
                'success': True,
                'script_content': script_content,
                'raw': api_data,
                'id': user.id,
                'name': user.name,
                'email': user.email or '',
            }
            return Response(
                json.dumps(res_data),
                headers={'Content-Type': 'application/json'},
                status=200
            )

        except urllib.error.HTTPError as e:
            return Response(
                json.dumps({'success': False, 'error': f'API HTTP {e.code}: {e.reason}'}),
                headers={'Content-Type': 'application/json'},
                status=200
            )
        except Exception as e:
            return Response(
                json.dumps({'success': False, 'error': str(e)}),
                headers={'Content-Type': 'application/json'},
                status=200
            )

    # ------------------------------------------------------------------ #
    #  NEW: Proxy – Dashboard pages                                       #
    # ------------------------------------------------------------------ #
    @http.route(['/datums/get_dashboard_pages', '/datums_dashboard/get_dashboard_pages'], type='http',
                auth='user', methods=['POST'], csrf=False, cors='*')
    def get_dashboard_pages(self, **kwargs):
        """
        Proxy for:
          POST https://panel-api.datums.ai/api/company/get-project-dashboard-pages
               Body: { access_key, secret_key }

        Returns JSON:  { success: true, pages: [{ id, name, url }, …] }
        """
        try:
            access_key, secret_key = self._get_api_credentials()
            if not access_key or not secret_key:
                return Response(
                    json.dumps({
                        'success': False,
                        'pages': [],
                        'error': 'Missing API keys. Configure Access Key and Secret Key in Settings first.',
                    }),
                    headers={'Content-Type': 'application/json'},
                    status=200
                )

            base_url = request.env['ir.config_parameter'].sudo().get_param('datums.api_url')
            url  = f"{base_url}/get-project-dashboard-pages"
            
            # Retrieve filter from JSON body or from urlencoded/query parameters
            filter_val = None
            if request.httprequest.headers.get('Content-Type') == 'application/json':
                try:
                    req_data = json.loads(request.httprequest.data.decode('utf-8'))
                    filter_val = req_data.get('filters') or req_data.get('filter')
                except Exception:
                    pass
            
            if not filter_val:
                filter_val = kwargs.get('filters') or kwargs.get('filter')

            payload = {
                'access_key': access_key,
                'secret_key': secret_key,
            }
            if filter_val:
                if isinstance(filter_val, dict):
                    payload['filters'] = filter_val
                elif isinstance(filter_val, str):
                    try:
                        payload['filters'] = json.loads(filter_val)
                    except Exception:
                        payload['filters'] = filter_val
                else:
                    payload['filters'] = filter_val

            body = json.dumps(payload).encode('utf-8')

            req = urllib.request.Request(url, data=body, method='POST')
            req.add_header('Content-Type', 'application/json')
            req.add_header('Accept', 'application/json')
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

            with urllib.request.urlopen(req, timeout=10) as resp:
                raw = resp.read().decode('utf-8')

            api_data = json.loads(raw)
            
            # Check for maintenance status in the API's own settings object
            api_status = api_data.get('settings', {}).get('status')
            if api_status and api_status != 200:
                return Response(
                    json.dumps({'success': False, 'pages': [], 'maintenance': True, 'error': api_data.get('settings', {}).get('message', 'Under Maintenance')}),
                    headers={'Content-Type': 'application/json'},
                    status=200 # Return 200 so the frontend receives the JSON
                )

            # Normalise pages list.
            # API may return:
            #   - a bare list:             [ { … }, … ]
            #   - { pages: [ … ] }
            #   - { data: { pages: [ … ] } }
            #   - { data: [ … ] }
            #   - { dashboards: [ … ] }
            raw_pages = []
            if isinstance(api_data, list):
                raw_pages = api_data
            elif isinstance(api_data, dict):
                data_block = api_data.get('data')
                if isinstance(api_data.get('pages'), list):
                    raw_pages = api_data.get('pages')
                elif isinstance(api_data.get('dashboards'), list):
                    raw_pages = api_data.get('dashboards')
                elif isinstance(data_block, list):
                    raw_pages = data_block
                elif isinstance(data_block, dict):
                    nested_pages = data_block.get('pages') or data_block.get('dashboards') or []
                    raw_pages = nested_pages if isinstance(nested_pages, list) else []

            # Determine allowed modules from filter_val (if any)
            allowed_modules = []
            is_admin_all = False
            if filter_val:
                if isinstance(filter_val, dict):
                    # Expected format: {'companies': [{'permissions': [...]}, ...]}
                    for comp in filter_val.get('companies', []):
                        perms = comp.get('permissions', [])
                        if perms == 'all_permission' or (isinstance(perms, list) and 'all_permission' in perms):
                            is_admin_all = True
                        if isinstance(perms, list):
                            allowed_modules.extend(perms)
                        elif isinstance(perms, str):
                            allowed_modules.append(perms)
                elif isinstance(filter_val, list):
                    if 'all_permission' in filter_val:
                        is_admin_all = True
                    allowed_modules = filter_val
                elif isinstance(filter_val, str):
                    if filter_val == 'all_permission':
                        is_admin_all = True
                    allowed_modules = [filter_val]

            # Normalise each page item to { id, name, url }
            pages = []
            for i, p in enumerate(raw_pages):
                if not isinstance(p, dict):
                    continue

                if allowed_modules and not is_admin_all:                    
                    modules = p.get('modules')
                    # Skip only when modules list is NOT empty
                    if modules:
                        allowed_module_prefixes = {
                            m.split('.')[0] for m in allowed_modules
                        }

                        # Exclude page if none of its modules are allowed
                        if not any(m in allowed_module_prefixes for m in modules):
                            continue
                    
                pages.append({
                    'id':   p.get('id') or p.get('page_id') or i,
                    'name': p.get('name') or p.get('title') or p.get('page_name') or f'Dashboard {i+1}',
                    'url':  p.get('url') or p.get('link') or p.get('dashboard_url') or p.get('page_url') or '',
                })

            return Response(
                json.dumps({'success': True, 'pages': pages, 'raw': api_data}),
                headers={'Content-Type': 'application/json'},
                status=200
            )

        except urllib.error.HTTPError as e:
            return Response(
                json.dumps({'success': False, 'pages': [], 'error': f'API HTTP {e.code}: {e.reason}'}),
                headers={'Content-Type': 'application/json'},
                status=200
            )
        except Exception as e:
            return Response(
                json.dumps({'success': False, 'pages': [], 'error': str(e)}),
                headers={'Content-Type': 'application/json'},
                status=200
            )
