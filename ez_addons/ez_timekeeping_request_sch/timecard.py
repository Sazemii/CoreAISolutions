from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
import logging
_logger=logging.getLogger(__name__)
class TimeRecordDetail(models.Model):
	_inherit='ez.time.record'
	def _extend_process_new_records(I,reqs,update_timecards):
		L={};M={}
		for C in reqs:
			D='%s-%s'%(C.employee_id.id,fields.Date.to_string(C.date))
			if C.type=='sch':
				if C.day_type:L[D]=C.day_type
				if C.schedule:M[D]=C.schedule
		N=I.env['ez.time.record'];O=I.env['ez.time.record']
		for A in I:
			D='%s-%s'%(A.employee_id.id,fields.Date.to_string(A.date));J=M.get(D,'')
			if J!=A.schedule:
				if J:A.schedule=J
				else:N|=A
			E=L.get(D,False)
			if E!=A.day_type:
				if E:A.day_type=E
				else:O|=A
		for B in N:
			G=B.timecard_id;K=G._get_schedule();H=fields.Date.to_string(B.date);F=K.get(H)
			if F:B.schedule=F.schedule
		for B in O:
			G=B.timecard_id;K=G._get_schedule();P=G._get_holidays();H=fields.Date.to_string(B.date);F=K.get(H)
			if F:E=F.get_day_type(H,P);B.day_type=E
			else:B.day_type='reg'