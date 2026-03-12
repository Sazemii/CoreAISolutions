from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
_logger=logging.getLogger(__name__)
DEBUG=0
def dprint(s):_logger.debug(s)
class Sss(models.Model):
	_name='hr.ph.sss';_description='SSS Contribution Table';_order='range_from asc'
	def _compute_total(B):
		for A in B:A.total=A.ee_premium+A.er_premium+A.ec_premium
	govded_id=fields.Many2one('hr.ph.gov.deductions','Ded. Version',required=True,ondelete='cascade');name=fields.Char('Name');range_from=fields.Float('Range From',digits='Payroll Amount',help='Range from (>=)');range_to=fields.Float('Range To',digits='Payroll Amount',help='Range to (<)');salary_credit=fields.Float('Salary Credit',digits='Payroll Amount');er_premium=fields.Float('ER Share',digits='Payroll Amount',help='Employer premium.');ee_premium=fields.Float('EE Share',digits='Payroll Amount',help='Employee premium.');ec_premium=fields.Float('EC',digits='Payroll Amount',help='EC premium.');note=fields.Char('Notes');total=fields.Float(compute='_compute_total',digits='Payroll Amount',string='Total')
	@api.model
	def create_sss_line(self,payslip,ptotal):
		C=self;A=payslip;E=[]
		if A.no_deductions:return E
		O='\n            SELECT sss_salary_base \n            FROM hr_ph_gov_deductions \n            WHERE (date_from <= %s AND date_to >= %s)\n            LIMIT 1\n        ';P=A.payroll_id.date_to,A.payroll_id.date_to;C.env.cr.execute(O,P);K=C.env.cr.fetchone()
		if not K:raise ValidationError(_('Government deductions not set properly.'))
		Q=K[0];D='SSS';F,S,R,G=ptotal;L=G.get(D,{}).get('amount',.0);M=G.get(D,{}).get('er_amount1',.0);N=G.get(D,{}).get('er_amount2',.0)
		if Q=='gross':H,I,J=C.compute_sss_using_table(A.gross_pay+F,A.payroll_id.date_to)
		else:H,I,J=C.compute_sss_using_table(A.basic_pay+R,A.payroll_id.date_to)
		B={'seq':10,'name':'SSS Premium','amount':max(.0,round(H-L,2)),'er_amount1':max(.0,round(I-M,2)),'er_amount2':max(.0,round(J-N,2)),'code':D,'computed':True,'tax_deductible':True,'payslip_id':A.id};dprint('SSS: %s'%A.name);dprint('pgross=%0.2f psss_ee=%0.2f psss_er=%0.2f psss_ec=%0.2f'%(F,L,M,N));dprint('gross=%0.2f sss_ee=%0.2f sss_er=%0.2f sss_ec=%0.2f'%(F+A.gross_pay,H,I,J));dprint('res=%s'%B)
		if B['amount']>.0 or B['er_amount1']>.0 or B['er_amount2']>.0:E.append(B)
		return E
	@api.model
	def compute_sss_using_table(self,gross,date):
		C=date;B=gross
		if B<=.0:return .0,.0,.0
		2025;G='\n            SELECT coalesce(s.ee_premium, 0.0), coalesce(s.er_premium, 0.0), coalesce(s.ec_premium, 0.0)\n            FROM hr_ph_sss AS s\n            INNER JOIN hr_ph_gov_deductions AS v ON v.id = s.govded_id\n            WHERE (v.date_from <= %s AND v.date_to >= %s) AND (range_from <= %s AND %s <= range_to)\n            ORDER BY v.date_from DESC\n            LIMIT 1\n        ';H=C,C,round(B,2),round(B,2);self.env.cr.execute(G,H);A=self.env.cr.fetchone()
		if not A:dprint('SSS error res=%s date=%s gross=%0.2f'%(A,C,B));raise ValidationError(_('SSS table configuration error.'));D=.0;E=.0;F=.0
		else:D=A[0];E=A[1];F=A[2]
		return D,E,F