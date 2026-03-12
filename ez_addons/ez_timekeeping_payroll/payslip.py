from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
import time,logging
_logger=logging.getLogger(__name__)
DEBUG=0
def dprint(s):_logger.debug(s)
def get_dhm(minutes):
	A=minutes
	if A:B=A%480;D=(A-B)/480;C=B%60;E=(B-C)/60;return D,E,C
	else:return 0,0,0
class PayslipInherit(models.Model):
	_inherit='hr.ph.payslip'
	def action_view_timerecords(A):A.ensure_one();return{'name':'Time Records','res_model':'ez.time.record','type':'ir.actions.act_window','view_mode':'list','domain':[('employee_id','=',A.employee_id.id),('date','>=',A.date_from),('date','<=',A.date_to)],'target':'current'}
	@api.model
	def custom_compensation(self,payslip_id,val):
		if payslip_id.salary_rate_period=='monthly':
			if val['name']=='Special Holiday Work':A=self.env['ir.config_parameter'].sudo().get_param('ez_timekeeping_payroll.sh_work_factor','0.3');val['factor']=float(A)
	@api.model
	def get_compensation_lines(self):A=super(PayslipInherit,self).get_compensation_lines();B=self.get_timecard_compensation_lines();return A+B
	@property
	def WORK_TYPE_KEYS(self):return['norm','norm_night','ot','ot_night']
	@property
	def WORK_TYPE_LOOKUP(self):return{'wt_reg_norm':'Regular','wt_reg_norm_night':'Night Differential','wt_reg_norm_night2':'Night Work','wt_reg_absent':'Absent','wt_reg_shutdown':'Shutdown','wt_reg_late':'Late','wt_reg_undertime':'Undertime','wt_reg_ot':'Regular Overtime','wt_reg_ot_night':'Regular Overtime (night)','wt_do_norm':'Restday Work','wt_do_norm_night':'Restday Work (night)','wt_do_ot':'Restday Overtime','wt_do_ot_night':'Restday Overtime (night)','wt_lh_norm':'Regular Holiday Work','wt_lh_norm_night':'RH Work (night)','wt_lh_ot':'RH Overtime','wt_lh_ot_night':'RH Overtime (night)','wt_sh_norm':'Special Holiday Work','wt_sh_norm_night':'SH Work (night)','wt_sh_ot':'SH Work Overtime','wt_sh_ot_night':'SH Work Overtime (night)','wt_reg_norm_night':'Night','wt_reg_norm_night':'Night','wt_reg_norm_night':'Night'}
	@property
	def WORK_TYPE_REFS(self):
		A=self;D=A.env['ez.time.record']._get_day_type_selection();E=A.WORK_TYPE_KEYS;B={}
		for F in D:
			G=F[0]
			for H in E:
				C='%s_%s'%(G,H)
				try:B[C]=A.env.ref('ez_payroll.wt_%s'%C)
				except:pass
		return B
	@api.model
	def _get_holiday_paid(self):0
	@api.model
	def get_timecard_compensation_lines(self):
		B=self;V=time.time();N=[];O=[];W=B.env['ez.time.record']._get_day_type_selection();Q=B.WORK_TYPE_REFS
		for X in['absent','late','undertime']:F='reg_%s'%X;Q[F]=B.env.ref('ez_payroll.wt_%s'%F)
		Y=int(B.env['ir.config_parameter'].sudo().get_param('ez_timekeeping.is_monthly_holiday_paid','0'));Z=int(B.env['ir.config_parameter'].sudo().get_param('ez_timekeeping.is_no_holiday_if_absent_before','1'));a=int(B.env['ir.config_parameter'].sudo().get_param('ez_timekeeping.is_no_holiday_if_absent_after','1'))
		for A in B:
			if A.payroll_id.is_13th_month:continue
			H=B.env['ez.time.record'].search([('employee_id','=',A.employee_id.id),('state','=','approved'),('date','>=',fields.Date.from_string(A.date_from)-relativedelta(days=5)),('date','<=',A.date_to+relativedelta(days=5))]);b=fields.Date.from_string(A.date_from);c=fields.Date.from_string(A.date_to)
			if A.salary_rate_period!='monthly'or Y:
				E=0;J=0;R='x';K=False
				for C in H:
					if K and C.day_type=='reg':
						K=False
						if not C.timelog and a:E=0
						elif E>0:J+=E
						E=0
					if C.date>=b and C.date<=c and C.day_type in['lh','do_lh']:
						if R or not Z:_logger.debug('HOL %s: prev log is not absent',C.date);E+=1;K=True
					elif C.day_type=='reg':R=C.timelog
				if K and E>0:J+=E
				if J>0:D={'payslip_id':A.id,'seq':500,'name':'Regular Holiday Paid','computed':True,'qty':J,'unit':'day','factor':1.,'basic_pay':False,'taxable':True};B.custom_compensation(A,D);d=True;N.append(D)
			H=B.env['ez.time.record'].search([('employee_id','=',A.employee_id.id),('state','=','approved'),('date','>=',A.date_from),('date','<=',A.date_to)]);e=H.summarize_time_record(H);S=0
			for f in W:
				L=f[0];I=e.get(L)
				if I:
					if L=='reg':
						if A.salary_rate_period=='monthly':P=['norm_night','absent','late','undertime','ot','ot_night']
						else:
							T=I.get('norm_night')
							if T:I['norm']=I.get('norm',0)+T
							P=['norm','norm_night','ot','ot_night']
					else:P=['norm','norm_night','ot','ot_night']
					for F in P:
						M=I.get(F);G=Q.get('%s_%s'%(L,F));_logger.debug('Processing %s_%s...',L,F)
						if G and M:
							S+=10;D={'payslip_id':A.id,'seq':S,'name':G.name,'computed':True,'factor':G.factor,'basic_pay':G.basic_pay,'taxable':G.taxable};B.custom_compensation(A,D)
							if M>=60:D.update({'qty':M/6e1,'unit':'hour'})
							else:D.update({'qty':M,'unit':'minute'})
							_logger.debug('dtr payslip compute: %s f=%s',D,G.factor);d=True;N.append(D)
			if 1:
				for C in H:O.append(B.env.cr.mogrify('(%s,%s)',(C.id,A.id)).decode('utf-8'))
		if O:U="\n                UPDATE ez_time_record AS t SET\n                    payslip_id = c.payslip_id,\n                    write_uid = %s,\n                    write_date = NOW() at time zone 'UTC'\n                FROM (\n                    VALUES %s\n                ) AS c(id, payslip_id)\n                WHERE c.id = t.id;\n            "%(B.env.uid,','.join(O));_logger.debug('update sql: %s',U);B.env.cr.execute(U);B.env['ez.time.record'].invalidate_recordset()
		_logger.debug('timekeeping get_compensation_lines: %s',time.time()-V);return N