from odoo import models, fields, api

class DatumsScript(models.Model):
    _name = 'datums.script'
    _description = 'Datums Script Configuration'
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True, default='Datums Scripts')
    embed_code = fields.Text(string='Embed Code', required=True, help="Paste your script tags here")
    active = fields.Boolean(string='Active', default=True)
    
    @api.model
    def get_active_scripts(self):
        """Return active chatbot scripts"""
        return self.search([('active', '=', True)], limit=1)

    def _get_visible_models(self, company_env):
        """Retrieve all model names linked to dashboard menus visible to the user"""
        visible_models = set()
        
        # Method 1: Use Odoo's standard, cached load_menus API
        try:
            menus_dict = company_env['ir.ui.menu'].load_menus(False)
            for menu_id, menu_data in menus_dict.items():
                if isinstance(menu_id, int) and isinstance(menu_data, dict):
                    action_str = menu_data.get('action')
                    if action_str and isinstance(action_str, str) and ',' in action_str:
                        try:
                            action_model, action_id = action_str.split(',')
                            action_id = int(action_id)
                            if action_model == 'ir.actions.act_window':
                                action = company_env['ir.actions.act_window'].sudo().browse(action_id)
                                if action.res_model:
                                    visible_models.add(action.res_model)
                            elif action_model == 'ir.actions.server':
                                action = company_env['ir.actions.server'].sudo().browse(action_id)
                                if action.model_id:
                                    visible_models.add(action.model_id.model)
                        except Exception:
                            pass
        except Exception:
            pass

        # Method 2: Fallback to recursive visibility filtering if load_menus fails
        if not visible_models:
            try:
                all_menus = company_env['ir.ui.menu'].sudo().search([])
                all_visible_menus = all_menus.with_env(company_env)._filter_visible_menus()
                
                # Filter to only get root menus and their reachable descendants
                root_menus = [menu for menu in all_visible_menus if not menu.parent_id]
                visible_root_ids = {menu.id for menu in root_menus}
                
                parent_to_children = {}
                for menu in all_visible_menus:
                    try:
                        parent_id = menu.sudo().parent_id.id
                        if parent_id:
                            parent_to_children.setdefault(parent_id, []).append(menu.id)
                    except Exception:
                        pass
                
                queue = list(visible_root_ids)
                reachable_menus = set(visible_root_ids)
                while queue:
                    current_id = queue.pop(0)
                    children = parent_to_children.get(current_id, [])
                    for child_id in children:
                        if child_id not in reachable_menus:
                            reachable_menus.add(child_id)
                            queue.append(child_id)
                            
                for menu_id in reachable_menus:
                    try:
                        menu = company_env['ir.ui.menu'].browse(menu_id)
                        action = menu.sudo().action
                        if action:
                            if action._name == 'ir.actions.act_window' and action.res_model:
                                            visible_models.add(action.res_model)
                            elif action._name == 'ir.actions.server' and action.model_id:
                                            visible_models.add(action.model_id.model)
                    except Exception:
                        pass
            except Exception:
                pass
                
        return visible_models

    @api.model
    def get_user_companies_config(self):
        """Return allowed companies and their permissions for the logged in user"""
        user = self.env.user
        
        if user._is_admin() or user.has_group('base.group_system'):
            # For admin, return selected companies only, with all permissions
            selected_companies = self.env.companies or self.env.company
            companies_data = []
            for company in selected_companies:
                companies_data.append({
                    'id': company.id,
                    'name': company.name,
                    'permissions': 'all_permission'
                })
            return {
                'is_admin': True,
                'user': {
                    'id': user.id,
                    'name': user.name,
                },
                'companies': companies_data
            }
            
        companies_data = []
        
        # Models to skip
        restricted_prefixes = (
            'ir.',
            'base.',
            'bus.',
            'web.',
            'mail.',
        )
        
        for company in user.company_ids:
            # Switch context to the company and explicitly force environment of the logged-in user with su=False
            if hasattr(self, 'with_company'):
                company_env = self.with_user(user).with_company(company).env
            else:
                company_env = self.with_user(user).with_context(force_company=company.id).env
            
            # Fetch visible models using our professional helper
            visible_models = self._get_visible_models(company_env)
            
            permissions = []
            for model in visible_models:
                if model in company_env:
                    # Skip restricted/system models
                    if model.startswith(restricted_prefixes):
                        continue
                    try:
                        model_obj = company_env[model]
                        # Skip abstract models which don't have tables/access rules
                        if model_obj._abstract:
                            continue
                        if model_obj.has_access('read'):
                            permissions.append(model)
                    except Exception:
                        pass
            
            companies_data.append({
                'id': company.id,
                'name': company.name,
                'permissions': permissions
            })
            
        return {
            'user': {
                'id': user.id,
                'name': user.name,
            },
            'companies': companies_data
        }
