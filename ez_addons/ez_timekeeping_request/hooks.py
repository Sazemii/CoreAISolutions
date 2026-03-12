from odoo import api,SUPERUSER_ID,fields,models
import random
from datetime import datetime
from dateutil.relativedelta import relativedelta
def load_demo_data(env,demo=True):
	B=env;G=B['ir.module.module'].search([('name','=','ez_timekeeping_request')])
	if demo and not G.demo:return
	H=B['ez.time.card'].search([]);H.to_draft();E=B['ez.time.request'];I=fields.Date.today().replace(day=1)-relativedelta(months=1);J=B['hr.employee'].search([]);A=I
	for C in J:
		if A.weekday()==7:A+=relativedelta(days=1)
		F=random.randint(1,4)/2.;D=E.create({'name':'Overtime Request - %s'%C.name,'employee_id':C.id,'auth_hrs':F,'date':A.strftime('%Y-%m-%d'),'type':'ot'});D.approve_record();D=E.create({'name':'Change of Timelog - %s'%C.name,'employee_id':C.id,'date':A.strftime('%Y-%m-%d'),'type':'ob','time':'08:00-11:30 12:30-%02d:00'%(17+int(F+.4))});D.approve_record();A+=relativedelta(days=1)