from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time,logging
_logger=logging.getLogger(__name__)
class GovtDeductions(models.Model):
	_name='hr.ph.gov.deductions';_description='PH Government Deductions Tables';_order='date_from desc';name=fields.Char('Version');date_from=fields.Date('Active Starting');date_to=fields.Date('Active Until');ee_code=fields.Char('Employee Computation',required=True);er_code=fields.Char('Employer Computation',required=True);phic_code=fields.Char('Computation Code');note=fields.Char('Notes');cola=fields.Float('COLA',digits=(6,4),help='Cost of Living Allowance per Day');lh_cola=fields.Boolean('Reg. Hol. worked with COLA',help='Add COLA to regular holidays worked for daily paid employees.');wtax_table=fields.One2many('hr.ph.wtax','govded_id','Withholding Tax Table',copy=True);wtax_table2023=fields.One2many('hr.ph.wtax2023','govded_id','Withholding Tax Table 2023',copy=True);sss_table=fields.One2many('hr.ph.sss','govded_id','SSS Contribution Table',copy=True);phic_table=fields.One2many('hr.ph.phic','govded_id','PhilHealth Contribution Table',copy=True);non_taxable_13thmp=fields.Float('Non-taxable 13th month pay limit',digits='Payroll Amount',copy=True,help='13th month pay non-taxable limit');minimun_gross=fields.Float('Minimun Gross with Deductions',default=5e2,digits='Payroll Amount',copy=True,help='Minimun gross pay to have deductions.');sss_salary_base=fields.Selection([('gross','Gross Pay'),('basic','Basic Pay')],string='SSS Salary Base',required=True,default='gross')
	def del_keys(B,d,klist):
		for A in klist:d.pop(A,None)
	def copy(B,default=None):A=default;B.ensure_one();A=dict(A or{});A.update(name=_('%s (copy)')%(B.name or''));return super(GovtDeductions,B).copy(A)
	@api.model
	def set_date_to(self,name,date_to):
		A=date_to;_logger.debug('GOVDED SET: name=%s date=%s',name,A);B=self.env['hr.ph.gov.deductions'].search([('name','=',name)])
		for C in B:C.date_to=A