from __future__ import print_function
import odoorpc,csv,re,random
from datetime import date
from pprint import pprint
from datetime import datetime,date
from dateutil.relativedelta import relativedelta
from string import ascii_lowercase
from faker import Faker
def csv_load(odoo,csv_file):
	B=csv_file;print('LOADING:',B);C=B.split('/');D=C[-1][:-4];A=[]
	with open(B)as E:
		F=csv.reader(E)
		for G in F:A.append(G)
	if A:H=A[0];I=odoo.env[D].load(H,A[1:]);print(I);print()
def create_timecard_demo(odoo):
	D=odoo;C=date.today().replace(day=1)-relativedelta(day=1);print('CREATE TIMECARD',C);O=D.env['hr.employee'].search([]);P=D.env['ir.model.data'].search_read([('model','=','hr.employee'),('res_id','in',O)],['module','name','res_id']);F=D.env['ez.time.card'];K=['id','employee_id/id','date1','date2','shift_id/id'];G=[];A=C+relativedelta(months=-1);B=C+relativedelta(days=-1);E=B;H=B
	for T in range(2):
		A=C+relativedelta(months=-1);B=C+relativedelta(days=-1);E=A;print(A,B)
		for I in P:G.append(['__export__.dtr_%s_%s'%(A.strftime('%Y_%m'),I['res_id']),'%s.%s'%(I['module'],I['name']),A.strftime('%Y-%m-%d'),B.strftime('%Y-%m-%d'),'ez_timekeeping.day_shift'])
		C+=relativedelta(months=-1)
	pprint(K);pprint(G)
	if 0:Q=F.load(K,G);print(Q)
	print(E,H)
	if 0:
		R=F.search([('date1','>=',E.strftime('%Y-%m-%d')),('date2','<=',H.strftime('%Y-%m-%d'))])
		for J in F.browse(R):print('DTR:s',J.name);J.onchange_shift_id();J.gen_default_lines()
	if 1:
		S=D.env['ez.time.record'].search([('date','>=',E.strftime('%Y-%m-%d')),('date','<=',H.strftime('%Y-%m-%d'))])
		for L in D.env['ez.time.record'].browse(S):
			if random.random()<.15 and L.timelog:A=datetime.today().replace(hour=8,minute=0);A+=relativedelta(minutes=random.randint(-5,30));B=datetime.today().replace(hour=17,minute=0);B+=relativedelta(minutes=random.randint(-30,120));M=A.strftime('%H:%M');N=B.strftime('%H:%M');L.timelog='%s-11:30 12:30-%s'%(M,N);print(M,N)
	print()
def create_timecard_log_demo(odoo):
	def D(n,tm):B=['__export__.dtr_log_%s_%s_%s'%(A.strftime('%Y_%m_%d'),C['identification_id'],n),A.strftime('%Y-%m-%d'),tm,C['identification_id']];return B
	E=odoo.env['hr.employee'].search_read([],['identification_id']);pprint(E);J=['id','name','time','identification_id'];B=[];A=date.today()
	for L in range(60):
		if A.weekday()!=6:
			for C in E:
				F='08:00';G='17:00'
				if C['identification_id']:
					if random.random()<.15:H=datetime.today().replace(hour=8,minute=0);H+=relativedelta(minutes=random.randint(-5,30));I=datetime.today().replace(hour=17,minute=0);I+=relativedelta(minutes=random.randint(-30,120));F=H.strftime('%H:%M');G=I.strftime('%H:%M')
					B.append(D(0,F));B.append(D(1,G))
		A+=relativedelta(days=-1)
	K=odoo.env['ez.time.log'].load(J,B);print(K)
if __name__=='__main__':
	odoo=odoorpc.ODOO('localhost',port=10017,protocol='jsonrpc');user='admin';pwd='12345';db='demo-ezpay';odoo.login(db,user,pwd)
	if 0:table=odoo.env['hr.employee'];recs=table.search_read([],['name']);pprint(recs)
	if 1:odoo.env['hr.attendance'].create_demo_data();odoo.env['ez.time.card'].create_demo_data()
	if 0:
		fake=Faker('en_PH')
		for i in range(10):print(fake.name());print(fake.address())