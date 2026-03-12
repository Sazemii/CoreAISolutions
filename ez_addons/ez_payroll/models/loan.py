from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import re,logging
_logger=logging.getLogger(__name__)
DEBUG=0
EPS=.005
def dprint(s):_logger.debug(s)
class LoanType(models.Model):_name='hr.ph.loan.type';_description='Loan Types';_order='name';company_id=fields.Many2one('res.company',string='Company',default=lambda self:self.env.company);name=fields.Char('Name',required=True);active=fields.Boolean('Active',default=True);note=fields.Text('Notes')
class Loan(models.Model):
	_name='hr.ph.loan';_description='Loan';_inherit=['mail.thread'];_order='date desc'
	def set_as_confirmed(A):
		for B in A:B.state='confirmed'
	def cancel_confirmed(A):
		for B in A:B.state='draft'
	def unlink(A):
		for B in A:
			if B.state!='draft':raise ValidationError(_('You cannot delete a confirmed loan sheet.'))
		return super(Loan,A).unlink()
	@api.depends('payment_line','payment_line.amount','payment_line.payslip_id','payment_line.payslip_id.payroll_id','payment_line.state','amount')
	def sum_payments(self):
		for A in self:
			D=.0;B=.0
			for C in A.payment_line:B+=C.amount
			A.balance=max(.0,A.amount-B);A.payments=B
	@api.depends('payment_line','payment_line.amount','payment_line.payslip_id','payment_line.payslip_id.payroll_id','payment_line.state','amount')
	def sum_cpayments(self):
		for A in self:
			B=.0
			for C in A.payment_line:
				if C.state!='draft':B+=C.amount
			A.cbalance=max(.0,A.amount-B);A.cpayments=B
	@api.model
	def create_loan_line(self,payslip):
		B=payslip;M=B.payroll_id.date_from;E=B.payroll_id.date_to;filter=[('employee_id','=',B.employee_id.id),('state','!=','draft'),('date_start','<=',E),('balance','>',.0)];F=self.search(filter);dprint(' Found: %d'%len(F));G=10
		for A in F:
			C=False;dprint(' Name: %s'%A.name)
			if A.payment_days:
				L=[A for A in re.split('[,\\s]+',A.payment_days.strip())if A];H=['%02d'%int(A)for A in L];I=fields.Date.to_string(E)[8:10];dprint(' Payment days: %s d2=%s'%(H,I))
				if I in H:C=True
			else:C=True
			if C:
				D=min(A.balance,A.amortization)
				if A.init_amort_count:
					J=len(A.payment_line);dprint(' Amort count: %d'%J)
					if J<A.init_amort_count:D=min(A.balance,A.init_amortization)
				if abs(D)>EPS:K={'payslip_id':B.id,'loan_id':A.id,'seq':G,'name':'%s - %s'%(A.loan_type_id.name,A.name),'amount':D};dprint(' Create line: %s'%K);N=A.payment_line.create(K);G+=10
	company_id=fields.Many2one('res.company',string='Company',related='employee_id.company_id');name=fields.Char('Reference No.',required=True);employee_id=fields.Many2one('hr.employee','Employee Name',ondelete='restrict',index=True,required=True);loan_type_id=fields.Many2one('hr.ph.loan.type','Loan Type',ondelete='restrict',required=True);date=fields.Date('Date',required=True);date_start=fields.Date('Payment Start',required=True);amortization=fields.Float('Amortization',digits='Payroll Amount',required=True);init_amortization=fields.Float('Initial Amortization',digits='Payroll Amount');init_amort_count=fields.Integer('Initial Amort. Count');payment_days=fields.Char('Payment Day/s',help='Day/s of month payment schedule, set blank if every payroll period. Separate with spaces for multiple days. Ex: 15 30');amount=fields.Float('Amount',digits='Payroll Amount',required=True);note=fields.Text('Notes');state=fields.Selection([('draft','Draft'),('confirmed','Confirmed')],tracking=True,default='draft',string='State',required=True);payment_line=fields.One2many('hr.ph.loan.payment','loan_id','Loan Payments',readonly=True);payments=fields.Float(compute='sum_payments',compute_sudo=True,store=True,digits='Payroll Amount',string='Payments');balance=fields.Float(compute='sum_payments',compute_sudo=True,store=True,digits='Payroll Amount',string='Balance');cpayments=fields.Float(compute='sum_cpayments',compute_sudo=True,digits='Payroll Amount');cbalance=fields.Float(compute='sum_cpayments',compute_sudo=True,digits='Payroll Amount')
class LoanPayment(models.Model):_description='Loan Payment';_name='hr.ph.loan.payment';_order='date_to, seq';payslip_id=fields.Many2one('hr.ph.payslip','Payslip',ondelete='cascade',index=True);employee_id=fields.Many2one(related='payslip_id.employee_id',store=True);category_ids=fields.Many2many(related='payslip_id.employee_id.category_ids',string='Tags');loan_id=fields.Many2one('hr.ph.loan','Loan',required=True,ondelete='restrict');loan_type_id=fields.Many2one(related='loan_id.loan_type_id',string='Loan Type',store=True);payroll_number=fields.Char(related='payslip_id.payroll_id.name',string='Payroll Number');year_month=fields.Char(related='payslip_id.year_month',string='Year-Month');state=fields.Selection(related='payslip_id.payroll_id.state',string='State');date_from=fields.Date(related='payslip_id.payroll_id.date_from',string='Pay Period From');date_to=fields.Date(related='payslip_id.payroll_id.date_to',string='Pay Period To',store=True);seq=fields.Integer('Sequence');name=fields.Char('Name');amount=fields.Float('Amount',digits='Payroll Amount',help='Loan Payment Amount');loan_balance=fields.Float('Balance',related='loan_id.cbalance',digits='Payroll Amount');loan_amount=fields.Float('Loan Amount',related='loan_id.amount',digits='Payroll Amount')