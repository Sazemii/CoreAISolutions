from odoo import api,SUPERUSER_ID
import logging,time
from odoo import api,fields,models
_logger=logging.getLogger(__name__)
class Company(models.Model):
	_inherit='res.company'
	@api.model
	def is_fast_insert(self):return False
def execute_insert(model,data,debug_sql=False,invalidate_cache=True,fast_mode=True):
	B=data;A=model
	if not fast_mode:
		for D in B:A.create(D)
		return'CREATE: %s'%D
	elif B:
		E=time.time();C=get_insert(A,B)
		if debug_sql:_logger.debug('execute_insert: sql=%s',C)
		A.env.cr.execute(C)
		if invalidate_cache:A.invalidate_recordset()
		_logger.debug('execute_insert: table=%s records=%s time=%s',A._name,len(B),time.time()-E);return C
def execute_update(model,fields,data,debug_sql=False,invalidate_cache=True):
	B=data;A=model
	if B:
		D=time.time();C=get_update(A,fields,B)
		if debug_sql:_logger.debug('execute_update: sql=%s',C)
		A.env.cr.execute(C)
		if invalidate_cache:A.invalidate_recordset();_logger.debug('clear cache: %s',A)
		_logger.debug('execute_update: table=%s records=%s time=%s',A._name,len(B),time.time()-D)
def get_insert(model,data):
	B=model;H=B.env.cr;I=B.env.uid;J=B._name.replace('.','_');F=[];A=set()
	for C in data:K=set(C.keys());A=A.union(K)
	D=[]
	for G in A:D.append('%s')
	D.append('%s')
	for C in data:
		E=[]
		for G in A:E.append(C.get(G))
		E.append(I);L='('+', '.join(D)+", NOW() at time zone 'UTC')";F.append(H.mogrify(L,tuple(E)).decode('utf-8'))
	M='\nINSERT INTO %s\n(%s, create_uid, create_date)\nVALUES\n%s'%(J,', '.join(A),',\n'.join(F));return M
def get_update(model,fields,data):B=model;A=fields;C=B.env.cr;D=B._name.replace('.','_');E=['%s = c.%s'%(A,A)for A in A];F=['id']+A;G=len(A)+1;H='('+','.join(['%s'for A in range(G)])+')';I=[C.mogrify(H,A).decode('utf-8')for A in data];J='\nUPDATE %s AS t\nSET %s\nFROM (VALUES\n%s\n) AS c(%s)\nWHERE c.id = t.id'%(D,', '.join(E),','.join(I),','.join(F));return J