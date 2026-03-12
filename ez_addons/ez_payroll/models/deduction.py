from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
_logger=logging.getLogger(__name__)
DEBUG=0
class PayslipDeduction(models.Model):
	_name='hr.ph.pay.deduction';_description='Deductions';_order='seq';payslip_id=fields.Many2one('hr.ph.payslip','Payslip',ondelete='cascade');seq=fields.Integer(string='Seq',help='Sequence or sorting order.');name=fields.Char('Deduction');amount=fields.Float('Amount',digits='Payroll Amount',help='Employee Deduction');er_amount=fields.Float('ER Amount',compute='_compute_er_amount',store=True,digits='Payroll Amount',help='Employer Contribution');er_amount1=fields.Float('ER Amount 1',digits='Payroll Amount',help='Employer Contribution 1');er_amount2=fields.Float('ER Amount 2',digits='Payroll Amount',help='Employer Contribution 2');tax_deductible=fields.Boolean('Tax Deductible');computed=fields.Boolean('Computed',default=False);code=fields.Char('Code',index=True);other_deduction_id=fields.Many2one('hr.ph.pay.deduction.entry',string='Other Deductions',ondelete='set null',readonly=True);employee_id=fields.Many2one(related='payslip_id.employee_id',string='Employee Name',store=True);category_ids=fields.Many2many(related='payslip_id.employee_id.category_ids',string='Tags');identification_id=fields.Char(related='employee_id.identification_id');payroll_number=fields.Char(related='payslip_id.payroll_id.name');sss_no=fields.Char(related='employee_id.sss_no');phic_no=fields.Char(related='employee_id.phic_no');pagibig_no=fields.Char(related='employee_id.pagibig_no');tin_no=fields.Char(related='employee_id.tin_no');company_id=fields.Many2one(related='payslip_id.company_id',string='Company');year_month=fields.Char(related='payslip_id.payroll_id.year_month',string='Year-Month',store=True);date=fields.Date(related='payslip_id.payroll_id.date_to',string='Date',store=True);state=fields.Selection(related='payslip_id.payroll_id.state',string='State',store=False)
	@api.depends('er_amount1','er_amount2')
	def _compute_er_amount(self):
		for rec in self:rec.er_amount=rec.er_amount1+rec.er_amount2
	@api.model
	def create_hdmf_line(self,payslip,ptotal):
		res0=[]
		if payslip.no_deductions:return res0
		code='HDMF';pgross_pay,ptaxable,pbasic,pded=ptotal;pee=pded.get(code,{}).get('amount',.0);per=pded.get(code,{}).get('er_amount1',.0);ee,er=self.compute_hdmf_using_table(payslip.gross_pay+pgross_pay,payslip.payroll_id.date_to,prev_ee=pee,prev_er=per);val1={'seq':40,'name':'HDMF/Pagibig','amount':max(.0,round(ee-pee,2)),'er_amount1':max(.0,round(er-per,2)),'er_amount2':.0,'code':code,'computed':True,'tax_deductible':True,'payslip_id':payslip.id};_logger.debug('HDMF: %s',payslip.name);_logger.debug('pgross=%0.2f phdmf_ee=%0.2f phdmf_er=%0.2f',pgross_pay,pee,per);_logger.debug('gross=%0.2f hdmf_ee=%0.2f hdmf_er=%0.2f',pgross_pay+payslip.gross_pay,ee,er);_logger.debug('res=%s',val1)
		if val1['amount']>.0 or val1['er_amount1']>.0:
			res0.append(val1)
			if payslip.employee_id.voluntary_hdmf:val2={'seq':41,'name':'HDMF/Pagibig V.','amount':payslip.employee_id.voluntary_hdmf,'er_amount1':.0,'er_amount2':.0,'code':'HDMFV','computed':True,'tax_deductible':False,'payslip_id':payslip.id};res0.append(val2)
		return res0
	@api.model
	def compute_hdmf_using_table(self,gross,date,prev_ee=0,prev_er=0):
		if gross<=.0:return .0,.0
		sql='\n            SELECT ee_code, er_code\n            FROM hr_ph_gov_deductions\n            WHERE date_from <= %s AND date_to >= %s\n            ORDER BY date_from DESC\n            LIMIT 1\n            ';param=date,date;self.env.cr.execute(sql,param);res=self.env.cr.fetchone()
		try:ee=eval(res[0]);er=eval(res[1])
		except:raise ValidationError(_('HDMF code configuration error.'))
		return ee,er