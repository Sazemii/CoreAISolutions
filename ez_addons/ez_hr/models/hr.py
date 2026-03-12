from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
from datetime import datetime,timedelta
from dateutil.relativedelta import relativedelta
import random,logging
_logger=logging.getLogger(__name__)
class EmpEducation(models.Model):_name='hr.employee.education';_description='Educational Background';_order='start_date';emp_id=fields.Many2one('hr.employee','Employee',ondelete='cascade');level=fields.Selection([('Elementary','Elementary'),('High School','High School'),('Vocational','Vocational'),('College','College'),('Masters','Masters'),('Doctorate','Doctorate')],string='Level');name=fields.Char(string='Name of School');course=fields.Char('Course');school_address=fields.Char(string='School Address');start_date=fields.Date(string='Start Date');end_date=fields.Date(string='End Date');note=fields.Text(string='Awards/Honors/Notes')
class EmpTraining(models.Model):_name='hr.employee.training';_description='Training';_order='start_date desc';emp_id=fields.Many2one('hr.employee',string='Employee',required=True,ondelete='cascade');name=fields.Char();start_date=fields.Date();end_date=fields.Date();bond_expiry=fields.Date();bond_amount=fields.Float(digits=(0,2));note=fields.Text(string='Notes')
class EmpExperience(models.Model):_name='hr.employee.experience';_description='Work Experience';_order='start_date desc';emp_id=fields.Many2one('hr.employee',string='Employee',required=True,ondelete='cascade');name=fields.Char(string='Position/Job Title');employer=fields.Char(string='Employer');start_date=fields.Date(string='Start Date');end_date=fields.Date(string='End Date');note=fields.Text(string='Responsibilities/Achievement/Notes')
class EmpDependents(models.Model):_name='hr.employee.dependents';_description='Employee Dependents';_order='birthday';emp_id=fields.Many2one('hr.employee','Employee',ondelete='cascade');name=fields.Char('Name');relation=fields.Char('Relation');birthday=fields.Date('Birthday');phone=fields.Char('Contact No.');qualified=fields.Boolean('Qualified',default=True,help='Check if dependent is a qualified one.');note=fields.Text('Notes')
class EmpInfractions(models.Model):_name='hr.employee.infraction';_description='Infractions/Violations';_order='date desc';emp_id=fields.Many2one('hr.employee','Employee',ondelete='cascade');name=fields.Char('Description');date=fields.Date('Date');penalty=fields.Selection([('Verbal Warning','Verbal Warning'),('Written Warning','Written Warning'),('Suspension','Suspension'),('Dismissal','Dismissal')],'Penalty');note=fields.Text('Notes')
class EmpCustodianship(models.Model):_name='hr.employee.custodianship';_description='Custodianship';_order='received desc';emp_id=fields.Many2one('hr.employee','Employee',ondelete='cascade');received=fields.Date('Received');returned=fields.Date('Returned');name=fields.Char('Item');description=fields.Char('Description');note=fields.Text('Notes')
class EmpHealthRecord(models.Model):_name='hr.employee.health';_description='Employee Health Record';_order='date desc';emp_id=fields.Many2one('hr.employee','Employee',ondelete='cascade');date=fields.Date('Date');alarm=fields.Boolean('Alarm',help='Included in daily report if date has passed. Uncheck this to remove it.');name=fields.Char('Description');temp=fields.Float('Temperature',digits=(7,2));weight=fields.Float('Weight',digits=(7,2));height=fields.Float('Height',digits=(7,2));bp=fields.Char('B.P.');note=fields.Text('Notes')
class HrEmployee(models.Model):
	_inherit='hr.employee';hired=fields.Date(string='Date Hired',related='date_start',groups='hr.group_hr_user',tracking=True);date_end=fields.Date(string='Resigned/Terminated',groups='hr.group_hr_user',tracking=True);regularization_date=fields.Date(string='Date Regularize',groups='hr.group_hr_user',compute='_get_date_regularize');nationality=fields.Char('Nationality',groups='hr.group_hr_user',tracking=True);employment_status=fields.Selection([('R','Regular'),('C','Casual'),('CP','Contractual/Project-Based'),('S','Seasonal'),('P','Probationary'),('S','Seasonal')],'Employment Status',default='R',groups='hr.group_hr_user',tracking=True);separation_reason=fields.Selection([('T','Terminated/Resigned'),('TR','Transferred'),('R','Retirement'),('D','Death')],'Reason of Separation',groups='hr.group_hr_user',tracking=True);for_separation=fields.Boolean('For Separation',groups='hr.group_hr_user',tracking=True);resignation_submitted=fields.Boolean('Resignation Submitted',groups='hr.group_hr_user',tracking=True);voluntary_separation=fields.Char(groups='hr.group_hr_user',tracking=True);home_address=fields.Text('Home Address',compute='_get_home_address',groups='hr.group_hr_user',tracking=True);home_zip=fields.Char('ZIP Code',groups='hr.group_hr_user',tracking=True);provincial_address=fields.Text('Provincial Address',groups='hr.group_hr_user',tracking=True);provincial_zip=fields.Char('Provl ZIP Code',groups='hr.group_hr_user',tracking=True);identification_id=fields.Char(string='ID Number',index=True,groups='hr.group_hr_user',tracking=True);sss_no=fields.Char(string='SSS Number',groups='hr.group_hr_user',tracking=True);tin_no=fields.Char(string='TIN',groups='hr.group_hr_user',tracking=True);phic_no=fields.Char(string='PHIC Number',groups='hr.group_hr_user',tracking=True);pagibig_no=fields.Char(string='HDMF Number',groups='hr.group_hr_user',tracking=True);atm_no=fields.Char(string='ATM Number',groups='hr.group_hr_user',tracking=True);hmo_no=fields.Char(string='HMO Number',groups='hr.group_hr_user',tracking=True);with_nbi=fields.Boolean(string='With NBI Clearance',groups='hr.group_hr_user',tracking=True);educ_line=fields.One2many('hr.employee.education','emp_id','Educational Background',groups='hr.group_hr_user');experience_line=fields.One2many('hr.employee.experience','emp_id','Work Experience',groups='hr.group_hr_user');dependent_line=fields.One2many('hr.employee.dependents','emp_id','Dependents',groups='hr.group_hr_user');infraction_line=fields.One2many('hr.employee.infraction','emp_id','Infractions/Violations',groups='hr.group_hr_user');custod_line=fields.One2many('hr.employee.custodianship','emp_id','Custodianship',groups='hr.group_hr_user');health_line=fields.One2many('hr.employee.health','emp_id','Health',groups='hr.group_hr_user');training_line=fields.One2many('hr.employee.training','emp_id','Training',groups='hr.group_hr_user');years_service=fields.Char('Years of Service',groups='hr.group_hr_user',compute='_get_years_service');age=fields.Float('Age',digits=(0,2),groups='hr.group_hr_user',compute='_get_age');personal_email=fields.Char('Personal E-mail',groups='hr.group_hr_user');emergency_address=fields.Char(groups='hr.group_hr_user',tracking=True);emergency_relation=fields.Char(groups='hr.group_hr_user',tracking=True)
	def _get_marital_status_selection(B):A=super()._get_marital_status_selection();A+=[('separated',_('Separated')),('annulled',_('Annulled'))];return A
	@api.depends('hired')
	def _get_date_regularize(self):
		for A in self:
			if A.hired:A.regularization_date=fields.Date.from_string(A.hired)+relativedelta(months=6)
			else:A.regularization_date=False
	@api.depends('private_street','private_street2','private_city','private_state_id','private_country_id')
	def _get_home_address(self):
		for A in self:
			B=[]
			if A.private_street:B.append(A.private_street)
			if A.private_street2:B.append(A.private_street2)
			if A.private_state_id:B.append(A.private_state_id.name)
			if A.private_country_id:B.append(A.private_country_id.name)
			A.home_address=', '.join(B)
	def _get_years_service(D):
		for A in D:
			if A.date_end:C=fields.Date.from_string(A.date_end)
			else:C=fields.Date.today()
			B=relativedelta(C,fields.Date.from_string(A.hired));A.years_service='%s years, %s months and %s days'%(B.years,B.months,B.days)
	def _get_age(C):
		for B in C:A=relativedelta(fields.Date.today(),fields.Date.from_string(B.birthday));B.age=A.years+A.months/12.+A.days/365.
	def check_6month_alarm(C):
		H=dict(C.env.context);M=H.get('days_before',15);I=fields.Date.from_string(fields.Date.context_today(C));E=I-relativedelta(months=6);J=E+timedelta(days=M);K=C.sudo().env['hr.employee'].search([('hired','<=',J),('hired','>=',E),('date_end','=',False)]);F=C.env.ref('hr.group_hr_user');G=[]
		for L in F.users:
			if'@'in L.partner_id.email:G.append(L.partner_id.email)
		A='\n            <style type="text/css">\n                #customers {\n                    font-family: Arial, Helvetica, sans-serif;\n                    border-collapse: collapse;\n                    width: 100%;\n                }\n\n                #customers td, #customers th {\n                    border: 1px solid #ddd;\n                    padding: 8px;\n                }\n\n                #customers tr:nth-child(even){background-color: #f2f2f2;}\n                #customers tr:hover {background-color: #ddd;}\n\n                #customers th {\n                    padding-top: 12px;\n                    padding-bottom: 12px;\n                    text-align: left;\n                    background-color: #04AA6D;\n                    color: white;\n                }\n            </style>\n        ';A+='<h2>%s</h2>'%C.env.company.name;A+='<div><b>Employees that were hired 5.5 to 6 months ago.</b></div><br/>\n';A+="<table id='customers'>\n";A+='<tr><th>ID Number</th><th>Name</th>';A+='<th>Title</th><th>Department</th>';A+='<th>Hired</th>';A+='</tr>\n'
		for B in K:A+='<tr>\n';A+='<td>%s</td>'*5%(B.identification_id,B.name,B.job_title,B.department_id.name,B.hired);A+='</tr>\n'
		A+='</table>\n';N={'subject':C.env.company.name+' '+I.strftime('Employee Report %m-%d-%Y'),'body_html':A,'email_to':','.join(G),'auto_delete':False};O=C.env['mail.mail'].sudo().create(N);O.sudo().send()
		if 0:
			D='CHK: ctx=%s dt6=%s dt6b4=%s'%(H,E,J)
			for B in K:D+='\n%s hired=%s '%(B.name,B.hired)
			D+='\n\nUsers: %s %s'%(F.users,','.join(G));D+='\n\nHR Group: %s'%F.name;raise ValidationError(D)
class Partner(models.Model):
	_inherit='res.partner';address_ph_format=fields.Char(compute='_get_address_ph_format')
	@api.depends('street','street2','city','state_id','zip','country_id')
	def _get_address_ph_format(self):
		for A in self:
			B=[]
			if A.street:B.append(A.street)
			if A.street2:B.append(A.street2)
			if A.city:B.append(A.city)
			if A.state_id:B.append(A.state_id.name)
			if A.country_id:B.append(A.country_id.name)
			C=', '.join(B)
			if A.zip:C+=' '+A.zip
			A.address_ph_format=C.strip()