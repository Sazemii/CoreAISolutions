from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError,UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
_logger=logging.getLogger(__name__)
DEBUG=0
def dprint(s):_logger.debug(s)
class Phic(models.Model):
	_name='hr.ph.phic';_description='Philhealth Contribution Table';_order='salary_base asc'
	def _compute_total(self):
		for rec in self:rec.total=rec.er_share+rec.ee_share
	govded_id=fields.Many2one('hr.ph.gov.deductions','Ded. Version',ondelete='cascade');range_from=fields.Float('Range From',digits='Payroll Amount',help='Range from (>=)');range_to=fields.Float('Range To',digits='Payroll Amount',help='Range to (<)');salary_base=fields.Float('Salary Base',digits='Payroll Amount');er_share=fields.Float('ER Share',digits='Payroll Amount',help='Employer premium.');ee_share=fields.Float('EE Share',digits='Payroll Amount',help='Employee premium.');note=fields.Char('Notes');total=fields.Float(compute='_compute_total',digits='Payroll Amount',string='Total')
	@api.model
	def create_phic_line(self,payslip,ptotal):
		res0=[]
		if payslip.no_deductions:return res0
		code='PHIC';pgross_pay,ptaxable,pbasic_pay,pded=ptotal;pee=pded.get(code,{}).get('amount',.0);per=pded.get(code,{}).get('er_amount1',.0);date=payslip.payroll_id.date_to;sql='\n            SELECT phic_code\n            FROM hr_ph_gov_deductions\n            WHERE date_from <= %s AND date_to >= %s\n            ORDER BY date_from DESC\n            LIMIT 1\n            ';param=date,date;self.env.cr.execute(sql,param);res=self.env.cr.fetchone()
		if res and res[0]:ee,er=eval(res[0])
		else:ee,er=self.compute_phic_using_table(payslip.gross_pay+pgross_pay,payslip.payroll_id.date_to)
		val1={'seq':30,'name':'Philhealth','amount':max(.0,round(ee-pee,2)),'er_amount1':max(.0,round(er-per,2)),'er_amount2':.0,'code':code,'computed':True,'tax_deductible':True,'payslip_id':payslip.id};dprint('PHIC: %s'%payslip.name);dprint('pgross=%0.2f pphic_ee=%0.2f pphic_er=%0.2f'%(pgross_pay,pee,per));dprint('gross=%0.2f phic_ee=%0.2f phic_er=%0.2f'%(pgross_pay+payslip.gross_pay,ee,er));dprint('res=%s'%val1)
		if val1['amount']>.0 or val1['er_amount1']>.0:res0.append(val1)
		return res0
	@api.model
	def get_phic_mbs(self,payslip,pded,factor=.0,percent=4.,limit=8e4):
		if payslip.gross_pay<=.0:return .0,.0
		if payslip.salary_rate_period=='monthly':mrate=payslip.salary_rate
		else:mrate=payslip.salary_rate*payslip.emr_days/12.
		if factor==.0:
			d1=fields.Date.from_string(payslip.date_from);d2=fields.Date.from_string(payslip.date_to);days=(d2-d1).days
			if days>=20:nfactor=1.
			elif days>=9:nfactor=.5
			elif days>=3:nfactor=.25
			else:nfactor=1.
		else:nfactor=factor
		date=payslip.date_to;t_ee,t_er=self.compute_phic(mrate,date,percent=percent,limit=limit);t_total=t_ee+t_er;code='PHIC'
		if 0:c_ee,c_er=self.compute_phic(mrate*nfactor,date,percent=percent,limit=limit);c_total=c_ee+c_er
		else:c_ee,c_er=self.compute_phic(mrate,date,percent=percent,limit=limit);c_total=(c_ee+c_er)*nfactor;a=round(c_total/2.,2);b=c_total-a;c_ee=min(a,b);c_er=max(a,b)
		p_ee=pded.get(code,{}).get('amount',.0);p_er=pded.get(code,{}).get('er_amount1',.0);p_total=p_ee+p_er;balance=t_total-p_total;_logger.debug('*PHICF basic=%s nfactor=%s total=%s cur=%s bal=%s mrate=%s',mrate*nfactor,nfactor,t_total,c_total,balance,mrate)
		if balance<=0:return .0,.0
		elif balance/c_total<1.5:a=round(t_total/2.,2);b=t_total-a;ee=min(a,b);er=max(a,b);_logger.debug('get_phic_mbs last: %s %s',ee,er);return ee,er
		else:_logger.debug('get_phic_mbs curr: %s %s',c_ee,c_er);return c_ee+p_ee,c_er+p_er
	@api.model
	def compute_phic(self,basic,date,percent=2.75,limit=4e4):
		if basic<=.0:premium=.0
		elif basic<=1e4:premium=percent*1e2
		elif basic>=limit:premium=round(limit*percent/1e2,2)
		else:premium=round(basic*percent/1e2,2)
		a=round(premium/2.,2);b=premium-a;ee=min(a,b);er=max(a,b);return ee,er
	@api.model
	def compute_phic_using_table(self,gross,date):
		if gross<=.0:return .0,.0
		sql='\n            SELECT coalesce(p.ee_share,0.0), coalesce(p.er_share,0.0)\n            FROM hr_ph_phic AS p\n            INNER JOIN hr_ph_gov_deductions AS v ON v.id = p.govded_id\n            WHERE (v.date_from <= %s AND v.date_to >= %s)\n                AND (p.range_from <= %s AND p.range_to > %s)\n            LIMIT 1\n            ';param=date,date,gross,gross;self.env.cr.execute(sql,param);res=self.env.cr.fetchone()
		if not res:dprint('PHIC error res=%s date=%s gross=%0.2f'%(res,date,gross));raise UserError(_('PHIC table configuration error.'));ee=.0;er=.0
		else:ee=res[0];er=res[1]
		return ee,er