# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class BirConfigSetPinWizard(models.TransientModel):
    """Wizard to set the manager PIN for BIR Config"""
    _name = 'bir.config.set.pin.wizard'
    _description = 'Set Manager PIN Wizard'
    
    config_id = fields.Many2one(
        'bir.config',
        string='BIR Configuration',
        required=True,
        readonly=True
    )
    
    new_pin = fields.Char(
        string='New PIN',
        size=6,
        required=True,
        help='Enter a 4-6 digit PIN'
    )
    
    confirm_pin = fields.Char(
        string='Confirm PIN',
        size=6,
        required=True,
        help='Re-enter the PIN to confirm'
    )
    
    @api.constrains('new_pin')
    def _check_pin_format(self):
        """Ensure PIN is numeric and correct length"""
        for wizard in self:
            if wizard.new_pin:
                if not wizard.new_pin.isdigit():
                    raise ValidationError(_("PIN must contain only numbers."))
                if len(wizard.new_pin) < 4:
                    raise ValidationError(_("PIN must be at least 4 digits."))
    
    def action_set_pin(self):
        """Set the manager PIN"""
        self.ensure_one()
        
        if self.new_pin != self.confirm_pin:
            raise UserError(_("PINs do not match. Please try again."))
        
        # Set the PIN
        self.config_id.write({'manager_pin': self.new_pin})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Manager PIN has been set successfully.'),
                'type': 'success',
                'sticky': False,
            }
        }


