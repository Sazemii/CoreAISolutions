from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
from odoo.modules.registry import Registry
from datetime import datetime
from dateutil.relativedelta import relativedelta
from io import StringIO,BytesIO
import base64,xlwt,logging,time,threading
_logger=logging.getLogger(__name__)
DF='%Y-%m-%d'
class Payroll(models.Model):
	_name='hr.ph.payroll';_description='Payroll Register';_inherit='mail.thread';_order='date_to desc,name'
	def add_new_employee(B,salary_rate=False,salary_rate_period=False,emr_days=False):
		F=emr_days;E=salary_rate_period;D=salary_rate;B.ensure_one()
		for G in B.payslip:
			if B.add_employee_id==G.employee_id:raise ValidationError('Cannot add. Employee already exists in payroll.')
		A=B.add_employee_id
		if not D:D=A.salary_rate
		if not E:E=A.salary_rate_period
		if not F:F=A.emr_days
		H={'payroll_id':B.id,'employee_id':A.id,'salary_rate':D,'salary_rate_period':E,'emr_days':F,'daily_rate':A.daily_rate,'minimum_wage':A.minimum_wage,'no_deductions':A.no_deductions,'voluntary_hdmf':A.voluntary_hdmf,'wtax_percent':A.wtax_percent,'tax_code':A.tax_code};C=B.payslip.create(H);C.recompute_compensation_button();C.recompute_deduction();C.generate_loans();B.add_employee_id=False;return C
	company_id=fields.Many2one('res.company',string='Company',default=lambda self:self.env.company);name=fields.Char('Payroll Number',tracking=True);department_id=fields.Many2one('hr.department','Department');emp_tag_ids=fields.Many2many('hr.employee.category','payroll_employee_tag_rel','alphalist_id','emp_tag_id',string='Employee Tags',tracking=True);date_from=fields.Date('Date From',required=True,tracking=True);date_to=fields.Date('Date To',required=True,tracking=True);year_month=fields.Char(compute='_compute_dates',compute_sudo=True,string='Year-Month',store=True);total_days=fields.Integer(compute='_compute_dates',compute_sudo=True,store=True,string='Total Days');days_in_month=fields.Integer(compute='_compute_dates',compute_sudo=True,type='integer',string='Days In Month',store=True);state=fields.Selection([('draft','Draft'),('done','Done')],string='State',default='draft',tracking=True,required=True);note=fields.Text('Notes');is_13th_month=fields.Boolean('13th Month',compute='compute_initial_import');initial_import=fields.Boolean('Initial Import',compute='compute_initial_import');payroll_type=fields.Selection([('standard','Standard'),('final-pay','Final Pay'),('initial-import','Initial Import'),('13th-month','13th Month - 1 month salary'),('13th-month-basic','13th Month - (Yearly Basic Salary)/12')],string='Type',default='standard',required=True,tracking=True);payslip=fields.One2many('hr.ph.payslip','payroll_id','Payslips');basic_pay=fields.Float(compute='_compute_totals',string='Basic Pay',digits='Payroll Amount');gross_pay=fields.Float(compute='_compute_totals',string='Gross Pay',digits='Payroll Amount');total_deductions=fields.Float(compute='_compute_totals',string='Deductions',digits='Payroll Amount');total_loan_payments=fields.Float(compute='_compute_totals',string='Loan Payments',digits='Payroll Amount');net_pay=fields.Float(compute='_compute_totals',string='Net Pay',digits='Payroll Amount');employees=fields.Integer(compute='_compute_totals');color=fields.Integer(compute='get_color');add_employee_id=fields.Many2one('hr.employee','Add Employee');fr_data=fields.Binary(string='Financial Report',readonly=True);fr_filename=fields.Char(string='Financial Report Filename');bank_data=fields.Binary(string='Bank Report',readonly=True);bank_filename=fields.Char(string='Bank Report Filename');is_favorite=fields.Boolean('Favorite');ym_adjustment=fields.Integer()
	@api.model
	def update_fin_reports_line(self,emp,pr,ps):A=emp;return{'0000000000-PAYROLL':pr.name,'0000000002-ID NO.#':A.identification_id or'','0000000004-NAME':A.name or'','0000000005-DEPARTMENT':A.department_id.name or'','B000000000-GROSS PAY':ps.gross_pay,'B000000001-BASIC PAY':ps.basic_pay,'B000000002-TAXABLE':ps.taxable,'E000000001-NET PAY':ps.net_pay}
	def generate_fin_reports(T):
		def D(d,seq,name,amt):
			A=name
			if amt:A=A.strip().upper();B=d.get(A,[.0,seq]);B[0]+=amt;d[A]=B
		def Z(d):
			A=[]
			for B in d:C=d[B];A.append((B,C[0],C[1]))
			return sorted(A,key=lambda z:z[2])
		def I(d,line,prefix):
			for A in Z(d):B='%s%09d-%s'%(prefix,A[2],A[0]);line[B]=A[1]
		def J(d):
			for A in d:d[A][0]=.0
		a=xlwt.easyxf('alignment: horizontal left;')
		for B in T:
			U=xlwt.Workbook();M=U.add_sheet('%s to %s'%(B.date_from,B.date_to));M.write(0,0,'FINANCIAL REPORT',xlwt.easyxf('font: bold on'));V=[];N={};O={};P={};Q={};E={}
			for F in B.payslip:
				b=F.employee_id;C=T.update_fin_reports_line(b,B,F)
				for G in C:N[G]=None
				for R in F.pay_computation_line:D(O,R.seq,R.name,R.amount)
				for A in F.deduction_line:
					D(P,A.seq,A.name,A.amount)
					if A.name=='SSS Premium':D(E,A.seq,A.name+' ER',A.er_amount1);D(E,A.seq+1,'EC',A.er_amount2)
					else:D(E,A.seq,A.name+' ER',A.er_amount1)
				for S in F.loan_line:D(Q,S.seq,S.loan_type_id.name,S.amount)
				I(O,C,'A');I(P,C,'C');I(Q,C,'D');I(E,C,'Z');V.append(C)
				for G in C:N[G]=None
				J(O);J(P);J(Q);J(E)
			W=sorted(N.keys());K=1;H=0
			for c in W:L=c[11:];M.write(K,H,L,a);H+=1
			K+=1
			for d in V:
				X=[]
				for G in W:X.append(d.get(G,.0))
				H=0
				for L in X:
					if L:M.write(K,H,L)
					H+=1
				K+=1
			Y=BytesIO();U.save(Y);e=base64.b64encode(Y.getvalue());B.fr_data=e;B.fr_filename='financial_report.xls';f,g=B.create_bank_report();B.bank_data=f;B.bank_filename=g
	@api.depends('payroll_type')
	def compute_initial_import(self):
		for A in self:
			if A.payroll_type=='initial-import':A.initial_import=True;A.is_13th_month=False
			elif A.payroll_type=='13th-month'or A.payroll_type=='13th-month-basic':A.initial_import=False;A.is_13th_month=True
			else:A.initial_import=False;A.is_13th_month=False
	@api.depends('state')
	def get_color(self):
		for A in self:
			B=1
			if A.state=='done':B=4
			A.color=B
	def del_blank(A):
		for B in A:B.payslip.del_blank()
	@api.model
	def get_employees_to_process(self,payroll):
		A=payroll;B=[]
		for D in A.payslip:B.append(D.employee_id.id)
		if A.payroll_type=='final-pay':filter=[('company_id','=',A.company_id.id),('exclude_from_payroll','=',False),('id','not in',B),('date_end','>=',A.date_from),('date_end','<=',A.date_to)]
		else:filter=[('company_id','=',A.company_id.id),('exclude_from_payroll','=',False),('id','not in',B),'|',('date_end','>',A.date_to),('date_end','=',False)]
		filter+=['|',('hired','<=',A.date_to),('hired','=',False)];C=[]
		for E in A.emp_tag_ids:C.append(E.id)
		if C:filter.append(('category_ids','in',C))
		if A.department_id:filter.append('|');filter.append(('department_id','=',A.department_id.id));filter.append(('department_id.master_department_id','=',A.department_id.id))
		F=self.env['hr.employee'].search(filter);return F
	@api.model
	def get_emp_rates(self,employee_id,date_from,date_to):A=employee_id;B={'employee_id':A.id,'salary_rate':A.salary_rate,'salary_rate_period':A.salary_rate_period,'emr_days':A.emr_days,'daily_rate':A.daily_rate,'minimum_wage':A.minimum_wage,'no_deductions':A.no_deductions,'voluntary_hdmf':A.voluntary_hdmf,'wtax_percent':A.wtax_percent,'tax_code':A.tax_code};return B
	def auto_gen(B):
		for A in B:
			B.clpay(A);C=time.time();E=B.get_employees_to_process(A);H=E.ids;F=[]
			for I in E:G=B.get_emp_rates(I,A.date_from,A.date_to);G.update({'payroll_id':B.id});F.append([0,0,G])
			A.payslip=F;_logger.debug('* Create payslips: %s',time.time()-C);D=B.env['hr.ph.payslip'].search([('payroll_id','=',A.id),('employee_id','in',H)]);J=B.env['ez.work.summary.sheet'].search([('state','!=','draft'),('date','>=',A.date_from),('date','<=',A.date_to)]);K=[A.id for A in J];D.recompute_compensation(work_sheet_ids=K);_logger.debug('* Compute compensation: %s',time.time()-C);D.recompute_deduction();_logger.debug('* Compute deductions: %s',time.time()-C);D.generate_loans();_logger.debug('* Compute loans: %s',time.time()-C)
		for A in B:
			for L in A.payslip:L._compute_totals()
	def auto_gen2(B):
		def M(data,chunksize):
			A=chunksize
			for B in range(0,len(data),A):yield data[B:B+A]
		def H(alist,wanted_parts=1):B=alist;A=wanted_parts;C=len(B);D=[B[D*C//A:(D+1)*C//A]for D in range(A)];return D
		for D in B:
			N=time.time();I=B.get_employees_to_process(D);C=I.ids;O=[];J=B.env['ez.work.summary.sheet'].search([('state','!=','draft'),('date','>=',D.date_from),('date','<=',D.date_to)]);F=[A.id for A in J];G=5
			if C and len(C)>G:
				K=H(C,wanted_parts=G);E=[]
				for L in range(5):_logger.debug('* Thread: %s',L);A=threading.Thread(target=B.threaded_gen_payslips,args=[K[0],F]);E.append(A)
				for A in E:A.start()
				for A in E:A.join()
				_logger.debug('* Thread stop')
			else:A=threading.Thread(target=B.threaded_gen_payslips,args=(C,F));A.start();A.join()
	def threaded_gen_payslips(B,emp_ids,work_sheet_ids):
		with Registry(B.env.cr.dbname).cursor()as C:
			G=time.time();B=B.with_env(B.env(cr=C))
			try:
				D=B.env['hr.ph.payslip'].browse(0)
				for E in emp_ids:A=B.env['hr.employee'].browse(E);F={'payroll_id':B.id,'employee_id':A.id,'name':A.name,'salary_rate':A.salary_rate,'salary_rate_period':A.salary_rate_period,'emr_days':A.emr_days,'daily_rate':A.daily_rate,'minimum_wage':A.minimum_wage,'no_deductions':A.no_deductions,'voluntary_hdmf':A.voluntary_hdmf,'wtax_percent':A.wtax_percent,'tax_code':A.tax_code};D=B.env['hr.ph.payslip'].create(F);D.recompute_compensation(work_sheet_ids=work_sheet_ids);D.recompute_deduction();D.generate_loans()
				C.commit()
			except Exception:C.rollback()
			finally:C.close()
			return{}
	def recompute_payroll(A):_logger.debug('recompute_all: Recompute');A.clpay(A);A.recompute_compensation();A.recompute_deduction();A.recompute_loan()
	def recompute_compensation(A):
		_logger.debug('recompute_compensation: start');C=A.env['hr.ph.payslip']
		for B in A:D=A.env['ez.work.summary.sheet'].search([('state','!=','draft'),('date','>=',B.date_from),('date','<=',B.date_to)]);E=[A.id for A in D];C|=B.payslip
		C.recompute_compensation(work_sheet_ids=E)
	def recompute_deduction(A):
		_logger.debug('recompute_deduction: start')
		for B in A:B.payslip.recompute_deduction()
	def recompute_loan(A):
		for B in A:B.payslip.recompute_loan()
	@api.depends('payslip','payslip.basic_pay','payslip.gross_pay','payslip.total_deductions','payslip.total_loan_payments','payslip.net_pay')
	def _compute_totals(self):
		for A in self:
			C=.0;D=.0;E=.0;F=.0;G=.0;H=0
			for B in A.payslip:C+=B.basic_pay;D+=B.gross_pay;E+=B.total_deductions;F+=B.total_loan_payments;G+=B.net_pay;H+=1
			A.basic_pay=C;A.gross_pay=D;A.total_deductions=E;A.total_loan_payments=F;A.net_pay=G;A.employees=H
	@api.depends('date_from','date_to','is_13th_month','ym_adjustment')
	def _compute_dates(self):
		for A in self:
			if A.date_to:B=fields.Date.from_string(A.date_to)-relativedelta(days=A.ym_adjustment);C=B.strftime('%Y-%m');A.year_month=C[:7]
			else:A.year_month=False
			if A.date_from and A.date_to:D=fields.Date.to_date(A.date_to);E=fields.Date.to_date(A.date_from);A.total_days=(D-E).days+1
			else:A.total_days=False
	def unlink(A):
		for B in A:
			if B.state!='draft':raise ValidationError(_('You cannot delete a payroll record that is not draft.'))
		return super(Payroll,A).unlink()
	def set_as_done(A):
		for B in A:B.state='done'
	def cancel_done(A):
		for B in A:B.state='draft'
	def recompute_all(A):
		for B in A:B.payslip._compute_totals()
	@api.model
	def amount_to_words(self,amt):
		'words = {} convert an integer number into words';F=['','one','two','three','four','five','six','seven','eight','nine'];L=['','eleven','twelve','thirteen','fourteen','fifteen','sixteen','seventeen','eighteen','nineteen'];J=['','ten','twenty','thirty','forty','fifty','sixty','seventy','eighty','ninety'];M=['','thousand','million','billion','trillion','quadrillion','quintillion','sextillion','septillion','octillion','nonillion','decillion','undecillion','duodecillion','tredecillion','quattuordecillion','sexdecillion','septendecillion','octodecillion','novemdecillion','vigintillion'];A=[];G=int(amt);N=(amt-G)*100
		if G==0:A.append('zero')
		else:
			C='%d'%G;O=len(C);H=int((O+2)/3);C=C.zfill(H*3)
			for E in range(0,H*3,3):
				I,D,B=int(C[E]),int(C[E+1]),int(C[E+2]);K=H-(int(E/3)+1)
				if I>=1:A.append(F[I]);A.append('hundred')
				if D>1:
					A.append(J[D])
					if B>=1:A.append(F[B])
				elif D==1:
					if B>=1:A.append(L[B])
					else:A.append(J[D])
				elif B>=1:A.append(F[B])
				if K>=1 and I+D+B>0:A.append(M[K])
		A.append('AND %d/100'%N);return' '.join(A)
	def action_view_payslips(A):A.ensure_one();return{'name':'Payslips','res_model':'hr.ph.payslip','type':'ir.actions.act_window','view_mode':'list,form','view_type':'form','domain':[('payroll_id','=',A.id)],'target':'current','context':{'default_payroll_id':A.id}}
class YearMonth(models.Model):
	_name='hr.ph.pay.year.month';_description='Payroll Year-Month';_auto=False;_rec_name='name';_order='name desc';name=fields.Char();color=fields.Integer(string='Color Index',compute='_get_default_color')
	def _get_default_color(B):
		for A in B:A.color=A.id%10+1
	def init(A):tools.drop_view_if_exists(A.env.cr,'hr_ph_pay_year_month');A.env.cr.execute("\n            CREATE VIEW hr_ph_pay_year_month AS (\n                SELECT\n                    MIN(id) AS id,\n                    year_month AS name\n                FROM hr_ph_payroll\n                WHERE state != 'draft'                         \n                GROUP BY year_month                \n            )")
class PayYear(models.Model):
	_name='hr.ph.pay.year';_description='Payroll Year';_auto=False;_rec_name='name';_order='name desc';name=fields.Char();color=fields.Integer(string='Color Index',compute='_get_default_color')
	def _get_default_color(B):
		for A in B:A.color=A.id%10+1
	def init(A):tools.drop_view_if_exists(A.env.cr,'hr_ph_pay_year');A.env.cr.execute("\n            CREATE VIEW hr_ph_pay_year AS (\n                SELECT\n                    MIN(id) AS id,\n                    LEFT(year_month,4) AS name\n                FROM hr_ph_payroll\n                WHERE state != 'draft'                         \n                GROUP BY LEFT(year_month,4)\n            )")