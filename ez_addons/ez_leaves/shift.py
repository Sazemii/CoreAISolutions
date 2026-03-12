from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError,UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
_logger=logging.getLogger(__name__)
DF='%Y-%m-%d'
class Shift(models.Model):
	_inherit='ez.shift'
	def sync_working_schedule(J):
		L=J.env['resource.calendar'];M={'0':'Monday','1':'Tuesday','2':'Wednesday','3':'Thursday','4':'Friday','5':'Saturday','6':'Sunday'}
		def O(l,n):return[l[A:A+n]for A in range(0,len(l),n)]
		def D(hrs):
			B=hrs;A=B.split(':')
			if len(A)!=2:return .0
			else:
				C=int(A[1]);B=.0
				if A[0][0]=='N':A[0]=A[0][1:];B=24.
				B+=int(A[0]);return B+C/6e1
		for I in J:
			A=L.search([('name','=',I.name)],limit=1)
			if not A:A=L.create({'name':I.name,'two_weeks_calendar':False})
			A.attendance_ids.unlink()
			for K in I.details:
				if not K.day_off:
					P=K.schedule.replace('-',' ').split();Q=O(P,2)
					for E in Q:
						B=int(K.day)-1;C=D(E[0]);F=D(E[1]);N=False
						if E[0][0]=='N':B+=1;C-=24.;F-=24.
						elif E[1][0]=='N':F=D('24:00');N=True
						G=C<12. and'morning'or'afternoon';H={'name':'%s %s'%(M.get('%s'%(B%7),'Undefined'),G.title()),'dayofweek':'%s'%(B%7),'day_period':G,'hour_from':C,'hour_to':F,'calendar_id':A.id};_logger.debug('sync_working_schedule 1: %s',H);A.attendance_ids.create(H)
						if N:C=D('24:00')-24.;F=D(E[1])-24.;B+=1;G=C<12. and'morning'or'afternoon';H={'name':'%s %s'%(M.get('%s'%(B%7),'Undefined'),G.title()),'dayofweek':'%s'%(B%7),'day_period':G,'hour_from':C,'hour_to':F,'calendar_id':A.id};_logger.debug('sync_working_schedule 2: %s',H);A.attendance_ids.create(H)
			R=J.env['hr.employee'].search([('shift_id','=',I.id)])
			for S in R:S.resource_calendar_id=A.id
class ResourceCalendarAttendance(models.Model):
	_inherit='resource.calendar.attendance'
	@api.depends('day_period','duration_hours')
	def _compute_duration_days(self):
		for A in self:
			if A.day_period=='lunch':A.duration_days=0
			else:
				_logger.debug('_compute_duration_days: %s %s %s',A.duration_hours,A.hour_from,A.hour_to)
				if A.calendar_id.hours_per_day>.0:A.duration_days=A.duration_hours/8.
				else:A.duration_days=1.
	@api.onchange('hour_from','hour_to')
	def _onchange_hours(self):A=self.hour_to;super()._onchange_hours();self.hour_to=min(A,48)