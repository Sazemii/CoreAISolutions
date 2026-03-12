from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
import xlrd,base64
from io import BytesIO
from datetime import datetime
import pprint,logging
_logger=logging.getLogger(__name__)
def chunks(data,chunksize):
	A=chunksize
	for B in range(0,len(data),A):yield data[B:B+A]
def format_id(s):return s.lower().strip().replace(' ','_').replace('-','_').replace('.','_').replace('&','_').replace(',','_').replace(':','_')
def time_to_float(time_str):
	A=time_str.split(':')
	if len(A)==1:A.append('0')
	B=int(A[0])+int(A[1])/6e1;return B
def float_to_time(dt,val):A=dt+' {0:02.0f}:{1:02.0f}'.format(*divmod(val*60,60));return A
def parse_time(tm):
	if not tm or len(tm)<2:return[]
	else:return[tm[0],tm[-1]]
class ImportWizard(models.TransientModel):
	_name='ez.attendance.log.wizard';_description='Attendance Import Wizard';xls_file=fields.Binary('Excel (xlsx) File');xls_filename=fields.Char();notes=fields.Text()
	def _import_attendance_xls(F,sh):
		A={};D=[]
		for G in range(1,sh.nrows):
			B=sh.row(G);H=B[0].value;I=[time_to_float(A)for A in B[4].value.split()];E=parse_time(I)
			if E:D.append([H,datetime.strptime(B[3].value,'%m/%d/%Y').strftime('%Y-%m-%d'),E])
		J=F.env['hr.employee'].search([]);A={}
		for C in J:A[C.barcode]=[C.id,C.name]
		return A,D
	def _update_attendance(E,employees,logs):
		F=['id','employee_id','check_in','check_out'];C=[]
		for A in logs:
			D=employees.get(A[0])
			if D:
				G=0
				for B in chunks(A[2],2):
					if B:H=['__import__.attendance_%s_%s_%s'%(D[0],format_id(A[0]),format_id(float_to_time(A[1],B[0]))),D[1],float_to_time(A[1],B[0]),float_to_time(A[1],B[1])];C.append(H);G+=1
		_logger.debug('Load:\n%s',pprint.pformat(C));I=E.env['hr.attendance'];I.load(F,C)
	def action_xls_import(A):
		G=base64.b64decode(A.xls_file);H=BytesIO(G)
		try:E=xlrd.open_workbook(file_contents=H.getvalue())
		except:raise ValidationError(_('Wrong excel format.'))
		B=E.sheet_by_index(0)
		if B.row(0)[0].value=='Staff'and B.row(0)[1].value=='In Date':F='UTAK'
		else:F='QUEST'
		if F=='UTAK':_logger.debug('UTAK: %s',B.row(0));A._import_attendance_utak(E,B)
		else:
			C,D=A._import_attendance_xls(B);A._update_attendance(C,D);A.notes='emp=%s logs=%s'%(len(C),len(D));_logger.info('XLS Import Quest: %s',C)
			if not D:raise ValidationError(_('No logs found.'))
		if not A.xls_file:raise ValidationError(_('Please upload biometrics file.'))
		if 1:return{'type':'ir.actions.client','tag':'reload'}
		else:I=A.env.context;J=A._name;return{'name':_('Biometrics Import'),'type':'ir.actions.act_window','context':I,'view_type':'form','view_mode':'form','res_model':J,'res_id':A.id,'view_id':A.env.ref('ez_timekeeping_attendance.form_attendance_import_wizard').id,'target':'new'}
	def _import_attendance_utak(I,wb,sh):
		C=wb
		def D(wb,rdate,rtime):
			C=rtime;B=rdate
			if B and C:A=xlrd.xldate_as_tuple(B,wb.datemode);D=xlrd.xldate_as_tuple(C,wb.datemode);return datetime(year=A[0],month=A[1],day=A[2],hour=D[3],minute=D[4]).strftime('%Y-%m-%d %H:%M:%S')
			else:return False
		def G(data):
			if B and F:A=[id,H,B,F];data.append(A);_logger.debug('%s',A)
		J=['id','employee_id','check_in','check_out'];E=[]
		for K in range(1,sh.nrows):
			A=sh.row(K);_logger.debug('log: %s',A);B=D(C,A[1].value,A[2].value)
			if B:
				H=A[0].value.strip();id='__import__.attendance_%s_%s'%(format_id(B),format_id(H));F=D(C,A[7].value,A[8].value)
				if F:G(E);B=D(C,A[9].value,A[10].value);F=D(C,A[3].value,A[4].value);id='__import__.attendance_%s_%s'%(format_id(B),format_id(H));G(E)
				else:F=D(C,A[3].value,A[4].value);G(E)
		if not E:raise ValidationError(_('No logs found.'))
		L=I.env['hr.attendance'];L.load(J,E)