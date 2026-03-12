import json,random,requests
from pprint import pprint
from datetime import datetime
from dateutil.relativedelta import relativedelta
req=requests.Session()
def json_rpc(url,method,params):A={'jsonrpc':'2.0','method':method,'params':params,'id':random.randint(0,1000000000)};B=req.post(url,data=json.dumps(A).encode(),headers={'Content-Type':'application/json'});return json.loads(B.text).get('result')
def call(url,service,method,*A):return json_rpc(url,'call',{'service':service,'method':method,'args':A})
def login(url,db,user,password):A=json_rpc(url+'/web/session/authenticate','call',{'db':db,'login':user,'password':password}).get('uid');B=req.cookies['session_id'];print('Session ID:',B);print('Login successful',A);return A
def mfa_request(url):A=URL+'/ess-api/mfa-request';B={'employee-email':'rberdin@eztechsoft.com'};C=json_rpc(A,'call',B);print(A);print('Parameters:');pprint(B);print('Result:');pprint(C)
def mfa_validate(url):B=URL+'/ess-api/mfa-validate';C={'employee-email':'rberdin@eztechsoft.com','mfa':'155208'};A=json_rpc(B,'call',C);print(B);print('Parameters:');pprint(C);print('Result:');pprint(A);D=A.get('employee_id');hash=A.get('hash');return D,hash
def mfa_next_process(url,emp_id,hash):A='%s%s/%s/%s'%(URL,'/ess-api/attendance/next-process',emp_id,hash);B={};C=json_rpc(A,'call',B);print(A);print('Parameters:');pprint(B);print('Result:');pprint(C);next=C.get('next-process');return next
if __name__=='__main__':
	URL='https://demo-ezpay.odoo17.eztechsoft.com';USER='pay-demo';PASS='12345';DB='demo-ezpay';url='%s/jsonrpc'%URL
	if 0:uid=login(URL,DB,USER,PASS);model_name='res.partner';domain=[];res=call(url,'object','execute',DB,uid,PASS,model_name,'search_read',domain,['name']);pprint(res)
	if 0:mfa_request(url)
	if 0:emp_id,hash=mfa_validate(url);next=mfa_next_process(url,emp_id,hash)
	if 0:
		emp_id,hash=mfa_validate(url);next=mfa_next_process(url,emp_id,hash)
		if next=='check_in':req_url='%s%s/%s/%s'%(URL,'/ess-api/attendance/check_in',emp_id,hash);now=datetime.now();param={'check_in':now.strftime('%Y-%m-%d %H:%M:%S'),'in_latitude':10.29998,'in_longitude':123.95216};res=json_rpc(req_url,'call',param);print(req_url);print('Parameters:');pprint(param);print('Result:');pprint(res)
		if next=='check_out':req_url='%s%s/%s/%s'%(URL,'/ess-api/attendance/check_out',emp_id,hash);now=datetime.now();param={'check_out':now.strftime('%Y-%m-%d %H:%M:%S'),'out_latitude':10.29998,'out_longitude':123.95216};res=json_rpc(req_url,'call',param);print(req_url);print('Parameters:');pprint(param);print('Result:');pprint(res)
	if 0:uid=login(URL,DB,USER,PASS);model_name='hr.employee';domain=[];res=call(url,'object','execute',DB,uid,PASS,model_name,'set_geofence_check_in',19,10.29998,123.95216);pprint(res);res=call(url,'object','execute',DB,uid,PASS,model_name,'set_geofence_check_out',19,10.29998,123.95216);pprint(res)
	if 0:emp_id,hash=mfa_validate(url);req_url='%s%s/%s/%s'%(URL,'/ess-api/payroll/get-payslips',emp_id,hash);param={};res=json_rpc(req_url,'call',param);print(req_url);print('Result:');pprint(res)
	if 0:emp_id,hash=mfa_validate(url);req_url='%s%s/%s/%s'%(URL,'/ess-api/payroll/get-payslip',6760,hash);param={};res=json_rpc(req_url,'call',param);print(req_url);print('Result:');pprint(res)
	if 1:emp_id,hash=mfa_validate(url);req_url='%s%s/%s/%s'%(URL,'/ess-api/payroll/get-2316',emp_id,hash);param={};res=json_rpc(req_url,'call',param);print(req_url);print('Result:');pprint(res)