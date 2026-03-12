from odoo import api,SUPERUSER_ID
import random
from datetime import datetime
def post_init_hook(env,demo=True):
	B=env['ez.employee.salary.rate'];C=env['hr.employee'].search([])
	for A in C:B.create({'date':A.hired or datetime.today().replace(day=1,month=1),'employee_id':A.id,'salary_rate':A.salary_rate,'salary_rate_period':A.salary_rate_period})
def uninstall_hook(env):
	B=env['hr.employee'].search([])
	for A in B:C=A.salary_rate_now;D=A.salary_rate_period_now;E=A.emr_days_now;env.cr.execute('\n            UPDATE ez_employee_salary_rate \n            SET salary_rate=%s, salary_rate_period=%s, emr_days=%s\n            WHERE id=%s;\n        ',(C,D,E,A.id))