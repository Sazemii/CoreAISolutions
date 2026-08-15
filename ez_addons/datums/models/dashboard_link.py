from odoo import models, fields, api
from odoo.exceptions import UserError

class DashboardLink(models.Model):
    _name = 'dashboard.link'
    _description = 'Dashboard Link Configuration'
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True)
    dashboard_link = fields.Char(string='Dashboard Link', required=True, help="Enter the dashboard URL")
    active = fields.Boolean(string='Active', default=True)
    description = fields.Text(string='Description')
    
    @api.model
    def get_active_dashboard(self):
        """Return active dashboard configuration"""
        return self.search([('active', '=', True)], limit=1)
    
    def action_open_dashboard(self):
        """Open the active dashboard link in an iframe via client action"""
        active_dashboard = self.search([('active', '=', True)], limit=1)
        if not active_dashboard:
            raise UserError("No active dashboard link configured. Please configure one in Settings -> Datums -> Dashboard Configuration.")
        
        return {
            'type': 'ir.actions.client',
            'tag': 'dashboard_viewer_action',
            'params': {
                'url': active_dashboard.dashboard_link,
            },
            'name': active_dashboard.name or 'Dashboard',
        }
