from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
import xlwt
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging,base64
from io import BytesIO
_logger=logging.getLogger(__name__)
DF='%Y-%m-%d'
class DeductionWizard(models.TransientModel):
	_name='ez.deduction.wizard';_description='Deduction Wizard'
	def get_default_ym(A):B=fields.Date.context_today(A);C=fields.Date.from_string(B);return C.strftime('%Y-%m')
	company_id=fields.Many2one('res.company',string='Company',default=lambda self:self.env.user.company_id.id);year_month=fields.Char(default=get_default_ym);employee_ids=fields.Many2many('hr.employee',string='Employees');xls_file=fields.Binary(string='Excel Output File',readonly=True);filename=fields.Char()
	def gen_excel(A):
		A.ensure_one();filter=[];E=[]
		if A.employee_ids:
			for L in A.employee_ids:E.append(L.id)
			filter.append(('employee_id','in',E))
		if A.company_id:filter.append(('company_id','=',A.company_id.id))
		if A.year_month:filter.append(('year_month','=',A.year_month))
		_logger.debug('gen_excel: filter=%s emp_ids=%s',filter,E);F=A.env['hr.ph.payslip'].search(filter);H=[A.id for A in F]
		if not H:raise ValidationError(_('No records found.'))
		A.env.cr.execute('\n            SELECT\n                e.identification_id,\n                e.name,\n                e.tin_no,\n                e.sss_no,\n                e.phic_no,\n                e.pagibig_no,\n                SUM(p.gross_pay) AS gross_pay,\n                SUM(p.basic_pay) AS basic_pay,\n                SUM(p.taxable) AS taxable,\n                SUM(p.wtax) AS wtax,\n                SUM(p.sss_ee) AS sss_ee,\n                SUM(p.sss_er - p.sss_ec) AS sss_er,\n                SUM(p.sss_ec) AS sss_ec,\n                SUM(p.phic_ee) AS phic_ee,\n                SUM(p.phic_er) AS phic_er,\n                SUM(p.hdmf_ee) AS hdmf_ee,\n                SUM(p.hdmf_er) AS hdmf_er\n            FROM hr_ph_payslip AS p\n            INNER JOIN hr_employee AS e ON e.id = p.employee_id\n            WHERE p.id IN %s\n            GROUP BY 1,2,3,4,5,6\n            ORDER BY 2\n        ',(tuple(H),));F=A.env.cr.dictfetchall();I=xlwt.Workbook();C=I.add_sheet(A.year_month);B=0;C.write(B,0,'DEDUCTION REPORT',xlwt.easyxf('font: bold on'));C.write(B+1,0,'Year-Month: ');C.write(B+1,1,A.year_month);J=[['ID Number','identification_id'],['Employee Name','name'],['TIN','tin_no'],['SSS Number','sss_no'],['PHIC Number','phic_no'],['HDMF Number','pagibig_no'],['Gross Pay','gross_pay'],['Basic Pay','basic_pay'],['Taxable','taxable'],['W.Tax','wtax'],['SSS EE','sss_ee'],['SSS ER','sss_er'],['SSS EC','sss_ec'],['PHIC EE','phic_ee'],['PHIC ER','phic_er'],['HDMF EE','hdmf_ee'],['HDMF ER','hdmf_er']];D=0;B=3
		for G in J:C.write(B,D,G[0]);D+=1
		B+=1
		for M in F:
			D=0
			for G in J:C.write(B,D,M.get(G[1]));D+=1
			B+=1
		K=BytesIO();I.save(K);N=base64.b64encode(K.getvalue());A.write({'xls_file':N,'filename':'deduction-%s.xls'%A.year_month});return{'name':'Generate Deduction Excel Report','view_type':'form','view_mode':'form','res_model':'ez.deduction.wizard','res_id':A.id,'type':'ir.actions.act_window','target':'new','context':A._context.copy()}