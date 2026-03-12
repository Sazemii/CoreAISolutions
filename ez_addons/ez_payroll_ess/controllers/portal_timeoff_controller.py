from collections import OrderedDict
from operator import itemgetter
from odoo import _,http,fields
from odoo.fields import Domain
from odoo.exceptions import AccessError,MissingError
from odoo.http import request
from odoo.tools import groupby as groupbyelem
from odoo.addons.portal.controllers.portal import CustomerPortal,pager as portal_pager
import random,hashlib
from dateutil.relativedelta import relativedelta
from.import portal_payslip_controller
import logging
_logger=logging.getLogger(__name__)
class PortalTimeoff(portal_payslip_controller.PortalPayslip):
	_items_per_page=21
	def _get_timeoff_counters(C):
		A={};B=request.env['ir.config_parameter'].sudo();A['timeoff_count']=int(B.get_param('timeoff_count','0').strip());D=int(B.get_param('timeoff_approve_count','0').strip())
		if D:E=request.env['hr.leave'].sudo();F=E.search_count(C._get_timeoff_domain(approve=1),limit=1);A['timeoff_approve_count']=F
		else:A['timeoff_approve_count']=0
		return A
	def _prepare_home_portal_values(D,counters):
		A=counters;B=super()._prepare_home_portal_values(A)
		for(C,E)in D._get_timeoff_counters().items():
			if C in A:B[C]=E
		return B
	def _timeoff_get_page_view_values(B,timeoff,access_token,**C):A=timeoff;D={'page_name':'timeoff','timeoff':A};return B._get_page_view_values(A,access_token,D,'my_timeoffs_history',False,**C)
	def _get_timeoff_domain(B,approve=False):
		A=[('company_id','=',request.env.company.id)]
		if approve:A.append(('employee_id.leave_manager_id','=',request.env.user.id))
		else:A.append(('employee_id.work_email','=',request.env.user.login))
		_logger.debug('DOMAIN: %s',A);return A
	def _get_timeoff_searchbar_sortings(B):A={'date':{'label':'Date','order':'request_date_from desc, employee_id'},'status':{'label':'Status','order':'holiday_status_id, request_date_from desc'},'employee':{'label':'Employee','order':'employee_id, request_date_from desc'}};_logger.debug('_get_searchbar_sortings 2316: %s',A);return A
	def _get_timeoff_searchbar_filters(A):return{'all':{'label':'All','domain':[]},'to_approve':{'label':'To Approve','domain':[('state','in',['draft','confirm','validate1'])]},'approved':{'label':'Approved','domain':[('state','=','validate')]},'refused':{'label':'Refused','domain':[('state','=','refuse')]}}
	def _timeoff_get_searchbar_inputs(B):A={'all':{'input':'all','label':'Search in All','order':1},'employee':{'input':'employee','label':'Search in Employee','order':2},'status':{'input':'status','label':'Search in Time Off Type','order':3},'name':{'input':'name','label':'Search in Description','order':4}};return dict(sorted(A.items(),key=lambda item:item[1]['order']))
	def _timeoff_get_search_domain(D,search_in,search):
		C=search;B=search_in;A=[]
		if B in('status','all'):A.append([('holiday_status_id','ilike',C)])
		if B in('name','all'):A.append([('name','ilike',C)])
		if B in('employee','all'):A.append([('employee_id.name','ilike',C)])
		return Domain.OR(A)
	def _timeoff_prepare_my_values(B,page,date_begin,date_end,sortby,filterby,searchbar_sortings,searchbar_filters,domain=None,url='/my/timeoffs',model='hr.leave',page_name='timeoff'):D=model;C=searchbar_filters;_logger.debug('_timeoff_prepare_my_values: page=%s searchbar_filters=%s',page,C);A=B._prepare_my_values(page,date_begin,date_end,sortby,filterby,searchbar_sortings,C,domain=domain,url=url,model=D,page_name=page_name);A['model']=D;A.update(B._get_timeoff_counters());return A
	@http.route(['/my/timeoffs','/my/timeoffs/<int:approve>','/my/timeoffs/<int:approve>/page/<int:page>'],type='http',auth='user',website=True)
	def portal_my_timeoff(self,page=1,approve=None,date_begin=None,date_end=None,sortby=None,filterby=None,search=None,search_in=None,**Q):
		H=date_end;G=date_begin;F=filterby;E=search;D=approve;C=search_in;B=self;G=False;H=False;I=B._get_timeoff_domain(approve=D);N=B._get_timeoff_searchbar_sortings();O=B._get_timeoff_searchbar_filters();P=B._timeoff_get_searchbar_inputs()
		if D and not F:F='to_approve'
		if not C:C='all'
		if E:I+=B._timeoff_get_search_domain(C,E)
		if D:J='/my/timeoffs/1'
		else:J='/my/timeoffs/0'
		A=B._timeoff_prepare_my_values(page,G,H,sortby,F,N,O,domain=I,url=J)
		if A['pager']:
			K={'search_in':C,'search':E}
			if'url_args'not in A['pager']:A['pager']['url_args']=K
			else:A['pager']['url_args'].update(K)
		L=portal_pager(**A['pager']);M=A['records'](L['offset']);request.session['my_timeoffs_history']=M.ids[:100];A.update({'records':M,'pager':L,'searchbar_inputs':P,'search_in':C,'search':E,'approve':D});return request.render('ez_payroll_ess.portal_my_timeoff',A)
	time_selections=[('0','12:00 AM'),('0.5','12:30 AM'),('1','1:00 AM'),('1.5','1:30 AM'),('2','2:00 AM'),('2.5','2:30 AM'),('3','3:00 AM'),('3.5','3:30 AM'),('4','4:00 AM'),('4.5','4:30 AM'),('5','5:00 AM'),('5.5','5:30 AM'),('6','6:00 AM'),('6.5','6:30 AM'),('7','7:00 AM'),('7.5','7:30 AM'),('8','8:00 AM'),('8.5','8:30 AM'),('9','9:00 AM'),('9.5','9:30 AM'),('10','10:00 AM'),('10.5','10:30 AM'),('11','11:00 AM'),('11.5','11:30 AM'),('12','12:00 PM'),('12.5','12:30 PM'),('13','1:00 PM'),('13.5','1:30 PM'),('14','2:00 PM'),('14.5','2:30 PM'),('15','3:00 PM'),('15.5','3:30 PM'),('16','4:00 PM'),('16.5','4:30 PM'),('17','5:00 PM'),('17.5','5:30 PM'),('18','6:00 PM'),('18.5','6:30 PM'),('19','7:00 PM'),('19.5','7:30 PM'),('20','8:00 PM'),('20.5','8:30 PM'),('21','9:00 PM'),('21.5','9:30 PM'),('22','10:00 PM'),('22.5','10:30 PM'),('23','11:00 PM'),('23.5','11:30 PM')]
	@http.route('/submitted/timeoff/<int:approve>',type='http',auth='user',website=True,csrf=True)
	def submit_timeoff(self,approve,**B):
		C=approve
		def F(kw,val):
			B=val;A=kw
			if not A.get('request_unit_half')and not A.get('request_unit_hours'):B.update({'request_date_from':A.get('date_from'),'request_date_to':A.get('date_to'),'request_unit_half':False,'request_unit_hours':False})
			elif A.get('request_unit_half')and not A.get('request_unit_hours'):B.update({'request_date_from':A.get('date_from'),'request_date_to':A.get('date_from'),'request_date_from_period':A.get('request_date_from_period'),'request_unit_half':True,'request_unit_hours':False})
			elif not A.get('request_unit_half')and A.get('request_unit_hours'):B.update({'request_date_from':A.get('date_from'),'request_date_to':A.get('date_from'),'request_hour_from':A.get('request_hour_from'),'request_hour_to':A.get('request_hour_to'),'request_unit_half':False,'request_unit_hours':True})
		_logger.debug('submit_timeof: %s',B);E=request.env['hr.leave'].sudo()
		if B.get('btn_back'):return request.redirect('/my/timeoffs/%s'%C)
		elif B.get('btn_delete'):
			A=E.browse(int(B.get('timeoff_id',0)))
			if A.state in['draft','confirm']:A.unlink()
			return request.redirect('/my/timeoffs/%s'%C)
		elif B.get('create'):D={'employee_id':int(B.get('employee_id',0)),'holiday_status_id':int(B.get('holiday_status_id',0)),'private_name':B.get('name_field'),'state':'confirm'};F(B,D);_logger.debug('CREATE: %s',D);A=E.create(D);return request.redirect('/my/timeoff/%s/%s'%(A.id,C))
		elif B.get('btn_refuse'):
			A=E.browse(int(B.get('timeoff_id',0)))
			if A.state!='refuse':A.state='refuse'
			return request.redirect('/my/timeoff/%s/%s'%(A.id,C))
		elif B.get('btn_draft'):
			A=E.browse(int(B.get('timeoff_id',0)))
			if A.state=='refuse':A.state='draft'
			return request.redirect('/my/timeoff/%s/%s'%(A.id,C))
		elif C:
			A=E.browse(int(B.get('timeoff_id',0)))
			if A.state=='draft':A.state='confirm'
			if A.state=='confirm':A.action_approve()
			elif A.state=='validate1':A.action_validate()
			return request.redirect('/my/timeoff/%s/%s'%(A.id,C))
		elif B.get('edit'):A=E.browse(int(B.get('timeoff_id',0)));D={'holiday_status_id':int(B.get('holiday_status_id',0)),'private_name':B.get('name_field')};F(B,D);_logger.debug('WRITE: %s',D);A.write(D);return request.redirect('/my/timeoffs/%s'%C)
		return request.redirect('/my/timeoffs/%s'%C)
	@http.route(['/my/timeoff/<int:timeoff_id>','/my/timeoff/<int:timeoff_id>/<int:approve>'],type='http',auth='user',website=True)
	def portal_my_timeoff_detail(self,timeoff_id,approve=None,access_token=None,report_type=None,download=False,**L):
		F=approve;C=timeoff_id;B=self;M=request.env['hr.employee'].sudo();N=request.env['hr.leave'].sudo();O=request.env['hr.leave.type'].sudo();P=request.env.company;Q=O.with_company(P.id).search([('active','=',True)]);G=B._get_timeoff_domain(approve=F);G.append(('id','=',int(C)));A=N.search(G,limit=1)
		if C:D=fields.Date.to_string(A.request_date_from);H=fields.Date.to_string(A.request_date_to);I=float(A.request_hour_from);J=float(A.request_hour_to)
		else:D=(fields.Date.today()+relativedelta(days=1)).strftime('%Y-%m-%d');H=D;I='9';J='17'
		R={'am':'Morning','pm':'Afternoon'}
		if A:K=A.employee_id
		else:K=M.search([('work_email','=',request.env.user.login)],limit=1)
		E=B._timeoff_get_page_view_values(A,access_token,**L);E.update({'timeoff':A,'employee_id':K,'leave_types':Q,'time_selections':B.time_selections,'holiday_status_id':A.holiday_status_id.id,'date_from':D,'date_to':H,'request_date_from_period_data':R,'request_hour_from':I,'request_hour_to':J,'name':A.private_name,'create':C==0,'edit':A.state in['draft','confirm'],'approve':F and 1 or 0});_logger.debug('portal_my_timeoff_detail: values=%s',E);return request.render('ez_payroll_ess.portal_timeoff_detail',E)
	@http.route(['/my/timeoff/unlink','/my/timeoff/unlink/<int:rec_id>'],methods=['POST'],type='jsonrpc',auth='user',cors='*')
	def portal_unlink_timeoffs(self,rec_id=False,**A):B=self._get_timeoff_domain()+[('state','in',['draft','confirm'])];return self._unlink_records(rec_id,A,domain=B,model='hr.leave')