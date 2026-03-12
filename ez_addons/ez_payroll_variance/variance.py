from odoo import models,fields,api,tools,_
from odoo.exceptions import ValidationError
import xlsxwriter
from dateutil.relativedelta import relativedelta
import base64
from io import BytesIO
import logging
_logger=logging.getLogger(__name__)
class VarianceWizard(models.TransientModel):
	_name='hr.ph.pay.variance.wizard';_description='Pay Variance Wizard'
	def _get_default_yms(A):B=fields.Date.from_string(fields.Date.context_today(A));C=1;D=(B-relativedelta(months=C)).strftime('%Y-%m');E=A.env['hr.ph.pay.year.month'].search([('name','<=',D)],limit=2);return E.ids
	report_type=fields.Selection([('pay_period','Per Payroll'),('monthly','Monthly'),('yearly','Yearly')],string='Report Type',default=lambda self:'pay_period');year_month_ids=fields.Many2many('hr.ph.pay.year.month','ym_variance_rel','var_id','ym_id',string='Compare Months');year_ids=fields.Many2many('hr.ph.pay.year','year_variance_rel','var_id','year_id',string='Compare Years');payroll_ids=fields.Many2many('hr.ph.payroll','payroll_variance_rel','var_id','payroll_id',string='Compare Payroll');xlsx_file=fields.Binary(string='Excel Report File',readonly=True);xlsx_filename=fields.Char()
	@api.model
	def get_domain(self):
		B=self;A=[]
		if B.report_type=='pay_period':
			for C in B.payroll_ids:A.insert(0,'|');A.append(('payroll_id','=',C.id))
		elif B.report_type=='monthly':
			for D in B.year_month_ids:A.insert(0,'|');A.append(('year_month','=',D.name))
		elif B.report_type=='yearly':
			for E in B.year_ids:A.insert(0,'|');A.append(('year','=',E.name))
		A.append(('id','=',False));_logger.debug('DOM: %s',A);return A
	def view_report(A):
		A.ensure_one();C=A._context.copy();D=A.get_domain();B={'name':'Pay Variance Report','view_mode':'pivot,list','res_model':'hr.ph.pay.variance.report','type':'ir.actions.act_window','context':C,'domain':D}
		if A.report_type=='pay_period':
			if A.payroll_ids:B.update({'views':[[A.env.ref('ez_payroll_variance.pivot_variance_payroll_report').id,'pivot'],[A.env.ref('ez_payroll_variance.tree_variance_report').id,'list']]});_logger.debug('VAR pay: %s',B);return B
		elif A.report_type=='monthly':
			if A.year_month_ids:B.update({'views':[[A.env.ref('ez_payroll_variance.pivot_variance_ym_report').id,'pivot'],[A.env.ref('ez_payroll_variance.tree_variance_report').id,'list']]});_logger.debug('VAR monthly: %s',B);return B
		elif A.report_type=='yearly':
			if A.year_ids:B.update({'views':[[A.env.ref('ez_payroll_variance.pivot_variance_year_report').id,'pivot'],[A.env.ref('ez_payroll_variance.tree_variance_report').id,'list']]});_logger.debug('VAR yearly: %s',B);return B
		return A.back()
	def gen_xlsx(M):
		M.ensure_one()
		if len(M.payroll_ids)!=2:raise ValidationError(_('You can only compare 2 months.'))
		q=M.get_domain();l=[A.name for A in M.payroll_ids];r=M.env['hr.ph.pay.variance.report'].search(q,order='');c=BytesIO();Q=xlsxwriter.Workbook(c,{'in_memory':True});Q.set_calc_mode('auto');A=Q.add_worksheet();K=Q.add_format({'bold':1,'align':'center','valign':'vcenter','border':1});m=8;L=Q.add_format({'num_format':'#,##0.00'});E={'number':[0,'No.',10],'identification_id':[1,'Employee No.',15],'employee_name':[2,'Employee Name',30],'hired':[3,'Join Date',12],'data_start':[4,'Start',12]};A.write(0,0,'VARIANCE REPORT %s'%' - '.join(l));s=Q.add_format({'num_format':'mm/dd/yyyy'});B=2;R={};n={};o={}
		for D in r:
			S='%s %s'%(D.employee_id.name,D.employee_id.id)
			if S not in R:R[S]={'employee_id':D.employee_id.id,'employee_name':D.employee_id.name,'identification_id':D.employee_id.identification_id,'hired':D.employee_id.hired,'lines':{}}
			Y='%s$%s'%(D.payroll_id.name,D.sorted_name);d=D.sorted_name;N=D.payroll_id.name;R[S]['lines'][Y]=R[S]['lines'].get(Y,.0)+float(D.amount);n[d]=1;o[N]=1
		def Z(ws,r,dcol,rec,name,format=False):
			B=rec;A=name
			if B[A]:
				if format:ws.write(r,dcol[A][0],B[A],format)
				else:ws.write(r,dcol[A][0],B[A])
		for T in E:
			if T!='data_start':F=E[T][0];A.merge_range(B,F,B+1,F,E[T][1],K);A.set_column(E[T][0],E[T][0],E[T][2])
		C=E['data_start'][0];e=sorted(n.keys());a=sorted(o.keys())
		for t in e:
			V=C
			for f in a:A.write(B+1,C,f,K);C+=1
			A.set_column(V,C-1,E['data_start'][2]);A.set_column(C,C+1,m);A.write(B+1,C,'Diff',K);C+=1;A.write(B+1,C,'Diff %',K);C+=1;A.merge_range(B,V,B,C-1,t[3:],K)
		V=C
		for f in a:A.write(B+1,C,f,K);C+=1
		A.set_column(V,C-1,E['data_start'][2]);A.set_column(C,C+1,m);A.write(B+1,C,'Diff',K);C+=1;A.write(B+1,C,'Diff %',K);C+=1;A.merge_range(B,V,B,C-1,'Net Pay',K);b='ABCDEFGHIJKLMNOPQRSTUVWXYZ';G=[A for A in b];G=G+['%s%s'%(A,B)for A in G for B in G];G+=['AA%s'%A for A in b]+['AB%s'%A for A in b]+['AC%s'%A for A in b];B+=2;p=1
		for S in sorted(R.keys()):
			D=R[S];A.write(B,E['number'][0],p);Z(A,B,E,D,'identification_id');Z(A,B,E,D,'employee_name');Z(A,B,E,D,'identification_id');Z(A,B,E,D,'hired',s);F=E['data_start'][0];p+=1;g={}
			for d in e:
				H=0;O=.0;P=.0;U=False;W=False
				for N in a:
					Y='%s$%s'%(N,d);I=D['lines'].get(Y,.0)
					if I:A.write(B,F,I,L);g[N]=g.get(N,.0)+I;W=True
					if H==0:O=I
					elif H==1:
						U=False;P=O-I;X=abs((O+I)/2.)
						if X:U=1e2*abs(P)/X
					F+=1;H+=1
				if W:
					try:h='%s%s'%(G[F-2],B+1);i='%s%s'%(G[F-1],B+1);j='(%s - %s)'%(h or .0,i or .0)
					except:h='';i='';j=''
					if P:
						try:A.write_formula('%s%s'%(G[F],B+1),'=%s'%j,L)
						except:pass
					if U:
						u='ABS((%s + %s) / 2.0)'%(h,i);v='=100.0 * ABS(%s) / %s'%(j,u)
						try:A.write_formula('%s%s'%(G[F+1],B+1),v,L)
						except:pass
				F+=2
			H=0;O=.0;P=.0;U=False;W=False
			for N in a:
				I=g.get(N,.0);A.write(B,F,I,L);W=True
				if H==0:O=I
				elif H==1:
					P=O-I;X=abs((O+I)/2.)
					if X:U=1e2*abs(P)/X
				F+=1;H+=1
			if W:A.write(B,F,P,L);A.write(B,F+1,U,L)
			F+=2;B+=1
		k=B
		for w in range(len(e)+1):H=4+w*4;J=G[H];A.write_formula('%s2'%J,'=SUM(%s5:%s%s)'%(J,J,k),L);J=G[H+1];A.write_formula('%s2'%J,'=SUM(%s5:%s%s)'%(J,J,k),L);J=G[H+2];A.write_formula('%s2'%J,'=SUM(%s5:%s%s)'%(J,J,k),L)
		Q.close();c.seek(0);M.xlsx_file=base64.b64encode(c.getvalue());M.xlsx_filename='Variance Report %s.xlsx'%' '.join(l);return M.back()
	@api.model
	def back(self):return{'name':'Pay Variance Wizard','view_mode':'form','res_model':'hr.ph.pay.variance.wizard','res_id':self.id,'type':'ir.actions.act_window','target':'new','context':self._context.copy()}
class VarianceReport(models.Model):
	_name='hr.ph.pay.variance.report';_description='Payroll Variance Report';_auto=False;_rec_name='id';_order='sequence, payroll_id, sorted_name';company_id=fields.Many2one('res.company',string='Company');year=fields.Char();year_month=fields.Char();payroll_id=fields.Many2one('hr.ph.payroll',string='Payroll');employee_id=fields.Many2one('hr.employee',string='Employee');sequence=fields.Integer();sorted_name=fields.Char('Name');amount=fields.Float(digits=(0,2));hired=fields.Date(related='employee_id.hired',compute_sudo=True);identification_id=fields.Char(related='employee_id.identification_id',compute_sudo=True)
	def init(A):tools.drop_view_if_exists(A.env.cr,'hr_ph_pay_variance_report');A.env.cr.execute("\n            CREATE VIEW hr_ph_pay_variance_report AS (\n                SELECT MIN(pc.id) AS id,\n                    ps.company_id,\n                    left(pr.year_month, 4) AS year,\n                    pr.year_month,\n                    ps.payroll_id,\n                    ps.employee_id,\n                    CASE \n                        WHEN pc.name='Regular' THEN 10\n                        ELSE 1000 + pc.seq\n                    END AS sequence,\n                    CASE \n                         WHEN pc.name='Regular' THEN '10 ' || pc.name\n                         ELSE '20 ' || pc.name\n                    END AS sorted_name,\n                    SUM(pc.amount) AS amount\n                FROM hr_ph_pay_computation AS pc\n                INNER JOIN hr_ph_payslip AS ps\n                    ON ps.id = pc.payslip_id\n                INNER JOIN hr_ph_payroll AS pr\n                    ON pr.id = ps.payroll_id\n                GROUP BY ps.company_id, year, pr.year_month, ps.payroll_id, ps.employee_id, sequence, sorted_name\n                         \n                UNION\n\n                SELECT MAX(-pd.id) AS id,\n                    pss.company_id,\n                    left(pr.year_month, 4) AS year,\n                    pr.year_month,\n                    pss.payroll_id,\n                    pss.employee_id,\n                    CASE \n                        WHEN pd.name='Withholding Tax' THEN 10000\n                        ELSE 2000 + pd.seq\n                    END AS sequence,\n                    CASE \n                         WHEN pd.name='Withholding Tax' THEN '90 ' || pd.name\n                         ELSE '40 ' || pd.name\n                    END AS sorted_name,\n                    SUM(-pd.amount) AS amount\n                FROM hr_ph_pay_deduction AS pd\n                INNER JOIN hr_ph_payslip AS pss\n                    ON pss.id = pd.payslip_id\n                INNER JOIN hr_ph_payroll AS pr\n                    ON pr.id = pss.payroll_id\n                GROUP BY pss.company_id, year, pr.year_month, pss.payroll_id, pss.employee_id, sequence, sorted_name\n\n                UNION\n\n                SELECT MAX(-l.id -500000000) AS id,\n                    ps2.company_id,\n                    left(pr.year_month, 4) AS year,\n                    pr.year_month,\n                    ps2.payroll_id,\n                    ps2.employee_id,\n                    5000 + l.seq AS sequence,\n                    '60 ' || SPLIT_PART(l.name,' - ',1) AS sorted_name,\n                    SUM(-l.amount) AS amount\n                FROM hr_ph_loan_payment AS l\n                INNER JOIN hr_ph_payslip AS ps2\n                    ON ps2.id = l.payslip_id\n                INNER JOIN hr_ph_payroll AS pr\n                    ON pr.id = ps2.payroll_id\n                GROUP BY ps2.company_id, year, pr.year_month, ps2.payroll_id, ps2.employee_id, sequence, sorted_name\n            )")