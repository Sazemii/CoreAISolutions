from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError,UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
from.timepairs import TimePairs
from.util import parse_sched,min_to_hstr,min_to_dhstr,min_to_hstr2
from.timeutils import timestr_to_timepair,compute_worktime,get_demo_timelog
_logger=logging.getLogger(__name__)
DF='%Y-%m-%d'
class Shift(models.Model):
	_name='ez.shift';_description='Shift';_order='name';name=fields.Char(required=True);auto_auth=fields.Boolean('Auto-authorize',help='Employees on this shift have flexible time hours.');flex_time=fields.Boolean('Flex Time',help='Employees on this shift have flexible time hours.');early_overtime=fields.Boolean('Early Overtime',help='Employees can have overtime work earlier than schedule.');rounding_regular_work_minutes=fields.Integer('Rounding Reg. Work',help='Floor rounding regular work in minutes.');minimum_ot_minutes=fields.Integer(string='Minimum O.T.',help='Minimum time in minutes to consider as overtime.');rounding_ot_minutes=fields.Integer(string='Rounding O.T.',help='Time in minutes to reach rounded off overtime.');late_allowance_minutes=fields.Integer(string='Late Allowance',help='Maximum late allowance time in minutes.');note=fields.Char('Notes');default_schedule=fields.Char('Default Schedule',required=True,help='Enter time in pairs. Prefix with N for next day. Example: 6p 10p 11p N07:30',default='08:00-11:30 12:30-17:00');details=fields.One2many('ez.shift.details','shift_id','Shift Details');invisible_sched=fields.Boolean(compute='_get_invisible_sched')
	def _get_invisible_sched(A):
		for B in A:B.invisible_sched=False
	@api.onchange('default_schedule')
	def onchange_sched(self):
		for B in self:
			A=parse_sched(B.default_schedule);C=[]
			for D in range(0,len(A),2):C.append('%s-%s'%(A[D],A[D+1]))
			B.default_schedule=' '.join(C)
	def create_details(B):
		for A in B:
			C=B.env['ez.shift.details']
			for D in range(7):
				E='%d'%D;F=C.search([('shift_id','=',A.id),('day','=',E)])
				if A.default_schedule and not F:C.create({'shift_id':A.id,'day':E,'day_off':D==0 and True,'schedule':A.default_schedule})
	@api.model
	def get_schedule(self,date1,date2):
		self.ensure_one();A=fields.Date.from_string(date1);E=fields.Date.from_string(date2);B={}
		for C in self.details:B[C.day]=C
		D={}
		while A<=E:D[A.strftime(DF)]=B.get(A.strftime('%w'));A+=relativedelta(days=1)
		return D
	@api.model
	def create_demo_data(self):0
	@api.model
	def compute_total_minutes(self,schedule):A=timestr_to_timepair(schedule);return A.get_minutes()
	@api.model
	def format_schedule(self,schedule,error=True):
		C=schedule;A=False
		if C:
			B=parse_sched(C,error=error);A=[]
			for D in range(0,len(B),2):A.append('%s-%s'%(B[D],B[D+1]))
			A=' '.join(A)
		return A
days=[('0','Sunday'),('1','Monday'),('2','Tuesday'),('3','Wednesday'),('4','Thursday'),('5','Friday'),('6','Saturday')]
class ShiftDetails(models.Model):
	_name='ez.shift.details';_description='Shift Details';_order='day';shift_id=fields.Many2one('ez.shift','Shift',required=True,ondelete='cascade');day=fields.Selection(days,'Day',required=True);schedule=fields.Char(required=True,help='Enter time in pairs. Prefix with N for next day. Example: 6p 10p 11p N07:30');day_off=fields.Boolean(string='Day-off')
	@api.onchange('schedule')
	def onchange_sched(self):
		for B in self:
			A=parse_sched(B.schedule);C=[]
			try:
				for D in range(0,len(A),2):C.append('%s-%s'%(A[D],A[D+1]))
			except:raise UserError(_('Error in schedule, auto-fill schedule first.'))
			B.schedule=' '.join(C)
	@api.model
	def get_day_type(self,date,holidays):
		B=self;B.ensure_one();C=holidays.get(date)
		if C:
			if B.day_off:A='do_'+C
			else:A=C
		elif B.day_off:A='do'
		else:A='reg'
		return A