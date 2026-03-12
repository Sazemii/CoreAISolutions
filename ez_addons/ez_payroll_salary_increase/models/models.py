from odoo import models,fields,api
from dateutil.relativedelta import relativedelta
import logging
_logger=logging.getLogger(__name__)
SALARY_RATES={'daily':'per day','monthly':'per month'}
class Payroll(models.Model):
	_inherit='hr.ph.payroll'
	@api.model
	def get_emp_rates(self,employee_id,date_from,date_to):
		B=employee_id;A=super().get_emp_rates(B,date_from,date_to);D,E,F,C,G=self.get_current_salary_rates(B);A.update({'salary_rate':D,'salary_rate_period':E,'emr_days':F,'is_salary_averaged':C})
		if C:A.update({'note':G})
		return A
	@api.model
	def get_current_salary_rates(self,employee_id):
		E=self;J=employee_id;D=.0;F='monthly';G=313;I=False;K=False
		if J:
			A=E.env['ez.employee.salary.rate'].search([('employee_id','=',J.id),('date','<=',E.date_to)],order='date desc',limit=2)
			if A:
				if E.is_13th_month:D=A[0].salary_rate;F=A[0].salary_rate_period;G=A[0].emr_days;I=False
				elif A[0].date<=E.date_from:D=A[0].salary_rate;F=A[0].salary_rate_period;G=A[0].emr_days
				elif len(A)==1:D=A[0].salary_rate;F=A[0].salary_rate_period;G=A[0].emr_days
				else:
					F=A[0].salary_rate_period;G=A[0].emr_days;L=fields.Date.from_string(E.date_from);M=fields.Date.from_string(E.date_to);H=fields.Date.from_string(A[0].date);B=(M-H).days+1;C=(H-L).days
					if A[0].salary_rate_period==A[1].salary_rate_period:D=round(A[0].salary_rate*B/(B+C)+A[1].salary_rate*C/(B+C),2)
					elif A[0].salary_rate_period=='monthly':N=A[1].salary_rate*A[1].emr_days/12.;D=round(A[0].salary_rate*B/(B+C)+N*C/(B+C),2)
					else:O=A[1].salary_rate*12./A[1].emr_days;D=round(A[0].salary_rate*B/(B+C)+O*C/(B+C),2)
					I=True;K='Pro-rated salary : %s %s.\nFrom %s to %s: %s %s\nFrom %s to %s: %s %s'%('{:,.2f}'.format(D),A[1].salary_rate_period,L.strftime('%B %d, %Y'),(H-relativedelta(days=1)).strftime('%B %d, %Y'),'{:,.2f}'.format(A[1].salary_rate),A[1].salary_rate_period,H.strftime('%B %d, %Y'),M.strftime('%B %d, %Y'),'{:,.2f}'.format(A[0].salary_rate),A[0].salary_rate_period)
		return D,F,G,I,K
	def add_new_employee(B,salary_rate=False,salary_rate_period=False,emr_days=False):
		E=emr_days;D=salary_rate_period;C=salary_rate;G=B.add_employee_id;C,D,E,F,H=B.get_current_salary_rates(G);A=super().add_new_employee(salary_rate=C,salary_rate_period=D,emr_days=E);A.is_salary_averaged=F
		if F:A.note=H
		return A
class Payslip(models.Model):_inherit='hr.ph.payslip';is_salary_averaged=fields.Boolean()
class HrEmployee(models.Model):
	_inherit='hr.employee';salary_rate_ids=fields.One2many('ez.employee.salary.rate','employee_id','Salary Rates',groups='ez_payroll.group_hr_payroll_user');salary_rate_now=fields.Float('Salary Rate Now',digits='Payroll Amount',compute='get_salary_rate_now',groups='ez_payroll.group_hr_payroll_user');salary_rate_period_now=fields.Char('Rate Period Now',compute='get_salary_rate_now',groups='ez_payroll.group_hr_payroll_user');emr_days_now=fields.Integer(string='EMR Days',compute='get_salary_rate_now',groups='ez_payroll.group_hr_payroll_user');salary_rate=fields.Float(compute='get_salary_rate',store=True,tracking=True);salary_rate_period=fields.Selection(compute='get_salary_rate',store=True);emr_days=fields.Integer(compute='get_salary_rate',store=True)
	@api.depends('salary_rate_ids','salary_rate_ids.salary_rate','salary_rate_ids.salary_rate_period','salary_rate_ids.emr_days')
	def get_salary_rate(self):
		for A in self:B=self.env['ez.employee.salary.rate'].search([('employee_id','=',A.id)],order='date desc',limit=1);A.salary_rate=B.salary_rate;A.salary_rate_period=B.salary_rate_period;A.emr_days=B.emr_days
	@api.model
	def get_salary_rate_current(self,employee_id,date):A=self.env['ez.employee.salary.rate'].search([('employee_id','=',employee_id.id),('date','<=',date)],order='date desc',limit=1);B=A.salary_rate;C=A.salary_rate_period;D=A.emr_days;return B,C,D
	def get_salary_rate_now(C):
		for A in C:B=C.env['ez.employee.salary.rate'].search([('employee_id','=',A.id),('date','<=',fields.Date.today())],order='date desc',limit=1);A.salary_rate_now=B.salary_rate;A.salary_rate_period_now=SALARY_RATES.get(B.salary_rate_period,'monthly');A.emr_days_now=B.emr_days
	@api.model
	def compute_salary_rates_model(self):
		A=self.search([]);B=self.env['ez.employee.salary.rate'].search([])
		if len(B.ids)==0:A.compute_salary_rates()
	def compute_salary_rates(C):
		for B in C:
			G=C.env['ez.employee.salary.rate'].search([('is_recomputed','=',True),('employee_id','=',B.id)]);G.unlink();J=C.env['hr.ph.payslip'].search([('employee_id','=',B.id),('state','!=','draft')],order='date_from asc');I=True
			for A in J:
				if I:D,E,F=B.get_salary_rate_current(B,A.date_to);I=False
				if D!=A.salary_rate or E!=A.salary_rate_period or F!=A.emr_days:
					D,E,F=B.get_salary_rate_current(B,A.date_to)
					if not A.is_salary_averaged and(D!=A.salary_rate or E!=A.salary_rate_period or F!=A.emr_days):
						H={'employee_id':B.id,'date':A.date_from,'salary_rate':A.salary_rate,'salary_rate_period':A.salary_rate_period,'emr_days':A.emr_days,'is_recomputed':True};K=C.env['ez.employee.salary.rate'].search([('employee_id','=',B.id),('date','=',A.date_from)])
						if not K:C.env['ez.employee.salary.rate'].create(H);D=A.salary_rate;E=A.salary_rate_period;F=A.emr_days
			G=C.env['ez.employee.salary.rate'].search([('employee_id','=',B.id)])
			if not G:H={'employee_id':B.id,'date':fields.Date.today().strftime('%Y-01-01'),'salary_rate':B.salary_rate,'salary_rate_period':B.salary_rate_period,'emr_days':B.emr_days,'is_recomputed':False};C.env['ez.employee.salary.rate'].create(H)
	def _get_daily_rate(C,date=False):
		D=date;C.ensure_one
		if not D:D=fields.Date.today()
		A,E,F=C.get_salary_rate_current(C,D)
		if E=='monthly':
			if F>0:B=A*12./F
			else:B=A*12./313.
		else:B=A
		_logger.debug('_get_daily_rate 2 Salary Rate: %s %s daily=%s',A,E,B);return B,A,E,F
class EmployeeSalaryRate(models.Model):
	_name='ez.employee.salary.rate';_description='Employee Salary Rates';_order='date desc';_unique_emp_date=models.Constraint('UNIQUE(employee_id, date)','Duplicate date and employee on Salary Rates.');date=fields.Date(required=True,index=True);employee_id=fields.Many2one('hr.employee','Employee',required=True,ondelete='cascade',index=True);salary_rate=fields.Float('Salary Rate',digits='Payroll Amount');salary_rate_period=fields.Selection([('daily','per day'),('monthly','per month')],'Rate Period',default='monthly',required=True);daily_rate=fields.Float(compute='compute_daily_rate',digits='Payroll Amount');emr_days=fields.Integer(string='Working Days',default=313,help='Working days in a year. Factor in computing daily rate for monthly employees.');is_recomputed=fields.Boolean()
	@api.onchange('employee_id')
	def oc_employee_id(self):self.emr_days=self.employee_id.emr_days
	@api.depends('salary_rate','salary_rate_period','emr_days')
	def compute_daily_rate(self):
		for A in self:
			if A.salary_rate_period=='monthly':
				if A.emr_days>0:A.daily_rate=A.salary_rate*12./A.emr_days
				else:A.daily_rate=A.salary_rate*12./314.
			else:A.daily_rate=A.salary_rate