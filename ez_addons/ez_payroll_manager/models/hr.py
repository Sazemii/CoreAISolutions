from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
from datetime import datetime,timedelta
from dateutil.relativedelta import relativedelta
import random,logging
_logger=logging.getLogger(__name__)
class HrEmployee(models.Model):_inherit='hr.employee';no_night_differential=fields.Boolean('No Night Diff',groups='ez_payroll.group_hr_payroll_user',help='Enable if employee will no night differential.');no_overtime=fields.Boolean('No Overtime',groups='ez_payroll.group_hr_payroll_user',help='Enable if employee will no overtime.')