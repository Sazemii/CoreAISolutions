from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
import time,logging
_logger=logging.getLogger(__name__)
class PayslipInherit(models.Model):
	_inherit='hr.ph.payslip'
	@api.model
	def get_timecard_compensation_lines(self):
		D=self
		def H(r,compensation_name,name,factor):
			B=factor;A=name;C=False
			if compensation_name in A:
				E=D.browse(r.get('payslip_id'));F=E.employee_id
				if F.no_night_differential:A=A.replace(' (night)','');B=r.get('factor',1.)/1.1;C=True
			return C,A,B
		def I(r,compensation_name,name,factor):
			A=factor;B=False
			if compensation_name in name:
				C=D.browse(r.get('payslip_id'));E=C.employee_id
				if E.no_overtime:A=.0;B=True
			return B,name,A
		J=super(PayslipInherit,D).get_timecard_compensation_lines();K=['Regular Overtime (night)','Restday Work (night)','Restday Overtime (night)','RH Work (night)','RH Overtime (night)','SH Work (night)','SH Work Overtime (night)','RH+RD Work (night)','RH+RD Overtime (night)','SH+RD Work (night)','SH+RD Overtime (night)'];L=['Regular Overtime','Restday Work','Restday Overtime'];G=[]
		for A in J:
			C=A.get('name','');B=A.get('factor',.0)
			if'Night Differential'in C:
				M=D.browse(A.get('payslip_id'));N=M.employee_id
				if N.no_night_differential:B=.0
			else:
				for E in K:
					F,C,B=H(A,E,C,B)
					if F:break
			for E in L:
				F,C,B=I(A,E,C,B)
				if F:break
			if B!=.0:A['name']=C;A['factor']=B;G.append(A)
		return G