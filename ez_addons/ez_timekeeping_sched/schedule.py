from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
_logger=logging.getLogger(__name__)
DF='%Y-%m-%d'
class Schedule(models.Model):
	_name='ez.shift.sched';_description='Shift Work Schedule';_order='date_from desc,name';name=fields.Char(required=True);shift_id=fields.Many2one('ez.shift','Shift',required=True,ondelete='restrict');date_from=fields.Date(required=True);date_to=fields.Date(required=True);note=fields.Text('Notes');lines=fields.One2many('ez.shift.sched.line','sched_id','Work Schedule Lines')
	def delete_schedule_lines(A):A.ensure_one();A.lines.unlink()
	def gen_schedule_lines(C):
		C.ensure_one();A=C;B=fields.Date.from_string(A.date_from);J=fields.Date.from_string(A.date_to);F=set()
		for K in A.lines:F.add(fields.Date.from_string(K.date))
		G={}
		for H in C.env['ez.holiday'].search([('date','>=',A.date_from),('date','<=',A.date_to)]):L=fields.Date.to_string(H.date);G[L]=H.type
		M=A.shift_id.get_schedule(A.date_from,A.date_to);D=[]
		while B<=J:
			I=B.strftime('%Y-%m-%d');E=M.get(B.strftime(DF))
			if E and B not in F:N=E.get_day_type(I,G);O={'sched_id':C.id,'date':I,'schedule':E.schedule,'day_type':N};D.append([0,0,O])
			B+=relativedelta(days=1)
		if D:A.lines=D
class ScheduleLine(models.Model):
	_name='ez.shift.sched.line';_description='Shift Work Schedule Line';_order='date asc';sched_id=fields.Many2one('ez.shift.sched','Work Schedule',required=True,ondelete='cascade');shift_id=fields.Many2one(string='Shift',related='sched_id.shift_id',store=True);date=fields.Date('Date',required=True,index=True);name=fields.Char(string='Name',compute='_name_compute');dow=fields.Char('Day of Week',compute='_name_compute');schedule=fields.Char('Schedule',required=True,help='Enter time in pairs. Prefix with N for next day. Example: 6p 10p 11p N07:30');day_type=fields.Selection(selection=lambda self:self.env['ez.time.record']._get_day_type_selection(),string='Type',required=True,default='reg');hours=fields.Float('Hours',compute='get_hours')
	@api.model
	def get_day_type(self,date,holidays):return self.day_type
	@api.depends('schedule','sched_id','sched_id.shift_id')
	def get_hours(self):
		for A in self:
			if A.schedule:B=A.sched_id.shift_id.compute_total_minutes(A.schedule);A.hours=round(B/6e1,2)
			else:A.hours=False
	@api.onchange('schedule')
	def onchange_sched(self):
		for A in self:A.schedule=A.sched_id.shift_id.format_schedule(A.schedule)
	@api.depends('date')
	def _name_compute(self):
		for A in self:
			if A.date:B=fields.Date.from_string(A.date);A.name=B.strftime('%m-%d-%Y %a');A.dow=B.strftime('%a')
			else:A.name=False;A.dow=False