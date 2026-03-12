from odoo import api,fields,models,tools,_,SUPERUSER_ID
from odoo.exceptions import ValidationError,UserError
import re
def min_to_hstr(minutes):
	A=minutes
	if A:B=A%60;C=(A-B)/60;return'%02d:%02d'%(C,B)
	else:return'00:00'
def min_to_hstr2(minutes):
	B=minutes
	if B:
		C=B%480;E=(B-C)/480;D=C%60;F=(C-D)/60;A=[]
		if E:A.append('%dd'%E)
		if F:A.append('%dh'%F)
		if D:A.append('%dm'%D)
		return' '.join(A)
	else:return''
def min_to_dhstr(minutes):
	A=minutes
	if A:
		B=A%480;D=(A-B)/480;C=B%60;E=(B-C)/60
		if D:return'%dd %02d:%02d'%(D,E,C)
		else:return'%02d:%02d'%(E,C)
	else:return'00:00'
def parse_sched(sched,def_time=None,error=True):
	D=def_time;A=sched
	if not A:return A
	if A and A[0]=='#':return[]
	B=[A for A in re.split('[, \\-!?]+',A)if A]
	if len(B)%2!=0 or len(B)==0:
		if error:raise ValidationError(_('Enter time in pairs (IN+OUT) separated by spaces.'))
		else:return[]
	E=[];F='';G=len(B)
	if not D:D=G
	for H in range(D):
		if H<G:
			C=parse_str_time(B[H])
			if not C:C=F
			E.append(C);F=C
		else:E.append(F)
	return E
valid_time_chars=set(['0','1','2','3','4','5','6','7','8','9',':'])
def parse_str_time(field):
	G=field;global valid_time_chars
	if not G:return
	B=G.strip().upper();H=re.sub('[^0-9:]+','',B)
	if H=='':return
	I='';E=0;F=False
	if'N'in B:I='N'
	if'P'in B:E=12
	elif'A'in B:F=True
	'\n    x = []\n    next_day = ""\n    hadd = 0\n    for p in field.upper():\n        if p in valid_time_chars:\n            x.append(p)\n        elif p==\'N\':\n            next_day = "N"\n        elif p==\'P\':\n            hadd = 12\n\n    if not x:\n        return None\n\n    a = "".join(x).split(\':\')\n\n    ';C=H.split(':');A=int('0'+C[0].strip());print('WITH A:',F,A,C,B)
	if F and A==12:A=0
	elif A<12 and E:A+=E
	if len(C)>1:
		D=int('0'+C[1].strip())
		if D>59:D=0
	else:D=0
	return'%s%02d:%02d'%(I,A,D)