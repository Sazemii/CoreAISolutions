from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
from odoo.addons.ez_sql import execute_insert
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import config
from pytz import timezone,utc
import random,time,logging
_logger=logging.getLogger(__name__)
class Attendance(models.Model):
	_inherit='hr.attendance'
	@api.model
	def create_demo_data(self,months=24):
		A=self;C=fields.Date.from_string(fields.Date.today()).replace(day=1)-relativedelta(months=months);I=fields.Date.today();J=A.env['hr.employee'].search([]);K=A.env['ez.time.card'].TIMEZONE_ADJUSTMENT();D=[];L=A.search([]);L.unlink()
		while C<I:
			for F in J:
				G=1
				if C.weekday()==6:G=random.randrange(1,31)
				if G==1:
					B=datetime.combine(C,datetime.min.time()).replace(hour=8,minute=0);B-=K;H=B+relativedelta(hours=9);M=random.randrange(1,6)
					if M==1:B+=relativedelta(minutes=random.randrange(1,20))
					N=random.randrange(1,6)
					if N==1:H+=relativedelta(minutes=random.randrange(10,120))
					O=timezone(F._get_tz());P=utc.localize(B).astimezone(O).date();Q={'employee_id':F.id,'check_in':B,'check_out':H,'date':P};D.append(Q)
			C+=relativedelta(days=1)
		if D:A.env.cr.execute('DELETE FROM hr_attendance');execute_insert(A,D,fast_mode=True)
		E=A.env['ez.time.card'].search([]);E.sudo().to_draft();E.sudo().fill_from_attendance();E.sudo().approve_record()
class TimeCard(models.Model):
	_inherit='ez.time.card'
	@api.model
	def create_demo_data(self,date_end=False,months=24,fast_mode=True,no_delete=False):
		J=fast_mode;I=date_end;G=months;B=self
		def R(self,new_recs):
			with self.env.cr.savepoint():execute_insert(self.env['ez.time.card'],new_recs,fast_mode=True)
		if not no_delete:B.env.cr.execute('DELETE FROM ez_time_card');B.env['ez.time.card'].invalidate_recordset();B.env.cr.execute('DELETE FROM ez_time_record');B.env['ez.time.record'].invalidate_recordset()
		if I:H=fields.Date.from_string(I).replace(day=1)-relativedelta(months=G)
		else:H=fields.Date.from_string(fields.Date.today()).replace(day=1)-relativedelta(months=G)
		N=H+relativedelta(months=G,days=-1);O=B.env['hr.employee'].search([('exclude_create_timecard','=',False)]);S=B.env['ez.time.card'].TIMEZONE_ADJUSTMENT();E=[];K=B.env['ez.time.card']
		for A in O:
			C=H
			while C<=N and A.shift_id:
				_logger.debug('DEMO: %s %s',A.name,A.shift_id.name);L={'employee_id':A.id,'date1':C,'date2':C+relativedelta(days=14),'note':'Demo Time Card1','state':'draft','shift_id':A.shift_id.id,'auto_auth':A.shift_id.auto_auth,'flex_time':A.shift_id.flex_time,'minimum_ot_minutes':A.shift_id.minimum_ot_minutes,'late_allowance_minutes':A.shift_id.late_allowance_minutes};E.append(L);M={'employee_id':A.id,'date1':C+relativedelta(days=15),'date2':C+relativedelta(months=1,days=-1),'note':'Demo Time Card2','state':'draft','shift_id':A.shift_id.id,'auto_auth':A.shift_id.auto_auth,'flex_time':A.shift_id.flex_time,'minimum_ot_minutes':A.shift_id.minimum_ot_minutes,'late_allowance_minutes':A.shift_id.late_allowance_minutes};E.append(M)
				if not J:
					with B.env.cr.savepoint():
						P=K.create(L);Q=K.create(M)
						for D in[P,Q]:D._name_compute();D.gen_default_lines();D.fill_from_attendance(summarized=False);D.approve_record()
				C+=relativedelta(months=1)
		if J:
			if E:execute_insert(B.env['ez.time.card'],E,fast_mode=True)
			F=B.env['ez.time.card'].search([]);F._name_compute()
			for D in F:D.gen_default_lines()
			F.fill_from_attendance(summarized=False);F.approve_record()