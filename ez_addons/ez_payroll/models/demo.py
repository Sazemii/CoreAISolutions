from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging,random
_logger=logging.getLogger(__name__)
DEBUG=0
DF='%Y-%m-%d'
today=datetime.now()
def_date1=today-relativedelta(days=5)
def_date2=def_date1+relativedelta(days=15)
def dprint(s):_logger.debug(s)
tax_code_list=[('Z','Zero Exemption'),('S/ME','Single or Married with no dependent'),('ME1/S1','Single or Married with 1 dependent'),('ME2/S2','Single or Married with 2 dependents'),('ME3/S3','Single or Married with 3 dependents'),('ME4/S4','Single or Married with 4 or more dependents')]
def rand_choice(arr):return arr[random.randint(0,len(arr)-1)]
class HrEmployee(models.Model):
	_inherit='hr.employee'
	@api.model
	def create_demo_data(self):
		dprint('***CREATE EMPLOYEE DEMO DATA');D=self.search([]);B=0
		for A in D:
			dprint('***CREATE EMPLOYEE DEMO DATA: %s'%A.name);B+=1
			if not A.salary_rate:
				if B==4:C=1e1
				else:C=.0
				A.write({'salary_rate_period':'monthly','salary_rate':1e4+random.random()*5e4,'tax_code':'Z','wtax_percent':C})
class Payroll(models.Model):
	_inherit='hr.ph.payroll'
	@api.model
	def create_demo_data(self,name,date1,date2,set_as_done):
		B=name;dprint('***CREATE DEMO PAYROLL %s'%B);A=self.search([('name','=',B)])
		if A:return False
		A=self.create({'name':B,'date_from':date1,'date_to':date2});A.auto_gen()
		if set_as_done:A.set_as_done()
		return True
class deduction_entry(models.Model):
	_inherit='hr.ph.pay.deduction.entry'
	@api.model
	def create_demo_data(self,date,name):
		B=self;dprint('***CREATE DEMO DATA DEDUCTIONS: %s'%name);C=B.env['hr.employee'].search([]);D=[]
		for G in range(1,len(C),2):D.append('%06d'%G)
		C=B.env['hr.employee'].search([('identification_id','in',D)]);E=name;A=B.search([('name','=',E)])
		if A:return False
		F=0;A=B.create({'name':E,'date':date})
		for H in C:F+=10;A.ded_detail_ids.create({'other_deduction_id':A.id,'seq':F,'employee_id':H.id,'amount':2e3*random.random()})
		A.state='done';return True
class WorkSummary(models.Model):
	_inherit='ez.work.summary.sheet'
	@api.model
	def create_demo_data(self,name,date,regular=True):
		C=name;A=self;dprint('***CREATE DEMO WORK SUMMARY SHEET: %s'%C);E=A.env['ez.work.summary.sheet'].search([('name','=',C)])
		if len(E)>0:return False
		F=A.env.ref('ez_payroll.wtg_default').id;J=A.env['hr.employee'].search([]);O=A.env['ez.work.type'].search([('work_type_group_id','=',F)])
		if regular:
			G=E.create({'name':C,'date':date,'work_type_group_id':F});M=A.env.ref('ez_payroll.wt_reg_norm').id;B=10
			for H in J:I=G.work_summary_line.create({'work_summary_sheet_id':G.id,'employee_id':H.id,'qty':.5,'work_type_id':M,'seq':B});B+=10;I.work_type_id_changed();I.unit='month'
			G.state='done'
		else:
			N=['wt_SPL','wt_VL','wt_CL','wt_PL','wt_ML','wt_LWOP','wt_SIL','wt_SL','wt_LHP'];D=E.create({'name':C,'date':date,'work_type_group_id':F});B=10
			for H in J:
				if 1:K=round(random.random()*22.-2.,2);L=A.env.ref('ez_payroll.wt_ADJ').id
				else:K=2.+round(random.random()*8.,4);L=A.env.ref('ez_payroll.%s'%rand_choice(N)).id
				I=D.work_summary_line.create({'work_summary_sheet_id':D.id,'employee_id':H.id,'qty':K,'seq':B,'work_type_id':L});B+=10
			D.work_summary_line.work_type_id_changed();D.state='done'
		return True
class Loan(models.Model):
	_inherit='hr.ph.loan'
	@api.model
	def create_demo_data(self,date,name):
		B=name;A=self;dprint('***CREATE DEMO LOANS: %s'%B);C=A.env['hr.ph.loan'].search([('name','ilike',B)])
		if len(C)>0:return False
		F=A.env['hr.employee'].search([]);G=A.env['hr.ph.loan.type'].search([]);H=[1e3,15e2,2e3,25e2];I=[2,6,12,24];J=0
		for D in F:J+=1;K=rand_choice(G).id;E=rand_choice(H);L=rand_choice(I)*E;C.create({'name':'%s %s'%(B,D.identification_id),'employee_id':D.id,'loan_type_id':K,'date':date,'date_start':date,'amortization':E,'amount':L,'state':'confirmed'})
		return True