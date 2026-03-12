from odoo import api,SUPERUSER_ID
import random
from datetime import datetime
from dateutil.relativedelta import relativedelta
def load_demo_data(env,demo=True):
	C=env;E=C['ir.module.module'].search([('name','=','ez_payroll')])
	if demo and not E.demo:return
	F=C['hr.employee'];D=C['hr.ph.pay.deduction.entry'];G=C['hr.ph.loan'];H=C['ez.work.summary.sheet'];F.create_demo_data();A=datetime.today().replace(day=2)-relativedelta(months=1);B=A.strftime('Canteen %b %Y A');D.create_demo_data(A,B);A=datetime.today().replace(day=3)-relativedelta(months=1);B=A.strftime('Union Dues %b %Y A');D.create_demo_data(A,B);A=datetime.today().replace(day=18)-relativedelta(months=1);B=A.strftime('Canteen %b %Y B');D.create_demo_data(A,B);A=datetime.today().replace(day=19)-relativedelta(months=1);B=A.strftime('Union Dues %b %Y B');D.create_demo_data(A,B);A=datetime.today()-relativedelta(months=2);G.create_demo_data(A,'A0001');A=datetime.today().replace(day=5)-relativedelta(months=1);H.create_demo_data(A.strftime('Adjustments %b %Y'),A,False)