from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
from odoo.modules.registry import Registry
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools.safe_eval import safe_eval
import threading,logging,time
_logger=logging.getLogger(__name__)
class TimeCardBatch(models.TransientModel):
	_name='wz.timecard.batch';_description='Wizard for Batch Timecard Processes'
	def start_month(A):return fields.Date.today().replace(day=1)
	def end_month(A):return A.start_month()+relativedelta(months=1)-relativedelta(days=1)
	company_id=fields.Many2one('res.company',string='Company',default=lambda self:self.env.company);date1=fields.Date('Date From',required=True,default=start_month);date2=fields.Date('Date To',required=True,default=end_month);skip_no_shift=fields.Boolean('Skip No Shift',default=True);batch_running=fields.Boolean('Running',compute='get_running_state');run_background=fields.Boolean('Background',default=False,help='Run in background.')
	@api.depends('date1','date2','skip_no_shift')
	def get_running_state(self):
		A=self.read_running_state_param()
		for B in self:B.batch_running=A
	@api.model
	def read_running_state_param(self):
		A=self.sudo().env.ref('ez_timekeeping.batch_active')
		if A:B=safe_eval(A.value)
		else:B=True
		return B
	@api.model
	def get_employees(self,company_id,skip_no_shift):
		A=[('company_id','=',company_id),('exclude_create_timecard','=',False)]
		if skip_no_shift:A.append(('shift_id','!=',False))
		B=self.sudo().env['hr.employee'].search(A);return B
	def generate_timecards(A):
		A.ensure_one()
		if A.read_running_state_param():raise ValidationError('Batch process is still running.  Please wait until it is done.')
		if not A.date1 or not A.date2 or A.date1>A.date2:raise ValidationError(_('Incomplete or wrong date range.'))
		C=A.env['ez.time.card'].search(['&',('company_id','=',A.company_id.id),'|','&',('date1','>=',A.date1),('date1','<=',A.date2),'&',('date2','>=',A.date1),('date2','<=',A.date2)],limit=1)
		if C:raise ValidationError(_('Timecards existing or already generated.'))
		B=A.get_employees(A.company_id.id,A.skip_no_shift)
		if not A.run_background:_logger.debug('non-thread generate timecards.');A.batch_gen_timecards(B.ids,fields.Date.to_string(A.date1),fields.Date.to_string(A.date2));time.sleep(1);return{'type':'ir.actions.client','tag':'reload'}
		else:D=threading.Thread(target=A.threaded_gen_timecards,args=(B.ids,fields.Date.to_string(A.date1),fields.Date.to_string(A.date2)));D.start()
	def threaded_gen_timecards(A,employee_ids,date1,date2):
		with Registry(A.env.cr.dbname).cursor()as B:
			D=time.time();A=A.with_env(A.env(cr=B))
			if A.read_running_state_param():_logger.debug('Batch thread is still running.');B.close();return{}
			C=A.sudo().env.ref('ez_timekeeping.batch_active');C.value='True';B.commit()
			try:A.sudo().batch_gen_timecards(employee_ids,date1,date2);C=A.sudo().env.ref('ez_timekeeping.batch_active');C.value='False';_logger.debug('threaded_gen_timecards: done %s',time.time()-D);B.commit()
			except Exception:B.rollback();C=A.sudo().env.ref('ez_timekeeping.batch_active');C.value='False';B.commit()
			finally:B.close()
		return{}
	def batch_gen_timecards(A,employee_ids,date1,date2):
		G=date2;F=date1;E=employee_ids;I=time.time();_logger.debug('Batch generate timecards: %s, %s, %s',F,G,E);J=A.sudo().env['hr.employee'].browse(E);K=A.env['ez.time.card'].search(['&',('company_id','=',A.env.user.company_id.id),'|','&',('date1','>=',A.date1),('date1','<=',A.date2),'&',('date2','>=',A.date1),('date2','<=',A.date2)]);H=set()
		for L in K:H.add(L.employee_id.id)
		C=[]
		for D in J:
			if D.id not in H:B=A.env['ez.time.card'].create({'employee_id':D.id,'date1':F,'date2':G,'shift_id':D.shift_id.id});B.onchange_shift_id();C.append(B.id)
		_logger.debug('tc created %s records: %s',len(C),time.time()-I)
		if C:B=A.env['ez.time.card'].browse(C);B.gen_default_lines();B.summarize()
	def update_summary(A):A.ensure_one();B=A.env['ez.time.card'].search(['&',('company_id','=',A.env.user.company_id.id),'|','&',('date1','>=',A.date1),('date1','<=',A.date2),'&',('date2','>=',A.date1),('date2','<=',A.date2)]);B.summarize()