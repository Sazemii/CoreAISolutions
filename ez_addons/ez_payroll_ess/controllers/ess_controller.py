from collections import OrderedDict
from operator import itemgetter
from odoo import _,http
from odoo.exceptions import AccessError,MissingError
from odoo.http import request
from odoo.tools import groupby as groupbyelem
import random,hashlib,logging
_logger=logging.getLogger(__name__)
class Controller(http.Controller):
	def _get_hash(E,employee_id):B=request.env['hr.employee'].sudo();A=B.browse(employee_id);C='RB-%s-%s'%(A.id,A.mfa_code);D='%s'%hashlib.md5(C.encode()).hexdigest();_logger.debug('_get_hash: %s',A.name);return D
	@http.route('/ess-api/mfa-request',type='jsonrpc',methods=['POST'],auth='public')
	def ess_mfa_request(self,**A):
		_logger.debug('ess_mfa_request: %s',A);C=A.get('employee-email','');D=request.env['hr.employee'].sudo();B=D.search([('work_email','=',C)],limit=1)
		if B:B.mfa_code='%6d'%random.randrange(999999);E=request.env.ref('ez_payroll_ess.ess_email_template').sudo();E.send_mail(B.id,force_send=True,email_layout_xmlid='mail.mail_notification_light')
		return{'res':True,'params':A}
	@http.route('/ess-api/mfa-validate',type='jsonrpc',methods=['POST'],auth='public')
	def ess_mfa_validate(self,**B):
		D=B.get('employee-email','none12345@example.com');C=B.get('mfa',False);E=request.env['hr.employee'].sudo();A=E.search([('work_email','=',D)],limit=1);_logger.debug('ess_mfa_validate: %s %s',B,C)
		if C and A.mfa_code and A.mfa_code==C:F='RB-%s-%s'%(A.id,A.mfa_code);hash='%s'%hashlib.md5(F.encode()).hexdigest();A.mfa_count=0;return{'res':True,'msg':'Success','employee_id':A.id,'hash':hash}
		else:
			A.mfa_count+=1
			if A.mfa_count>=5:A.mfa_count=0;A.mfa_code=False;return{'res':False,'msg':'Too many wrong retries. MFA code will reset.'}
			else:return{'res':False,'msg':'Invalid email or MFA.'}
	@http.route('/ess-api/attendance/check_in/<int:employee_id>/<string:hash>',type='jsonrpc',methods=['POST'],auth='public')
	def ess_att_checkin(self,employee_id,hash,**G):
		A=employee_id;H=self._get_hash(A);B=request.env['hr.attendance'].sudo();C=False;D='Invalid parameters.'
		if H==hash:
			E=B.search([('employee_id','=',A),('check_out','=',False)],limit=1);_logger.debug('ess_att_checkin: ATT %s',E)
			if not E:F={'employee_id':A,'in_mode':False};F.update(G);B.create(F);D='Success.';C=True
		return{'res':C,'msg':D}
	@http.route('/ess-api/attendance/check_out/<int:employee_id>/<string:hash>',type='jsonrpc',methods=['POST'],auth='public')
	def ess_att_checkout(self,employee_id,hash,**F):
		B=employee_id;G=self._get_hash(B);H=request.env['hr.attendance'].sudo();C=False;D='Invalid parameters.'
		if G==hash:
			A=H.search([('employee_id','=',B),('check_out','=',False)],limit=1);_logger.debug('ess_att_checkout: ATT %s',A)
			if A:E={'out_mode':False};E.update(F);A.write(E);D='Success.';C=True
		return{'res':C,'msg':D}
	@http.route('/ess-api/attendance/next-process/<int:employee_id>/<string:hash>',type='jsonrpc',methods=['POST'],auth='public')
	def ess_att_next(self,employee_id,hash,**G):
		A=employee_id;E=self._get_hash(A);F=request.env['hr.attendance'].sudo();B=False;C='Invalid parameters.';next=False
		if E==hash:
			D=F.search([('employee_id','=',A),('check_out','=',False)],limit=1);_logger.debug('ess_att_next: ATT %s',D);C='Success.';B=True
			if D:next='check_out'
			else:next='check_in'
		return{'next-process':next,'res':B,'msg':C}
	@http.route(['/ess-api/payroll/get-payslips/<int:employee_id>/<string:hash>','/ess-api/payroll/get-payslips/<int:employee_id>/<string:hash>/<int:offset>/<int:limit>'],type='jsonrpc',methods=['POST'],auth='public')
	def ess_get_payslips(self,employee_id,hash,offset=0,limit=10):
		A=employee_id;B=self._get_hash(A)
		if B!=hash:return[]
		C=request.env['hr.ph.payslip'].sudo();D=C.search([('employee_id','=',A),('state','!=','draft')],limit=limit,offset=offset);return[{'payslip_id':A.id,'employee_id':[A.employee_id.id,A.employee_id.name],'payroll_id':[A.payroll_id.id,A.payroll_id.name],'gross_pay':A.gross_pay,'total_deductions':A.total_deductions,'total_loan_payments':A.total_loan_payments,'net_pay':A.net_pay,'pdf_payslip':'/report/pdf/ez_payroll.action_print_single_payslip/%s'%A.id}for A in D]
	@http.route('/ess-api/payroll/get-payslip/<int:payslip_id>/<string:hash>',type='jsonrpc',methods=['POST'],auth='public')
	def ess_get_payslip(self,payslip_id,hash):
		B=request.env['hr.ph.payslip'].sudo();A=B.browse(payslip_id);C=A.employee_id.id;D=self._get_hash(C)
		if D!=hash:return{}
		return{'payslip_id':A.id,'employee_id':[A.employee_id.id,A.employee_id.name],'payroll_id':[A.payroll_id.id,A.payroll_id.name],'gross_pay':A.gross_pay,'total_deductions':A.total_deductions,'total_loan_payments':A.total_loan_payments,'net_pay':A.net_pay,'pdf_payslip':'/report/pdf/ez_payroll.action_print_single_payslip/%s'%A.id}
	@http.route(['/ess-api/payroll/get-2316/<int:employee_id>/<string:hash>','/ess-api/payroll/get-2316/<int:employee_id>/<string:hash>/<int:offset>/<int:limit>'],type='jsonrpc',methods=['POST'],auth='public')
	def ess_get_2316(self,employee_id,hash,offset=0,limit=10):
		E=limit;D=offset;A=employee_id;F=self._get_hash(A)
		if F!=hash:return[]
		G=request.env['ez.bir.alphalist.schedule1'].sudo();B=G.search([('employee_id','=',A),('state','!=','draft')],limit=E,offset=D);C=1
		if not B:H=request.env['ez.bir.alphalist.schedule2'].sudo();B=H.search([('employee_id','=',A),('state','!=','draft')],limit=E,offset=D);C=21
		return[{'schedule':C,'schedule_id':A.id,'employee_id':[A.employee_id.id,A.employee_id.name],'alphalist_id':[A.alphalist_id.id,A.alphalist_id.name],'net_taxable_income':A.net_taxable_income,'tax_due':A.tax_due,'pdf_2316':(C==1 and'/bir2316-sched1/%s'or'/bir2316-sched2/%s')%A.id}for A in B]