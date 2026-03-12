from collections import OrderedDict
from operator import itemgetter
from odoo import _,http
from odoo.exceptions import AccessError,MissingError
from odoo.http import request
from odoo.tools import groupby as groupbyelem
from datetime import datetime
import json,pprint,random,hashlib,logging
_logger=logging.getLogger(__name__)
class AppController(http.Controller):
	def _get_employee_id(C):A=request.env['hr.employee'].sudo();B=A.search([('company_id','=',request.env.company.id),('work_email','=',request.env.user.login)],limit=1);return B.id
	@http.route('/ess/payslips',type='jsonrpc',methods=['POST'],auth='user')
	def ess_payslips(self,**A):_logger.debug('ess_payslips: %s',A);B=request.env['hr.ph.payslip'].sudo();C=A.get('limit',None);D=A.get('offset',None);E=A.get('fields',['name']);F=B.search_read([('employee_id','=',self._get_employee_id())],E,order='date_to desc',limit=C,offset=D);return F
	@http.route('/ess/attendance',type='jsonrpc',methods=['POST'],auth='user')
	def ess_attendance(self,**D):
		_logger.debug('ess_attendance: %s',D);B=self._get_employee_id()
		if not B:return{}
		E=request.env['hr.employee'].sudo();F=request.env['hr.attendance'].sudo();A=E.browse(B);C=F.search([('employee_id','=',B)],order='check_in desc',limit=1);G={'employee_id':A.id,'employee_name':A.name,'employee_picture':A.avatar_512,'check_in_ids':[[A.name,A.latitude,A.longitude,A.radius]for A in A.check_in_ids],'check_out_ids':[[A.name,A.latitude,A.longitude,A.radius]for A in A.check_out_ids],'last_log':[C.check_in,C.check_out],'last_log_id':C.id};return G
	@http.route('/ess/attendance_log',type='jsonrpc',methods=['POST'],auth='user')
	def ess_attendance_log(self,**A):
		_logger.debug('ess_attendance_log: %s',A);C=A.get('is_checkin',False);F=self._get_employee_id()
		if not F:return 0
		_logger.debug('ess_attendance_log is_checkin: %s',C);G=request.env['hr.attendance'].sudo()
		if C:D={'check_in':datetime.now(),'employee_id':F};D.update(A.get('create',{}));_logger.debug('ess_attendance_log create: %s',D);G.create(D);return 1
		H=A.get('update_id')
		if not C and H:E={'check_out':datetime.now()};E.update(A.get('update',{}));_logger.debug('ess_attendance_log update: %s',E);B=G.browse(int(H));_logger.debug('ess_attendance_log att %s: in=%sm out=%s',B.id,B.check_in,B.check_out);B.write(E);return 2
	@http.route('/ess/get_config',type='jsonrpc',methods=['POST'],auth='user')
	def ess_get_config(self,**D):
		E=request.env['ez.time.record'].sudo();B=request.env['ir.config_parameter'].sudo().get_param('kinsenas_ess.config');C=False
		if B:
			try:A=json.loads(B);C=True
			except:C=False;_logger.debug('ess_get_config: wrong json format %s',B)
		if not C:A={'tab_attendance':True,'tab_payslips':True,'tab_requests':False,'tab_timeoffs':False,'config_attendance':{'enable_check_button':True}}
		A.update({'selections_day_type':E._get_day_type_selection(),'selections_request_type':[['ot','Overtime'],['sch','Change Schedule'],['ob','Official Business']]});_logger.debug('ess_get_config: %s res=%s',D,A);return A
	@http.route('/ess/requests',type='jsonrpc',methods=['POST'],auth='user')
	def ess_requests(self,**A):D=request.env['ez.time.request'].sudo();E=A.get('limit',None);F=A.get('offset',None);G=A.get('fields',['name']);B=A.get('domain',[]);B=[('employee_id','=',self._get_employee_id())]+B;C=D.search_read(B,G,order='date desc, type',limit=E,offset=F);_logger.debug('ess_requests emp=%s: param=%s res=\n%s',self._get_employee_id(),A,pprint.pformat(C));return C
	@http.route('/ess/request/update',type='jsonrpc',methods=['POST'],auth='user')
	def ess_request_update(self,**C):
		D=request.env['ez.time.request'].sudo();id=C.get('id',-1);B=C.get('vals',{})
		if id==0:B.update({'employee_id':self._get_employee_id()});A=D.create(B);_logger.debug('ess_request_update rec=%s: create=\n%s',A.id,pprint.pformat(B))
		else:E=[('employee_id','=',self._get_employee_id()),('id','=',id)];A=D.search(E);A.update(B);_logger.debug('ess_request_update rec=%s: update=\n%s',A.id,pprint.pformat(B))
		if A.type=='ob':A.onchange_time()
		elif A.type=='sch':A.onchange_sched()
		_logger.debug('ess_request_update result=%s: time=\n%s',A.id,A.time);return A.id
	@http.route('/ess/request/delete',type='jsonrpc',methods=['POST'],auth='user')
	def ess_request_delete(self,**A):
		B=request.env['ez.time.request'].sudo();id=A.get('id')
		if id:C=[('employee_id','=',self._get_employee_id()),('id','=',id)];D=B.search(C);D.unlink();return True
		else:return False
	@http.route('/ess/request/submit',type='jsonrpc',methods=['POST'],auth='user')
	def ess_request_submit(self,**B):
		C=request.env['ez.time.request'].sudo();id=B.get('id')
		if id:
			D=[('employee_id','=',self._get_employee_id()),('id','=',id)];A=C.search(D)
			if A.state=='draft':A.state='sent';return True
		return False
	@http.route('/ess/timeoffs',type='jsonrpc',methods=['POST'],auth='user')
	def ess_timeoffs(self,**A):_logger.debug('ess_timeoffs: %s',A);D=request.env['hr.leave'].sudo();E=A.get('limit',None);F=A.get('offset',None);B=A.get('fields',['name']);G=self._get_employee_id();C=[('employee_id','=',G)];C+=A.get('domain',[]);B=A.get('fields',['name']);H=D.search_read(C,B,order='date_from desc',limit=E,offset=F);return H
	@http.route('/ess/timeoff/leave_types',type='jsonrpc',methods=['POST'],auth='user')
	def ess_leave_types(self,**A):
		_logger.debug('ess_leave_types: %s',A);B=self._get_employee_id()
		if not B:return[]
		D=A.get('fields',['name']);E=A.get('limit',100);C=['|',['requires_allocation','=','no'],'&',['has_valid_allocation','=',True],'|',['allows_negative','=',True],'&',['virtual_remaining_leaves','>',0],['allows_negative','=',False]];C+=A.get('domain',[]);F=A.get('date_from',datetime.today().strftime('%Y-%m-%d'));G=A.get('date_to',datetime.today().strftime('%Y-%m-%d'));H=A.get('context',{'employee_id':B,'default_date_from':F,'default_date_to':G});I=request.env['hr.leave.type'].with_context(H).sudo();J=I.search_read(C,D,limit=E);return J
	@http.route('/ess/timeoff/update',type='jsonrpc',methods=['POST'],auth='user')
	def ess_timeoff_update(self,**C):
		D=request.env['hr.leave'].sudo();id=C.get('id',-1);A=C.get('vals',{})
		if id==0:A.update({'employee_id':self._get_employee_id()});B=D.create(A);_logger.debug('ess_timeoff_update rec=%s: create=\n%s',B.id,pprint.pformat(A))
		else:E=[('employee_id','=',self._get_employee_id()),('id','=',id)];B=D.search(E);_logger.debug('ess_timeoff_update rec=%s: update=\n%s',B.id,pprint.pformat(A));B.update(A)
		return B.id
	@http.route('/ess/timeoff/delete',type='jsonrpc',methods=['POST'],auth='user')
	def ess_timeoff_delete(self,**A):
		B=request.env['hr.leave'].sudo();id=A.get('id')
		if id:C=[('employee_id','=',self._get_employee_id()),('id','=',id)];D=B.search(C);D.unlink();return True
		else:return False