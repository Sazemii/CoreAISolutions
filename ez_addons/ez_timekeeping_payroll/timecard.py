from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
from datetime import datetime,date
from dateutil.relativedelta import relativedelta
import time,base64,logging
_logger=logging.getLogger(__name__)
class TimeRecordDetailInherit(models.Model):_inherit='ez.time.record';payslip_id=fields.Many2one('hr.ph.payslip','Payslip',readonly=True,ondelete='set null',copy=False);payroll_id=fields.Many2one(related='payslip_id.payroll_id',string='Payroll Link')
class Employee(models.Model):
	_inherit='hr.employee'
	@api.model
	def get_dtr_lines(self,employee_id,date1,date2):A=self.env['ez.time.record'].search([('employee_id','=',employee_id),('state','=','approved'),('date','>=',date1),('date','<=',date2)]);B=A.summarize_time_record(A);return A,B
class TimeCardReport(models.TransientModel):
	_name='wz.timecard.report';_description='Wizard for Time Card Report'
	def start_month(A):return fields.Date.today().replace(day=1)
	def end_month(A):return A.start_month()+relativedelta(months=1)-relativedelta(days=1)
	date1=fields.Date('Date From',required=True,default=start_month);date2=fields.Date('Date To',required=True,default=end_month);category_ids=fields.Many2many('hr.employee.category','wz_timecard_report_category_rel','report_id','category_id',groups='hr.group_hr_manager',string='Tags');group_ids=fields.Many2many('ez.employee.group','wz_timecard_report_group_rel','report_id','group_id',groups='hr.group_hr_manager',string='Groups');pdf_data=fields.Binary(string='PDF Report',readonly=True);pdf_filename=fields.Char(string='PDF Report Filename')
	def generate_report(A):
		if A.date1>A.date2:raise ValidationError(_('Dates must be inclusive.'))
		if A.date1+relativedelta(months=2)<=A.date2:raise ValidationError(_('Dates must be less than 2 months.'))
		H=A.env.context;I=A._name;J=A.env.ref('ez_timekeeping_payroll.form_wizard_timecard_report').id;filter=[];D=[A.id for A in A.group_ids];E=[A.id for A in A.category_ids]
		if D:filter.append(('group_ids','in',D))
		if E:filter.append(('category_ids','in',E))
		B=A.env['hr.employee'].search(filter);_logger.debug('EMPS: %s',len(B.ids))
		if 1:F=A.env['ez.time.card'].search([('state','=','approved'),('employee_id','in',B.ids),'|','&',('date1','>=',A.date1),('date2','<=',A.date2),'&',('date1','<=',A.date1),('date2','>=',A.date2),'|','&',('date1','<=',A.date1),('date2','<=',A.date2),'&',('date1','>=',A.date1),('date2','>=',A.date2)],order='employee_id,date1');_logger.debug('TCS: %s',len(F.ids));C=A.env.ref('ez_timekeeping.timecard_report');G,K=C._render_qweb_pdf('ez_timekeeping.print_timecard',res_ids=F.ids)
		else:B=A.env['ez.time.record'].search([('id','in',B.ids),('company_id','=',A.env.user.company_id.id)],order='employee_id,date');C=A.env.ref('ez_timekeeping_payroll.timecard_wz_report');L={'date1':A.date1,'date2':A.date2,'day_types':A.env['ez.time.record']._get_day_type_selection(),'day_type_names':A.env['ez.time.record']._get_day_type_names(),'date_range':fields.Date.from_string(A.date1).strftime('%m/%d/%Y to ')+fields.Date.from_string(A.date2).strftime('%m/%d/%Y')};G,K=C._render_qweb_pdf('ez_timekeeping_payroll.print_wz_timecard',res_ids=B.ids,data=L)
		A.pdf_data=base64.b64encode(G).decode();return{'name':_('Time Card Report'),'type':'ir.actions.act_window','view_mode':'form','res_model':I,'target':'new','context':H,'res_id':A.id,'view_id':J}