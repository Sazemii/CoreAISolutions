from odoo import api,fields,models,tools,_
import logging
_logger=logging.getLogger(__name__)
class Payslip(models.Model):_inherit='hr.ph.payslip';signature_enabled=fields.Boolean(related='company_id.signature_enabled');is_signed=fields.Boolean()