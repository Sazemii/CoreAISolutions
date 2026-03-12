from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
import re,logging
_logger=logging.getLogger(__name__)
class Company(models.Model):
	_inherit='res.company';signature_enabled=fields.Boolean(compute='_compute_signature_enabled')
	def _compute_signature_enabled(A):
		B=int(A.env['ir.config_parameter'].sudo().get_param('ez_hr_esignature.signature_enabled',1))
		for C in A:C.signature_enabled=B and True or False