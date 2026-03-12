from openpyxl import load_workbook
import csv
from pprint import pprint
import json,re,random
from datetime import datetime
from dateutil.relativedelta import relativedelta
from string import ascii_lowercase
import urllib.request,odoorpc
if __name__=='__main__':
	dbname='bms';host='bms.odoo17.eztechsoft.com';port=443;protocol='jsonrpc+ssl';user='rberdin@eztechsoft.com';admin_pwd='3e150940eb33ab3f49f713979bcf12269efc14f7';super_password='x';odoo=odoorpc.ODOO(host,port=port,protocol=protocol);print('Connect',host);odoo.login(dbname,user,admin_pwd);companies=odoo.env['res.company'].search_read([],['name']);comps=[A['id']for A in companies];pprint(companies);pprint(comps);emps=odoo.env['hr.employee'].search_read([('company_id','in',comps)],['name','company_id']);emp_ids=[A['id']for A in emps]
	for e in odoo.env['hr.employee'].browse(emp_ids):print(e.name,e.company_id.name);e.get_salary_rate()