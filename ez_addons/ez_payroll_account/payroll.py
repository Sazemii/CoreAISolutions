from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
import logging,re
_logger=logging.getLogger(__name__)
class Payroll(models.Model):
	_inherit='hr.ph.payroll';journal_line_count=fields.Integer(compute='_get_journal_line_count',compute_sudo=True,string='Total Lines');move_id=fields.Many2one('account.move',string='Journal Entry',ondelete='set null')
	def action_view_journal(A):A.ensure_one();B={'type':'ir.actions.act_window','res_model':'account.move','context':{'create':False},'name':'Journal Entry','view_mode':'form','res_id':A.move_id.id};return B
	def create_journal(A):
		A.ensure_one()
		if A.move_id:
			if A.move_id.state!='draft':raise ValidationError(_('Cannot create/edit non-draft journal entry.'))
			A.move_id.write(A.get_journal_rec(A))
		else:A.move_id=A.env['account.move'].create(A.get_journal_rec(A))
		C=A.env['ez.payroll.account.setting'].search([],limit=1)
		if not C:raise ValidationError(_('Payroll Journal not set. Please define in Configuration menu.'))
		F=[];K=.0
		for D in A.payslip:
			F.append((0,0,{'move_id':A.id,'name':'Gross Pay: %s'%D.employee_id.name,'account_id':C.salary_expense_acct_id.id,'partner_id':D.employee_id.user_id.partner_id.id,'debit':D.gross_pay}));L=.0;M=.0;I=.0;R=.0;N=.0;E=[];O=.0;J=.0;S=.0
			for B in D.deduction_line:
				if B.code=='WTAX':L+=B.amount;E.append((0,0,{'move_id':A.id,'name':'W.Tax: %s'%D.employee_id.name,'account_id':C.wtax_acct_id.id,'partner_id':C.bir_partner_id.id,'credit':B.amount}))
				elif B.code=='SSS':M+=B.amount;O+=B.er_amount;E.append((0,0,{'move_id':A.id,'name':'SSS EE: %s'%D.employee_id.name,'account_id':C.sss_acct_id.id,'partner_id':C.sss_partner_id.id,'credit':B.amount}));E.append((0,0,{'move_id':A.id,'name':'SSS ER: %s'%D.employee_id.name,'account_id':C.sss_acct_id.id,'partner_id':C.sss_partner_id.id,'credit':B.er_amount}))
				elif B.code=='PHIC':I+=B.amount;J+=B.er_amount;E.append((0,0,{'move_id':A.id,'name':'Philhealth EE: %s'%D.employee_id.name,'account_id':C.philhealth_acct_id.id,'partner_id':C.philhealth_partner_id.id,'credit':B.amount}));E.append((0,0,{'move_id':A.id,'name':'Philhealth ER: %s'%D.employee_id.name,'account_id':C.philhealth_acct_id.id,'partner_id':C.philhealth_partner_id.id,'credit':B.er_amount}))
				elif B.code=='HDMF':I+=B.amount;J+=B.er_amount;E.append((0,0,{'move_id':A.id,'name':'HDMF EE: %s'%D.employee_id.name,'account_id':C.hdmf_acct_id.id,'partner_id':C.hdmf_partner_id.id,'credit':B.amount}));E.append((0,0,{'move_id':A.id,'name':'HDMF ER: %s'%D.employee_id.name,'account_id':C.hdmf_acct_id.id,'partner_id':C.hdmf_partner_id.id,'credit':B.er_amount}))
				elif B.amount:H=A.get_other_journal_deduction(C,D,B);H.update({'move_id':A.id});E.append((0,0,H));N+=H.get('credit',.0)-H.get('debit',.0)
			P=O+J+S
			if P:F.append((0,0,{'move_id':A.id,'name':'ER Govt Contributions: %s'%D.employee_id.name,'account_id':C.salary_expense_acct_id.id,'partner_id':D.employee_id.user_id.partner_id.id,'debit':P}))
			F+=E;Q=.0
			for G in D.loan_line:Q+=G.amount;F.append((0,0,{'move_id':A.id,'name':'%s: %s'%(G.loan_type_id.name,D.employee_id.name),'account_id':G.loan_type_id.loan_acct_id.id,'partner_id':G.loan_type_id.partner_id.id,'credit':G.amount}))
			K+=D.gross_pay-L-M-I-R-N-Q
		F.append((0,0,{'move_id':A.id,'name':'%s Payment'%A.name,'account_id':C.bank_acct_id.id,'credit':K}));A.move_id.line_ids=[(5,0,0)]+A.process_recs(F)
	@api.model
	def get_journal_rec(self,payroll):return{'ref':payroll.name}
	@api.model
	def process_recs(self,recs):return recs
	@api.model
	def get_other_journal_deduction(self,settings,payslip,deduction):
		B=settings;A=deduction
		if B.other_ded_acct_id:D=B.other_ded_acct_id.id
		else:D=B.bank_acct_id.id
		C={'name':'%s: %s'%(A.name,payslip.employee_id.name),'account_id':D,'partner_id':A.other_deduction_id.partner_id.id}
		if A.amount>.0:C.update({'credit':A.amount})
		else:C.update({'debit':-A.amount})
		return C
	@api.depends('move_id')
	def _get_journal_line_count(self):
		for A in self:A.journal_line_count=len(A.move_id.line_ids)
class OtherDeductions(models.Model):_inherit='hr.ph.pay.deduction.entry';partner_id=fields.Many2one('res.partner',string='Partner')