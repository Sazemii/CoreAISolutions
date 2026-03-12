from datetime import datetime
from dateutil.relativedelta import relativedelta
import time,sys,xmlrpc.client
class Struct:
	def __init__(A,**B):A.__dict__.update(B)
def change_date(conn):
	A=conn;B=xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(A.url));C=B.execute_kw(A.db,A.uid,A.password,'res.company','search_read',[[['name','=','Ramon Branch']]],{'limit':1})
	if not C:return
	D=Struct(**C[0]);print('Company',D.name,D.id);E=B.execute_kw(A.db,A.uid,A.password,'wc.account.transaction','search',[[]]);print('IDs',len(E))
	if 1:F=B.execute_kw(A.db,A.uid,A.password,'wc.account.transaction','write',[E,{'is_printed':False}])
if __name__=='__main__':
	if 1:url='http://localhost';admin_password='pass1234';super_password='pass1234';admin='admin';language='en_US';db='test-taman'
	common=xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url));print('VERSION',common.version());uid=common.authenticate(db,admin,admin_password,{});print('UID:',uid);p={'uid':uid,'password':admin_password,'db':db,'url':url};conn=Struct(**p);change_date(conn)