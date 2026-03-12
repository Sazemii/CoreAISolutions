from odoo import api,SUPERUSER_ID
import random
from datetime import datetime
def load_demo_data(env,demo=True):
	A=env['ir.module.module'].search([('name','=','ez_hr')])
	if demo and not A.demo:return
	B=env['hr.employee'];B.demo_hr_ph()