from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import hashlib,base64,logging
_logger=logging.getLogger(__name__)
class Payroll(models.Model):
	_inherit='hr.ph.payroll'
	def get_compensation_lines(A,ps):B={};A.get_totals(ps.pay_computation_line,B);return A.get_sorted_totals(B)
	def get_totals(D,obj,pdict):
		B=pdict
		for A in obj:
			C=A.name and A.name.strip()or'/'
			if C not in B:B[C]=[A.amount,A.seq]
			else:B[C]=[B[C][0]+A.amount,min(A.seq,B[C][1])]
	def get_loan_totals(D,obj,pdict):
		A=pdict
		for B in obj:
			C=B.loan_type_id.name
			if C not in A:A[C]=[B.amount,B.seq]
			else:A[C]=[A[C][0]+B.amount,min(B.seq,A[C][1])]
	def get_sorted_totals(D,totals):
		A=totals;C=[]
		for B in A:C.append([A[B][1],B,A[B][0]])
		return sorted(C,key=lambda t:t[0])
	@api.model
	def format_curr(self,value):A=self;B=A.env.context.get('lang')or'en_US';C=A.env['res.lang'].search([('code','=',B)])or A.env['res.lang'].search([('code','=','en_US')]);return C.format('%0.2f',value,grouping=True)
	@api.model
	def clpay(self,payroll):
		B=payroll;D=self.env['ir.config_parameter'].sudo();E=B.company_id.name or'x';G=D.get_param('database.uuid',default='x');C=D.get_param('EzPay %s'%E,default='1:x').split(':');F=len(B.payslip);H=fields.Date.to_string(B.date_from);A=C[0].split()
		if len(A)==1:A.append('2999-01-01')
		I='%s:%s:%s:%s'%(G,C[0],'8939',E);J=hashlib.md5(I.encode()).hexdigest()
		if J!=C[1]or F>int(A[0])or A[1]<H:
			K=self.env['hr.ph.payroll'].search([])
			if len(K)>2 and F>=20:L='TGljZW5zZSBFcnJvci4gQ29udGFjdDogcmJlcmRpbkBnbWFpbC5jb20=';M=base64.b64decode(L);N=M.decode('ascii');raise ValidationError(N)
		else:0
	@api.model
	def get_summary(self,payslip):
		A=self;C={};D={};E={}
		for B in payslip:A.get_totals(B.pay_computation_line,C);A.get_totals(B.deduction_line,D);A.get_loan_totals(B.loan_line,E)
		return{'pay':A.get_sorted_totals(C),'ded':A.get_sorted_totals(D),'loan':A.get_sorted_totals(E)}
	@api.model
	def get_dept_summary(self,payslips):
		A={}
		for C in payslips:
			B=C.employee_id.department_id.name or''
			if B not in A:A[B]={'department':B,'gross_pay':.0,'deductions':.0,'loan_payments':.0,'net_pay':.0}
			A[B]['gross_pay']+=C.gross_pay;A[B]['deductions']+=C.total_deductions;A[B]['loan_payments']+=C.total_loan_payments;A[B]['net_pay']+=C.net_pay
		D=[A[B]for B in sorted(A.keys())];_logger.debug('get_dept_summary: %s',D);return D
'\nclass ParticularReport(models.AbstractModel):\n    _name = \'report.ez_payroll.report_payroll\'\n\n    def render_html(self, data=None):\n\n        report_obj = self.env[\'report\']\n        report = report_obj._get_report_from_name(\'ez_payroll.report_payroll\')\n        docargs = {\n            \'doc_ids\': self._ids,\n            \'doc_model\': report.model,\n            #\'docs\': self,\n            #\'data\': data,\n            \'docs\': self.env[\'hr.ph.payroll\'].browse(self._ids),\n            \'rep\': self,\n        }\n        return report_obj.render(\'ez_payroll.report_payroll\', docargs)\n\n    def format_curr(self, value):\n        lang_code = self._context.get(\'lang\') or \'en_US\'\n        lang = self.env[\'res.lang\'].search([(\'code\', \'=\', lang_code)])                 or self.env[\'res.lang\'].search([(\'code\', \'=\', \'en_US\')])\n        return lang.format("%0.2f", value, grouping=True)\n\n    def get_totals(self, obj, pdict):\n        for rec in obj:\n            rname = rec.name.strip()\n            if rname not in pdict:\n                pdict[rname] = [ rec.amount, rec.seq ]\n            else:\n                pdict[rname] = [ pdict[rname][0] + rec.amount, min(rec.seq, pdict[rname][1]) ]\n\n    def get_sorted_totals(self, totals):\n        res = []\n        for k in totals:\n            res.append([totals[k][1],k,totals[k][0]])\n        return sorted(res, key=lambda t:t[0])\n\n    def get_summary(self, payslip):\n        tpay = {}\n        tded = {}\n        tloan = {}\n        for ps in payslip:\n            self.get_totals(ps.pay_computation_line, tpay)\n            self.get_totals(ps.deduction_line, tded)\n            self.get_totals(ps.loan_line, tloan)\n\n        return {\n            \'pay\':self.get_sorted_totals(tpay),\n            \'ded\':self.get_sorted_totals(tded),\n            \'loan\':self.get_sorted_totals(tloan),\n        }\n'