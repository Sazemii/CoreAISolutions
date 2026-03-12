from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api,fields,models
from odoo import tools,_
from odoo.exceptions import ValidationError
from datetime import*
import time,math,logging
_logger=logging.getLogger(__name__)
class PayslipInherit(models.Model):
	_inherit='hr.ph.payslip'
	@api.model
	def get_compensation_lines(self):
		res0=super(PayslipInherit,self).get_compensation_lines();t0=time.time();updates=[];leaves=self.env['hr.leave'].search([('payslip_id','in',self.ids)]);leaves.write({'payslip_id':False});res=[]
		for ps in self:
			if ps.payroll_id.is_13th_month or ps.payroll_id.initial_import:continue
			leaves=self.env['hr.leave'].search([('employee_id','=',ps.employee_id.id),('state','=','validate'),('request_date_from','<=',ps.date_to),('payslip_id','=',False)],order='date_from');seq=900
			for lv in leaves:
				if lv.holiday_status_id and not lv.holiday_status_id.unpaid:d0=fields.Datetime.from_string(lv.request_date_from);val={'payslip_id':ps.id,'name':'%s'%lv.holiday_status_id.name,'seq':seq,'computed':True,'qty':lv.number_of_days,'unit':'day','factor':1,'basic_pay':True,'taxable':True};seq+=1;res.append(val);updates.append(self.env.cr.mogrify('(%s,%s)',(lv.id,ps.id)).decode('utf-8'))
		if updates:sql="\n                UPDATE hr_leave AS t SET\n                    payslip_id = c.payslip_id,\n                    write_uid = %s,\n                    write_date = NOW() at time zone 'UTC'\n                FROM (\n                    VALUES %s\n                ) AS c(id, payslip_id)\n                WHERE c.id = t.id;\n            "%(self.env.uid,','.join(updates));_logger.debug('update sql: %s',sql);self.env.cr.execute(sql);self.env.registry.clear_cache()
		_logger.debug('leaves get_compensation_lines: recs=%s %s',len(res),time.time()-t0);return res0+res