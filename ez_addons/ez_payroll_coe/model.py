from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
import logging
_logger=logging.getLogger(__name__)
class CertificateOfEmploymentLine(models.Model):_name='hr.ph.coe.line';_description='Certificate of Employment Lines';_order='sequence';coe_id=fields.Many2one('hr.ph.coe',string='Cert. of Employment');sequence=fields.Integer();name=fields.Char();amount=fields.Float(digits=(0,2))
class CertificateOfEmployment(models.Model):
	_name='hr.ph.coe';_description='Certificate of Employment';_inherit='mail.thread';_order='date desc'
	def _get_emp(A):
		B=A.env['hr.employee'].search([('user_id','=',A.env.user.id)])
		if B:return B[0].id
		else:return False
	def _get_notify_users(A):
		D=A.env.ref('ez_payroll_coe.group_coe_notify').user_ids.ids;E=A.env['res.users'].browse(D);B=[]
		for C in E:
			if C.company_id.id==A.env.company.id:B.append(C.id)
		return B
	company_id=fields.Many2one(related='employee_id.company_id');date=fields.Date(default=fields.Date.today);proper_date=fields.Char(compute='get_proper_date');employee_id=fields.Many2one('hr.employee',string='Employee',required=True,default=_get_emp);partner_id=fields.Many2one(related='employee_id.user_id.partner_id');image_1920=fields.Binary(related='employee_id.image_1920');avatar_128=fields.Binary(related='employee_id.avatar_128');certificate_type=fields.Selection([('without-compensation','Without Compensation'),('with-compensation','With Compensation'),('separated','Separated')],string='Certificate Type',default='without-compensation',required=True);date_from=fields.Date('Hired');date_to=fields.Date('Separated');gross=fields.Float(digits=(0,2),compute='_get_gross');gross_words=fields.Char(compute='_get_gross');purpose=fields.Selection([('Credit Card Application','Credit Card Application'),('Bank Loan Application','Bank Loan Application'),('International Travel','International Travel'),('Co-maker - Loan Application','Co-maker - Loan Application'),('Housing Loan Application','Housing Loan Application'),('Car Loan Application','Car Loan Application'),('Post-paid Cellular Plans','Post-paid Cellular Plans'),('Motor-vehicle Loan Applications','Motor-vehicle Loan Applications'),("Child's School Requirement","Child's School Requirement"),('Training and Certification Program','Training and Certification Program'),('Visa Application','Visa Application'),('Others','Others')],string='Purpose',default='Credit Card Application',required=True);country=fields.Char();others_purpose=fields.Char();position=fields.Char();assignment=fields.Char();employment_status=fields.Char();title=fields.Char();pronoun=fields.Char();possessive_pronoun=fields.Char();company=fields.Char('Company Name');company_address=fields.Char();company_city=fields.Char();company_phone=fields.Char();company_email=fields.Char();certified_name=fields.Char();certified_position=fields.Char('Cert. Position');certified_department=fields.Char('Cert. Department');state=fields.Selection([('draft','Draft'),('for-approval','For Approval'),('cancel','Cancelled'),('done','Done')],string='State',default='draft',required=True,tracking=True);salary_ids=fields.One2many('hr.ph.coe.line','coe_id','Salary Lines');user_access=fields.Boolean(compute='_get_user_access');approver_ids=fields.Many2many('res.users','coe_user_rel','coe_id','user_id',string='Notify Users',default=_get_notify_users);approver_emails=fields.Char('Notify Emails',compute='_get_approve_email')
	@api.depends('approver_ids')
	def _get_approve_email(self):
		for A in self:A.approver_emails=','.join([A.partner_id.email for A in A.approver_ids if'@'in(A.partner_id.email or'')])
	@api.depends('employee_id')
	def _get_user_access(self):
		B=self
		for A in B:
			if not A.employee_id:A.user_access=False
			elif B.env.user.has_group('ez_payroll_coe.group_coe_approver'):A.user_access=False
			elif B.env.user.id==A.employee_id.user_id.id:A.user_access=True
			else:A.user_access=False
	@api.depends('salary_ids')
	def _get_gross(self):
		for A in self:
			B=.0
			for E in A.salary_ids:B+=E.amount
			A.gross=B;C=self.env['hr.ph.payroll'].amount_to_words(A.gross).upper();D=C.split(' AND ')
			if'0/100'==D[1]:A.gross_words=D[0]
			else:A.gross_words=C
	def for_approval(B):
		for A in B:
			if A.user_access and A.certificate_type=='separated':raise ValidationError(_('You cannot "Set for Approval" the "separated" type certificate.'))
			A.date=fields.Date.today();A.state='for-approval'
	def to_done(A):
		if not A.env.user.has_group('hr.group_hr_user'):raise ValidationError(_('Invalid action. Not an HR user.'))
		for B in A:
			if B.state!='done':B.state='done'
	def to_draft(A):
		if not A.env.user.has_group('hr.group_hr_user'):raise ValidationError('Invalid action. Not an HR user.')
		for B in A:B.state='draft'
	def to_cancel(A):
		if not A.env.user.has_group('hr.group_hr_user'):raise ValidationError('Invalid action. Not an HR user.')
		for B in A:B.state='cancel'
	@api.depends('employee_id','date')
	def _compute_display_name(self):
		for A in self:A.display_name='Certificate of Employment [%s]'%A.employee_id.name
	@api.depends('date')
	def get_proper_date(self):
		for B in self:
			if B.date:
				A='%s'%int(B.date.strftime('%d'))
				if A=='1':A+='st'
				elif A=='21':A+='st'
				elif A=='31':A+='st'
				elif A=='2':A+='nd'
				elif A=='22':A+='nd'
				elif A=='3':A+='rd'
				elif A=='23':A+='rd'
				else:A+='th'
				C=B.date.strftime('%B %Y');B.proper_date=A+' day of '+C
			else:B.proper_date='(no date specified)'
	@api.onchange('certificate_type','date')
	def type_onchange(self):
		A=self;B=A.sudo().employee_id
		if B and A.certificate_type=='with-compensation':
			if B.salary_rate_period=='daily':C=B.salary_rate*B.emr_days
			else:C=B.salary_rate*12.
			H=C/12.;A.salary_ids=False;E=[(0,0,{'sequence':10,'coe_id':A.id,'name':'Annual Basic Salary','amount':C}),(0,0,{'sequence':20,'coe_id':A.id,'name':'13th Month Pay','amount':H})];I=A.env['ez.deminimis'].sudo().search([('employee_id','=',B.id)]);J=30;F=.0
			for D in I:
				if D.days_variable:G=D.qty*B.emr_days
				else:G=D.qty*12.
				F+=G
			E.append((0,0,{'sequence':J,'coe_id':A.id,'name':'Total Annual Allowance','amount':F}));A.salary_ids=E
	@api.onchange('employee_id')
	def employee_id_onchange(self):
		A=self;B=A.sudo().employee_id;A.type_onchange();A.date_from=B.hired;A.date_to=B.date_end
		if not A.date:A.date=fields.Date.today()
		A.position=(B.job_title or'').title();A.assignment=(B.department_id.name or'').title();E=dict(B._fields['employment_status'].selection);A.employment_status=E.get(B.employment_status,'(employment status not defined)').lower();A.title=B.sex=='female'and'Ms.'or'Mr.';A.pronoun=B.sex=='female'and'She'or'He';A.possessive_pronoun=B.sex=='female'and'her'or'his';A.company=B.company_id.name;A.company_city=B.company_id.city;A.company_address=B.company_id.partner_id.address_ph_format;A.company_phone=B.company_id.phone;A.company_email=B.company_id.email;F=int(A.sudo().env['ir.config_parameter'].get_param('coe_certified_id','0').strip());C=A.sudo().env['hr.employee'].browse(F);D=[]
		if C.first_name:D.append(C.first_name)
		if C.middle_name:D.append(C.middle_name[0]+'.')
		if C.last_name:D.append(C.last_name)
		A.certified_name=' '.join(D);A.certified_position=C.job_title;A.certified_department=C.department_id.name
	def _track_template(A,changes):
		C=super()._track_template(changes);_logger.debug('TRACK: %s',A.state);D=A[0];B=False
		if D.state=='done':B=A.env.ref('ez_payroll_coe.approved_coe_email_template')
		elif D.state=='for-approval':B=A.env.ref('ez_payroll_coe.for_approval_coe_email_template')
		if B:_logger.debug('TRACK2: %s %s',A.state,B);C['stage_id']=B,{'auto_delete_keep_log':False,'subtype_id':A.env['ir.model.data']._xmlid_to_res_id('mail.mt_note'),'email_layout_xmlid':'mail.mail_notification_layout'}
		return C