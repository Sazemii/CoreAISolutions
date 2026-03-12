from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
import logging
_logger=logging.getLogger(__name__)
DF='%Y-%m-%d'
class TimeCard(models.Model):
	_inherit='ez.time.card'
	def gen_default_lines(B,demo=False):
		G=super(TimeCard,B).gen_default_lines(demo=demo)
		for A in B:
			C=fields.Date.to_string(A.date1);D=fields.Date.to_string(A.date2);F=B.sudo().env['hr.leave'].search([('employee_id','=',A.employee_id.id),('state','=','validate'),'|','|','&',('request_date_from','<=',C),('request_date_to','>=',C),'&',('request_date_from','<=',D),('request_date_to','>=',D),'|','&',('request_date_from','>=',C),('request_date_from','<=',D),'&',('request_date_to','>=',C),('request_date_to','<=',D)]);_logger.debug('ez_leaves: leaves=%s',F)
			for E in F:H=B.sudo().env['ez.time.record'].search([('employee_id','=',A.employee_id.id),('timecard_id','=',A.id),('date','>=',E.request_date_from),('date','<=',E.request_date_to)]);H.write({'note':E.holiday_status_id.name})
		return G