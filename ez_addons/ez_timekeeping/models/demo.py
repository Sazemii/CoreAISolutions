from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
from datetime import*
from dateutil.relativedelta import*
import logging
_logger=logging.getLogger(__name__)
class TimeCard(models.Model):
	_inherit='ez.time.card'
	@api.model
	def X_create_demo_record(self,vals):res=super(TimeCard,self).create(vals);res.gen_default_lines();res.summarize();return res
	@api.model
	def demo_add_emp_shift(self):
		Employee=self.env['hr.employee'];Timecard=self.env['ez.time.card'];s=self.env.ref('ez_timekeeping.day_shift');s.create_details();emps=Employee.search([('shift_id','=',False)]);_logger.debug('demo_add_emp_shift: %s',len(emps))
		for e in emps:e.shift_id=s.id
		last_month=fields.Date.today().replace(day=1)-relativedelta(months=1);self.env['ez.holiday'].create_holiday_year(last_month.year)
		if 0:
			dates=[(last_month,last_month+relativedelta(days=14)),(last_month.replace(day=16),last_month+relativedelta(months=1,days=-1))];employee_ids=Employee.search([])
			for dt in dates:
				d1,d2=dt
				for e in employee_ids:timecard=Timecard.create({'employee_id':e.id,'date1':d1,'date2':d2,'shift_id':e.shift_id.id});timecard.onchange_shift_id();timecard.gen_default_lines_nodemo();timecard.summarize();timecard.approve_record()