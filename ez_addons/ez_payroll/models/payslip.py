from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.addons.ez_sql import execute_insert
import time,re,logging
from pprint import pformat
_logger=logging.getLogger(__name__)
class PayslipLineTemplate(models.Model):_name='hr.ph.payslip.line.template';_description='Payslip Line Template';seq=fields.Integer(string='Seq',help='Sequence or sorting order.',default=10,index=True);name=fields.Char(string='Name');qty=fields.Float('Quantity',digits='Payslip Line Unit');unit=fields.Selection([('day','days'),('hour','hours'),('minute','minutes'),('month','month'),('piece','pieces'),('fixed','fixed rate')],string='Unit',required=True,default='hour');factor=fields.Float('Factor',digits='Payslip Line Unit',help='Set to rate if unit is fixed or per piece.',default=1.);basic_pay=fields.Boolean('Basic',help='Enable if included in basic pay.',default=True);taxable=fields.Boolean('Taxable',help='Enable if taxable.',default=True);_order='seq, name'
class PayComputation(models.Model):
	_name='hr.ph.pay.computation';_description='Pay Computation';_inherit='hr.ph.payslip.line.template';_order='seq, name, unit';payslip_id=fields.Many2one('hr.ph.payslip','Payslip',ondelete='cascade',index=True);employee_id=fields.Many2one('hr.employee','Employee',compute='_compute_amount',store=True);category_ids=fields.Many2many(related='employee_id.category_ids',string='Tags');state=fields.Selection(related='payslip_id.payroll_id.state',string='State');payroll_number=fields.Char(related='payslip_id.payroll_id.name',string='Payroll Number');year_month=fields.Char('Year-Month',compute='_compute_amount',store=True);date_from=fields.Date(related='payslip_id.payroll_id.date_from',string='Pay Period From');date_to=fields.Date(string='Pay Period To',compute='_compute_amount',store=True);amount=fields.Float(compute='_compute_amount',digits='Payroll Amount',store=True);computed=fields.Boolean('Computed',default=False)
	@api.model
	def create_new(self,payslip):0
	@api.depends('qty','unit','factor','payslip_id','payslip_id.emr_days','payslip_id.year_month','payslip_id.salary_rate','payslip_id.salary_rate_period','payslip_id.employee_id','payslip_id.payroll_id','payslip_id.payroll_id.date_to')
	def _compute_amount(self):
		for A in self:
			A.year_month=A.payslip_id.payroll_id.year_month;A.employee_id=A.payslip_id.employee_id;A.date_to=A.payslip_id.payroll_id.date_to;D=A.payslip_id.emr_days or 313.
			if A.unit=='month':
				if A.payslip_id.salary_rate_period=='monthly':A.amount=A.qty*A.factor*A.payslip_id.salary_rate
				else:A.amount=A.qty*A.factor*A.payslip_id.salary_rate*D/12.
				continue
			if A.payslip_id.salary_rate_period=='monthly':B=A.payslip_id.salary_rate*12./D
			else:B=A.payslip_id.salary_rate
			if A.unit=='day':C=B
			elif A.unit=='hour':C=B/8.
			elif A.unit=='minute':C=B/48e1
			else:C=1.
			A.amount=round(A.qty,4)*A.factor*C
def XXcompute_basic_days(v):
	B=.0
	if v.get('basic_pay'):
		C=v.get('unit');A=v.get('qty',0);D=v.get('factor',1)
		if D<0:A=-A
		if C=='day':B+=A
		elif C=='hour':B+=A/8.
		elif C=='minute':B+=A/48e1
	return B
class Payslip(models.Model):
	_name='hr.ph.payslip';_description='Payslip';_order='date_to desc, name asc'
	@api.model
	def compute_basic_days(self,v):
		B=.0
		if v.get('basic_pay'):
			C=v.get('unit');A=v.get('qty',0);F=v.get('factor',1)
			if F<0:A=-A
			D=self.browse(v.get('payslip_id'))
			if D:
				E=D.emr_days/12.
				if D.salary_rate_period=='monthly':
					if C=='month':B+=A
					elif C=='day':B+=A/E
					elif C=='hour':B+=A/(E*8.)
					elif C=='minute':B+=A/(E*48e1)
				elif C=='month':B+=A*D.emr_days/12.
				elif C=='day':B+=A
				elif C=='hour':B+=A/8.
				elif C=='minute':B+=A/48e1
			_logger.debug('compute_basic_days: %s period=%s emr=%s unit=%s qty=%s basic_days=%s',D.employee_id.name,D.salary_rate_period,D.emr_days,C,A,B)
		return B
	def del_blank(B):
		for A in B:
			if A.net_pay==.0 and A.gross_pay==.0:A.unlink()
	@api.model
	def get_totals(self,payslips):
		C={'amount':.0,'er_amount':.0,'er_amount1':.0,'er_amount2':.0};E=.0;F=.0;G=.0;B={}
		for D in payslips:
			E+=D.taxable;F+=D.gross_pay;G+=D.basic_pay
			for A in D.deduction_line:B[A.code]={'amount':B.get(A.code,dict(C))['amount']+A.amount,'er_amount':B.get(A.code,dict(C))['er_amount']+A.er_amount,'er_amount1':B.get(A.code,dict(C))['er_amount1']+A.er_amount1,'er_amount2':B.get(A.code,dict(C))['er_amount2']+A.er_amount2}
		return F,E,G,B
	@api.model
	def get_prev_totals(self,payslip):
		A=payslip;filter=[('employee_id','=',A.employee_id.id),('year_month','=',A.year_month),('date_to','<',A.payroll_id.date_from)];B=A.search(filter)
		for C in B:
			if C.state=='draft':raise ValidationError(_('Cannot compute deductions. A previous payroll record is still draft. %s')%C.payroll_id.name)
		return A.get_totals(B)
	def recompute_compensation_button(A):A.ensure_one();B=A.env['ez.work.summary.sheet'].search([('state','!=','draft'),('date','>=',A.date_from),('date','<=',A.date_to)]);C=[A.id for A in B];A.recompute_compensation(work_sheet_ids=C)
	@api.model
	def get_compensation_lines(self):
		C=[]
		for A in self:
			B={};_logger.debug('get_compensation_lines: init=%s, 13mo=%s, period=%s',A.payroll_id.initial_import,A.payroll_id.is_13th_month,A.salary_rate_period)
			if A.payroll_id.initial_import:0
			elif A.payroll_id.is_13th_month:B=A.get_13th_month_line()
			elif A.salary_rate_period=='monthly':B=A.get_monthly_compensation_line()
			if B:C.append(B);_logger.debug('get_compensation_lines: val=%s',B)
		return C
	@api.model
	def get_monthly_compensation_line(self):A=self;A.ensure_one();return{'payslip_id':A.id,'name':'Regular','seq':5,'computed':True,'qty':A.payroll_id.total_days<21 and .5 or 1.,'unit':'month','factor':1,'basic_pay':True,'taxable':True,'employee_id':A.employee_id.id,'date_to':A.payroll_id.date_to}
	@api.model
	def get_13th_month_line(self):
		A=self;A.ensure_one()
		if A.payroll_id.payroll_type=='13th-month-basic':
			C=A.env['hr.ph.payslip'].search([('employee_id','=',A.employee_id.id),('date_from','>=',A.date_from),('date_to','<=',A.date_to),('state','!=','draft')]);B=.0
			for D in C:B+=D.basic_pay
			E=round((A.date_to-A.date_from).days*12./365.,0);return{'payslip_id':A.id,'name':'13th Month Pay - %1.0f months'%E,'seq':5,'computed':True,'qty':B/12.,'unit':'fixed','factor':1,'basic_pay':False,'taxable':False}
		else:return{'payslip_id':A.id,'name':'13th Month Pay','seq':5,'computed':True,'qty':1,'unit':'month','factor':1,'basic_pay':False,'taxable':False}
	def recompute_compensation(B,work_sheet_ids):
		N=work_sheet_ids;G=time.time();E={};_logger.debug('recompute_compensation default: %s ws=%s',len(B),len(N));P=B.env['hr.ph.pay.computation'].search([('payslip_id','in',B.ids),('computed','=',True)]);P.unlink();_logger.debug('del pc lines: %s',time.time()-G);Q=B.env['ez.work.summary.line'].search([('payslip_id','in',B.ids)]);Q.write({'payslip_id':False});_logger.debug('set payslip_id to false: %s',time.time()-G);I=B.get_compensation_lines();_logger.debug('get comp lines: %s',time.time()-G);D={}
		for F in I:
			J=F.get('payslip_id')
			if J:
				if J not in D:D[J]=.0
				D[J]+=B.compute_basic_days(F)
		for A in B:
			K=B.env['ez.work.summary.sheet'].get_pay_lines(A,N)
			for H in K:
				F=dict(K[H]);del F['ws_lines'];I.append(F)
				if A.id not in E:E[A.id]=[]
				E[A.id]+=K[H]['ws_lines']
				if A.id not in D:D[A.id]=.0
				D[A.id]+=B.compute_basic_days(F)
			if not A.payroll_id.initial_import and not A.payroll_id.is_13th_month:
				for C in A.employee_id.deminimis_line:
					L=False
					if C.payment_days and C.payment_days.strip():
						R=[A for A in re.split('[,\\s]+',C.payment_days.strip())if A];S=['%02d'%int(A)for A in R];T=fields.Date.to_string(A.date_to)[8:10]
						if T in S:L=True
					else:L=True
					if L:
						O={'payslip_id':A.id,'name':C.name,'seq':C.seq+500,'computed':True,'unit':C.unit,'factor':C.factor,'basic_pay':C.basic_pay,'taxable':C.taxable}
						if C.days_variable:M=C.qty*D.get(A.id,.0)
						else:M=C.qty
						if M:O['qty']=M;I.append(O)
		_logger.debug('get ws lines: %s',time.time()-G);B.create_computations(I)
		if E:
			U=B.env['ez.work.summary.line']
			for H in E:V=U.search([('id','in',list(E[H]))]);V.payslip_id=H
		_logger.debug('update ws lines: %s',time.time()-G)
	@api.model
	def create_computations(self,new_recs):
		B=new_recs;A=self
		if B:C=A.env.company.is_fast_insert();D=[A for A in B if A['qty']or A['factor']];execute_insert(A.env['hr.ph.pay.computation'],D,fast_mode=C);E=A.env['hr.ph.pay.computation'].search([('payslip_id','in',A.ids),('computed','=',True)]);E._compute_amount()
	def recompute_loan(A):
		for B in A:B.loan_line.unlink()
		A.generate_loans()
	def generate_loans(B):
		_logger.debug('Generate loan payments')
		for A in B:
			if not(A.payroll_id.is_13th_month or A.payroll_id.initial_import):B.env['hr.ph.loan'].create_loan_line(A)
	def recompute_deduction(A):
		D=time.time();J=A.env['hr.ph.pay.deduction']
		for B in A:J|=B.deduction_line
		J.unlink();_logger.debug('recompute_deduction del records: %s',time.time()-D);K=A.env['hr.ph.pay.deduction.entry.details'].search([('payslip_id','in',A.ids)]);K.write({'payslip_id':False});E=A.env['hr.ph.gov.deductions'].search([('date_from','<=',fields.Date.context_today(A)),('date_to','>=',fields.Date.context_today(A))],limit=1);_logger.debug('DED: %s %s',E.minimun_gross,E);C=[];M=False
		for B in A:
			if not(B.payroll_id.is_13th_month or B.payroll_id.initial_import or B.gross_pay<E.minimun_gross):F=A.get_prev_totals(B);C+=A.env['hr.ph.sss'].create_sss_line(B,F);C+=A.env['hr.ph.phic'].create_phic_line(B,F);C+=A.env['hr.ph.pay.deduction'].create_hdmf_line(B,F)
			if not(B.payroll_id.is_13th_month or B.gross_pay<E.minimun_gross):C+=A.env['hr.ph.pay.deduction.entry'].create_oded_line(B)
		for H in C:H.update({'er_amount':H.get('er_amount1',.0)+H.get('er_amount2',.0)})
		G=True
		if C:I=A.env.company.is_fast_insert();execute_insert(A.env['hr.ph.pay.deduction'],C,fast_mode=I);_logger.debug('insert ded lines: %s',time.time()-D);A._compute_totals();G=False;_logger.debug('recompute ded totals: %s',time.time()-D)
		C=[]
		for B in A:
			if not(B.payroll_id.is_13th_month or B.payroll_id.initial_import or B.gross_pay<E.minimun_gross):C+=A.env['hr.ph.wtax'].create_wtax_line(B,F);G=True
		if C:I=A.env.company.is_fast_insert();execute_insert(A.env['hr.ph.pay.deduction'],C,fast_mode=I);_logger.debug('insert ded lines2: %s',time.time()-D);G=True
		if G:
			A._compute_totals();_logger.debug('recompute ded totals2: %s',time.time()-D)
			for B in A:L=A.env['hr.ph.pay.deduction'].search([('payslip_id','=',B.id)]);L.write({'employee_id':B.employee_id.id,'date':B.payroll_id.date_to,'year_month':B.payroll_id.year_month})
	@api.model
	def create_new(self,payroll,emp):A=emp;B=self.create({'payroll_id':payroll.id,'employee_id':A.id,'name':A.name,'salary_rate':A.salary_rate,'salary_rate_period':A.salary_rate_period,'emr_days':A.emr_days,'daily_rate':A.daily_rate,'minimum_wage':A.minimum_wage,'no_deductions':A.no_deductions,'voluntary_hdmf':A.voluntary_hdmf,'wtax_percent':A.wtax_percent,'tax_code':A.tax_code})
	payroll_id=fields.Many2one('hr.ph.payroll','Payroll No.',ondelete='cascade',index=True);payroll_name=fields.Char(related='payroll_id.name',string='Payroll');year_month=fields.Char(related='payroll_id.year_month',string='Year-Month',store=True);year=fields.Char('Year',compute='_get_year',store=True,index=True);company_id=fields.Many2one(related='payroll_id.company_id',string='Company',store=True);date_from=fields.Date(related='payroll_id.date_from',string='Date From',store=True,index=True);date_to=fields.Date(related='payroll_id.date_to',string='Date To',store=True,index=True);state=fields.Selection(related='payroll_id.state',string='State',store=True);name=fields.Char(string='Employee Name',related='employee_id.name',store=True,readonly=True);employee_id=fields.Many2one('hr.employee','Employee',ondelete='restrict',index=True);image_1920=fields.Binary(related='employee_id.image_1920');avatar_128=fields.Binary(related='employee_id.avatar_128');atm_no=fields.Char(related='employee_id.atm_no');category_ids=fields.Many2many(related='employee_id.category_ids',string='Tags');identification_id=fields.Char('ID No.',related='employee_id.identification_id',related_sudo=True,readonly=True);emp_number=fields.Char(compute='_compute_emp_number',string='ID Number',store=True);salary_rate=fields.Float('Salary Rate',digits='Payroll Amount',readonly=False);salary_rate_period=fields.Selection([('daily','per day'),('monthly','per month')],'Rate Period',readonly=False);emr_days=fields.Integer(string='Working Days',help='Working days in a year. Factor in computing daily rate for monthly employees.');daily_rate=fields.Float('Daily Rate',digits='Payroll Amount');minimum_wage=fields.Boolean('Minimum Wage');no_deductions=fields.Boolean('No Deductions',help='Enable if employee will not have deductions.');voluntary_hdmf=fields.Float('Voluntary HDMF',digits='Payroll Amount',help='Amount of voluntary HDMF contribution of employee.');wtax_percent=fields.Float('W.Tax percent',digits='Payslip Line Unit',help='Withholding Tax percentage. Set to 0.0 if using table.');tax_code=fields.Char('Tax Code');note=fields.Text('Notes');basic_pay=fields.Float(compute='_compute_totals',string='Basic Pay',digits='Payroll Amount',store=True);gross_pay=fields.Float(compute='_compute_totals',string='Gross Pay',digits='Payroll Amount',store=True);mwe_basic_pay=fields.Float(compute='_compute_totals',string='MWE Basic',digits='Payroll Amount',store=True);mwe_hol=fields.Float(compute='_compute_totals',string='MWE Hol/OT/etc',digits='Payroll Amount',store=True);total_non_tax=fields.Float(compute='_compute_totals',string='T. Non-Taxable',digits='Payroll Amount',store=True);total_taxable=fields.Float(compute='_compute_totals',string='T. Taxable',digits='Payroll Amount',store=True);total_250k=fields.Float(compute='_compute_totals',string='<=250K',digits='Payroll Amount',store=True);net_taxable=fields.Float(compute='_compute_totals',string='Net Taxable',digits='Payroll Amount',store=True);taxable=fields.Float(compute='_compute_totals',string='Taxable',digits='Payroll Amount',store=True);total_deductions=fields.Float(compute='_compute_totals',string='Deductions',digits='Payroll Amount',store=True);total_loan_payments=fields.Float(compute='_compute_totals',string='Loan Payments',digits='Payroll Amount',store=True);net_pay=fields.Float(compute='_compute_totals',string='Net Pay',digits='Payroll Amount',store=True);de_minimis=fields.Float('De Minimis',compute='_compute_totals',digits='Payroll Amount',store=True);amount_13mp=fields.Float('13th Month',compute='_compute_totals',digits='Payroll Amount',store=True);td_deductions=fields.Float(compute='_compute_totals',string='Govt. Deductions',digits='Payroll Amount',store=True);nt_income=fields.Float(compute='_compute_totals',string='Non-Taxable',digits='Payroll Amount',store=True);holiday_pay=fields.Float(compute='_compute_totals',string='Holiday Pay',digits='Payroll Amount',store=True);overtime_pay=fields.Float(compute='_compute_totals',string='Overtime',digits='Payroll Amount',store=True);night_diff=fields.Float(compute='_compute_totals',string='Night Diff.',digits='Payroll Amount',store=True);hazard_pay=fields.Float(compute='_compute_totals',string='Hazard Pay',digits='Payroll Amount',store=True);other_pay=fields.Float(compute='_compute_totals',string='Other Pay',digits='Payroll Amount',store=True);wtax=fields.Float(compute='_compute_totals',string='W.Tax',digits='Payroll Amount',store=True);sss_ee=fields.Float(compute='_compute_totals',string='SSS EE',digits='Payroll Amount',store=True);sss_er=fields.Float(compute='_compute_totals',string='SSS ER',digits='Payroll Amount',store=True);sss_ec=fields.Float(compute='_compute_totals',string='SSS EC',digits='Payroll Amount',store=True);phic_ee=fields.Float(compute='_compute_totals',string='PHIC EE',digits='Payroll Amount',store=True);phic_er=fields.Float(compute='_compute_totals',string='PHIC ER',digits='Payroll Amount',store=True);hdmf_ee=fields.Float(compute='_compute_totals',string='HDMF EE',digits='Payroll Amount',store=True);hdmf_er=fields.Float(compute='_compute_totals',string='HDMF ER',digits='Payroll Amount',store=True);pay_computation_line=fields.One2many('hr.ph.pay.computation','payslip_id','Pay Computation');deduction_line=fields.One2many('hr.ph.pay.deduction','payslip_id','Deduction Line');loan_line=fields.One2many('hr.ph.loan.payment','payslip_id','Loan Payment Line');print_header=fields.Char('Header',compute='get_print_header')
	def _get_report_base_filename(A):return _('Payslips')
	@api.depends('date_from','date_to','employee_id')
	def _compute_display_name(self):
		for A in self:A.display_name='%s-%s (%s)'%(A.date_from and A.date_from.strftime('%m/%d/%Y')or'',A.date_to and A.date_to.strftime('%m/%d/%Y')or'',A.employee_id.name)
	@api.depends('company_id','company_id.payslip_header','payroll_id','payroll_id.emp_tag_ids')
	def get_print_header(self):
		for A in self:
			if A.company_id.payslip_header:A.print_header=A.company_id.payslip_header
			elif A.payroll_id.emp_tag_ids:B=[A.name for A in A.payroll_id.emp_tag_ids];C='/'.join(B);A.print_header=C
			else:A.print_header=A.company_id.name
	@api.depends('employee_id','employee_id.identification_id')
	def _compute_emp_number(self):
		for A in self:A.emp_number=A.sudo().employee_id.identification_id
	@api.depends('employee_id','employee_id.name')
	def get_name(self):
		for A in self:A.name=A.employee_id.name
	@api.depends('year_month')
	def _get_year(self):
		for A in self:
			if A.year_month:B=A.year_month.split('-');A.year=B[0]
	def compute_totals(A):A._compute_totals()
	@api.depends('employee_id','minimum_wage','salary_rate','salary_rate_period','pay_computation_line','pay_computation_line.name','pay_computation_line.basic_pay','pay_computation_line.taxable','pay_computation_line.amount','deduction_line','deduction_line.tax_deductible','deduction_line.amount','deduction_line.er_amount','deduction_line.code','loan_line','loan_line.amount','emr_days','payroll_id','payroll_id.is_13th_month')
	def _compute_totals(self):
		def a(payslip_id):
			A=payslip_id;C=A.emr_days or 313.
			if A.salary_rate_period=='monthly':B=12.*A.salary_rate
			else:B=A.salary_rate*C
			return B
		for A in self:
			V=.0;H=.0;E=.0;J=.0;K=.0;L=.0;I=.0;M=.0;W=.0;N=.0;O=.0;P=.0;Q=.0;R=.0;X=.0;Y=.0;F={};G={};Z=.0;S=.0;b=.0;T=.0;U=.0
			for B in A.pay_computation_line:
				H+=B.amount;D=B.name and B.name.upper()or''
				if A.payroll_id.is_13th_month or'13'in D or'(NT-ALLOW)'in D or'(NTALLOW)'in D:
					U+=B.amount
					if B.taxable:E+=B.amount
				elif B.basic_pay:
					V+=B.amount;E+=B.amount
					if A.minimum_wage:J+=B.amount
				elif B.taxable:
					E+=B.amount
					if'OVERTIME'in D or'RESTDAY'in D:O+=B.amount
					elif'HOLIDAY'in D or'RH'in D or'SH'in D:N+=B.amount
					elif'NIGHT DIFF'in D:P+=B.amount
					elif'HAZ'in D:Q+=B.amount
					else:R+=B.amount
					if A.minimum_wage:K+=O+N+P+Q+R
				else:T+=B.amount
			for C in A.deduction_line:
				X+=C.amount
				if C.tax_deductible:E-=C.amount;S+=C.amount
				F[C.code]=F.get(C.code,.0)+C.amount;G[C.code]=G.get(C.code,.0)+C.er_amount
				if C.code=='SSS':Z+=C.er_amount2
			L+=J+K+U+T+S;I+=H-L
			if not A.minimum_wage and a(A)<=25e4:M=I
			W=I-M
			for c in A.loan_line:Y+=c.amount
			A.basic_pay=V;A.gross_pay=H;A.mwe_basic_pay=J;A.mwe_hol=K;A.total_250k=M;A.net_taxable=W;A.total_non_tax=L;A.total_taxable=I;A.de_minimis=T;A.amount_13mp=U
			if E<.0:E=.0
			A.taxable=E;A.total_deductions=X;A.total_loan_payments=Y;A.net_pay=A.gross_pay-A.total_deductions-A.total_loan_payments;A.td_deductions=S;A.nt_income=b;A.wtax=F.get('WTAX',.0);A.sss_ee=F.get('SSS',.0);A.sss_er=G.get('SSS',.0);A.sss_ec=Z;A.phic_ee=F.get('PHIC',.0);A.phic_er=G.get('PHIC',.0);A.hdmf_ee=F.get('HDMF',.0)+F.get('HDMFV',.0);A.hdmf_er=G.get('HDMF',.0);A.holiday_pay=N;A.overtime_pay=O;A.night_diff=P;A.hazard_pay=Q;A.other_pay=R;_logger.debug('PS _compute_totals: %s',H)
	api.onchange('employee_id')
	def onchange_employee_id(A):_logger.debug('ONCHANGE employee_id: %s',A.employee_id.name)
	def action_view_compensations(A):A.ensure_one();return{'name':'Compensations','res_model':'ez.work.summary.line','type':'ir.actions.act_window','view_mode':'list','domain':[('employee_id','=',A.employee_id.id),('date','>=',A.date_from),('date','<=',A.date_to),('state','=','done')],'target':'current'}
	def action_view_deductions(A):A.ensure_one();return{'name':'Deductions','res_model':'hr.ph.pay.deduction.entry.details','type':'ir.actions.act_window','view_mode':'list','domain':[('employee_id','=',A.employee_id.id),('date','>=',A.date_from),('date','<=',A.date_to),('state','=','done')],'target':'current'}