from datetime import*
class TimePairs:
	def __init__(self,time1=None,time2=None,data=None,show_day=False,debug=False):
		self.show_day=show_day;self.debug=debug
		if data:self.data=data[:]
		else:self.data=[]
		if time1 and time2:
			try:
				if type(time1)==str:time1=self.str_to_dt(time1)
				if type(time2)==str:time2=self.str_to_dt(time2)
				if time1<=time2:self.data.append([time1,time2,0])
			except:print('TimePairs: Error parsing time:',time1,time2)
	def str_to_dt(self,ptime):
		ptime=ptime.strip().upper();tadd=timedelta(days=0);with_p=False;with_a=False
		if ptime[-1]=='A':with_a=True;ptime=ptime[:-1]
		if ptime[-1]=='P':with_p=True;ptime=ptime[:-1]
		if ptime[0]=='N':tadd=tadd+timedelta(hours=24);ptime=ptime[1:]
		if':'not in ptime:ptime=ptime+':00'
		h=int(ptime.split(':')[0])
		if h<12 and with_p:tadd=tadd+timedelta(hours=12)
		if h==12 and with_a:tadd=tadd-timedelta(hours=12)
		return datetime.strptime(ptime,'%H:%M')+tadd
	def __repr__(self):
		if len(self.data)==0:return'##:##-##:## m:0'
		else:return self.to_str()+' m:%d'%self.get_minutes()
	def to_str(self):
		res=[]
		for t in self.data:d0=t[0].day>1 and'N'or'';d1=t[1].day>1 and'N'or'';fmt='%H:%M';res.append('%s%s-%s%s'%(d0,t[0].strftime(fmt),d1,t[1].strftime(fmt)))
		return' '.join(res)
	def copy(self):data=[t[:]for t in self.data];return TimePairs(data=data,show_day=self.show_day)
	def __add__(self,other):
		if type(other)in[int,float]:minutes=int(other);return self.tp_add_minutes(minutes)
		else:
			if len(self.data)==0:return other.copy()
			if len(other.data)==0:return self.copy()
			data=self.data[:]
			for b in other.data:
				data=add1(data,b,debug=self.debug)
				if self.debug:print('RES',ashow(data))
			return TimePairs(data=data)
	def __sub__(self,other):
		if type(other)in[int,float]:minutes=int(other);return self.tp_add_minutes(-minutes)
		else:
			if len(self.data)==0:return TimePairs(show_day=self.show_day)
			if len(other.data)==0:return self.copy()
			data=self.data[:]
			for b in other.data:
				data=sub1(data,b,debug=self.debug)
				if self.debug:print('RES',ashow(data))
			return TimePairs(data=data)
	def __and__(self,other):return self-(self-other)
	def tp_add_minutes(self,other):
		if self.debug:print('tp_add_minutes: a=%s b=%d'%(self,other))
		res=self.copy()
		if other==0 or len(self.data)==0:return res
		elif other>0:
			if self.debug:print('tp_add_minutes+:',res,other)
			res.data[-1][1]+=timedelta(minutes=other);return res
		else:
			r=-other;data=[]
			for t in reversed(res.data):
				if self.debug:print(vt(t),r,get_minutes(t))
				if r==0:add_if_ok(data,t,0)
				else:
					tmin=get_minutes(t)
					if r<tmin:t[1]=t[1]-timedelta(minutes=r);add_if_ok(data,t,0);r=0
					else:r-=tmin
			res.data=[t for t in reversed(data)];return res
	def __rshift__(self,other):
		if type(other)==TimePairs:minutes=other.get_minutes()
		else:minutes=int(other)
		res=self.copy()+minutes;t=res-self.get_minutes();return res-t
	def remove_blanks(self):
		data=[]
		for t in self.data:add_if_ok(data,t,t[2])
		self.data=data;return self
	def get_minutes(self):
		res=0
		for t in self.data:res+=get_minutes(t)
		return res
def get_minutes(tp):return int((tp[1]-tp[0]).total_seconds()/60)
'\n1 - [ a ]\n          [ b ]\n2 - [ a ]\n      [ b ]\n3 - [   a   ]\n      [ b ]\n4 -   [ a ]\n    [   b   ]\n5 -   [ a ]\n    [ b ]\n6 -       [ a ]\n    [ b ]\n'
def sub1(data,b,debug=False):
	res=[];i=0
	for a in data:
		if not b:
			add_if_ok(res,a,0)
			if debug:print('0: i=%d A=%s B=%s'%(i,vt(a),vt(b)));print('NULL0: res =',ashow(res))
		elif a[1]<=b[0]:
			add_if_ok(res,a,a[2])
			if debug:print('1: i=%d A=%s B=%s'%(i,vt(a),vt(b)));print('RES:',ashow(res))
		elif b[1]<=a[0]:
			add_if_ok(res,a,6)
			if debug:print('6: i=%d A=%s B=%s'%(i,vt(a),vt(b)));print('RES:',ashow(res))
		elif a[0]<=b[0]and a[1]<=b[1]:
			add_if_ok(res,[a[0],b[0],0],2)
			if debug:print('2: i=%d A=%s B=%s'%(i,vt(a),vt(b)));print('RES:',ashow(res))
		elif a[0]<=b[0]and b[1]<=a[1]:
			add_if_ok(res,[a[0],b[0],0],3);add_if_ok(res,[b[1],a[1],0],0)
			if debug:print('3: i=%d A=%s B=%s'%(i,vt(a),vt(b)));print('RES:',ashow(res))
		elif b[0]<=a[0]and a[1]<=b[1]:
			if debug:print('4: i=%d A=%s B=%s'%(i,vt(a),vt(b)));print('RES:',ashow(res))
		elif b[0]<=a[0]and b[1]<=a[1]:
			add_if_ok(res,[b[1],a[1],0],5)
			if debug:print('5: i=%d A=%s B=%s'%(i,vt(a),vt(b)));print('RES:',ashow(res))
		i+=1
	return res
def add1(data,b,debug=False):
	res=[];n=len(data)
	for i in range(n):
		a=data[i];merge=0
		if not b:
			add_if_ok(res,a,0)
			if debug:print('0: i=%d A=%s B=%s'%(i,vt(a),vt(b)));print('NULL0: res =',ashow(res))
		elif a[1]<b[0]:
			add_if_ok(res,a,1)
			if i==n-1:add_if_ok(res,b,1)
			if debug:print('1: i=%d A=%s B=%s'%(i,vt(a),vt(b)));print('ADD1: res =',ashow(res))
		elif b[1]<a[0]:
			a[2]=6;add_if_ok(res,b,6);add_if_ok(res,a,6)
			if debug:print('6: i=%d A=%s B=%s'%(i,vt(a),vt(b)));print('ADD6: res =',ashow(res))
			b=None
		elif a[0]<=b[0]and a[1]<=b[1]:
			merge=2
			if debug:print('2: i=%d A=%s B=%s'%(i,vt(a),vt(b)))
		elif a[0]<=b[0]and b[1]<=a[1]:
			merge=3
			if debug:print('3: i=%d A=%s B=%s'%(i,vt(a),vt(b)))
		elif b[0]<=a[0]and a[1]<=b[1]:
			merge=4
			if debug:print('4: i=%d A=%s B=%s'%(i,vt(a),vt(b)))
		elif b[0]<=a[0]and b[1]<=a[1]:
			merge=5
			if debug:print('5: i=%d A=%s B=%s'%(i,vt(a),vt(b)))
		if merge:
			t0=min(a[0],b[0]);t1=max(a[1],b[1]);add_if_ok(res,[t0,t1,0],merge)
			if debug:print('MERGE: res =',ashow(res))
			b=None
	return res
def add_if_ok(parray,t,op_type):
	r=t[:];r[2]=op_type
	if r[0]<r[1]:parray.append(r)
def ashow(plist):a1=[vt(t)for t in plist];return' '.join(a1)
def vt(t):
	if t:return t[0].strftime('%H:%M')+'-'+t[1].strftime('%H:%M')
	else:return'##:##-##:##'