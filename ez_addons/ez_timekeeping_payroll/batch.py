from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
import time,logging
_logger=logging.getLogger(__name__)
class TimeCardBatch(models.TransientModel):
	_inherit='wz.timecard.batch'
	@api.model
	def get_employees(self,company_id,skip_no_shift):
		A=[('company_id','=',company_id),('exclude_create_timecard','=',False),('exclude_from_payroll','=',False)]
		if skip_no_shift:A.append(('shift_id','!=',False))
		B=self.sudo().env['hr.employee'].search(A);return B