from collections import OrderedDict
from operator import itemgetter
from odoo import _,http
from odoo.exceptions import AccessError,MissingError
from odoo.http import request
from odoo.tools import groupby as groupbyelem
from odoo.addons.portal.controllers.portal import CustomerPortal,pager as portal_pager
from odoo.fields import Domain
import random,hashlib,logging
_logger=logging.getLogger(__name__)
class PortalPayslip(CustomerPortal):
	_items_per_page=20
	def _get_payslip_counters(B):
		A={};C=request.env['ir.config_parameter'].sudo();D=int(C.get_param('payslip_count','0').strip())
		if D:E=request.env['hr.ph.payslip'].sudo();F=E.search_count(B._get_payslip_domain(),limit=1);A['payslip_count']=F
		else:A['payslip_count']=0
		_logger.debug('COUNTERS _get_payslip_counters: %s',A);return A
	def _prepare_home_portal_values(D,counters):
		B=counters;A=super()._prepare_home_portal_values(B)
		for(C,E)in D._get_payslip_counters().items():
			if C in B:A[C]=E
		_logger.debug('COUNTERS: %s',A);return A
	def _get_payslip_domain(B):A=[('company_id','=',request.env.company.id),('employee_id.work_email','=',request.env.user.login),('state','!=','draft')];return A
	def _get_payslip_searchbar_sortings(B):A={'date':{'label':_('Date'),'order':'date_to desc'},'net_pay':{'label':_('Net Pay'),'order':'net_pay'},'deduction':{'label':_('Deductions'),'order':'total_deductions'}};_logger.debug('_get_searchbar_sortings payslip: %s',A);return A
	def _get_payslip_searchbar_filters(A):return{'all':{'label':_('All'),'domain':[]}}
	def _prepare_my_values(C,page,date_begin,date_end,sortby,filterby,searchbar_sortings,searchbar_filters,domain=None,url='/my/payslips',model='hr.ph.payslip',page_name='payslip'):
		I=searchbar_sortings;G=searchbar_filters;F=date_end;E=domain;D=date_begin;B=filterby;A=sortby;_logger.debug('_prepare_my_values: page=%s searchbar_filters=%s',page,G);H=C._prepare_portal_layout_values();J=request.env[model].sudo()
		if not A:A='date'
		K=I[A]['order']
		if not B:B='all'
		E+=G[B]['domain']
		if D and F:E+=[('date_to','>=',D),('date_to','<=',F)]
		H.update({'company_id':request.env.company.sudo(),'date':D,'records':lambda pager_offset:J.search(E,order=K,limit=C._items_per_page,offset=pager_offset),'page_name':page_name,'pager':{'url':url,'url_args':{'date_begin':D,'date_end':F,'sortby':A,'filterby':B},'total':J.search_count(E),'page':page,'step':C._items_per_page},'default_url':url,'searchbar_sortings':I,'sortby':A,'searchbar_filters':OrderedDict(sorted(G.items())),'filterby':B});H.update(C._get_payslip_counters());return H
	@http.route(['/my/payslips','/my/payslips/page/<int:page>'],type='http',auth='user',website=True)
	def portal_my_payslips(self,page=1,date_begin=None,date_end=None,sortby=None,filterby=None,**H):A=self;E=A._get_payslip_domain();F=A._get_payslip_searchbar_sortings();G=A._get_payslip_searchbar_filters();B=A._prepare_my_values(page,date_begin,date_end,sortby,filterby,F,G,domain=E);C=portal_pager(**B['pager']);D=B['records'](C['offset']);request.session['my_payslips_history']=D.ids[:100];B.update({'records':D,'pager':C});return request.render('ez_payroll_ess.portal_my_payslips',B)
	@http.route(['/my/payslips/pdf/<int:payslip_id>'],type='http',auth='user',website=True)
	def portal_my_payslip_pdf_detail(self,payslip_id,**E):
		B=request.env['hr.ph.payslip'].sudo();A=B.browse(payslip_id)
		if A.employee_id.work_email!=request.env.user.login:return request.redirect('/my')
		C='pdf';D=False;return self._show_report(model=A,report_type=C,report_ref='ez_payroll.action_print_single_payslip',download=D)
	def _unlink_records(H,rec_id,kw,domain=[],model='hr.ph.payslip'):
		D=model;C=rec_id;A=domain;G=request.env[D].sudo();E=kw.get('records',[])
		if C:E.append(C)
		A.append(('id','in',E));B=G.search(A);F=B.ids;_logger.debug('_unlink_records: model=%s domain=%s kw=%s ids=%s',D,A,kw,F)
		if B:B.unlink();return{'res':True,'unlink':F}
		else:return{'res':False}
	@http.route('/ess-api/sign_payslip/<int:payslip_id>/<int:is_signed>',type='jsonrpc',methods=['POST'],auth='user')
	def ess_mfa_request(self,payslip_id,is_signed,**C):
		B=payslip_id
		if B:
			A=request.env['hr.ph.payslip'].browse(B);A.is_signed=is_signed and True or False
			if A.is_signed and not A.employee_id.signature_image:A.employee_id.action_generate_signature()
		return{}