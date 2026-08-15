from odoo import models, fields, api
import requests
import logging
import json
_logger = logging.getLogger(__name__)

class DatumsConfig(models.Model):
    _name = 'datums.config'
    _description = 'Datums AI Configuration'

    datums_access_key = fields.Char(string="Access Key")
    datums_secret_key = fields.Char(string="Secret Key")
    datums_chatbot_enabled = fields.Boolean(string="Chatbot Enabled", default=True)
    datums_validation_success = fields.Boolean(string="Validation Status", default=False)

    @api.model
    def check_config_status(self):
        """ Check config status securely without exposing key values to frontend """
        config = self.sudo().search([], limit=1)
        has_keys = bool(config and config.datums_access_key and config.datums_secret_key)
        is_admin = self.env.user._is_admin() or self.env.user.has_group('base.group_system')
        return {
            'has_keys': has_keys,
            'is_admin': is_admin,
        }

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    datums_validation_success = fields.Boolean(
        string="Validation Status",
        compute='_compute_validation_success',
        store=False,
    )

    datums_secret_key = fields.Char(
        string="Secret Key",
        required=False,
        help="Enter the secret key"
    )

    datums_access_key = fields.Char(
        string="Access Key",
        required=False,
        help="Enter the access key"
    )

    datums_chatbot_enabled = fields.Boolean(
        string="Chatbot Enabled",
        default=True,
        help="Toggle to show/hide the chatbot button in the toolbar."
    )

    chatbot_status_label = fields.Char(
        compute="_compute_chatbot_status_label"
    )

    @api.depends()
    def _compute_validation_success(self):
        """ Load validation success from datums.config """
        config = self.env['datums.config'].sudo().search([], limit=1)
        for rec in self:
            rec.datums_validation_success = config.datums_validation_success if config else False

    @api.model
    def get_values(self):
        res = super().get_values()
        config = self.env['datums.config'].sudo().search([], limit=1)
        if config:
            res.update(
                datums_access_key=config.datums_access_key,
                datums_secret_key=config.datums_secret_key,
                datums_validation_success=config.datums_validation_success,
                datums_chatbot_enabled=config.datums_chatbot_enabled,
            )
        else:
            res.update(
                datums_access_key='',
                datums_secret_key='',
                datums_validation_success=False,
                datums_chatbot_enabled=False,
            )
        return res

    @api.depends('datums_chatbot_enabled')
    def _compute_chatbot_status_label(self):
        for rec in self:
            rec.chatbot_status_label = (
                "Chatbot: Enabled" if rec.datums_chatbot_enabled else "Chatbot: Disabled"
            )

    def set_values(self):
        """ Save keys """
        super().set_values()
        config = self.env['datums.config'].sudo().search([], limit=1)
        vals = {
            'datums_access_key': self.datums_access_key or "",
            'datums_secret_key': self.datums_secret_key or "",
            'datums_chatbot_enabled': True,
        }
        if config:
            config.write(vals)
        else:
            self.env['datums.config'].sudo().create(vals)

    def action_validate_keys(self):
        """ Validate keys → Save validation flag → Enable button """
        self.ensure_one()
        self.set_values()

        access_key = self.datums_access_key
        secret_key = self.datums_secret_key
        base_url = self.env['ir.config_parameter'].sudo().get_param('datums.api_url')
        api_url = f"{base_url}/verify-app-access"

        setting_success = 0
        api_message = "Unknown error"

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            response = requests.get(api_url, params={
                "access_key": access_key,
                "secret_key": secret_key
            }, headers=headers, timeout=10)

            data = response.json()
            setting_success = data.get("settings", {}).get("success", 0)
            api_message = data.get("settings", {}).get("message", "")

            if setting_success == 0:
                status_data = data.get("data") or {}
                if isinstance(status_data, dict):
                    status_val = str(status_data.get("status") or "").strip().lower()
                    if status_val == "pending":
                        api_message = "Project configuration has not been initiated. Please start setup on datums."
                    elif status_val == "initiated":
                        api_message = "Project setup is in progress. Please wait while datums completes the configuration."
                    elif status_val == "failed":
                        api_message = "Project setup failed. Please review the setup details on datums and try again."

        except Exception as e:
            api_message = str(e)

        # Save validation result persistently!
        config = self.env['datums.config'].sudo().search([], limit=1)
        if config:
            config.write({'datums_validation_success': setting_success == 1})
        else:
            self.env['datums.config'].sudo().create({
                'datums_access_key': access_key or '',
                'datums_secret_key': secret_key or '',
                'datums_validation_success': setting_success == 1,
            })

        # Refresh compute
        self._compute_validation_success()

        # Show popup
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': "Key Validation",
                'message': api_message,
                'type': 'success' if setting_success == 1 else 'danger',
                'sticky': False,
                'next': {'type': 'ir.actions.client', 'tag': 'reload'},
            }
        }

    def action_reset(self):
        """ Reset all configurations and clear related records """
        config = self.env['datums.config'].sudo().search([], limit=1)
        if config:
            config.write({
                'datums_access_key': '',
                'datums_secret_key': '',
                'datums_validation_success': False,
                'datums_chatbot_enabled': True,
            })
        
        # Clear records in related models
        self.env['datums.script'].sudo().search([]).unlink()
        self.env['dashboard.link'].sudo().search([]).unlink()
        
        # Refresh the compute fields for the current record
        self._compute_validation_success()
        self.datums_access_key = ''
        self.datums_secret_key = ''
        self.datums_chatbot_enabled = True

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': "Settings Reset",
                'message': "All keys and configurations have been cleared successfully.",
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.client', 'tag': 'reload'},
            }
        }

    def action_sync_db_structure(self):
        """
        1. Calls the local Odoo controller API (/api/db_structure) to get the structure.
        2. Sends the retrieved structure data to the external sync API.
        """
        self.ensure_one()
        
        access_key = self.datums_access_key
        secret_key = self.datums_secret_key
        base_url = self.env['ir.config_parameter'].sudo().get_param('datums.api_url')
        external_sync_api_url = f"{base_url}/sync-database-structure"
        
        if not access_key or not secret_key:
            title = 'Sync Skipped'
            message = "Keys are required for synchronization. Please validate them first."
            # Display the result to the user
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {'title': title, 'message': message, 'sticky': True}
            }

        # --- STEP 1: Get DB Structure from Local Odoo Controller API ---
        try:
            # Construct the URL for the local Odoo controller (assuming /api/db_structure is local)
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            local_structure_api_url = base_url + '/api/db_structure'
            
            # Make the POST request to the local Odoo controller
            # The controller expects a POST with data=json, but since we want ALL models, 
            # we send an empty body as per your controller logic for 'No model → return ALL models'.
            headers = {'Content-Type': 'application/json'}
            local_response = requests.post(local_structure_api_url, data='{}', headers=headers, timeout=500)
            local_response.raise_for_status()

            local_data = local_response.json()
            # Assuming the local API uses the format_api_response structure:
            local_settings = local_data.get('settings', {})
            local_success = local_settings.get('success', 0)
            db_structure_data = local_data.get('data') # This is the list of models/fields

            if local_success != 1 or not db_structure_data:
                local_message = local_settings.get('message', 'Local API call failed.')
                raise Exception(f"Failed to retrieve structure from local API: {local_message}")

        except requests.exceptions.RequestException as e:
            message = f"Failed to connect to local structure API ({local_structure_api_url}). Check network/URL: {e}"
            _logger.error(message)
            return {'type': 'ir.actions.client', 'tag': 'display_notification', 'params': {'message': message, 'sticky': True}}
        except Exception as e:
            message = str(e)
            _logger.error("Error retrieving DB structure: %s", e)
            return {'type': 'ir.actions.client', 'tag': 'display_notification', 'params': {'message': message, 'sticky': True}}

        # --- STEP 2: Send Retrieved Data to External Sync API ---
        sync_success = 0
        sync_message = 'No sync message provided by the external API.'
        
        try:
            # 1. Prepare the final JSON payload
            data_list = db_structure_data if isinstance(db_structure_data, list) else [db_structure_data]

            payload = {
                "access_key": access_key,
                "secret_key": secret_key,
                "data": data_list
            }

            # 2. Make the POST request to the external API
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            external_response = requests.post(external_sync_api_url, data=json.dumps(payload), headers=headers, timeout=500)
            external_response_text = external_response.text 
            
            try:
                sync_data = external_response.json()
                sync_settings = sync_data.get('settings', {}) 
                sync_message = sync_settings.get('message', 'No sync message provided by the external API.')
                sync_success = sync_settings.get('success', 0)
            except ValueError:
                sync_message = f"Non-JSON response received. Raw response: {external_response_text[:100]}..."
                sync_success = 0
            external_response.raise_for_status() 

            # If successful
            title = 'DB Sync SUCCESS'
            message = sync_message
            
        except requests.exceptions.HTTPError as e:
            sync_message = f"HTTP Error {e.response.status_code}. External API Message: {sync_message}"
            _logger.error("External DB Sync HTTP failed: %s - %s", e, sync_message)
            
        except requests.exceptions.RequestException as e:
            sync_message = f"Request failed: {str(e)}"
            _logger.error("External DB Sync request failed: %s", e)
            
        except Exception as e:
            sync_message = f"An internal error occurred during sync: {e}"
            _logger.error("An unexpected error occurred during DB sync: %s", e)

        # 3. Display the final sync result
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                # 'title': "Success",
                'message': sync_message,
                'type': 'success' if sync_success == 1 else 'danger',
                'sticky': False, 
            }
        }