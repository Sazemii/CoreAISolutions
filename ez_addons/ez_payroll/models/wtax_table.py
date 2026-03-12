from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
_logger=logging.getLogger(__name__)
DEBUG=0
DF='%Y-%m-%d'
def dprint(s):_logger.debug(s)
class Wtax(models.Model):
	_name='hr.ph.wtax';_description='Withholding Tax Table';_order='seq asc';govded_id=fields.Many2one('hr.ph.gov.deductions','Ded. Version',ondelete='cascade');seq=fields.Integer('Seq');name=fields.Char('Class');period=fields.Selection([('Daily','Daily'),('Weekly','Weekly'),('Semi-monthly','Semi-monthly'),('Monthly','Monthly')],'Period');t1=fields.Float('T1',digits='Payroll Amount');t2=fields.Float('T2',digits='Payroll Amount');t3=fields.Float('T3',digits='Payroll Amount');t4=fields.Float('T4',digits='Payroll Amount');t5=fields.Float('T5',digits='Payroll Amount');t6=fields.Float('T6',digits='Payroll Amount');t7=fields.Float('T7',digits='Payroll Amount');t8=fields.Float('T8',digits='Payroll Amount');is_compute=fields.Boolean('Compute',default=True);note=fields.Char('Notes')
	@api.model
	def create_wtax_line(self,payslip,ptotal):
		A=payslip;B=[]
		if A.minimum_wage:return B
		C=A.taxable
		if C<=.0:return B
		if A.wtax_percent:D=round(C*A.wtax_percent/1e2,2)
		else:H=A.payroll_id.date_from;F=A.payroll_id.date_to;G=A.payroll_id.total_days;D=self.compute_tax_using_table(G,C,A.tax_code and'Z',F)
		E={'seq':10000,'name':'Withholding Tax','amount':D,'code':'WTAX','computed':True,'tax_deductible':False,'payslip_id':A.id};dprint('WTAX: %s'%A.name);dprint('taxable=%0.2f, wtax=%02f'%(C,D));dprint('res=%s'%E)
		if E['amount']>.0:B.append(E)
		return B
	@api.model
	def compute_tax_using_table(self,ndays,taxable,tax_code,date):
		K=tax_code;J=ndays;G=self;C=date;B=taxable
		if J<3:D='Daily'
		elif J<10:D='Weekly'
		elif J<23:D='Semi-monthly'
		else:D='Monthly'
		P=fields.Date.to_string(C)
		if P>='2023-01-01':
			L='\n                SELECT t.name, t.amount_from, t.amount_to, t.tax, t.rate_excess\n                FROM hr_ph_wtax2023 AS t\n                INNER JOIN hr_ph_gov_deductions AS v ON v.id = t.govded_id\n                WHERE t.period = %s\n                    AND (v.date_from <=%s AND v.date_to >= %s)\n                    AND (t.amount_from<=%s)\n                    AND ((t.amount_to+0.01)>%s)\n            ';M=D,C,C,B,B;G.env.cr.execute(L,M);H=.0
			for A in G.env.cr.dictfetchall():H=round(A['tax']+A['rate_excess']*(B-A['amount_from']),2);break
		else:
			L="\n                SELECT t.t1, t.t2, t.t3, t.t4, t.t5, t.t6, t.t7, t.t8, t.name\n                FROM hr_ph_wtax AS t\n                INNER JOIN hr_ph_gov_deductions AS v ON v.id = t.govded_id\n                WHERE t.period = %s\n                AND (v.date_from <=%s AND v.date_to >= %s)\n                AND t.name in ('Tax','Over %%',%s,'Z')\n            ";M=D,C,C,K;G.env.cr.execute(L,M);E={}
			for A in G.env.cr.fetchall():E[A[8]]=A
			N=E.get('Tax');O=E.get('Over %');F=E.get(K)
			if not F:F=E.get('Z')
			H=.0
			if N and O and F:
				for I in range(7,-1,-1):
					if B>=F[I]:H=round(N[I]+(B-F[I])*O[I]/1e2,2);break
			else:raise ValidationError('INVALID tax settings or table error: code=%s'%K)
		return H
class Wtax(models.Model):_name='hr.ph.wtax2023';_description='Withholding Tax Table 2023';_order='seq asc';seq=fields.Integer('Seq');govded_id=fields.Many2one('hr.ph.gov.deductions','Ded. Version',ondelete='cascade');period=fields.Selection([('Daily','Daily'),('Weekly','Weekly'),('Semi-monthly','Semi-monthly'),('Monthly','Monthly')],'Period');name=fields.Char();amount_from=fields.Float('From',digits='Payroll Amount');amount_to=fields.Float('To',digits='Payroll Amount');tax=fields.Float(digits='Payroll Amount');rate_excess=fields.Float(digits='Payroll Amount')