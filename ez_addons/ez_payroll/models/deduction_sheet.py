from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import xlrd,base64,re
from io import BytesIO
import logging
_logger=logging.getLogger(__name__)
class deduction_entry(models.Model):
	_name='hr.ph.pay.deduction.entry';_description='Deductions Sheet';_inherit=['mail.thread'];_order='date desc, name asc';company_id=fields.Many2one('res.company',string='Company',default=lambda self:self.env.company);name=fields.Char(string='Name',required=True,tracking=True);date=fields.Date(string='Date',required=True,tracking=True);code=fields.Char(tracking=True);xls_file=fields.Binary(string='Excel File');filename=fields.Char(tracking=True);notes=fields.Text();complete=fields.Boolean(compute='_check_complete');state=fields.Selection([('draft','Draft'),('done','Done')],string='State',tracking=True,required=True,default='draft');ded_detail_ids=fields.One2many('hr.ph.pay.deduction.entry.details','other_deduction_id','Deduction Details')
	def unlink(A):
		for B in A:
			if B.state!='draft':raise ValidationError(_('You cannot delete a deduction sheet that is not draft.'))
		return super(deduction_entry,A).unlink()
	@api.depends('ded_detail_ids')
	def _check_complete(self):
		for A in self:
			B=True
			for C in A.ded_detail_ids:
				if not C.payslip_id:B=False;break
			A.complete=B
	def set_as_done(B):
		for A in B:A.state='done';A.ded_detail_ids.write({'name':A.name})
	def cancel_done(A):
		for B in A:B.state='draft'
	def copy(B,default=None):A=default;A=dict(A or{});A.update(name=_('%s (copy)')%(B.name or''));return super(deduction_entry,B).copy(A)
	@api.model
	def create_oded_line(self,payslip):
		B=payslip;F=B.payroll_id.date_from;G=B.payroll_id.date_to;H=self.search([('state','=','done'),('date','>=',F),('date','<=',G)]);C=self.env['hr.ph.pay.deduction.entry.details'].search([('payslip_id','=',False),('employee_id','=',B.employee_id.id),('other_deduction_id','in',H.ids)]);D=False;E=[]
		for A in C:I={'payslip_id':B.id,'seq':A.seq+500,'name':A.other_deduction_id.name,'amount':A.amount,'er_amount1':A.er_amount1,'er_amount2':A.er_amount2,'computed':True,'tax_deductible':A.tax_deductible,'code':A.other_deduction_id.code and A.other_deduction_id.code.upper()or'OTHERS','other_deduction_id':A.other_deduction_id.id};E.append(I);D=True
		if D:C.write({'payslip_id':B.id})
		else:0
		return E
	def delete_lines(A):
		A.ensure_one()
		for B in A.ded_detail_ids:
			if B.payslip_id:raise ValidationError(_('Cannot delete! Payslip already created for for deduction sheet.'))
		A.ded_detail_ids.unlink()
	def import_excel(A):
		A.ensure_one();A.delete_lines();K=base64.b64decode(A.xls_file);L=BytesIO(K)
		try:M=xlrd.open_workbook(file_contents=L.getvalue())
		except:raise ValidationError(_('Wrong excel format.'))
		C=M.sheet_by_index(0);N=[A.value for A in C.row(0)];_logger.debug('Import excel %s',N);F=0
		for D in range(1,C.nrows):
			B=C.row(D);_logger.debug('Row %s: %s',D,B);O='%s'%(B[1].value or'');G=O.strip().split(' [')[0]
			if G:
				E=A.env['hr.employee'].search([('name','=ilike','%s%%'%G)],limit=1)
				if E:
					H=int(B[0].value or 0)
					if H:F=H
					if B[3].value:I=True
					else:I=False
					J={'other_deduction_id':A.id,'seq':F,'employee_id':E[0].id,'amount':round(B[2].value or .0,2),'tax_deductible':I,'notes':'%s'%B[4].value};E=A.ded_detail_ids.create(J);_logger.debug('Val %s: %s',D,J)
class deduction_entry_detail(models.Model):
	_name='hr.ph.pay.deduction.entry.details';_description='Deductions Sheet Details';_order='seq, employee_id'
	def _get_default_seq(C):
		B=dict(C.env.context);A=B.get('ded_detail_ids');_logger.debug('Deduction line context:%s',B);_logger.debug('ded_detail_ids :%s',A)
		if A:return len(A)*10+10
		else:return 10
	other_deduction_id=fields.Many2one('hr.ph.pay.deduction.entry','Deduction Sheet',ondelete='cascade');seq=fields.Integer('Seq',default=_get_default_seq);name=fields.Char('Name');date=fields.Date(related='other_deduction_id.date');employee_id=fields.Many2one('hr.employee','Employee Name',required=True,ondelete='restrict');amount=fields.Float('Amount',digits='Payroll Amount');tax_deductible=fields.Boolean('Tax Deductible',default=False);notes=fields.Char();er_amount1=fields.Float('ER Amount 1',digits='Payroll Amount',help='Employer Contribution 1');er_amount2=fields.Float('ER Amount 2',digits='Payroll Amount',help='Employer Contribution 2');state=fields.Selection(related='other_deduction_id.state');payslip_id=fields.Many2one('hr.ph.payslip','Payslip',readonly=True,ondelete='set null',copy=False,index=True);payroll_name=fields.Char(related='payslip_id.payroll_id.name',string='Payroll No.')
	@api.onchange('employee_id')
	def emp_change(self):
		for A in self:A.name=A.other_deduction_id.name
	def unlink(A):
		for B in A:
			if B.payslip_id:raise ValidationError(_('You cannot delete a deduction line with a linked payslip.'))
		return super(deduction_entry_detail,A).unlink()