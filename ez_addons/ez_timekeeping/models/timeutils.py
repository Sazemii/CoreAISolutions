from datetime import*
from dateutil.relativedelta import relativedelta
from.timepairs import TimePairs,get_minutes,vt
import re,random,math,logging
_logger=logging.getLogger(__name__)
DEBUG=1
def timestr_to_timepair(time_str):
	if time_str:
		ts=[_f for _f in re.split('[, \\-!?]+',time_str)if _f];res=TimePairs();n=len(ts)
		for i in range(1,n,2):t0=ts[i-1];t1=ts[i];res+=TimePairs(t0,t1)
		return res
	else:return TimePairs()
def compute_undertime(tp_sch,tp_log,defs):
	late_allowance_minutes=defs.get('late_allowance_minutes',0);tp_ut=tp_sch-tp_log;ut_remarks=set();tp_late_allow=TimePairs()
	for t in tp_ut.data:
		print('LATE',vt(t),t[2])
		if t[2]in[2,3]:
			if late_allowance_minutes>=get_minutes(t):tp_late_allow.data.append(t[:]);t[1]=t[0];ut_remarks.add('LateAllow')
			else:ut_remarks.add('Late')
		else:ut_remarks.add('Undertime')
	return tp_ut.remove_blanks(),ut_remarks,tp_late_allow
def compute_worktime(tp_sch,tp_log,defs={},debug=DEBUG):
	remarks=set();ut_remarks=set();sch_minutes=tp_sch.get_minutes();auth_min=int(round(defs.get('auth_hrs',0)*6e1,0));minimum_ot_minutes=defs.get('minimum_ot_minutes',0);flex_time=defs.get('flex_time',False);auto_auth=defs.get('auto_auth',False);day_type=defs.get('day_type','reg');rounding_ot_minutes=defs.get('rounding_ot_minutes',0);rounding_regular_work_minutes=defs.get('rounding_regular_work_minutes',0);rounding_on_out=defs.get('rounding_on_out',False);early_overtime=defs.get('early_overtime',0)
	if auto_auth:auth_min=1440
	if len(tp_log.data)==0:auth_min=0
	if debug:print('compute_worktime:');print('   auth_min = %d'%auth_min);print('     min_ot = %d'%minimum_ot_minutes);print('        sch = %s'%tp_sch);print('        log = %s'%tp_log)
	tp_otmask=TimePairs();tp_norm_night=TimePairs();tp_ot=TimePairs();tp_ot_night=TimePairs()
	if rounding_regular_work_minutes and not flex_time:
		for d in tp_log.data:
			min1=int(math.ceil(d[0].minute/rounding_regular_work_minutes))*rounding_regular_work_minutes
			if min1>=60:d[0]=d[0].replace(minute=0,hour=d[0].hour+1)
			else:d[0]=d[0].replace(minute=min1)
			if rounding_on_out:
				min2=d[1].minute//rounding_regular_work_minutes*rounding_regular_work_minutes
				if min2>=60:d[1]=d[1].replace(minute=0,hour=d[1].hour+1)
				else:d[1]=d[1].replace(minute=min2)
	if auth_min==0 and day_type!='reg':
		tp_ut=TimePairs();tp_norm=TimePairs()
		if len(tp_log.data)>0:remarks.add('NoAuth')
	else:
		tp_ut,ut_remarks,tp_late_allow=compute_undertime(tp_sch,tp_log,defs)
		if day_type!='reg':ut_remarks=set()
		tp_norm=tp_sch-tp_ut
		if auth_min>0:
			norm_minutes=tp_sch.get_minutes();over_8hrs=False
			if day_type!='reg'and auth_min>=norm_minutes:auth_min-=norm_minutes;over_8hrs=True
			if day_type=='reg'or over_8hrs:
				ut_min=tp_ut.get_minutes()
				if ut_min>=auth_min:add_wt_min=auth_min;c_auth_min=0
				else:add_wt_min=ut_min;c_auth_min=auth_min-ut_min
				tp_norm=tp_sch+add_wt_min-tp_ut&tp_log+tp_late_allow
				if flex_time and tp_sch.get_minutes()==0:tp_otmask=tp_log-(tp_log.get_minutes()-c_auth_min)
				else:tp_otmask=tp_sch+auth_min-(tp_sch+add_wt_min)
				tp_ot=tp_log&tp_otmask
				if minimum_ot_minutes>=tp_ot.get_minutes():tp_ot=TimePairs()
			else:
				ut_min=tp_ut.get_minutes()
				if ut_min>=auth_min:add_wt_min=auth_min;c_auth_min=0
				else:add_wt_min=ut_min;c_auth_min=auth_min-ut_min
				tp_mask=tp_sch+auth_min-tp_sch.get_minutes();tp_norm=tp_log+tp_late_allow&tp_mask;tp_ot=TimePairs()
		else:
			tp_ot=TimePairs();tp_mask=tp_sch+1440;tp_no_auth=(tp_mask&tp_log)-tp_sch;no_auth_minutes=tp_no_auth.get_minutes()
			if minimum_ot_minutes<no_auth_minutes:remarks.add('NoAuth')
		if tp_log.data and tp_sch.data:
			sch_start=tp_sch.data[0][0];log_start=tp_log.data[0][0];ot_minutes=tp_ot.get_minutes();_logger.debug('Early OT: ot_minutes=%s auth_min=%s',ot_minutes,auth_min)
			if auth_min>ot_minutes and early_overtime and log_start<sch_start:early_ot_min=auth_min-ot_minutes;tp_sch_early=TimePairs(sch_start-relativedelta(minutes=early_ot_min),sch_start);tp_ot_early=tp_log&tp_sch_early;tp_ot+=tp_ot_early;_logger.debug('  OT: early_ot_min=%s tp_sch_early=%s tp_ot_early=%s',early_ot_min,tp_sch_early,tp_ot_early)
		tp_night=TimePairs('12a','6a')+TimePairs('10p','N6a');tp_norm_night=tp_norm&tp_night;tp_norm-=tp_norm_night;tp_ot_night=tp_ot&tp_night;tp_ot-=tp_ot_night
	norm_minutes=tp_norm.get_minutes();ot_minutes=tp_ot.get_minutes();norm_night_minutes=tp_norm_night.get_minutes();ot_night_minutes=tp_ot_night.get_minutes();late_minutes=0;undertime_minutes=0;absent_minutes=0;tp_night=TimePairs('12a','6a')+TimePairs('10p','N6a');tp_sch_day=tp_sch-tp_night;tp_sch_night=tp_sch&tp_night;lacking_norm_minutes=tp_sch_day.get_minutes()-norm_minutes
	if lacking_norm_minutes>0 and ot_minutes:
		if ot_minutes>lacking_norm_minutes:norm_minutes+=lacking_norm_minutes;lacking_norm_minutes-=lacking_norm_minutes
		else:norm_minutes+=ot_minutes;ot_minutes=0
	lacking_night_minutes=tp_sch_night.get_minutes()-norm_night_minutes
	if lacking_night_minutes>0 and ot_night_minutes:
		if ot_night_minutes>lacking_night_minutes:norm_night_minutes+=lacking_night_minutes;ot_night_minutes-=lacking_night_minutes
		else:norm_night_minutes+=ot_night_minutes;ot_night_minutes=0
	if norm_minutes+norm_night_minutes<tp_sch.get_minutes():
		if ot_minutes:norm_minutes+=ot_minutes;ot_minutes=0
		if ot_night_minutes:norm_night_minutes+=ot_night_minutes;ot_night_minutes=0
	if rounding_ot_minutes:
		ot_all=ot_minutes+ot_night_minutes;rounded_all=ot_all//rounding_ot_minutes*rounding_ot_minutes
		if rounded_all>=ot_minutes:ot_night_minutes=rounded_all-ot_minutes
		elif ot_minutes>=rounded_all:ot_minutes=rounded_all;ot_night_minutes=0
		else:rounded_all-=ot_minutes;ot_night_minutes=rounded_all
	if day_type=='reg':
		if norm_minutes==0 and norm_night_minutes==0:
			ut_remarks=set()
			if sch_minutes:remarks=set(['Absent']);tp_ut=TimePairs();absent_minutes=sch_minutes
		else:
			for t in tp_ut.data:
				if t[2]in[2,3]:late_minutes+=get_minutes(t)
				else:undertime_minutes+=get_minutes(t)
			c_ut_minutes=sch_minutes-norm_minutes;print('c_ut_minutes',c_ut_minutes)
			if c_ut_minutes==0:late_minutes=0;undertime_minutes=0;c_ut_minutes=0
			elif late_minutes+undertime_minutes>c_ut_minutes:
				if late_minutes>=c_ut_minutes:late_minutes=c_ut_minutes;undertime_minutes=0
				elif undertime_minutes>=c_ut_minutes:late_minutes=0;undertime_minutes=c_ut_minutes
				elif late_minutes<c_ut_minutes:late_minutes-=c_ut_minutes
				elif undertime_minutes<c_ut_minutes:undertime_minutes-=c_ut_minutes
	if ot_minutes>0:remarks.add('Overtime')
	if ot_night_minutes>0 or norm_night_minutes>0:remarks.add('NightWork')
	remarks.update(ut_remarks);res={'norm_minutes':norm_minutes,'norm_night_minutes':norm_night_minutes,'ot_minutes':ot_minutes,'ot_night_minutes':ot_night_minutes,'undertime_minutes':undertime_minutes,'late_minutes':late_minutes,'absent_minutes':absent_minutes,'remarks':', '.join(remarks)}
	if debug:print('       norm = %s'%tp_norm);print(' norm_night = %s'%tp_norm_night);print('       otm  = %s'%tp_otmask);print('         ot = %s'%tp_ot);print('   ot_night = %s'%tp_ot_night);print('         ut = %s'%tp_ut);print('        res = %s'%res);print('   auth_min = %s'%auth_min)
	return res
def get_demo_timelog(schedule):
	tp_log=timestr_to_timepair(schedule);r=random.randrange(100);auth_hrs=.0
	if r<50:
		for d in tp_log.data:ut=random.randrange(10);tp=TimePairs(data=[d]);tp=tp-(tp.get_minutes()-ut);tp_log=tp_log-tp
	r=random.randrange(100)
	if r<80:ot=int(random.random()*6e1*3.);tp_log+=ot;auth_hrs=max(0,ot+random.uniform(-6e1,6e1))/60
	return tp_log.to_str(),auth_hrs
def test():
	tests=[['7-11:00 12:00p-4p','7:4 11:25 12:45p 7:35p',{'auth_hrs':1,'day_type':'reg','late_allowance_minutes':5,'minimum_ot_minutes':15}],['7 11:00 12:00p 4p','7:4 11:25 12:45p 7:35p',{'auth_hrs':0,'day_type':'reg','late_allowance_minutes':5,'minimum_ot_minutes':15}],['7 11:00 12:00p 4p','7:4 11:25 12:45p 7:35p',{'auth_hrs':.5,'day_type':'reg','late_allowance_minutes':5,'minimum_ot_minutes':15}],['10p 6:00p 7:00p 11p','10:04p 6:30p 6:45p n8a',{'auth_hrs':24,'day_type':'reg','late_allowance_minutes':5,'minimum_ot_minutes':15}],['7a 12:00p 1:00p 5p','7:04a 6:30p 6:45p n8a',{'auth_hrs':24,'day_type':'reg','late_allowance_minutes':5,'minimum_ot_minutes':15}],['12p 6:00p 7:00p 9p','12:04p 6:30p 6:45p n8a',{'auth_hrs':24,'day_type':'reg','late_allowance_minutes':5,'minimum_ot_minutes':15}]]
	for test in tests:tsch=test[0];tlog=test[1];defs=test[2];print();print('-----------------------------------');compute_worktime(tsch,tlog,defs=defs)
if __name__=='__main__':sch='7a 6:00p N7:00p N9p';tp=timestr_to_timepair(sch);print(tp);print(tp>>480)