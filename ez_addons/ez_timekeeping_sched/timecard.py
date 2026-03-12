from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
_logger=logging.getLogger(__name__)
DF='%Y-%m-%d'
class TimeCard(models.Model):
	_inherit='ez.time.card'
	@api.model
	def _get_schedule(self):
		A=self;B=super(TimeCard,A)._get_schedule();D=A.env['ez.shift.sched.line'].search([('shift_id','=',A.shift_id.id),('date','>=',A.date1),('date','<=',A.date2)],order='id')
		for C in D:E=fields.Date.to_string(C.date);B[E]=C
		return B