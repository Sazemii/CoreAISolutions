from odoo import api,fields,models,tools,_,SUPERUSER_ID
from odoo.exceptions import ValidationError,UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.addons.ez_sql import execute_insert
import base64,time,re,random
from.util import parse_sched,min_to_hstr,min_to_dhstr,min_to_hstr2
from.timeutils import timestr_to_timepair,compute_worktime,get_demo_timelog
from.timepairs import TimePairs
import logging
_logger=logging.getLogger(__name__)
DF='%Y-%m-%d'
DEBUG=0
DAY_TYPES=[('reg','REG'),('do','RD'),('lh','RH'),('sh','SH'),('do_lh','RHRD'),('do_sh','SHRD')]
DAY_TYPE_NAMES={'reg':'Regular','do':'Restday','lh':'Regular Holiday','sh':'Special Holiday','do_lh':'Restday & Regular Holiday','do_sh':'Restday & Special Holiday'}
def dprint(s):_logger.debug(s)
class TimeCard(models.Model):
	_name='ez.time.card';_description='Time Card';_inherit=['mail.thread'];_order='date1 desc, employee_id'
	def _default_employee(A):return A.env.context.get('default_employee_id')or A.env['hr.employee'].search([('user_id','=',A.env.uid)],limit=1)
	state=fields.Selection([('draft','Draft'),('sent','For Approval'),('denied','Denied'),('approved','Approved')],string='State',default=lambda self:'draft',tracking=True,readonly=True);company_id=fields.Many2one('res.company','Company',related='employee_id.company_id');name=fields.Char(string='Name',compute='_name_compute',readonly=True,store=True);employee_id=fields.Many2one('hr.employee','Employee',domain=[('exclude_create_timecard','=',False)],default=_default_employee,required=True,related_sudo=True,tracking=True,index=True);category_ids=fields.Many2many(related='employee_id.category_ids',string='Tags');department_id=fields.Many2one(string='Department',readonly=True,related='employee_id.department_id');shift_id=fields.Many2one('ez.shift',string='Shift',tracking=True,default=lambda self:self._get_shift());image_1920=fields.Binary(related='employee_id.image_1920',related_sudo=True);avatar_128=fields.Binary(related='employee_id.avatar_128',related_sudo=True);edit_schedule=fields.Boolean('Edit Schedule');auto_auth=fields.Boolean('Auto-authorize',tracking=True);flex_time=fields.Boolean('Flex Time',tracking=True,help='Employees on this shift have flexible time hours.');early_overtime=fields.Boolean('Early Overtime',tracking=True,help='Employees can have overtime work earlier than schedule.');rounding_regular_work_minutes=fields.Integer('Rounding Reg. Work',tracking=True,help='Floor rounding regular work in minutes.');minimum_ot_minutes=fields.Integer(string='Minimum O.T.',tracking=True,help='Minimum time in minutes to consider as overtime.');rounding_ot_minutes=fields.Integer(string='Rounding O.T.',tracking=True,help='Time in minutes to reach rounded off overtime.');late_allowance_minutes=fields.Integer(string='Late Allowance',help='Maximum late allowance time in minutes.',tracking=True);date1=fields.Date(string='Date From',required=True,tracking=True,index=True);date2=fields.Date(string='Date To',required=True,tracking=True,index=True);note=fields.Text(string='Notes',tracking=True);details=fields.One2many('ez.time.record','timecard_id','Details');summary=fields.One2many('ez.time.card.summary','timecard_id','Summary',readonly=True);can_approve=fields.Boolean('Can Approve',compute='_compute_can_approve');is_timekeeping_user=fields.Boolean(compute='_compute_can_approve')
	@api.depends('date1','date2','employee_id')
	def _compute_display_name(self):
		for A in self:A.display_name='%s-%s (%s)'%(A.date1 and A.date1.strftime('%m/%d/%Y')or'',A.date2 and A.date2.strftime('%m/%d/%Y')or'',A.employee_id.name)
	@api.depends('state','employee_id')
	def _compute_can_approve(self):
		A=self;C=A.env.user.has_group('ez_timekeeping.group_timekeeping_manager');D=A.env.user.has_group('ez_timekeeping.group_timekeeping_user')
		for B in A.sudo():
			B.is_timekeeping_user=D
			if B.employee_id.timekeeping_manager_id.id==A.env.user.id or C:B.can_approve=True
			else:B.can_approve=False
	@api.depends('employee_id','employee_id.name','date1','date2')
	def _name_compute(self):
		for A in self:
			if A.date1 and A.date2 and A.employee_id:B=fields.Date.from_string(A.date1);C=fields.Date.from_string(A.date2);A.name='%s to %s'%(B.strftime('%b-%d-%Y'),C.strftime('%b-%d-%Y'))
			else:A.name='New Time Card'
	def unlink(A):
		for B in A:
			if B.state!='draft':raise ValidationError(_('You cannot delete a non-draft time card.'))
		return super(TimeCard,A).unlink()
	@api.model
	def _Xcreate(self,vals):A=super(TimeCard,self).create(vals);A.gen_default_lines();A.summarize();return A
	@api.onchange('employee_id')
	def onchange_employee(self):A=self;A.shift_id=A.sudo().employee_id.shift_id;A.onchange_shift_id()
	@api.onchange('shift_id')
	def onchange_shift_id(self):A=self;A.auto_auth=A.sudo().shift_id.auto_auth;A.flex_time=A.sudo().shift_id.flex_time;A.minimum_ot_minutes=A.sudo().shift_id.minimum_ot_minutes;A.late_allowance_minutes=A.sudo().shift_id.late_allowance_minutes;A.rounding_ot_minutes=A.sudo().shift_id.rounding_ot_minutes;A.rounding_regular_work_minutes=A.sudo().shift_id.rounding_regular_work_minutes;A.early_overtime=A.sudo().shift_id.early_overtime
	@api.model
	def _get_shift(self):
		A=self
		if A.employee_id:return A.sudo().employee_id.shift_id
		else:
			B=A.sudo().env['hr.employee'].search([('user_id','=',A.env.user.id)])
			if B:return B[0].sudo().shift_id
			else:return False
	@api.model
	def format_summary(self,minutes,hm_format=False):
		A=minutes
		if hm_format:return min_to_hstr(A)
		else:return min_to_hstr2(A)
	def summarize(A,ignore_error=False):
		_logger.debug('summarize: %s',A);E=time.time();F=[]
		for B in A:F+=B.summary.ids
		A.env['ez.time.card.summary'].browse(F).unlink();_logger.debug('summary unlink: time=%s',time.time()-E);L=A.env['ez.time.record']._get_day_type_names();M=A.env['ez.time.record']._get_day_type_selection();C=[]
		for B in A:
			G=B.details.summarize_time_record(B.details,ignore_error=ignore_error);_logger.debug('summarize: summary %s',G);H=0
			for I in M:
				D=G.get(I[0])
				if D:
					H+=10;J={'timecard_id':B.id,'seq':H,'name':L.get(I[0],'Undefined')}
					for K in D:J[K]=A.format_summary(D[K])
					C.append(J)
		if C:N=A.env.company.is_fast_insert();execute_insert(A.env['ez.time.card.summary'],C,fast_mode=N)
		_logger.debug('summary: done time=%s',time.time()-E)
	def approve_record(B):
		B._check_approval_update('approved');C=B.env['ez.time.card']
		for A in B:
			if A.state in['draft','sent','denied']:
				A.state='approved';C|=A
				for D in A.details:D.done=True
		_logger.debug('To summarize: %s',C);C.summarize()
	def to_denied(A):
		A._check_approval_update('denied')
		for B in A:B.state='denied'
	def to_draft(A):
		A._check_approval_update('draft')
		for B in A:
			B.state='draft'
			for C in B.details:C.done=False
	def to_sent(A):
		A._check_approval_update('sent')
		for B in A:B.state='sent'
		A.summarize()
	def del_time_lines(A):
		for B in A:
			if B.state!='draft':raise ValidationError(_('You can only delete lines on draft time cards.'))
			B.details.unlink()
		A.summarize()
	def gen_default_lines_nodemo(A):A.ensure_one();A.onchange_shift_id();A.sudo().gen_default_lines();A.sudo().summarize()
	@api.model
	def _get_holidays(self):
		A=self;A.ensure_one();B={};D=A.env['ez.holiday'].search([('date','>=',A.date1),('date','<=',A.date2)])
		for C in D:E=fields.Date.to_string(C.date);B[E]=C.type
		return B
	@api.model
	def _get_schedule(self):A=self;A.ensure_one();B=A.shift_id.get_schedule(A.date1,A.date2);return B
	def gen_default_lines(B,demo=False):
		I=time.time();_logger.debug('gen_default_lines: %s',B);O=B.env['ez.time.record'];P=B.env['ez.time.card'];D=[]
		for A in B:
			if A.state!='draft':raise ValidationError(_('You can only generate time card lines on draft time cards.'))
			if not A.shift_id:raise ValidationError(_('No shift defined. Please contact Timekeeping Officer to define employee shift.')+' %s'%A.employee_id.name)
			C=fields.Date.from_string(A.date1);J=fields.Date.from_string(A.date2);G=set()
			for K in A.details:G.add(fields.Date.from_string(K.date))
			H=A._get_holidays();_logger.debug('Holidays %s',H);L=A._get_schedule()
			while C<=J:
				E=fields.Date.to_string(C);F=L.get(E)
				if F and C not in G:M=F.get_day_type(E,H);D.append({'timecard_id':A.id,'date':E,'day_type':M,'schedule':F.schedule,'employee_id':A.employee_id.id,'identification_id':A.sudo().employee_id.identification_id})
				C+=relativedelta(days=1)
		if D:
			N=B.env.company.is_fast_insert();execute_insert(B.env['ez.time.record'],D,fast_mode=N)
			for A in B:A.details._process_new_records()
		_logger.debug('gen_default_lines: done %s',time.time()-I);B.sudo().fill_time_logs(demo=demo)
	@api.model
	def fill_time_logs(self,demo=False,process_new_records=True):
		for A in self:
			if A.state!='draft':raise ValidationError(_('You can only auto-fill logs on draft time cards. %s')%A.name)
			for B in A.details:
				if not B.done:B.get_time_logs(demo=demo)
	def _check_approval_update(A,state):
		' Check if target state is achievable. ';C=state;D=A.env['hr.employee'].search([('user_id','=',A.env.uid)],limit=1);G=A.env.user.has_group('ez_timekeeping.group_timekeeping_user');E=A.env.user.has_group('ez_timekeeping.group_timekeeping_manager')
		for B in A:
			F=B.employee_id.work_email==A.env.user.login
			if C in['draft','sent']and(B.employee_id==D or F):continue
			if not B.can_approve:raise UserError(_('You do not have approving rights.'))
			if C=='approved':
				if B.employee_id==D and not E:raise UserError(_('Only a Timekeeping Manager can approve its own time card.'))
				continue
			if C=='denied':
				if B.employee_id==D and not E:raise UserError(_('Only a Timekeeping Manager can deny its own time card.'))
				continue
	def write(B,values):
		A=values
		if A.get('state'):B._check_approval_update(A['state'])
		return super(TimeCard,B).write(A)
	def _track_template(A,changes):
		D=super()._track_template(changes);_logger.debug('TRACK: %s',A.state);C=A[0];B=False
		if C.state=='sent':B=A.env.ref('ez_timekeeping.timecard_for_approval_email_template')
		elif C.state=='denied':B=A.env.ref('ez_timekeeping.timecard_denied_email_template')
		elif C.state=='approved':B=A.env.ref('ez_timekeeping.timecard_approved_email_template')
		if B:D['stage_id']=B,{'auto_delete_keep_log':False,'subtype_id':A.env['ir.model.data']._xmlid_to_res_id('mail.mt_note'),'email_layout_xmlid':'mail.mail_notification_layout'}
		return D
STORE_COMPUTED=True
class TimeRecordDetail(models.Model):
	_name='ez.time.record';_description='Time Record';_order='date asc';_unique_emp_date=models.Constraint('UNIQUE(employee_id, date)','Duplicate date on employee timecard.\nOr date is already defined on another timecard.');timecard_id=fields.Many2one('ez.time.card','Time Card',ondelete='cascade',index=True);employee_id=fields.Many2one(string='Employee',related='timecard_id.employee_id',related_sudo=True,readonly=True,store=True);category_ids=fields.Many2many(related='timecard_id.employee_id.category_ids',string='Tags');department_id=fields.Many2one(string='Department',readonly=True,related='employee_id.department_id');company_id=fields.Many2one(string='Company',related='timecard_id.employee_id.company_id',readonly=True);identification_id=fields.Char(string='ID#',readonly=True);state=fields.Selection(related='timecard_id.state',store=False);date=fields.Date('Date',required=True,index=True);name=fields.Char(string='Day of Week',compute='_name_compute');day_type=fields.Selection(selection=lambda self:self._get_day_type_selection(),string='Type',default='reg',required=True);done=fields.Boolean('Done');edit_schedule=fields.Boolean(related='timecard_id.edit_schedule');schedule=fields.Char('Schedule',required=True,help='Enter time in pairs. Prefix with N for next day. Example: 6p 10p 11p N07:30');timelog=fields.Char('Time Log',help='Enter time in pairs. Prefix with N for next day. Example: 6p 10p 11p N07:30');note=fields.Text();auth_hrs=fields.Float(string='Auth',help='Authorized hours overtime, restday or holidays worked.');sch_minutes=fields.Integer(string='Schedule Work Minutes',compute_sudo=True,compute='_compute_work_time',store=STORE_COMPUTED);norm_minutes=fields.Integer(string='Normal Work Minutes',compute_sudo=True,compute='_compute_work_time',store=STORE_COMPUTED);norm_night_minutes=fields.Integer(string='Night Work Minutes',compute_sudo=True,compute='_compute_work_time',store=STORE_COMPUTED);ot_minutes=fields.Integer(string='Overtime Minutes',compute_sudo=True,compute='_compute_work_time',store=STORE_COMPUTED);ot_night_minutes=fields.Integer(string='Night Overtime Minutes',compute_sudo=True,compute='_compute_work_time',store=STORE_COMPUTED);late_minutes=fields.Integer(string='Late Minutes',compute_sudo=True,compute='_compute_work_time',store=STORE_COMPUTED);undertime_minutes=fields.Integer(string='Undertime Minutes',compute_sudo=True,compute='_compute_work_time',store=STORE_COMPUTED);absent_minutes=fields.Integer(string='Absent Minutes',compute_sudo=True,compute='_compute_work_time',store=STORE_COMPUTED);vnorm_time=fields.Char(string='Normal',compute='_compute_work_time',compute_sudo=True,store=STORE_COMPUTED,help='Normal time in hrs:min. Night work is with # suffix');vot_time=fields.Char(string='Overtime',compute='_compute_work_time',compute_sudo=True,store=STORE_COMPUTED,help='Overtime in hrs:min. Night work is with # suffix');vremarks=fields.Char(string='Remarks',compute='_compute_work_time',compute_sudo=True,store=STORE_COMPUTED);is_timekeeping_user=fields.Boolean(related='timecard_id.is_timekeeping_user')
	@api.model
	def _get_day_type_selection(self):return DAY_TYPES
	@api.model
	def _get_day_type_names(self):return DAY_TYPE_NAMES
	def get_time_logs(B,demo=False):
		for A in B:
			if demo:
				if A.schedule:A.timelog,A.auth_hrs=get_demo_timelog(A.schedule)
			elif A.day_type=='reg':A.timelog=A.schedule
	def get_time_demologs(B):
		for A in B:
			if A.schedule:A.timelog,A.auth_hrs=get_demo_timelog(A.schedule)
	@api.depends('date')
	def _name_compute(self):
		for A in self:
			if A.date:B=fields.Date.from_string(A.date);A.name=B.strftime('%m-%d %a')
	@api.onchange('employee_id')
	def onchange_employee_id(self):A=self;A.ensure_one();A.identification_id=A.employee_id.employee_id
	@api.onchange('schedule')
	def onchange_sched(self):
		for A in self:
			if A.schedule:
				B=parse_sched(A.schedule);C=[]
				for D in range(0,len(B),2):C.append('%s-%s'%(B[D],B[D+1]))
				A.schedule=' '.join(C)
	@api.onchange('timelog')
	def onchange_timelog(self):
		for B in self:
			'\n            #print "REC", rec.timelog, rec.timelog[0]\n            timelogs = parse_sched(rec.timelog)\n            res = []\n            for i in range(0, len(timelogs), 2):\n                if timelogs[i] < timelogs[i+1]:\n                    res.append("%s-%s" % (timelogs[i],timelogs[i+1]))\n                else:\n                    raise ValidationError(_("Wrong format."))\n            rec.timelog = " ".join(res)\n            '
			if B.timelog and B.timelog[:3]!='ERR':
				if 0:
					A=parse_sched(B.timelog);D=[]
					for C in range(0,len(A),2):
						if A[C]<A[C+1]:D.append('%s-%s'%(A[C],A[C+1]))
						else:raise ValidationError(_('Wrong format.'))
					B.timelog=B.timelog_format(D)
				else:
					G=False;E=B.timelog.strip()
					if E[-2:]=='OB':E=E[:-2];G=True
					try:
						A=parse_sched(E);D=[]
						for C in range(0,len(A),2):
							if A[C]<A[C+1]:D.append('%s-%s'%(A[C],A[C+1]))
							else:raise ValidationError(_('Wrong format.'))
						F=B.timelog_format(D)
					except:F='ERR '+B.timelog
					if G:F+=' OB'
					B.timelog=F
	def timelog_format(A,logs):return' '.join(logs)
	@api.model
	def compute_flex_worktime(self,tp_sch,tp_log,defs={},debug=False):
		C=tp_log;B=tp_sch
		if C.data:
			if B.get_minutes()>0:A=B+0;A.data[0][0]=C.data[0][0];A.data[-1][1]=A.data[-1][0];E=B.get_minutes()-A.get_minutes();A=A+E
			else:D=C.data[0][0];A=TimePairs(data=[[D,D,0]])
		else:A=B
		return compute_worktime(A,C,defs=defs,debug=debug)
	def recompute(A):
		for B in A:B._compute_work_time()
	@api.depends('day_type','schedule','timelog','auth_hrs','date','timecard_id','timecard_id.flex_time','timecard_id.auto_auth','timecard_id.minimum_ot_minutes','timecard_id.late_allowance_minutes')
	def _compute_work_time(self):
		C=self
		for A in C:
			G={'auth_hrs':min(A.auth_hrs,10000),'day_type':A.day_type,'late_allowance_minutes':A.timecard_id.late_allowance_minutes,'minimum_ot_minutes':A.timecard_id.minimum_ot_minutes!=0 and A.timecard_id.minimum_ot_minutes-1 or 0,'flex_time':A.timecard_id.flex_time,'auto_auth':A.timecard_id.auto_auth,'rounding_ot_minutes':A.timecard_id.rounding_ot_minutes,'rounding_regular_work_minutes':A.timecard_id.rounding_regular_work_minutes,'early_overtime':A.timecard_id.early_overtime,'rounding_on_out':False}
			if A.timelog and A.timelog[:3]=='ERR':A.vremarks='Wrong log format';A.sch_minutes=0;A.norm_minutes=0;A.norm_night_minutes=0;A.ot_minutes=0;A.ot_night_minutes=0;A.late_minutes=0;A.undertime_minutes=0;A.absent_minutes=0;A.vnorm_time='';A.vot_time='';continue
			else:
				I=C.env['ez.time.card'];D=timestr_to_timepair(A.schedule);H=timestr_to_timepair(A.timelog)
				if A.timecard_id.flex_time:B=C.env['ez.time.record'].compute_flex_worktime(D,H,defs=G,debug=DEBUG)
				else:B=compute_worktime(D,H,defs=G,debug=DEBUG)
			A.sch_minutes=D.get_minutes();A.norm_minutes=B['norm_minutes'];A.norm_night_minutes=B['norm_night_minutes'];A.ot_minutes=B['ot_minutes'];A.ot_night_minutes=B['ot_night_minutes'];A.late_minutes=B['late_minutes'];A.undertime_minutes=B['undertime_minutes'];A.absent_minutes=B['absent_minutes'];E=[]
			if A.norm_minutes:E.append(min_to_hstr(A.norm_minutes))
			if A.norm_night_minutes:E.append(min_to_hstr(A.norm_night_minutes)+'#')
			F=[]
			if A.ot_minutes:F.append(min_to_hstr(A.ot_minutes))
			if A.ot_night_minutes:F.append(min_to_hstr(A.ot_night_minutes)+'#')
			A.vnorm_time=' '.join(E);A.vot_time=' '.join(F);A.vremarks=B['remarks']
	@api.model
	def summarize_time_record(self,time_recs,ignore_error=False):
		B={};C=self.env['ez.time.record']._get_day_type_selection()
		for D in C:B[D[0]]={}
		for A in time_recs:
			if not ignore_error and A.timelog and A.timelog[:3]=='ERR':raise ValidationError(_('Cannot continue. There are errors on the time card.\n%s\n%s %s',A.employee_id.name,A.name,A.timelog))
			if 0:dprint('Time rec: %s dtype=%s sch=%d norm=%d night=%d ot=%d ot-night=%d late=%d ut=%d'%(A.name,A.day_type,A.sch_minutes,A.norm_minutes,A.norm_night_minutes,A.ot_minutes,A.ot_night_minutes,A.late_minutes,A.undertime_minutes))
			add_summary(B[A.day_type],'absent',A.absent_minutes);add_summary(B[A.day_type],'late',A.late_minutes);add_summary(B[A.day_type],'undertime',A.undertime_minutes);add_summary(B[A.day_type],'norm',A.norm_minutes);add_summary(B[A.day_type],'norm_night',A.norm_night_minutes);add_summary(B[A.day_type],'ot',A.ot_minutes);add_summary(B[A.day_type],'ot_night',A.ot_night_minutes)
		return B
	def parse_sched(A,schedule,def_time=None,error=True):return parse_sched(schedule,def_time=def_time,error=error)
	def timestr_to_timepair(A,time_str):return timestr_to_timepair(time_str)
	def _process_new_records(A):A._compute_work_time()
	def TimePairs(A,data=None):return TimePairs(data=data)
	def compute_worktime(A,tp_sch,tp_log,defs={},debug=DEBUG):return compute_worktime(tp_sch,tp_log,defs=defs,debug=DEBUG)
def add_summary(pdict,kname,qty):
	B=kname;A=pdict
	if qty:
		if B not in A:A[B]=0
		A[B]+=qty
def char_to_minute(value):
	B=0;C=value.split()
	for A in C:
		if'd'in A:B+=480*int(re.sub('[^0-9]','',A))
		elif'h'in A:B+=60*int(re.sub('[^0-9]','',A))
		elif'm'in A:B+=int(re.sub('[^0-9]','',A))
	return B
class TimeCardSummary(models.Model):
	_name='ez.time.card.summary';_description='Time Card Summary';_order='seq asc';timecard_id=fields.Many2one('ez.time.card','Time Card',ondelete='cascade');seq=fields.Integer(readonly=True);name=fields.Char(string='Day Type',readonly=True);norm=fields.Char(string='Normal Time',readonly=True);norm_night=fields.Char(string='Night',readonly=True);ot=fields.Char(string='Overtime',readonly=True);ot_night=fields.Char(string='Overtime Night',readonly=True);late=fields.Char(string='Late',readonly=True);undertime=fields.Char(string='Undertime',readonly=True);absent=fields.Char(string='Absent',readonly=True)
	@api.model
	def hrs(self,value):
		A=value
		if A:B=char_to_minute(A)/6e1;return round(B,4)
		else:return''