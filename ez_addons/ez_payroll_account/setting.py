from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
import logging,re
_logger=logging.getLogger(__name__)
class LoanType(models.Model):_inherit='hr.ph.loan.type';loan_acct_id=fields.Many2one('account.account',string='Loan Account');partner_id=fields.Many2one('res.partner',string='Partner')
class AccountSetting(models.Model):
	_name='ez.payroll.account.setting';_description='Payroll Account Settings';_order='id desc';company_id=fields.Many2one('res.company',string='Company',default=lambda self:self.env.company,readonly=True);name=fields.Char('Name',required=True);salary_expense_acct_id=fields.Many2one('account.account',string='Salary Expense');bank_acct_id=fields.Many2one('account.account',string='Bank/Cash Account');other_ded_acct_id=fields.Many2one('account.account',string='Other Deduction');wtax_acct_id=fields.Many2one('account.account',string='W.Tax Payable');sss_acct_id=fields.Many2one('account.account',string='SSS Payable');philhealth_acct_id=fields.Many2one('account.account',string='Philhealth Payable');hdmf_acct_id=fields.Many2one('account.account',string='HDMF Payable');bir_partner_id=fields.Many2one('res.partner',string='BIR',default=lambda self:self.env.ref('ez_payroll_account.res_partner_bir'));sss_partner_id=fields.Many2one('res.partner',string='SSS',default=lambda self:self.env.ref('ez_payroll_account.res_partner_sss'));philhealth_partner_id=fields.Many2one('res.partner',string='Philhealth',default=lambda self:self.env.ref('ez_payroll_account.res_partner_philhealth'));hdmf_partner_id=fields.Many2one('res.partner',string='HDMF',default=lambda self:self.env.ref('ez_payroll_account.res_partner_hdmf'));note=fields.Text('Notes')
	@api.model
	def create_demo_data(self):
		A=self;B=A.env.ref('ez_payroll.hr_ph_loan_type_1');C=A.env.ref('ez_payroll.hr_ph_loan_type_2');D=A.env.ref('ez_payroll.hr_ph_loan_type_3');E=A.env.ref('ez_payroll.hr_ph_loan_type_4')
		if B:B.loan_acct_id=A.env['account.account'].search([('name','=','Current Liabilities')],limit=1).id;B.partner_id=A.env.ref('ez_payroll_account.res_partner_sss').id
		if C:C.loan_acct_id=A.env['account.account'].search([('name','=','Current Liabilities')],limit=1).id;C.partner_id=A.env.ref('ez_payroll_account.res_partner_sss').id
		if D:D.loan_acct_id=A.env['account.account'].search([('name','=','Current Liabilities')],limit=1).id;D.partner_id=A.env.ref('ez_payroll_account.res_partner_hdmf').id
		if E:E.loan_acct_id=A.env['account.account'].search([('name','=','Current Assets')],limit=1).id;E.partner_id=A.env.company.partner_id.id