from __future__ import print_function
from odoo_connection import OdooConnection
from datetime import datetime
from dateutil.relativedelta import relativedelta
from pprint import pprint
import math,random,csv,random_names,os,time
from multiprocess import multi_load,chunks,MultiProcess,lprint
from odoo_utils import*
def get_companies():
	table='res.company';ids=odoo.env[table].search([]);recs=odoo.execute(table,'read',ids,['name']);res={}
	for r in recs:res[r['name']]=r['id']
	print('Companies:',res);return res
def get_emp(odoo):
	table='hr.employee';Obj=odoo.env[table];ids=Obj.search([])
	for r in Obj.browse(ids):pprint([r.name,r.salary_rate,r.salary_rate_period,r.tax_code])
def create_emp(odoo):
	header=['id','last_name','first_name','middle_name','salary_rate','salary_rate_period','minimum_wage','hired','identification_id','tin_no'];res=[header]
	for i in range(2500):
		ln,fn,mn=random_names.get_random_name();minimum_wage=False
		if random.random()<.7:monthly=True;salary_rate=3e4+random.randint(0,10)*1000;salary_rate_period='monthly'
		else:
			monthly=False;salary_rate=4e2+random.randint(0,10)*50;salary_rate_period='daily'
			if salary_rate<500:minimum_wage=True
		hired=datetime.now()-relativedelta(months=1)-relativedelta(days=random.randint(0,400));r=['_payroll_.emp_%d'%i,ln,fn,mn,salary_rate,salary_rate_period,minimum_wage and'1'or'',hired.strftime('%Y-%m-%d'),'%06d'%(i+10000),'%03d-%03d-%03d-0000'%(random.randint(100,999),random.randint(0,999),random.randint(0,999))];res.append(r)
	return res
dt1='2022-05-15'
dt2='2022-05-31'
DF='%Y-%m-%d'
def create_shift(odoo):table='ez.shift';Obj=odoo.env[table];am_shift_id=Obj.create({'name':'Day Shift','auto_auth':True});table='hr.employee';Obj=odoo.env[table];Obj.set_shift(am_shift_id)
def create_timecard(odoo):
	table='ez.shift';Obj=odoo.env[table];am_shift_id=Obj.search([('name','=','Day Shift')]);header=['id','employee_id/id','date1','date2','auto_auth'];res=[header]
	for i in range(2500):r=['_payroll_.timecard_%d'%i,'_payroll_.emp_%d'%i,dt1,dt2,'1','Day Shift'];res.append(r)
	return res
def gen_timecards(odoo):
	table='ez.time.card';Obj=odoo.env[table];ids=Obj.search([('date1','>=',dt1),('date2','<=',dt2),('state','=','draft')])
	for r in Obj.browse(ids):print('Generating time card: %s %s'%(r.employee_id.name,r.id));r.gen_default_lines(demo=True);r.approve_record()
def create_request(odoo):
	header=['id','employee_id:id','name','date','type','day_type','schedule'];res=[header]
	for i in range(2500):dt=datetime.strptime(dt1,'%Y-%m-%d')+relativedelta(days=random.randint(1,14));r=['_payroll_.reqsch_%d'%i,'_payroll_.emp_%d'%i,'Request #%06d'%i,dt.strftime(DF),'sch',random.choice(['do','lh','sh','do_lh','do_sh']),'08:00-11:30 12:30-17:00'];res.append(r)
	return res
def thread_change_emp(conn,l,name,table,ids):
	odoo=odoo_login(conn);TableObj=odoo.env[table];lprint(l,'%s: load records=%d'%(name,len(ids)))
	for r in TableObj.browse(ids):print('On change: %s %s'%(r.employee_id.name,r.id));r.onchange_employee()
	lprint(l,'%s: res=%s'%(name,res));odoo.logout()
def multi_change(conn,table,data,threads=4,chunk_size=100):
	bt=MultiProcess(threads);l=bt.lock;lprint(l,'Loading data to table: %s recs=%d'%(table,len(data)));i=0
	for chunk in chunks(data,chunk_size):params=[conn,l,'Thread %02d'%i,table,chunk];bt.spawn_thread(thread_change_emp,params);i+=1
	bt.wait()
if __name__=='__main__':
	odoo=False
	if 1:dbname='payroll-test2';host='leadgen.ezpayrollweb.com';port=443;admin_pwd='pass1234';super_password='ebfeYUx2i5D2PZ6';conn=OdooConnection(host,port,admin_pwd,super_password);conn2={'host':host,'port':port,'admin_pwd':admin_pwd,'super_password':super_password,'dbname':dbname}
	if 0:get_emp(odoo)
	if 0:conn.drop_database(dbname);time.sleep(3);conn.create_database(dbname);conn.install_modules(dbname,['ez_hr_namesplit','ez_payroll','ez_leaves','ez_timekeeping_payroll','ez_timekeeping_sched','ez_payroll_alphalist','ez_timekeeping_log','ez_timekeeping_request','ez_timekeeping_request_sch','ez_timekeeping_request_sched','muk_web_theme'])
	time.sleep(5);odoo=conn.get_session(dbname)
	if 0:data=create_emp(odoo);multi_load(conn2,'hr.employee',data[0],data[1:],threads=12,chunk_size=100)
	if 0:create_shift(odoo)
	if 0:data=create_timecard(odoo);multi_load(conn2,'ez.time.card',data[0],data[1:],threads=8,chunk_size=100)
	if 0:table='ez.time.card';Obj=odoo.env[table];data=Obj.search([('shift_id','=',False)]);multi_change(conn2,'ez.time.card',data,threads=8,chunk_size=100)
	if 1:gen_timecards(odoo)