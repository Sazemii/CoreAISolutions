from collections import OrderedDict
from operator import itemgetter
from odoo import _,http,fields
from odoo.exceptions import AccessError,MissingError
from odoo.http import request
from odoo.tools import groupby as groupbyelem
from odoo.addons.portal.controllers.portal import CustomerPortal,pager as portal_pager
from odoo.fields import Domain
import random,hashlib
from dateutil.relativedelta import relativedelta
from.import portal_payslip_controller
import logging
_logger=logging.getLogger(__name__)
class PortalTkRequest(portal_payslip_controller.PortalPayslip):
	_items_per_page=21
	def _get_tkrequest_counters(C):
		A={};B=request.env['ir.config_parameter'].sudo();A['tkrequest_count']=int(B.get_param('tkrequest_count','0').strip());D=int(B.get_param('tkrequest_approve_count','0').strip())
		if D:E=request.env['ez.time.request'].sudo();F=E.search_count(C._get_tkrequest_domain(approve=1),limit=1);A['tkrequest_approve_count']=F
		else:A['tkrequest_approve_count']=0
		return A
	def _prepare_home_portal_values(D,counters):
		A=counters;B=super()._prepare_home_portal_values(A)
		for(C,E)in D._get_tkrequest_counters().items():
			if C in A:B[C]=E
		return B
	def _tkrequest_get_page_view_values(B,tkrequest,access_token,**C):A=tkrequest;D={'page_name':'tkrequest','tkrequest':A};return B._get_page_view_values(A,access_token,D,'my_tkrequests_history',False,**C)
	def _get_tkrequest_domain(B,approve=False):
		A=[('company_id','=',request.env.company.id),('type','not ilike','approver')]
		if approve:A.append(('employee_id.timekeeping_manager_id','=',request.env.user.id));A.append(('state','!=','draft'))
		else:A.append(('employee_id.work_email','=',request.env.user.login))
		_logger.debug('DOMAIN: %s',A);return A
	def _get_tkrequest_searchbar_sortings(B):A={'date':{'label':'Date','order':'date desc, employee_id'},'type':{'label':'Request Type','order':'type, date desc'},'employee':{'label':'Employee','order':'employee_id, date desc'}};_logger.debug('_get_tkrequest_searchbar_sortings: %s',A);return A
	def _get_tkrequest_searchbar_filters(A):return{'all':{'label':'All','domain':[]},'f0_draft':{'label':'Draft','domain':[('state','=','draft')]},'f1_sent':{'label':'For Approval','domain':[('state','=','sent')]},'f2_refused':{'label':'Denied','domain':[('state','=','denied')]},'f3_approved':{'label':'Approved','domain':[('state','=','approved')]}}
	def _get_tkrequest_searchbar_inputs(B):A={'all':{'input':'all','label':'Search in All','order':1},'name':{'input':'name','label':'Search in Name','order':2},'employee':{'input':'employee','label':'Search in Employee','order':3},'type':{'input':'type','label':'Search in Request Type','order':4},'note':{'input':'note','label':'Search in Description','order':5}};return dict(sorted(A.items(),key=lambda item:item[1]['order']))
	def _get_tkrequest_search_domain(D,search_in,search):
		C=search;B=search_in;A=[]
		if B in('name','all'):A.append([('name','ilike',C)])
		if B in('employee','all'):A.append([('employee_id.name','ilike',C)])
		if B in('type','all'):A.append([('type','ilike',C)])
		if B in('note','all'):A.append([('note','ilike',C)])
		return Domain.OR(A)
	def _tkrequest_prepare_my_values(B,page,date_begin,date_end,sortby,filterby,searchbar_sortings,searchbar_filters,domain=None,url='/my/tkrequests',model='ez.time.request',page_name='tkrequest'):D=model;C=searchbar_filters;_logger.debug('_tkrequest_prepare_my_values: page=%s searchbar_filters=%s',page,C);A=B._prepare_my_values(page,date_begin,date_end,sortby,filterby,searchbar_sortings,C,domain=domain,url=url,model=D,page_name=page_name);A['model']=D;A.update(B._get_tkrequest_counters());return A
	@http.route(['/my/tkrequests','/my/tkrequests/<int:approve>','/my/tkrequests/<int:approve>/page/<int:page>'],type='http',auth='user',website=True)
	def portal_my_tkrequests(self,page=1,approve=None,date_begin=None,date_end=None,sortby=None,filterby=None,search=None,search_in=None,**a):
		I=date_end;H=date_begin;G=filterby;F=search;E=search_in;C=approve;B=self;H=False;I=False;J=B._get_tkrequest_domain(approve=C);P=B._get_tkrequest_searchbar_sortings();Q=B._get_tkrequest_searchbar_filters();R=B._get_tkrequest_searchbar_inputs()
		if C and not G:G='f1_sent'
		if not E:E='all'
		if F:J+=B._get_tkrequest_search_domain(E,F)
		C=C and 1 or 0;S='/my/tkrequests/%s'%C;A=B._tkrequest_prepare_my_values(page,H,I,sortby,G,P,Q,domain=J,url=S)
		if A['pager']:
			K={'search_in':E,'search':F}
			if'url_args'not in A['pager']:A['pager']['url_args']=K
			else:A['pager']['url_args'].update(K)
		L=portal_pager(**A['pager']);D=A['records'](L['offset']);request.session['my_tkrequests_history']=D.ids[:100];M=request.env['ez.time.record'].sudo();T=request.env['hr.employee'].sudo();U=[A for A in D._fields['type'].selection if'Approver'not in A[1]];V=dict(D._fields['type'].selection);N=[[A[0],M._get_day_type_names().get(A[0])]for A in M._get_day_type_selection()];W=dict(N);O=D._fields['state'].selection;X=dict(O);Y=[{'id':A.id,'name':A.name,'employee_id':[A.employee_id.id,A.employee_id.name],'state':A.state,'type':A.type,'day_type':A.day_type,'date':A.date and A.date.strftime('%Y-%m-%d')or False,'time':A.time,'auth_hrs':A.auth_hrs,'schedule':A.schedule,'note':A.note}for A in D];Z=T.search([('employee_id.work_email','=',request.env.user.login)],limit=1);A.update({'employee_id':Z.id,'records':D,'records2':Y,'selections':{'type':U,'day_type':N,'state':O},'lookups':{'type':V,'day_type':W,'state':X},'pager':L,'searchbar_inputs':R,'search_in':E,'search':F,'approve':C});return request.render('ez_payroll_ess.portal_my_tkrequest',A)
	@http.route(['/my/tkrequest/<int:rec_id>','/my/tkrequest/<int:rec_id>/<int:approve>'],type='http',auth='user',website=True)
	def portal_my_tkrequest_detail(self,rec_id,approve=None,access_token=None,model='ez.time.request',**F):
		C=approve;G=request.env[model].sudo();H=request.env['hr.employee'].sudo();D=self._get_tkrequest_domain(approve=C);D.append(('id','=',int(rec_id)));A=G.search(D,limit=1)
		if A:E=A.employee_id
		else:E=H.search([('work_email','=',request.env.user.login)],limit=1)
		B=self._tkrequest_get_page_view_values(A,access_token,**F);B.update({'rec':A,'employee_id':E,'approve':C and 1 or 0});_logger.debug('portal_my_tkrequest_detail: values=%s',B);return request.render('ez_payroll_ess.portal_my_tkrequest_detail',B)
	@http.route(['/my/tkrequest/get/<int:rec_id>','/my/tkrequest/get/<int:rec_id>/<int:approve>'],methods=['POST'],type='jsonrpc',auth='user',cors='*')
	def portal_my_tkrequest_get_detail(self,rec_id,approve=None,model='ez.time.request',**M):
		D=approve;I=request.env[model].sudo();J=request.env['hr.employee'].sudo();K=request.env['ez.time.record'].sudo();F=self._get_tkrequest_domain(approve=D);F.append(('id','=',rec_id));A=I.search(F,limit=1);B=False;E=A.employee_id
		if A:B=A.state!='draft';G=fields.Date.to_string(A.date)
		else:E=J.search([('work_email','=',request.env.user.login)],limit=1);G=fields.Date.to_string(fields.Date.today())
		L=A.state or'draft';D=D and 1 or 0
		def C(name,label,value,readonly=False,**B):A={'name':name,'label':label,'value':value,'readonly':readonly};A.update(B);return A
		H={'employee_id':E.display_name,'readonly':D or B,'approve':D,'state':L,'fields':[C('employee_id','Employee',E.id,readonly=A and True or False,selections=[[E.id,E.display_name]]),C('name','Description',A.name,readonly=B),C('date','Date',G,type='date',readonly=B),C('type','Request Type',A.type,readonly=B,selections=list(filter(lambda rec:'approver'not in rec[0],A._fields['type'].selection))),C('auth_hrs','Authorized Hours',A.auth_hrs,readonly=B),C('time','Time Range',A.time,readonly=B),C('day_type','Day Type',A.day_type,readonly=B,selections=K._get_day_type_selection()),C('schedule','Schedule',A.schedule,readonly=B),C('note','Notes',A.note,readonly=B),C('state','Status',A.state,readonly=True,selections=A._fields['state'].selection)]};_logger.debug('portal_my_tkrequest_get_detail: values=%s',H);return H
	@http.route('/my/tkrequest/state/<string:state>/<int:rec_id>/<int:approve>',methods=['POST'],type='jsonrpc',auth='user',cors='*')
	def portal_change_state_tkrequest(self,state,rec_id,approve,model='ez.time.request',**E):
		B=rec_id;C=request.env[model].sudo();D=self._get_tkrequest_domain(approve)+[('id','=',B)];A=C.search(D,limit=1)
		if A:_logger.debug('portal_change_state_tkrequest: id=%s',B);A.sudo()._check_timecard();A.sudo()._change_state(state)
	@http.route('/my/tkrequest/read/<int:rec_id>/<int:approve>',methods=['POST'],type='jsonrpc',auth='user',cors='*')
	def portal_read_tkrequest(self,rec_id,approve,model='ez.time.request',**A):C=request.env[model].sudo();D=self._get_tkrequest_domain(approve)+[('id','=',rec_id)];B=C.search_read(D,A.get('fields',[]),limit=1);_logger.debug('portal_read_tkrequest: READ kw=%s rec=%s',A,B);return B
	@http.route('/my/tkrequest/write/<int:rec_id>/<int:approve>',methods=['POST'],type='jsonrpc',auth='user',cors='*')
	def portal_write_tkrequest(self,rec_id,approve,model='ez.time.request',**C):
		B=rec_id;D=request.env[model].sudo();E=self._get_tkrequest_domain(approve)+[('id','=',B)];A=D.search(E,limit=1)
		if B:
			_logger.debug('portal_write_tkrequest: WRITE kw=%s id=%s',C,B)
			if A.state=='draft':A.write(C)
		else:_logger.debug('portal_write_tkrequest: CREATE kw=%s id=%s',C,B);A=D.create(C)
		if A.type=='ob':A.onchange_time()
		elif A.type=='sch':A.onchange_sched()
		return A.id
	@http.route(['/my/tkrequest/unlink','/my/tkrequest/unlink/<int:rec_id>'],methods=['POST'],type='jsonrpc',auth='user',cors='*')
	def portal_unlink_tkrequest(self,rec_id=False,**B):A=[('company_id','=',request.env.company.id),('state','=','draft'),('employee_id.work_email','=',request.env.user.login)];_logger.debug('portal_unlink_tkrequest: doman=%s',A);return self._unlink_records(rec_id,B,domain=A,model='ez.time.request')