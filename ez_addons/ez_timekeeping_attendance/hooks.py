from odoo import api,SUPERUSER_ID,fields,models
import random
from datetime import datetime
from dateutil.relativedelta import relativedelta
def load_demo_data(env,demo=True):
	D=env;J=D['ir.module.module'].search([('name','=','ez_timekeeping_attendance')])
	if demo and not J.demo:return
	if 1:K=D['hr.attendance'];L=D['ez.time.card'];K.create_demo_data();L.create_demo_data()
	E=D['hr.ph.payroll'];F=E.search([])
	if F:F.cancel_done();F.unlink()
	N=datetime.today().replace(day=1)-relativedelta(months=1);H=24;I=fields.Date.from_string(fields.Date.today()).replace(day=1)-relativedelta(months=H);M=I+relativedelta(months=H,days=-1);A=I
	while A<=M:C=A+relativedelta(days=14);G={'name':f"Payroll {A.strftime("%B A %Y")}",'date_from':A,'date_to':C};B=E.create(G);B.auto_gen();B.generate_fin_reports();B.set_as_done();A=C+relativedelta(days=1);C=A.replace(day=1)+relativedelta(months=1)+relativedelta(days=-1);G={'name':f"Payroll {A.strftime("%B B %Y")}",'date_from':A,'date_to':C};B=E.create(G);B.auto_gen();B.generate_fin_reports();B.set_as_done();A=C+relativedelta(days=1)