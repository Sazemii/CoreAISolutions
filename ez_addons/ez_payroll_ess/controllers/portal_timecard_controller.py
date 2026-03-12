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
class PortalTimecard(portal_payslip_controller.PortalPayslip):
	_items_per_page=20
	def _get_timecard_counters(C):
		A={};B=request.env['ir.config_parameter'].sudo();A['timecard_count']=int(B.get_param('timecard_count','0').strip());D=int(B.get_param('timecard_approve_count','0').strip())
		if D:E=request.env['ez.time.card'].sudo();F=E.search_count(C._get_timecard_domain(approve=1),limit=1);A['timecard_approve_count']=F
		else:A['timecard_approve_count']=0
		return A
	def _prepare_home_portal_values(D,counters):
		A=counters;B=super()._prepare_home_portal_values(A)
		for(C,E)in D._get_timecard_counters().items():
			if C in A:B[C]=E
		return B
	def _timecard_get_page_view_values(B,timecard,access_token,**C):A=timecard;D={'page_name':'timecard','timecard':A};return B._get_page_view_values(A,access_token,D,'my_timecards_history',False,**C)
	def _get_timecard_domain(B,approve=False):
		A=[('company_id','=',request.env.company.id)]
		if approve:A.append(('employee_id.timekeeping_manager_id','=',request.env.user.id));A.append(('state','!=','draft'))
		else:A.append(('employee_id.work_email','=',request.env.user.login))
		_logger.debug('DOMAIN: %s',A);return A
	def _get_timecard_searchbar_sortings(B):A={'date':{'label':'Date','order':'date2 desc, employee_id'},'employee':{'label':'Employee','order':'employee_id, date2 desc'}};_logger.debug('_get_timecard_searchbar_sortings: %s',A);return A
	def _get_timecard_searchbar_filters(A):return{'all':{'label':'All','domain':[]},'f0_draft':{'label':'Draft','domain':[('state','=','draft')]},'f1_to_approve':{'label':'For Approval','domain':[('state','=','sent')]},'f2_approved':{'label':'Approved','domain':[('state','=','approved')]},'f3_denied':{'label':'Denied','domain':[('state','=','denied')]}}
	def _timecard_get_searchbar_inputs(B):A={'all':{'input':'all','label':'Search in All','order':1},'employee':{'input':'employee','label':'Search in Employee','order':2},'shift':{'input':'shift','label':'Search in Shifts','order':3}};return dict(sorted(A.items(),key=lambda item:item[1]['order']))
	def _timecard_get_search_domain(D,search_in,search):
		C=search;B=search_in;A=Domain.TRUE
		if B in('employee','all'):A.append([('employee_id.name','ilike',C)])
		if B in('shift','all'):A.append([('shift_id.name','ilike',C)])
		return Domain.OR(A)
	def _timecard_prepare_my_values(B,page,date_begin,date_end,sortby,filterby,searchbar_sortings,searchbar_filters,domain=None,url='/my/timecards',model='ez.time.card',page_name='timecard'):C=model;A=B._prepare_my_values(page,date_begin,date_end,sortby,filterby,searchbar_sortings,searchbar_filters,domain=domain,url=url,model=C,page_name=page_name);A['model']=C;A.update(B._get_timecard_counters());return A
	@http.route(['/my/timecards','/my/timecards/<int:approve>','/my/timecards/<int:approve>/page/<int:page>'],type='http',auth='user',website=True)
	def portal_my_timecards(self,page=1,approve=None,date_begin=None,date_end=None,sortby=None,filterby=None,search=None,search_in=None,**Q):
		H=date_end;G=date_begin;F=filterby;E=search;D=approve;C=search_in;B=self;G=False;H=False;I=B._get_timecard_domain(approve=D);N=B._get_timecard_searchbar_sortings();O=B._get_timecard_searchbar_filters();P=B._timecard_get_searchbar_inputs()
		if D and not F:F='f1_to_approve'
		if not C:C='all'
		if E:I+=B._timecard_get_search_domain(C,E)
		if D:J='/my/timecards/1'
		else:J='/my/timecards/0'
		A=B._timecard_prepare_my_values(page,G,H,sortby,F,N,O,domain=I,url=J)
		if A['pager']:
			K={'search_in':C,'search':E}
			if'url_args'not in A['pager']:A['pager']['url_args']=K
			else:A['pager']['url_args'].update(K)
		L=portal_pager(**A['pager']);M=A['records'](L['offset']);request.session['my_timecards_history']=M.ids[:100];A.update({'records':M,'pager':L,'searchbar_inputs':P,'search_in':C,'search':E,'approve':D and 1 or 0});return request.render('ez_payroll_ess.portal_my_timecards',A)
	@http.route(['/my/timecard/<int:timecard_id>','/my/timecard/<int:timecard_id>/<int:approve>'],type='http',auth='user',website=True)
	def portal_my_timecard_detail(self,timecard_id,approve=0,access_token=None,report_type=None,download=False,**G):
		D=approve;C=timecard_id;H=request.env['hr.employee'].sudo();I=request.env['ez.time.card'].sudo();J=request.env['ez.shift'].sudo();K=request.env['ez.time.record'].sudo();E=self._get_timecard_domain(approve=D);E.append(('id','=',int(C)));A=I.search(E,limit=1)
		if C:F=A.employee_id
		else:F=H.search([('work_email','=',request.env.user.login)],limit=1)
		L=fields.Date.today();M=J.search([]);B=self._timecard_get_page_view_values(A,access_token,**G);B.update({'timecard':A,'employee_id':F,'current_date':L,'approve':D and 1 or 0,'shift_ids':M,'day_type_selections':K._get_day_type_selection()});_logger.debug('portal_my_timecard_detail: values=%s',B);return request.render('ez_payroll_ess.portal_timecard_detail',B)
	@http.route('/submitted/timecard/<int:approve>',type='http',auth='user',website=True,csrf=True)
	def submit_timecard(self,approve,**B):
		E=approve;_logger.debug('submit_timecard: %s',B);G=request.env['ez.time.card'].sudo();A=G.browse(int(B.get('timecard_id')or 0));C=B.get('btn_submit')
		if C=='Back':_logger.debug('submit_timecard: Back approve=%s',E);return request.redirect('/my/timecards/%s'%E)
		elif A:
			if E:
				if A.state in['sent','approved']:
					if C=='Approve':
						A.state='approved'
						for F in A.details:F.done=True
						A.summarize()
					elif C=='Deny':A.state='denied'
				_logger.debug('submit_timecard: Approval %s',A.state)
			elif C=='Submit':D={'date1':B.get('date1'),'date2':B.get('date2'),'shift_id':int(B.get('shift_id'))};A.write(D);A.onchange_shift_id();A.gen_default_lines();_logger.debug('submit_timecard: Submit %s',D)
			elif C=='Attendance Fill'and A.state=='draft':A.fill_from_attendance()
			elif C=='For Approval'and A.state=='draft':D={'date1':B.get('date1'),'date2':B.get('date2'),'shift_id':int(B.get('shift_id')),'state':'sent'};_logger.debug('submit_timecard: For Approval %s',D);A.write(D);A.onchange_shift_id();A.summarize()
			elif C=='Back to Draft'and A.state=='denied':
				A.state='draft'
				for F in A.details:F.done=False
				_logger.debug('submit_timecard: Back to Draft')
			return request.redirect('/my/timecard/%s/%s'%(A.id,E))
		else:
			if C=='Create New'and not E:H=int(B.get('employee_id',0))or False;D={'employee_id':H,'date1':B.get('date1'),'date2':B.get('date2'),'shift_id':int(B.get('shift_id')),'state':'draft'};A=G.create(D);A.onchange_employee();A.gen_default_lines();_logger.debug('submit_timecard: Create New %s',D);return request.redirect('/my/timecard/%s/%s'%(A.id,E))
			return request.redirect('/my/timecards/%s'%E)
	@http.route('/my/timecard/unlink',methods=['POST'],type='jsonrpc',auth='user',cors='*')
	def portal_my_timecard_unlink(self,**A):B=self._get_timecard_domain(approve=0)+[('state','=','draft')];return self._unlink_records(False,A,domain=B,model='ez.time.card')
	@http.route('/my/timerecord/get/<int:trec_id>',methods=['POST'],type='jsonrpc',auth='user',cors='*')
	def portal_get_timerecord(self,trec_id,**E):
		def B(rec):return[rec.id,rec.display_name]
		C=request.env['ez.time.record'].sudo();D=[('company_id','=',request.env.company.id),('id','=',trec_id),'|',('employee_id.timekeeping_manager_id','=',request.env.user.id),('employee_id.work_email','=',request.env.user.login)];A=C.search(D,limit=1);return{'employee_id':B(A.employee_id),'name':A.name,'day_type':A.day_type,'schedule':A.schedule,'timelog':A.timelog,'auth_hrs':A.auth_hrs,'vnorm_time':A.vnorm_time,'vot_time':A.vot_time,'vremarks':A.vremarks,'note':A.note,'state':A.state}
	def _get_timerecord(C,trec_id):A=request.env['ez.time.record'].sudo();B=[('id','=',trec_id),('company_id','=',request.env.company.id),('state','=','draft'),('employee_id.work_email','=',request.env.user.login)];return A.search(B,limit=1)
	@http.route('/my/timerecord/write/<int:trec_id>',methods=['POST'],type='jsonrpc',auth='user',cors='*')
	def portal_write_timerecord(self,trec_id,**B):
		A=self._get_timerecord(trec_id)
		if A:_logger.debug('portal_write_timerecord: kw=%s id=%s',B,A.id);A.write(B);A.onchange_timelog();return True
		else:return False
	@http.route(['/my/timerecord/unlink','/my/timerecord/unlink/<int:rec_id>'],methods=['POST'],type='jsonrpc',auth='user',cors='*')
	def portal_unlink_timerecord(self,rec_id=False,**A):B=[('company_id','=',request.env.company.id),('state','=','draft'),('employee_id.work_email','=',request.env.user.login)];return self._unlink_records(rec_id,A,domain=B,model='ez.time.record')