from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import base64,time,logging
_logger=logging.getLogger(__name__)
class TimeRecordDetail(models.Model):
	_inherit='ez.time.record';auth_hrs=fields.Float(readonly=True)
	def _extend_process_new_records(A,reqs,update_timecards):0
	def _process_new_records(D):
		N=time.time();I=[];J=[]
		for A in D:I.append(A.employee_id.id);J.append(A.date)
		F={};H={};K=D.env['ez.time.request'].search([('state','=','approved'),('employee_id','in',I),('date','in',J)])
		for B in K:
			C='%s-%s'%(B.employee_id.id,fields.Date.to_string(B.date))
			if B.type=='ot':
				if B.state=='approved':F[C]=B.auth_hrs
				else:F[C]=.0
			elif B.type=='ob':
				if B.state=='approved':
					if B.auth_hrs:F[C]=B.auth_hrs
					H[C]=B.time
				else:F[C]=.0;H[C]=''
		G=D.env['ez.time.card']
		for A in D:
			C='%s-%s'%(A.employee_id.id,fields.Date.to_string(A.date));L=F.get(C,.0);O=E=H.get(C,'')
			if L!=A.auth_hrs:A.auth_hrs=L
			if E and E!=A.timelog:
				if E:
					if A.timelog and'ERR'in A.timelog:raise _('Cannot approve. There are errors in employee timecard on this date.')
					M=D.env['ez.time.record'];P=M.timestr_to_timepair(E);Q=M.timestr_to_timepair(A.timelog);R=P+Q
					if O:E=R.to_str()+' OB';A.done=True
				_logger.debug('** timelog %s: %s',C,E);A.timelog=E;G|=A.timecard_id
		D._extend_process_new_records(K,G)
		if G:_logger.debug('_process_new_records: fill_time_logs');G.fill_time_logs(process_new_records=False);G.summarize(ignore_error=True)
		_logger.debug('add requests: %s seconds',time.time()-N);return super(TimeRecordDetail,D)._process_new_records()