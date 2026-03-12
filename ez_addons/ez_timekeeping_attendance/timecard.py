from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time,re,logging
_logger=logging.getLogger(__name__)
class TimeRecordDetail(models.Model):
	_inherit='ez.time.record'
	def get_time_logs(B,demo=False):
		for A in B:
			if not demo:
				if A.day_type=='reg':A.timelog=False
			elif A.schedule:A.timelog,A.auth_hrs=get_demo_timelog(A.schedule)
class Attendance(models.Model):_inherit='hr.attendance';check_in=fields.Datetime(index=True)
class TimeCard(models.Model):
	_inherit='ez.time.card'
	def test_demo(A):A.env['hr.attendance'].create_demo_data()
	def TIMEZONE_ADJUSTMENT(A):return relativedelta(hours=8)
	def fill_from_attendance(F,summarized=True):
		def L(hrs):
			A=hrs;B=0
			if A[0]=='N':B+=1440;A=A[1:]
			C=A.split(':');B+=60*int(C[0])+int(C[1]);return B
		def M(dt,schedule):
			A=schedule
			if not A:return dt,dt
			B=re.split('\\s|-',A);C=B[0];D=B[-1];E=L(C);F=L(D);return dt+relativedelta(minutes=E),dt+relativedelta(minutes=F)
		E=F.TIMEZONE_ADJUSTMENT();J=set()
		for G in F:
			if G.state!='draft':raise ValidationError(_('You can only auto-fill logs on draft time cards. %s')%G.name)
			for B in G.details:
				C=fields.Date.from_string(B.date)-E;K=C+relativedelta(hours=24)+E;N=C+relativedelta(hours=48)+E;O=C+relativedelta(hours=24);P,Q=M(C,B.schedule);_logger.debug('sched: dt=%s sched=%s-%s',C,P,Q);R=F.env['hr.attendance'].search([('employee_id','=',B.employee_id.id),('check_in','>=',C),('check_in','<',O)],order='check_in asc');A=[]
				for D in R:
					_logger.debug('%s: %s %s',B.date,D.check_in,D.check_out)
					if D.check_in and D.check_out:
						H=fields.Datetime.from_string(D.check_in)+E;_logger.debug('check: t0=%s nextday=%s',H,K)
						if H>=K:A.append(H.strftime('N%H:%M'))
						else:A.append(H.strftime('%H:%M'))
						I=fields.Datetime.from_string(D.check_out)+E
						if I>=N:A.append('N23:59')
						elif I>=K:A.append(I.strftime('N%H:%M'))
						else:A.append(I.strftime('%H:%M'))
				S=' '.join(A)
				if A and S!=B.timelog:B.timelog=' '.join(A);J.add(G.id)
		if J and summarized:T=F.env['ez.time.card'].browse(list(J));T.summarize()
class TimeCardBatch(models.TransientModel):
	_inherit='wz.timecard.batch'
	def batch_generate_fill_attendance(A):A.run_background=False;A.generate_timecards();A.batch_fill_attendance();return{'type':'ir.actions.client','tag':'reload'}
	def batch_fill_attendance(A):
		A.ensure_one()
		if not A.date1 or not A.date2 or A.date1>A.date2:raise ValidationError(_('Incomplete or wrong date range.'))
		B=A.env['ez.time.card'].search([('company_id','=',A.company_id.id),('date1','=',A.date1),('date2','=',A.date2)]);_logger.debug('batch_fill_time_logs');B.fill_from_attendance();return{'type':'ir.actions.client','tag':'reload'}