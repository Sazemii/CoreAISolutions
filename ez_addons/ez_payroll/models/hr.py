from odoo import api,fields,models,tools,_
from datetime import datetime
from dateutil.relativedelta import relativedelta
import re
from random import randint
import xlrd,base64,re
from io import BytesIO
import logging
_logger=logging.getLogger(__name__)
class Deminimis(models.Model):_name='ez.deminimis';_description='Deminimis';_inherit=['hr.ph.payslip.line.template'];employee_id=fields.Many2one('hr.employee','Employee',required=True,ondelete='cascade');seq=fields.Integer(readonly=False);name=fields.Char(readonly=False);qty=fields.Float(string='Amount',digits='Payroll Amount');days_variable=fields.Boolean('Days Variable',default=False,help='Amount will be multiplied by basic days.');basic_pay=fields.Boolean(default=False);taxable=fields.Boolean(default=False);unit=fields.Selection(default='fixed');notes=fields.Char('Notes');state=fields.Char(default='draft');payment_days=fields.Char('Payment Day/s',help='Day/s of month payment schedule, set blank if every payroll period. Separate with spaces for multiple days. Ex: 15 30')
tax_code_list=[('Z','Zero Exemption'),('S/ME','Single or Married with no dependent'),('ME1/S1','Single or Married with 1 dependent'),('ME2/S2','Single or Married with 2 dependents'),('ME3/S3','Single or Married with 3 dependents'),('ME4/S4','Single or Married with 4 or more dependents')]
class EmployeeGroup(models.Model):
	_name='ez.employee.group';_description='Employee Group'
	def _get_default_color(A):return randint(1,11)
	_name_uniq=models.Constraint('unique (name)','Group name already exists !');name=fields.Char(string='Group Name',required=True);xls_data=fields.Binary(string='XLS File');xls_filename=fields.Char(string='XLS Filename');color=fields.Integer(string='Color Index',default=_get_default_color);employee_ids=fields.Many2many('hr.employee','employee_group_rel','group_id','emp_id',string='Employees')
	def set_exclude_from_payroll(A):
		for B in A:
			for C in B.employee_ids:C.exclude_from_payroll=True
	def unset_exclude_from_payroll(A):
		for B in A:
			for C in B.employee_ids:C.exclude_from_payroll=False
	def import_xls(A):
		A.ensure_one();I=base64.b64decode(A.xls_data);J=BytesIO(I)
		try:K=xlrd.open_workbook(file_contents=J.getvalue())
		except:raise ValidationError(_('Wrong excel format. Use .XLS format.'))
		F=K.sheet_by_index(0);G=[];H=set();D=0;L=A.env['hr.employee']
		for E in range(F.nrows):
			B=F.cell(E,0).value
			if B:
				C=L.search([('identification_id','=',B.strip())])
				if C:
					G.append(C.id)
					if C.id in H:_logger.debug('DUPLICATE: %s %s %s',D,E,B)
					else:H.add(C.id)
					D+=1
				else:_logger.debug('NOT FOUND: %s %s %s',D,E,B)
		A.employee_ids=[(4,id)for id in G]
class HrEmployee(models.Model):
	_inherit='hr.employee';tax_code=fields.Selection(tax_code_list,'W.Tax Class',default='Z',groups='ez_payroll.group_hr_payroll_user');wtax_percent=fields.Float('W.Tax Percent',digits='Payslip Line Unit',groups='ez_payroll.group_hr_payroll_user',help='Withholding Tax percentage. Set to 0.0 if using table.');salary_rate=fields.Float('Salary Rate',digits='Payroll Amount',groups='ez_payroll.group_hr_payroll_user');salary_rate_period=fields.Selection([('daily','per day'),('monthly','per month')],'Rate Period',default='monthly',groups='ez_payroll.group_hr_payroll_user');emr_days=fields.Integer(string='Working Days',default=313,groups='ez_payroll.group_hr_payroll_user',help='Working days in a year. Factor in computing daily rate for monthly employees.');daily_rate=fields.Float(compute='compute_daily_rate',digits='Payroll Amount',groups='ez_payroll.group_hr_payroll_user');minimum_wage=fields.Boolean('Minimum Wage',groups='ez_payroll.group_hr_payroll_user',help='Enable if employee is minimum wage worker.');no_deductions=fields.Boolean('No Deductions',groups='ez_payroll.group_hr_payroll_user',help='Enable if employee will not have deductions.');exclude_from_payroll=fields.Boolean('Exclude',groups='ez_payroll.group_hr_payroll_user',help='Exclude from payroll computation.');voluntary_hdmf=fields.Float('Voluntary HDMF',digits='Payroll Amount',default=.0,groups='ez_payroll.group_hr_payroll_user',help='Amount of voluntary HDMF contribution of employee.');deminimis_line=fields.One2many('ez.deminimis','employee_id','De minimis',groups='ez_payroll.group_hr_payroll_user');group_ids=fields.Many2many('ez.employee.group','employee_group_rel','emp_id','group_id',groups='hr.group_hr_manager',string='Groups')
	def _get_daily_rate(A,date=False):
		A.ensure_one;_logger.debug('_get_daily_rate Salary Rate: %s',A.salary_rate)
		if A.salary_rate_period=='monthly':
			if A.emr_days>0:B=A.salary_rate*12./A.emr_days
			else:B=A.salary_rate*12./313.
		else:B=A.salary_rate
		return B,A.salary_rate,A.salary_rate_period,A.emr_days
	@api.depends('salary_rate','salary_rate_period','emr_days')
	def compute_daily_rate(self):
		for A in self:A.daily_rate,B,C,D=A._get_daily_rate()