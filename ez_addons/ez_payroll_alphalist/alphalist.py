from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
from datetime import datetime
import datetime
from dateutil.relativedelta import relativedelta
from io import StringIO,BytesIO
from.wtax_formula import compute_income_tax
from.pdfutil import create_pdf2
import base64,os,inspect,csv,xlrd,xlwt
try:from odoo.tools.misc import xlsxwriter
except ImportError:import xlsxwriter
import logging
_logger=logging.getLogger(__name__)
list_employment_status=[('R','Regular'),('C','Casual'),('CP','Contractual/Project-Based'),('S','Seasonal'),('P','Probationary'),('AL','Apprentices/Learners')]
list_separation_reason=[('T','Terminated/Resigned'),('TR','Transferred'),('R','Retirement'),('D','Death')]
list_region=[('I','I'),('II','II'),('III','III'),('IV-A','IV-A'),('IV-B','IV-B'),('V','V'),('VI','VI'),('VII','VII'),('VIII','VIII'),('IX','IX'),('X','X'),('XI','XI'),('XII','XII'),('XIII','XIII'),('ARMM','ARMM'),('CAR','CAR'),('NCR','NCR')]
def parse_float(plist):
	A=plist
	for B in range(len(A)):
		C=A[B]
		if isinstance(C,float):A[B]=round(C,2)
def _get_income_tax(amount):return compute_income_tax(amount)
def format_tin(tin):
	A=tin
	try:
		D=filter(str.isdigit,A);A=''.join(D)
		if len(A)>9:B='%09d'%int(A[0:9]);C='%04d'%int(A[9:])
		else:B='%09d'%int(A);C='0000'
	except:return'',''
	return B,C
def format_tin2(tin):
	A=tin
	try:
		D=filter(str.isdigit,A);A=''.join(D)
		if len(A)>9:B='%09d'%int(A[0:9]);C='%04d'%int(A[9:])
		else:B='%09d'%int(A);C='0000'
	except:return'',''
	return B[0:3]+'-'+B[3:6]+'-'+B[6:],C
def format_name(n):A=(n or'').upper().replace('"','').replace('Ñ','N').replace('\n','');return A
def cell_name(row,col):
	A=col;C='ABCDEFGHIJKLMNOPQRSTUVWXYZ';B=[]
	while A:A,D=divmod(A-1,26);B[:0]=C[D]
	return''.join(B)+str(row)
class AlphaList(models.Model):
	_name='ez.bir.alphalist';_description='BIR Alphalist';_inherit=['mail.thread'];_order='year desc, name'
	def default_company_name(A):return A.env.company.name
	def default_company_address(C):
		A=C.env.company;B=A.street or''
		if A.street2:B+=', '+A.street2
		if A.city:B+=', '+A.city
		if A.country_id:B+=', '+A.country_id.name
		return B
	def default_company_zip(A):return A.env.company.zip
	def default_company_vat(A):return A.env.company.vat
	company_id=fields.Many2one('res.company',string='Company',default=lambda self:self.env.company,readonly=True);name=fields.Char(tracking=True);company_name=fields.Char(default=default_company_name,tracking=True);company_address=fields.Char(default=default_company_address,tracking=True);company_zip=fields.Char(default=default_company_zip,tracking=True);company_vat=fields.Char('Company TIN',default=default_company_vat,tracking=True);signatory=fields.Char(tracking=True);signature_data=fields.Binary(string='Signature Image');signature_filename=fields.Char(string='Signature Image Filename',tracking=True);sign_date=fields.Date('Date Signed');sig_width=fields.Integer('Signature Width',default=lambda self:100);sig_position1=fields.Integer('Position 1',default=lambda self:130);sig_position2=fields.Integer('Position 2',default=lambda self:15);year=fields.Char(required=True,tracking=True,default=lambda self:fields.Date.to_string(fields.Date.context_today(self))[:4]);emp_tag_ids=fields.Many2many('hr.employee.category','alphalist_employee_tag_rel','alphalist_id','emp_tag_id',string='Employee Tags',tracking=True);region=fields.Selection(list_region,'Region',default='NCR',tracking=True);rdo=fields.Char('RDO',tracking=True);limit_13mp=fields.Float('13-MP Limit',default=9e4,digits='Payroll Amount',tracking=True);mwe_daily_amount=fields.Float('Min. Daily Wage',digits=(0,2),default=537.,tracking=True);mwe_monthly_amount=fields.Float('Min. Monthly Wage',digits=(0,2),store=True,compute='_get_my_amount',tracking=True);mwe_yearly_amount=fields.Float('Min. Yearly Wage',digits=(0,2),store=True,compute='_get_my_amount');mwe_days_in_year=fields.Integer('Days in a Year',default=313,tracking=True);sch1_data=fields.Binary('Schedule 1 Data');sch1_filename=fields.Char('Schedule 1 DAT');sch2_data=fields.Binary('Schedule 2 Data');sch2_filename=fields.Char('Schedule 2 DAT');sch_combined_data=fields.Binary('Schedule Combined');sch_combined_filename=fields.Char('Combined DAT');bir1604c1_data=fields.Binary('1604C Schedule 1');bir1604c1_filename=fields.Char('1604C-1 Filename');bir1604c2_data=fields.Binary('1604C Schedule 2');bir1604c2_filename=fields.Char('1604C-2 Filename');url1_2316=fields.Char('Form 2316 Sch 1',compute='_get_url2316');url2_2316=fields.Char('Form 2316 Sch 2',compute='_get_url2316');schedule1_ids=fields.One2many('ez.bir.alphalist.schedule1','alphalist_id','Schedule 1');schedule2_ids=fields.One2many('ez.bir.alphalist.schedule2','alphalist_id','Schedule 2');shedule1_count=fields.Integer(compute='_get_schedule_count');shedule2_count=fields.Integer(compute='_get_schedule_count');state=fields.Selection([('draft','Draft'),('done','Done')],string='State',default='draft',tracking=True,required=True)
	def compute_zip_sched1(A):A.ensure_one();B='/bir2316-1/%s'%A.id;return{'name':'Sched 1 Form 2316','res_model':'ir.actions.act_url','type':'ir.actions.act_url','target':'self','url':B}
	def compute_zip_sched2(A):A.ensure_one();B='/bir2316-2/%s'%A.id;return{'name':'Sched 2 Form 2316','res_model':'ir.actions.act_url','type':'ir.actions.act_url','target':'self','url':B}
	@api.depends('schedule1_ids','schedule2_ids')
	def _get_schedule_count(self):
		for A in self:A.shedule1_count=len(A.schedule1_ids);A.shedule2_count=len(A.schedule2_ids)
	def action_view_schedule1(A):A.ensure_one();return{'name':'Schedule 1','res_model':'ez.bir.alphalist.schedule1','type':'ir.actions.act_window','view_mode':'list,form','view_type':'form','domain':[('alphalist_id','=',A.id)],'target':'current','context':{'default_alphalist_id':A.id}}
	def action_view_schedule2(A):A.ensure_one();return{'name':'Schedule 2','res_model':'ez.bir.alphalist.schedule2','type':'ir.actions.act_window','view_mode':'list,form','view_type':'form','domain':[('alphalist_id','=',A.id)],'target':'current','context':{'default_alphalist_id':A.id}}
	def set_as_done(A):A.ensure_one();A.state='done'
	def cancel_done(A):A.ensure_one();A.state='draft'
	def _get_url2316(B):
		C=B.env['ir.config_parameter'].sudo().get_param('web.base.url')
		for A in B:A.url1_2316='%s/bir2316-1/%s'%(C,A.id);A.url2_2316='%s/bir2316-2/%s'%(C,A.id)
	@api.depends('mwe_daily_amount','mwe_days_in_year')
	def _get_my_amount(self):
		for A in self:A.mwe_monthly_amount=A.mwe_daily_amount*A.mwe_days_in_year/12.;A.mwe_yearly_amount=A.mwe_daily_amount*A.mwe_days_in_year
	@api.model
	def add_sch1(self,alphalist,employees):
		E=alphalist;M=[]
		for A in employees:
			_logger.debug('**add_employees: sch1 - %s',A);M.append(A.id);N=self.env['hr.ph.payslip'].search([('employee_id','=',A.id),('year','=',E.year),('state','!=','draft')])
			if N:
				F=.0;I=.0;J=.0;C=.0;G=.0;O=.0
				for B in N:G+=B.td_deductions;I+=B.basic_pay;O+=B.wtax;F+=B.gross_pay;C+=B.amount_13mp;J+=B.de_minimis
				P=min(E.limit_13mp,C);T=C-P;U=F-C-G
				try:K=int(E.year)
				except:K=1900
				L='%04d-01-01'%K;Q='%04d-12-31'%K;D=fields.Date.to_string(A.hired)
				if not D or D<L:D=L
				H=fields.Date.to_string(A.date_end)
				if not H or H>Q:H=Q
				if not A.country_id or A.country_id.name=='Phlippines':R='FILIPINO'
				else:R=A.country_id.name.upper()
				S={'alphalist_id':E.id,'employee_id':A.id,'hired':D,'date_end':H,'nationality':R,'tin_no':A.tin_no,'employment_status':A.employment_status,'separation_reason':A.separation_reason,'pres_tax_withheld':O,'pres_nt_income':.0,'pres_nt_13mp':P,'pres_nt_deminimis':J,'pres_nt_govded':G,'pres_nt_others':.0,'pres_t_income':I-G,'pres_t_13mp':T,'pres_t_others':F-I-C-J,'substituted_filing':D==L};_logger.debug('***add_employees: %s',S)
				if F:self.schedule1_ids.create(S)
		return M
	@api.model
	def add_sch2(self,alphalist,employees):
		D=alphalist;K=[]
		for A in employees:
			_logger.debug('**add_employees: sch1 - %s',A);K.append(A.id);L=self.env['hr.ph.payslip'].search([('employee_id','=',A.id),('year','=',D.year),('state','!=','draft')])
			if L:
				H=.0;M=.0;N=.0;O=.0;P=.0;Q=.0;R=.0;S=.0;E=.0;F=.0;X=.0
				for B in L:F+=B.td_deductions;M+=B.basic_pay;X+=B.wtax;H+=B.gross_pay;E+=B.amount_13mp;S+=B.de_minimis;N+=B.holiday_pay;O+=B.overtime_pay;P+=B.night_diff;Q+=B.hazard_pay;R+=B.other_pay
				T=min(D.limit_13mp,E);Y=E-T;Z=H-E-F
				try:I=int(D.year)
				except:I=1900
				J='%04d-01-01'%I;U='%04d-12-31'%I;C=fields.Date.to_string(A.hired)
				if not C or C<J:C=J
				G=fields.Date.to_string(A.date_end)
				if not G or G>U:G=U
				if not A.country_id or A.country_id.name=='Phlippines':V='FILIPINO'
				else:V=A.country_id.name.upper()
				W={'alphalist_id':D.id,'employee_id':A.id,'hired':C,'date_end':G,'nationality':V,'tin_no':A.tin_no,'employment_status':A.employment_status,'separation_reason':A.separation_reason,'pres_nt_basic':M-F,'pres_nt_holiday':N,'pres_nt_overtime':O,'pres_nt_night_diff':P,'pres_nt_hazard':Q,'pres_nt_13mp':T,'pres_nt_deminimis':S,'pres_nt_govded':F,'pres_nt_others':R,'pres_t_13mp':Y,'substituted_filing':C==J};_logger.debug('***add_employees: %s',W)
				if H:self.schedule2_ids.create(W)
		return K
	def auto_gen(B):
		for C in B:
			F=[]
			for E in C.schedule1_ids:F.append(E.employee_id.id)
			G=[]
			for E in C.schedule2_ids:G.append(E.employee_id.id)
			A=[]
			for K in C.emp_tag_ids:A.append(K.id)
			try:H=int(C.year)
			except:raise ValidationError(_('Wrong year.'))
			I='%s-01-01'%H;J='%s-12-31'%H;_logger.debug('***auto-gen: tags=%s',A);filter=[('minimum_wage','=',False),('id','not in',F),'|',('date_end','=',False),('date_end','>=',I),'|',('hired','=',False),('hired','<=',J),'|',('active','=',True),('active','=',False)]
			if A:filter.append(('category_ids','in',A))
			D=B.env['hr.employee'].search(filter)
			if A:filter.append(('category_ids','in',A))
			D=B.env['hr.employee'].search(filter);B.add_sch1(C,D);filter=[('minimum_wage','=',True),('id','not in',G),'|',('date_end','=',False),('date_end','>=',I),'|',('hired','=',False),('hired','<=',J),'|',('active','=',True),('active','=',False)];D=B.env['hr.employee'].search(filter)
			if A:filter.append(('category_ids','in',A))
			D=B.env['hr.employee'].search(filter);B.add_sch2(C,D);C.schedule1_ids.swap_income_lte250K()
	def recompute_annualization(A):
		A.ensure_one();C=A.env['hr.ph.payslip'].search([('year_month','=like',A.year+'%'),('state','!=','draft')])
		for B in C:_logger.debug('compute pay: %s',B.name);B.compute_pay()
	def action_swap_lte250K(A):A.ensure_one();A.schedule1_ids.swap_income_lte250K();A.adjust_wtax()
	def adjust_wtax(C):
		C.ensure_one()
		for A in C.schedule1_ids:
			B=A.pres_tax_withheld+A.prev_tax_withheld+A.pera_tax_credit
			if B>A.tax_due:A.tax_paid=.0;A.tax_refunded=B-A.tax_due
			else:A.tax_paid=A.tax_due-B;A.tax_refunded=.0
		for A in C.schedule2_ids:
			B=A.pres_tax_withheld+A.prev_tax_withheld+A.pera_tax_credit
			if B>A.tax_due:A.tax_paid=.0;A.tax_refunded=B-A.tax_due
			else:A.tax_paid=A.tax_due-B;A.tax_refunded=.0
	def gen_files(B):
		for A in B:E=B.create_csv1(A.schedule1_ids,with_header=True);A.sch1_data=B.list_to_csv(E);F=B.create_csv2(A.schedule2_ids,with_header=True);A.sch2_data=B.list_to_csv(F);G=B.company_vat and B.company_vat.replace('-','')or'';C,D=format_tin(G);A.sch1_filename='%s%s1231%s1604C.DAT'%(C,D,A.year);A.sch2_filename='%s%s1231%s1604C.DAT'%(C,D,A.year);A.sch_combined_data=B.list_to_csv(E+F[1:]);A.sch_combined_filename='%s%s1231%s1604C.DAT'%(C,D,A.year);A.bir1604c1_data=B.create_1604C1_xls(A);A.bir1604c1_filename='1604C-1.xlsx';A.bir1604c2_data=B.create_1604C2_xls(A);A.bir1604c2_filename='1604C-2.xlsx'
	@api.model
	def create_1604C1_xls(self,r):
		def I(ri,r_source=False,format=False):
			C=ri;B=r_source
			if not B:B=C
			for A in range(F.ncols):
				D=F.cell_type(B,A)
				if D in(1,2,3,4):
					if 1:
						if format:E.write_string(C,A,F.cell_value(B,A),format)
						else:E.write_string(C,A,F.cell_value(B,A))
					elif format:E.write(C,A,F.cell_value(B,A),format)
					else:E.write(C,A,F.cell_value(B,A))
		def C(ri,ci,value,cell_format,with_zero=False):
			B=cell_format;A=value
			if A or with_zero:
				if B:E.write(ri,ci,A,B)
				else:E.write(ri,ci,A)
		S=os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())));P=os.path.join(S,'template/1604c-2022-1.xls');_logger.debug('1604c-1: file: %s',P);T=xlrd.open_workbook(P);F=T.sheet_by_index(0);K=BytesIO()
		if 1:H=xlsxwriter.Workbook(K,{'in_memory':True});H.set_calc_mode('auto');E=H.add_worksheet();E.set_column(0,F.ncols,25)
		else:
			H=xlwt.Workbook();E=H.add_sheet('Schedule 1')
			for G in range(F.ncols):E.col(G).width=8294
		U=self.company_vat and self.company_vat.replace('-','')or'';V,W=format_tin2(U);I(0);I(1);E.write(2,0,'AS OF DECEMBER 31, %s'%r.year);E.write(4,0,'TIN : %s-%s'%(V,W));E.write(6,0,"WITHHOLDING AGENT'S NAME: %s"%r.company_name)
		for X in range(7,16):I(X)
		M=1
		if 1:J=H.add_format({'num_format':'m/d/yyyy'});D=H.add_format({'num_format':'#,##0.00'})
		else:J=xlwt.XFStyle();J.num_format_str='mm/dd/yyyy';D=xlwt.XFStyle();D.num_format_str='#,##0.00'
		L=0;N=datetime.date(year=int(r.year),month=1,day=1);O=datetime.date(year=int(r.year),month=12,day=31)
		for B in r.schedule1_ids:
			A=M+15;L+=1;Y=format_name(B.employee_id.last_name);Z=format_name(B.employee_id.first_name);a=format_name(B.employee_id.middle_name)
			if B.hired:Q=min(max(N,fields.Date.from_string(B.hired)),O)
			else:Q=N
			if B.date_end:R=max(min(fields.Date.from_string(B.date_end),O),N)
			else:R=O
			E.write(A,0,M);E.write(A,1,'%s, %s %s'%(Y,Z,a));C(A,2,B.nationality,False);C(A,3,B.employment_status,False);C(A,4,Q,J);C(A,5,R,J);C(A,6,B.separation_reason,False);C(A,7,B.pres_gross_income,D,with_zero=True);C(A,8,B.pres_nt_13mp,D);C(A,9,B.pres_nt_deminimis,D);C(A,10,B.pres_nt_govded,D);C(A,11,B.pres_nt_others+B.pres_nt_income,D);C(A,12,B.pres_nt_total,D,with_zero=True);C(A,13,B.pres_t_income,D);C(A,14,B.pres_t_13mp,D);C(A,15,B.pres_t_others,D);C(A,16,B.pres_t_total,D,with_zero=True);b=B.tin_no and B.tin_no.replace('-','')or'';c,d=format_tin2(b);C(A,17,'%s-%s'%(c,d),False);C(A,18,B.previous_employer_employment_status,False);C(A,19,B.previous_employer_hired,J);C(A,20,B.previous_employer_date_end,J);C(A,21,B.previous_employer_separation_reason,False);C(A,22,B.prev_gross_income,D);C(A,23,B.prev_nt_13mp,D);C(A,24,B.prev_nt_deminimis,D);C(A,25,B.prev_nt_govded,D);C(A,26,B.prev_nt_income+B.prev_nt_others,D);C(A,27,B.prev_nt_total,D);C(A,28,B.prev_t_income,D);C(A,29,B.prev_t_13mp,D);C(A,30,B.prev_t_others,D);C(A,31,B.prev_t_total,D);C(A,32,B.net_taxable_income,D,with_zero=True);C(A,33,B.tax_due,D,with_zero=True);C(A,34,B.prev_tax_withheld,D);C(A,35,B.pres_tax_withheld,D);C(A,36,B.pera_tax_credit,D);C(A,37,B.tax_paid,D);C(A,38,B.tax_refunded,D);C(A,39,B.tax_withheld,D,with_zero=True);C(A,40,B.substituted_filing and'Yes'or'No',False);M+=1
		if L:
			A+=1;I(A,17);I(A+2,19);I(A+3,20);C(A+1,0,'Grand Total :',False)
			for G in range(7,F.ncols):
				e=F.cell_value(17,G)
				if e:
					if 1:E.write_formula(A+1,G,'=SUM(%s:%s)'%(cell_name(17,G+1),cell_name(L+16,G+1)),D)
					else:E.write(A+1,G,xlwt.Formula('SUM(%s:%s)'%(cell_name(17,G+1),cell_name(L+16,G+1))),D)
		if 1:H.close();K.seek(0)
		else:H.save(K)
		f=base64.b64encode(K.getvalue());return f
	@api.model
	def create_1604C2_xls(self,r):
		def J(ri,r_source=False,format=False):
			C=ri;B=r_source
			if not B:B=C
			for A in range(F.ncols):
				D=F.cell_type(B,A)
				if D in(1,2,3,4):
					if 1:
						if format:E.write_string(C,A,F.cell_value(B,A),format)
						else:E.write_string(C,A,F.cell_value(B,A))
					elif format:E.write(C,A,F.cell_value(B,A),format)
					else:E.write(C,A,F.cell_value(B,A))
		def C(ri,ci,value,cell_format,with_zero=False):
			B=cell_format;A=value
			if A or with_zero:
				if B:E.write(ri,ci,A,B)
				else:E.write(ri,ci,A)
		S=os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())));P=os.path.join(S,'template/1604c-2022-2.xls');_logger.debug('1604c-2: file: %s',P);T=xlrd.open_workbook(P);F=T.sheet_by_index(0);K=BytesIO()
		if 1:H=xlsxwriter.Workbook(K,{'in_memory':True});H.set_calc_mode('auto');E=H.add_worksheet();E.set_column(0,F.ncols,25)
		else:
			H=xlwt.Workbook();E=H.add_sheet('Schedule 2')
			for G in range(F.ncols):E.col(G).width=8294
		U=self.company_vat and self.company_vat.replace('-','')or'';V,W=format_tin2(U);J(0);J(1);E.write(2,0,'AS OF DECEMBER 31, %s'%r.year);E.write(4,0,'TIN : %s-%s'%(V,W));E.write(6,0,"WITHHOLDING AGENT'S NAME: %s"%r.company_name)
		for X in range(7,16):J(X)
		M=1
		if 1:I=H.add_format({'num_format':'m/d/yyyy'});D=H.add_format({'num_format':'#,##0.00'})
		else:I=xlwt.XFStyle();I.num_format_str='mm/dd/yyyy';D=xlwt.XFStyle();D.num_format_str='#,##0.00'
		L=0;N=datetime.date(year=int(r.year),month=1,day=1);O=datetime.date(year=int(r.year),month=12,day=31)
		for B in r.schedule2_ids:
			A=M+15;L+=1;Y=format_name(B.employee_id.last_name);Z=format_name(B.employee_id.first_name);a=format_name(B.employee_id.middle_name)
			if B.hired:Q=min(max(N,fields.Date.from_string(B.hired)),O)
			else:Q=N
			if B.date_end:R=max(min(fields.Date.from_string(B.date_end),O),N)
			else:R=O
			E.write(A,0,M);E.write(A,1,'%s, %s %s'%(Y,Z,a));C(A,2,B.employment_status,False);C(A,3,r.region,False);C(A,4,Q,I);C(A,5,R,I);C(A,6,B.separation_reason,False);C(A,7,B.pres_gross_income,D,with_zero=True);C(A,8,B.mwe_daily_amount,D);C(A,9,B.mwe_monthly_amount,D);C(A,10,B.mwe_yearly_amount,D);C(A,11,B.mwe_days_in_year,False);C(A,12,B.pres_nt_basic,D);C(A,13,B.pres_nt_holiday,D);C(A,14,B.pres_nt_overtime,D);C(A,15,B.pres_nt_night_diff,D);C(A,16,B.pres_nt_hazard,D);C(A,17,B.pres_nt_13mp,D);C(A,18,B.pres_nt_deminimis,D);C(A,19,B.pres_nt_govded,D);C(A,20,B.pres_nt_others,D);C(A,21,B.pres_nt_total,D);C(A,22,B.pres_t_13mp,D);C(A,23,B.pres_t_others,D);C(A,24,B.pres_t_total,D);b=B.tin_no and B.tin_no.replace('-','')or'';c,d=format_tin2(b);C(A,25,'%s-%s'%(c,d),False);C(A,26,B.previous_employer_employment_status,False);C(A,27,B.previous_employer_hired,I);C(A,28,B.previous_employer_date_end,I);C(A,29,B.previous_employer_separation_reason,False);C(A,30,B.prev_gross_income,D);C(A,31,B.prev_nt_basic,D);C(A,32,B.prev_nt_holiday,D);C(A,33,B.prev_nt_overtime,D);C(A,34,B.prev_nt_night_diff,D);C(A,35,B.prev_nt_hazard,D);C(A,36,B.prev_nt_13mp,D);C(A,37,B.prev_nt_deminimis,D);C(A,38,B.prev_nt_govded,D);C(A,39,B.prev_nt_others,D);C(A,40,B.prev_nt_total,D);C(A,41,B.prev_t_13mp,D);C(A,42,B.prev_t_others,D);C(A,43,B.prev_t_total,D);C(A,44,B.net_taxable_income,D,with_zero=True);C(A,45,B.tax_due,D,with_zero=True);C(A,46,B.prev_tax_withheld,D);C(A,47,B.pres_tax_withheld,D);C(A,48,B.pera_tax_credit,D);C(A,49,B.tax_paid,D);C(A,50,B.tax_refunded,D);C(A,51,B.tax_withheld,D,with_zero=True);C(A,52,B.substituted_filing and'Yes'or'No',False);M+=1
		if L:
			A+=1;J(A,17);J(A+2,19);C(A+1,0,'Grand Total :',False)
			for G in range(7,F.ncols):
				e=F.cell_value(17,G)
				if e:
					if 1:E.write_formula(A+1,G,'=SUM(%s:%s)'%(cell_name(17,G+1),cell_name(L+16,G+1)),D)
					else:E.write(A+1,G,xlwt.Formula('SUM(%s:%s)'%(cell_name(17,G+1),cell_name(L+16,G+1))),D)
		if 1:H.close();K.seek(0)
		else:H.save(K)
		f=base64.b64encode(K.getvalue());return f
	def list_to_csv(E,data):
		A=StringIO();B=csv.writer(A,delimiter=',',lineterminator='\r\n',quoting=csv.QUOTE_MINIMAL)
		for C in data:B.writerow(C)
		D=base64.b64encode(A.getvalue().encode());return D
	@api.model
	def create_csv1(self,schedule1_ids,with_header=True):
		E=[];D=self;s=D.company_vat and D.company_vat.replace('-','')or'';F,G=format_tin(s);H='12/31/%s'%D.year
		if with_header:E.append(['H1604C',F,G,H])
		I=.0;I=.0;L=.0;M=.0;N=.0;O=.0;P=.0;Q=.0;R=.0;S=.0;T=.0;U=.0;V=.0;W=.0;X=.0;Y=.0;Z=.0;a=.0;b=.0;c=.0;d=.0;e=.0;f=.0;g=.0;h=.0;i=.0;j=.0;k=.0;l=.0;m=.0;n=.0;o=.0;p=1;J=datetime.date(year=int(D.year),month=1,day=1);K=datetime.date(year=int(D.year),month=12,day=31)
		for A in schedule1_ids:
			B=['D1','1604C'];B.append(F);B.append(G);B.append(H);B.append(p);t=A.tin_no and A.tin_no.replace('-','')or'';u,v=format_tin(t);B.append(u);B.append(v);B.append(format_name(A.employee_id.last_name));B.append(format_name(A.employee_id.first_name));B.append(format_name(A.employee_id.middle_name));B.append(A.alphalist_id.region);B.append(A.prev_gross_income);B.append(A.prev_nt_income);B.append(A.prev_nt_13mp);B.append(A.prev_nt_deminimis);B.append(A.prev_nt_govded);B.append(A.prev_nt_others);B.append(A.prev_nt_total);I+=A.prev_gross_income;L+=A.prev_nt_income;M+=A.prev_nt_13mp;N+=A.prev_nt_deminimis;O+=A.prev_nt_govded;P+=A.prev_nt_others;Q+=A.prev_nt_total;B.append(A.prev_t_income);B.append(A.prev_t_13mp);B.append(A.prev_t_others);B.append(A.prev_t_total);R+=A.prev_t_income;S+=A.prev_t_13mp;T+=A.prev_t_others;U+=A.prev_t_total
			if A.hired:q=min(max(J,fields.Date.from_string(A.hired)),K)
			else:q=J
			if A.date_end:r=max(min(fields.Date.from_string(A.date_end),K),J)
			else:r=K
			w=fields.Date.from_string(q);x=fields.Date.from_string(r);B.append(w.strftime('%m/%d/%Y'));B.append(x.strftime('%m/%d/%Y'));B.append(A.pres_gross_income);B.append(A.pres_nt_income);B.append(A.pres_nt_13mp);B.append(A.pres_nt_deminimis);B.append(A.pres_nt_govded);B.append(A.pres_nt_others);B.append(A.pres_nt_total);V+=A.pres_gross_income;W+=A.pres_nt_income;X+=A.pres_nt_13mp;Y+=A.pres_nt_deminimis;Z+=A.pres_nt_govded;a+=A.pres_nt_others;b+=A.pres_nt_total;B.append(A.pres_t_income);B.append(A.pres_t_13mp);B.append(A.pres_t_others);B.append(A.pres_t_total);c+=A.pres_t_income;d+=A.pres_t_13mp;e+=A.pres_t_others;f+=A.pres_t_total;B.append(A.taxable_total);B.append(A.net_taxable_income);B.append(A.tax_due);g+=A.taxable_total;h+=A.net_taxable_income;i+=A.tax_due;B.append(A.prev_tax_withheld);B.append(A.pres_tax_withheld);B.append(A.tax_paid);B.append(A.tax_refunded);B.append(A.tax_withheld);j+=A.prev_tax_withheld;k+=A.pres_tax_withheld;l+=A.tax_paid;m+=A.tax_refunded;n+=A.tax_withheld;B.append(A.nationality or'FILIPINO');B.append(A.employment_status or'R')
			if A.alphalist_id.year>='2024':B.append(A.separation_reason or'NA');B.append(A.substituted_filing and'Y'or'N');B.append(A.pera_tax_credit);o+=A.pera_tax_credit
			else:B.append(A.separation_reason or'')
			p+=1;parse_float(B);E.append(B)
		C=['C1','1604C'];C.append(F);C.append(G);C.append(H);C.append(I);C.append(L);C.append(M);C.append(N);C.append(O);C.append(P);C.append(Q);C.append(R);C.append(S);C.append(T);C.append(U);C.append(V);C.append(W);C.append(X);C.append(Y);C.append(Z);C.append(a);C.append(b);C.append(c);C.append(d);C.append(e);C.append(f);C.append(g);C.append(h);C.append(i);C.append(j);C.append(k);C.append(l);C.append(m);C.append(n)
		if D.year>='2024':C.append(o)
		parse_float(C);E.append(C);return E
	@api.model
	def create_csv2(self,schedule2_ids,with_header=True):
		E=[];D=self;A2=D.company_vat and D.company_vat.replace('-','')or'';F,G=format_tin(A2);H='12/31/%s'%D.year
		if with_header:E.append(['H1604C',F,G,H])
		K=.0;L=.0;M=.0;N=.0;O=.0;P=.0;Q=.0;R=.0;S=.0;T=.0;U=.0;V=.0;W=.0;X=.0;Y=.0;Z=.0;a=.0;b=.0;A3=.0;c=.0;d=.0;e=.0;f=.0;g=.0;h=.0;i=.0;j=.0;k=.0;l=.0;m=.0;n=.0;o=.0;p=.0;q=.0;r=.0;s=.0;t=.0;u=.0;v=.0;w=.0;x=.0;y=1;I=datetime.date(year=int(D.year),month=1,day=1);J=datetime.date(year=int(D.year),month=12,day=31)
		for A in schedule2_ids:
			B=['D2','1604C'];B.append(F);B.append(G);B.append(H);B.append(y);A4=A.tin_no and A.tin_no.replace('-','')or'';A5,A6=format_tin(A4);B.append(A5);B.append(A6);B.append(format_name(A.employee_id.last_name));B.append(format_name(A.employee_id.first_name));B.append(format_name(A.employee_id.middle_name));B.append(A.alphalist_id.region);B.append(A.prev_gross_income);B.append(A.prev_nt_basic);B.append(A.prev_nt_holiday);B.append(A.prev_nt_overtime);B.append(A.prev_nt_night_diff);B.append(A.prev_nt_hazard);B.append(A.prev_nt_13mp);B.append(A.prev_nt_deminimis);B.append(A.prev_nt_govded);B.append(A.prev_nt_others);B.append(A.prev_nt_total);K+=A.prev_gross_income;L+=A.prev_nt_basic;M+=A.prev_nt_holiday;N+=A.prev_nt_overtime;O+=A.prev_nt_night_diff;P+=A.prev_nt_hazard;Q+=A.prev_nt_13mp;R+=A.prev_nt_deminimis;S+=A.prev_nt_govded;T+=A.prev_nt_others;U+=A.prev_nt_total;B.append(A.prev_t_13mp);B.append(A.prev_t_others);B.append(A.prev_t_total);V+=A.prev_t_13mp;W+=A.prev_t_others;X+=A.prev_t_total
			if A.hired:z=min(max(I,fields.Date.from_string(A.hired)),J)
			else:z=I
			if A.date_end:A0=max(min(fields.Date.from_string(A.date_end),J),I)
			else:A0=J
			A7=fields.Date.from_string(z);A8=fields.Date.from_string(A0);B.append(A7.strftime('%m/%d/%Y'));B.append(A8.strftime('%m/%d/%Y'));B.append(A.pres_gross_income);B.append(A.mwe_daily_amount);B.append(A.mwe_monthly_amount);B.append(A.mwe_yearly_amount);B.append(A.mwe_days_in_year);Z+=A.mwe_daily_amount;a+=A.mwe_monthly_amount;b+=A.mwe_yearly_amount;B.append(A.pres_nt_holiday);B.append(A.pres_nt_overtime);B.append(A.pres_nt_night_diff);B.append(A.pres_nt_hazard);B.append(A.pres_nt_13mp);B.append(A.pres_nt_deminimis);B.append(A.pres_nt_govded);B.append(A.pres_nt_others);B.append(A.pres_nt_total);Y+=A.pres_gross_income;A3+=A.pres_nt_basic;c+=A.pres_nt_holiday;d+=A.pres_nt_overtime;e+=A.pres_nt_night_diff;f+=A.pres_nt_hazard;g+=A.pres_nt_13mp;h+=A.pres_nt_deminimis;i+=A.pres_nt_govded;j+=A.pres_nt_others;k+=A.pres_nt_total;B.append(A.pres_t_13mp);B.append(A.pres_t_others);B.append(A.pres_t_total);l+=A.pres_t_13mp;m+=A.pres_t_others;n+=A.pres_t_total;B.append(A.taxable_total);B.append(A.net_taxable_income);B.append(A.tax_due);o+=A.taxable_total;p+=A.net_taxable_income;q+=A.tax_due;B.append(A.prev_tax_withheld);B.append(A.pres_tax_withheld);B.append(A.tax_paid);B.append(A.tax_refunded);B.append(A.tax_withheld);r+=A.prev_tax_withheld;s+=A.pres_tax_withheld;t+=A.tax_paid;u+=A.tax_refunded;v+=A.tax_withheld;B.append(A.nationality or'FILIPINO');B.append(A.employment_status or'R')
			if A.alphalist_id.year>='2024':B.append(A.separation_reason or'NA');B.append(A.substituted_filing and'Y'or'N');B.append(A.pera_tax_credit);A1=A.pres_nt_basic+A.prev_nt_basic;B.append(A1);x+=A1;w+=A.pera_tax_credit
			else:B.append(A.separation_reason or'')
			y+=1;parse_float(B);E.append(B)
		C=['C2','1604C'];C.append(F);C.append(G);C.append(H);C.append(K);C.append(L);C.append(M);C.append(N);C.append(O);C.append(P);C.append(Q);C.append(R);C.append(S);C.append(T);C.append(U);C.append(V);C.append(W);C.append(X);C.append(Y);C.append(Z);C.append(a);C.append(b);C.append(c);C.append(d);C.append(e);C.append(f);C.append(g);C.append(h);C.append(i);C.append(j);C.append(k);C.append(l);C.append(m);C.append(n);C.append(o);C.append(p);C.append(q);C.append(r);C.append(s);C.append(t);C.append(u);C.append(v)
		if D.year>='2024':C.append(w);C.append(x)
		parse_float(C);E.append(C);return E
class AlphaListSchedule1(models.Model):
	_name='ez.bir.alphalist.schedule1';_description='Alphalist Schedule 1';_order='employee_name';alphalist_id=fields.Many2one('ez.bir.alphalist','Alphalist',ondelete='cascade');employee_id=fields.Many2one('hr.employee','Employee',ondelete='restrict',readonly=False);employee_name=fields.Char('Name',related='employee_id.name',store=True,readonly=True);tin_no=fields.Char('TIN');hired=fields.Date('From');date_end=fields.Date('To');tax_code=fields.Char(readonly=True);nationality=fields.Char();employment_status=fields.Selection(list_employment_status,'Employment Status');separation_reason=fields.Selection(list_separation_reason,'Reason of Separation');is_main_employer=fields.Boolean('Main Employer',default='True');substituted_filing=fields.Boolean('Subst. Filing',default=True);url_2316=fields.Char('Form 2316',compute='_get_url2316');previous_employer=fields.Char('Prev Employer');previous_employer_address=fields.Char('Prev Employer Address');previous_employer_zip=fields.Char('Prev Employer ZIP');previous_employer_tin=fields.Char('Prev Employer TIN');previous_employer_hired=fields.Date('Prev From');previous_employer_date_end=fields.Date('Prev To');previous_employer_employment_status=fields.Selection(list_employment_status,'Prev Employment Status');previous_employer_separation_reason=fields.Selection(list_separation_reason,'Prev Reason of Separation');prev_gross_income=fields.Float('Prev Gross Income',digits=(0,2),store=True,compute='_get_prev_gross_income');prev_nt_income=fields.Float('Prev NT Income',digits=(0,2));prev_nt_13mp=fields.Float('Prev NT 13-MP',digits=(0,2));prev_nt_deminimis=fields.Float('Prev NT Deminimis',digits=(0,2));prev_nt_govded=fields.Float('Prev NT Gov Deductions',digits=(0,2));prev_nt_others=fields.Float('Prev NT Other Salaries',digits=(0,2));prev_nt_total=fields.Float('Prev NT Total',digits=(0,2),store=True,compute='_get_prev_nt_total');pres_gross_income=fields.Float('Pres Gross Income',digits=(0,2),store=True,compute='_get_pres_gross_income');pres_nt_income=fields.Float('Pres NT Income',digits=(0,2));pres_nt_13mp=fields.Float('Pres NT 13-MP',digits=(0,2));pres_nt_deminimis=fields.Float('Pres NT Deminimis',digits=(0,2));pres_nt_govded=fields.Float('Pres NT Gov Deductions',digits=(0,2));pres_nt_others=fields.Float('Pres NT Others',digits=(0,2));pres_nt_total=fields.Float('Pres NT Total',digits=(0,2),store=True,compute='_get_pres_nt_total');prev_t_income=fields.Float('Prev T.Income',digits=(0,2));prev_t_13mp=fields.Float('Prev T.13-MP',digits=(0,2));prev_t_others=fields.Float('Prev T.Others',digits=(0,2));prev_t_total=fields.Float('Prev T.Total',digits=(0,2),store=True,compute='_get_taxable_total');pres_t_income=fields.Float('Pres T.Income',digits=(0,2));pres_t_13mp=fields.Float('Pres T.13-MP',digits=(0,2));pres_t_others=fields.Float('Pres T.Others',digits=(0,2));pres_t_total=fields.Float('Pres T.Total',digits=(0,2),store=True,compute='_get_taxable_total');pres_t_others_text=fields.Char('Other Salary Text',default='Leaves/Night Diff./Adj.');taxable_total=fields.Float('Taxable Total',digits=(0,2),store=True,compute='_get_taxable_total');net_taxable_income=fields.Float(digits=(0,2),store=True,compute='_get_taxable_total');tax_due=fields.Float(digits=(0,2),store=True,compute='_get_taxable_total');prev_tax_withheld=fields.Float('Prev Tax Withheld',digits=(0,2));pres_tax_withheld=fields.Float('Pres Tax Withheld',digits=(0,2));pera_tax_credit=fields.Float('PERA 5% Credit',digits=(0,2));tax_paid=fields.Float('Tax Paid (Dec.)',digits=(0,2));tax_refunded=fields.Float('Tax Refunded',digits=(0,2));tax_withheld=fields.Float('Adj. Tax Withheld',digits=(0,2),compute_sudo=True,store=True,compute='_get_tax_withheld');notice=fields.Char('Notice',compute_sudo=True,store=True,compute='_get_tax_withheld');state=fields.Selection(related='alphalist_id.state')
	@api.depends('employee_id','employee_id.name')
	def _compute_display_name(self):
		for A in self:A.display_name=A.employee_id.name
	def _get_url2316(A):
		C=A.env['ir.config_parameter'].sudo().get_param('web.base.url')
		for B in A.sudo():B.url_2316='%s/bir2316-sched1/%s'%(C,B.id)
	def compute_single_pdf(A):A.ensure_one();B='/bir2316-sched1/%s'%A.id;return{'name':'Form 2316','res_model':'ir.actions.act_url','type':'ir.actions.act_url','target':'self','url':B}
	def swap_income_lte250K(C):
		for A in C:
			D=A.prev_t_income+A.pres_t_income+A.prev_nt_income+A.pres_nt_income+A.prev_t_others+A.pres_t_others+A.prev_nt_others+A.pres_nt_others;B=False
			if D>25e4:B=True
			if not B:A.pres_nt_income=A.pres_nt_income+A.pres_t_income;A.prev_nt_income=A.prev_nt_income+A.prev_t_income;A.pres_t_income=.0;A.prev_t_income=.0;A.pres_nt_others=A.pres_nt_others+A.pres_t_others;A.prev_nt_others=A.prev_nt_others+A.prev_t_others;A.pres_t_others=.0;A.prev_t_others=.0
			else:A.pres_t_income=A.pres_nt_income+A.pres_t_income;A.prev_t_income=A.prev_nt_income+A.prev_t_income;A.pres_nt_income=.0;A.prev_nt_income=.0;A.pres_t_others=A.pres_nt_others+A.pres_t_others;A.prev_t_others=A.prev_nt_others+A.prev_t_others;A.pres_nt_others=.0;A.prev_nt_others=.0
	@api.depends('prev_tax_withheld','pres_tax_withheld','tax_paid','tax_refunded','tax_due','pera_tax_credit')
	def _get_tax_withheld(self):
		for A in self:
			A.tax_withheld=A.prev_tax_withheld+A.pres_tax_withheld+A.tax_paid-A.tax_refunded
			if abs(A.tax_due-A.tax_withheld)>.001:A.notice='WARNING! Tax due is not equal to tax withheld.'
			else:A.notice=False
	@api.depends('prev_nt_total','prev_t_total')
	def _get_prev_gross_income(self):
		for A in self:A.prev_gross_income=A.prev_nt_total+A.prev_t_total
	@api.depends('pres_nt_total','pres_t_total')
	def _get_pres_gross_income(self):
		for A in self:A.pres_gross_income=A.pres_nt_total+A.pres_t_total
	@api.depends('pres_t_income','pres_t_13mp','pres_t_others','prev_t_income','prev_t_13mp','prev_t_others')
	def _get_taxable_total(self):
		for A in self:A.prev_t_total=A.prev_t_income+A.prev_t_13mp+A.prev_t_others;A.pres_t_total=A.pres_t_income+A.pres_t_13mp+A.pres_t_others;A.taxable_total=A.prev_t_total+A.pres_t_total;A.net_taxable_income=A.taxable_total;A.tax_due=compute_income_tax(A.taxable_total,year=A.alphalist_id.year)
	@api.depends('prev_nt_income','prev_nt_13mp','prev_nt_deminimis','prev_nt_govded','prev_nt_others')
	def _get_prev_nt_total(self):
		for A in self:A.prev_nt_total=A.prev_nt_income+A.prev_nt_13mp+A.prev_nt_deminimis+A.prev_nt_govded+A.prev_nt_others
	@api.depends('pres_nt_income','pres_nt_13mp','pres_nt_deminimis','pres_nt_govded','pres_nt_others')
	def _get_pres_nt_total(self):
		for A in self:A.pres_nt_total=A.pres_nt_income+A.pres_nt_13mp+A.pres_nt_deminimis+A.pres_nt_govded+A.pres_nt_others
	def action_calc_wtax(C):
		for A in C:
			B=A.pres_tax_withheld+A.prev_tax_withheld+A.pera_tax_credit
			if B>A.tax_due:A.tax_paid=.0;A.tax_refunded=B-A.tax_due
			else:A.tax_paid=A.tax_due-B;A.tax_refunded=.0
class AlphaListSchedule2_MWE(models.Model):
	_name='ez.bir.alphalist.schedule2';_description='Alphalist Schedule 2 (MWE)';_order='employee_name';alphalist_id=fields.Many2one('ez.bir.alphalist','Alphalist',ondelete='cascade');employee_id=fields.Many2one('hr.employee','Employee',ondelete='restrict',readonly=False);employee_name=fields.Char('Name',related='employee_id.name',store=True,readonly=True);tin_no=fields.Char('TIN');hired=fields.Date('From');date_end=fields.Date('To');tax_code=fields.Char(readonly=True);nationality=fields.Char();employment_status=fields.Selection(list_employment_status,'Employment Status');separation_reason=fields.Selection(list_separation_reason,'Reason of Separation');is_main_employer=fields.Boolean('Main Employer',default='True');substituted_filing=fields.Boolean('Subst. Filing',default=True);previous_employer=fields.Char('Prev Employer');previous_employer_address=fields.Char('Prev Employer Address');previous_employer_zip=fields.Char('Prev Employer ZIP');previous_employer_tin=fields.Char('Prev Employer TIN');previous_employer_hired=fields.Date('Prev From');previous_employer_date_end=fields.Date('Prev To');previous_employer_employment_status=fields.Selection(list_employment_status,'Prev Employment Status');previous_employer_separation_reason=fields.Selection(list_separation_reason,'Prev Reason of Separation');url_2316=fields.Char('Form 2316',compute='_get_url2316');mwe_daily_amount=fields.Float(related='alphalist_id.mwe_daily_amount');mwe_monthly_amount=fields.Float(related='alphalist_id.mwe_monthly_amount');mwe_yearly_amount=fields.Float(related='alphalist_id.mwe_yearly_amount');mwe_days_in_year=fields.Integer(related='alphalist_id.mwe_days_in_year');prev_gross_income=fields.Float('Prev Gross Income',digits=(0,2),store=True,compute='_get_prev_gross_income');prev_nt_basic=fields.Float('Prev NT Basic Min Wage',digits=(0,2));prev_nt_holiday=fields.Float('Prev NT Holiday Pay',digits=(0,2));prev_nt_overtime=fields.Float('Prev NT Overtime Pay',digits=(0,2));prev_nt_night_diff=fields.Float('Prev NT Night Diff',digits=(0,2));prev_nt_hazard=fields.Float('Prev NT Hazard Pay',digits=(0,2));prev_nt_13mp=fields.Float('Prev NT 13-MP',digits=(0,2));prev_nt_deminimis=fields.Float('Prev NT Deminimis',digits=(0,2));prev_nt_govded=fields.Float('Prev NT Gov Deductions',digits=(0,2));prev_nt_others=fields.Float('Prev NT Others',digits=(0,2));prev_nt_total=fields.Float('Prev NT Income',digits=(0,2),store=True,compute='_get_prev_nt_total');pres_gross_income=fields.Float('Pres Gross Income',digits=(0,2),store=True,compute='_get_pres_gross_income');pres_nt_basic=fields.Float('Pres NT Basic Min Wage',digits=(0,2));pres_nt_holiday=fields.Float('Pres NT Holiday Pay',digits=(0,2));pres_nt_overtime=fields.Float('Pres NT Overtime Pay',digits=(0,2));pres_nt_night_diff=fields.Float('Pres NT Night Diff',digits=(0,2));pres_nt_hazard=fields.Float('Pres NT Hazard Pay',digits=(0,2));pres_nt_13mp=fields.Float('Pres NT 13-MP',digits=(0,2));pres_nt_deminimis=fields.Float('Pres NT Deminimis',digits=(0,2));pres_nt_govded=fields.Float('Pres NT Gov Deductions',digits=(0,2));pres_nt_others=fields.Float('Pres NT Others',digits=(0,2));pres_nt_total=fields.Float('Pres NT Income',digits=(0,2),store=True,compute='_get_pres_nt_total');prev_t_13mp=fields.Float('Prev T.13-MP',digits=(0,2));prev_t_others=fields.Float('Prev T.Others',digits=(0,2));prev_t_total=fields.Float('Prev T.Total',digits=(0,2),store=True,compute='_get_taxable_total');pres_t_13mp=fields.Float('Pres T.13-MP',digits=(0,2));pres_t_others=fields.Float('Pres T.Others',digits=(0,2));pres_t_total=fields.Float('Pres T.Total',digits=(0,2),store=True,compute='_get_taxable_total');taxable_total=fields.Float('Taxable Total',digits=(0,2),store=True,compute='_get_taxable_total');net_taxable_income=fields.Float(digits=(0,2),store=True,compute='_get_taxable_total');tax_due=fields.Float(digits=(0,2),store=True,compute='_get_taxable_total');prev_tax_withheld=fields.Float('Prev Tax Withheld',digits=(0,2));pres_tax_withheld=fields.Float('Pres Tax Withheld',digits=(0,2));pera_tax_credit=fields.Float('PERA 5% Credit',digits=(0,2));tax_paid=fields.Float('Tax Paid (Dec.)',digits=(0,2));tax_refunded=fields.Float('Tax Refunded',digits=(0,2));tax_withheld=fields.Float('Adj. Tax Withheld',digits=(0,2),compute_sudo=True,store=True,compute='_get_tax_withheld');notice=fields.Char('Notice',compute_sudo=True,store=True,compute='_get_tax_withheld');state=fields.Selection(related='alphalist_id.state')
	@api.depends('employee_id','employee_id.name')
	def _compute_display_name(self):
		for A in self:A.display_name=A.employee_id.name
	def _get_url2316(A):
		C=A.env['ir.config_parameter'].sudo().get_param('web.base.url')
		for B in A.sudo():B.url_2316='%s/bir2316-sched2/%s'%(C,B.id)
	def compute_single_pdf(A):A.ensure_one();B='/bir2316-sched2/%s'%A.id;return{'name':'Form 2316','res_model':'ir.actions.act_url','type':'ir.actions.act_url','target':'self','url':B}
	@api.depends('prev_tax_withheld','pres_tax_withheld','tax_paid','tax_refunded','tax_due','pera_tax_credit')
	def _get_tax_withheld(self):
		for A in self:
			A.tax_withheld=A.prev_tax_withheld+A.pres_tax_withheld+A.tax_paid-A.tax_refunded
			if abs(A.tax_due-A.tax_withheld)>.001:A.notice='WARNING! Tax due is not equal to tax withheld.'
			else:A.notice=False
	@api.depends('pres_t_others','pres_t_13mp','prev_t_others','prev_t_13mp')
	def _get_taxable_total(self):
		for A in self:A.prev_t_total=A.prev_t_others+A.prev_t_13mp;A.pres_t_total=A.pres_t_others+A.pres_t_13mp;A.taxable_total=A.prev_t_total+A.pres_t_total;A.net_taxable_income=A.taxable_total;A.tax_due=compute_income_tax(A.taxable_total,year=A.alphalist_id.year)
	@api.depends('prev_nt_total','prev_t_total')
	def _get_prev_gross_income(self):
		for A in self:A.prev_gross_income=A.prev_nt_total+A.prev_t_total
	@api.depends('pres_nt_total','pres_t_total')
	def _get_pres_gross_income(self):
		for A in self:A.pres_gross_income=A.pres_nt_total+A.pres_t_total
	@api.depends('prev_nt_basic','prev_nt_holiday','prev_nt_overtime','prev_nt_night_diff','prev_nt_hazard','prev_nt_13mp','prev_nt_deminimis','prev_nt_govded','prev_nt_others')
	def _get_prev_nt_total(self):
		for A in self:A.prev_nt_total=A.prev_nt_basic+A.prev_nt_holiday+A.prev_nt_overtime+A.prev_nt_night_diff+A.prev_nt_hazard+A.prev_nt_13mp+A.prev_nt_deminimis+A.prev_nt_govded+A.prev_nt_others
	@api.depends('pres_nt_basic','pres_nt_holiday','pres_nt_overtime','pres_nt_night_diff','pres_nt_hazard','pres_nt_13mp','pres_nt_deminimis','pres_nt_govded','pres_nt_others')
	def _get_pres_nt_total(self):
		for A in self:A.pres_nt_total=A.pres_nt_basic+A.pres_nt_holiday+A.pres_nt_overtime+A.pres_nt_night_diff+A.pres_nt_hazard+A.pres_nt_13mp+A.pres_nt_deminimis+A.pres_nt_govded+A.pres_nt_others