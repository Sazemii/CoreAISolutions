from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
from pytz import timezone,utc
from datetime import datetime,timedelta,time
import logging
_logger=logging.getLogger(__name__)
DF='%Y-%m-%d'
class HrLeave(models.Model):
	_inherit='hr.leave';payslip_id=fields.Many2one('hr.ph.payslip','Payslip',readonly=True,ondelete='set null',copy=False);payroll_name=fields.Many2one(related='payslip_id.payroll_id',string='Payroll Link',readonly=True)
	def _validate_leave_request(B):
		super(HrLeave,B)._validate_leave_request();C=B
		for A in C:D=B.sudo().env['ez.time.record'].search([('employee_id','=',A.employee_id.id),('date','>=',A.request_date_from),('date','<=',A.request_date_to)]);D.write({'note':A.holiday_status_id.name})
		return True
	def _get_duration(A,check_leave_type=True,resource_calendar=None):
		A.ensure_one()
		if not(A.holiday_status_id.name or'').lower()=='maternity leave':return super()._get_duration(check_leave_type=check_leave_type,resource_calendar=resource_calendar)
		else:
			E,D=0,0;B=datetime.combine(A.date_from.date(),time.min);C=datetime.combine(A.date_to.date(),time.max)
			if not B.tzinfo:B=B.replace(tzinfo=utc)
			if not C.tzinfo:C=C.replace(tzinfo=utc)
			D=(C-B).total_seconds()/36e2;E=D/24.;return E,D