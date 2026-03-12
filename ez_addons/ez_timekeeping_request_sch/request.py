from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError,UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import base64,time,logging
_logger=logging.getLogger(__name__)
class RequestsBulk(models.Model):
	_inherit='ez.time.request.bulk';type=fields.Selection(selection_add=[('sch','Change Schedule')]);day_type=fields.Selection(selection=lambda self:self.env['ez.time.record']._get_day_type_selection(),string='Day Type');schedule=fields.Char('Schedule',help='Enter time in pairs. Prefix with N for next day. Example: 6p 10p 11p N07:30')
	@api.model
	def custom_add(self,rec,request,employee_id):
		B=request;A=self;C=super(RequestsBulk,A).custom_add(rec,B,employee_id)
		if B.type=='sch'and(A.day_type or A.schedule):rec.update({'day_type':A.day_type,'schedule':A.schedule});return True
		else:return C
	@api.onchange('schedule')
	def onchange_sched(self):
		E=self.env['ez.time.record']
		for A in self:
			if A.schedule:
				B=E.parse_sched(A.schedule);C=[]
				for D in range(0,len(B),2):C.append('%s-%s'%(B[D],B[D+1]))
				A.schedule=' '.join(C)
class Requests(models.Model):
	_inherit='ez.time.request';type=fields.Selection(selection_add=[('sch','Change Schedule')]);day_type=fields.Selection(selection=lambda self:self.env['ez.time.record']._get_day_type_selection(),string='Day Type');schedule=fields.Char('Schedule',help='Enter time in pairs. Prefix with N for next day. Example: 6p 10p 11p N07:30')
	@api.onchange('schedule')
	def onchange_sched(self):
		E=self.env['ez.time.record']
		for A in self:
			if A.schedule:
				B=E.parse_sched(A.schedule);C=[]
				for D in range(0,len(B),2):C.append('%s-%s'%(B[D],B[D+1]))
				A.schedule=' '.join(C)