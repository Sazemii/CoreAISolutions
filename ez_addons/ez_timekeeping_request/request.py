from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError,UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import base64,time,logging
_logger=logging.getLogger(__name__)
class Requests(models.Model):
	_name='ez.time.request';_description='Timekeeping Request';_inherit=['mail.thread'];_order='date desc, name asc, employee_id'
	def _default_employee(A):return A.env.context.get('default_employee_id')or A.env['hr.employee'].search([('user_id','=',A.env.uid)],limit=1)
	name=fields.Char('Request Name');employee_id=fields.Many2one('hr.employee','Employee',default=_default_employee,ondelete='cascade',index=True);department_id=fields.Many2one(string='Department',readonly=True,related='employee_id.department_id');company_id=fields.Many2one('res.company','Company',related='employee_id.company_id',related_sudo=True);user_id=fields.Many2one('res.users',string='User',related='employee_id.user_id',related_sudo=True,store=True,readonly=True);date=fields.Date('Date',default=fields.Date.context_today,required=True,index=True);time=fields.Char('Time Range',required=False,help='Enter time in pairs. Prefix with N for next day. Example: 6p 10p 11p N07:30');auth_hrs=fields.Float('Auth. Hours');note=fields.Text(string='Notes');type=fields.Selection([('ot','Overtime'),('ob','Official Business')],string='Request Type',default=lambda self:'ot');state=fields.Selection([('draft','Draft'),('sent','For Approval'),('denied','Denied'),('approved','Approved')],string='State',default=lambda self:'draft',tracking=True,readonly=True);can_approve=fields.Boolean('Can Approve',compute='_compute_can_approve');bulk_id=fields.Many2one('ez.time.request.bulk',string='Bulk',ondelete='set null');is_timekeeping_user=fields.Boolean(compute='_compute_can_approve')
	@api.depends('state','employee_id')
	def _compute_can_approve(self):
		A=self;C=A.env.user.has_group('ez_timekeeping.group_timekeeping_manager');D=A.env.user.has_group('ez_timekeeping.group_timekeeping_user')
		for B in A.sudo():
			B.is_timekeeping_user=D
			if B.employee_id.timekeeping_manager_id.id==A.env.user.id or C:B.can_approve=True
			else:B.can_approve=False
	@api.onchange('time')
	def onchange_time(self):
		E=self.env['ez.time.record']
		for A in self:
			if A.time and A.time[:3]!='ERR':
				try:
					B=E.parse_sched(A.time);D=[]
					for C in range(0,len(B),2):
						if B[C]<B[C+1]:D.append('%s-%s'%(B[C],B[C+1]))
						else:raise ValidationError(_('Wrong format.'))
					A.time=' '.join(D)
				except:A.time='ERR '+A.time
	def unlink(A):
		if'approved'in A.mapped('state'):raise UserError(_('You cannot delete an approved request.'))
		return super(Requests,A).unlink()
	def write(B,values):
		A=values
		if A.get('state'):B._check_approval_update(A['state'])
		return super(Requests,B).write(A)
	def to_sent(A):A._check_timecard();A.sudo()._change_state('sent',process_new_records=False)
	def to_draft(A):A._check_timecard();A._change_state('draft')
	def to_denied(A):A._check_timecard();A._change_state('denied')
	def _check_timecard(B):
		E=B.env['ez.time.record']
		for A in B:
			D=B.env['ez.time.record'].search([('employee_id','=',A.employee_id.id),('date','=',A.date)])
			for C in D:
				if'approv'in C.state or'sent'in C.state:raise UserError(_('Time card of employee is done and not editable.\nRevert timecard to non-approved state before changing request.\n%s %s')%(A.employee_id.name,A.date))
	def _change_state(A,new_state,process_new_records=True):
		B=new_state;_logger.debug('_change_state: %s',B);A._check_approval_update(B);D=A.env['ez.time.record']
		for C in A:E=A.env['ez.time.record'].search([('employee_id','=',C.employee_id.id),('date','=',C.date)]);D|=E;C.state=B
		if process_new_records:D._process_new_records()
	def _check_approval_update(A,state):
		' Check if target state is achievable. ';B=state;D=A.env['hr.employee'].search([('user_id','=',A.env.uid)],limit=1);F=A.env.user.has_group('ez_timekeeping.group_timekeeping_user');E=A.env.user.has_group('ez_timekeeping.group_timekeeping_manager')
		for C in A:
			_logger.debug('_check_approval_update: state=%s',B)
			if B in['draft','sent']and C.employee_id==D:continue
			if not(A.env.user._is_admin or C.can_approve or F or E):raise UserError(_('You do not have approving rights.'))
			if B=='approved':
				if C.employee_id==D and not E:raise UserError(_('Only a Timekeeping Manager can approve its own time card.'))
				continue
			if B=='denied':
				if C.employee_id==D and not E:raise UserError(_('Only a Timekeeping Manager can deny its own time card.'))
				continue
	def approve_record(A):A._check_approval_update('approved');A._check_timecard();A._change_state('approved')
	def _track_template(A,changes):
		D=super()._track_template(changes);_logger.debug('TRACK: %s',A.state);C=A[0];B=False
		if C.state=='sent':B=A.env.ref('ez_timekeeping_request.request_for_approval_email_template')
		elif C.state=='denied':B=A.env.ref('ez_timekeeping_request.request_denied_email_template')
		elif C.state=='approved':B=A.env.ref('ez_timekeeping_request.request_approved_email_template')
		if B:D['stage_id']=B,{'auto_delete_keep_log':False,'subtype_id':A.env['ir.model.data']._xmlid_to_res_id('mail.mt_note'),'email_layout_xmlid':'mail.mail_notification_layout'}
		return D
class RequestsBulk(models.Model):
	_name='ez.time.request.bulk';_description='Timekeeping Bulk Request';_inherit=['mail.thread'];_order='date desc, name asc';company_id=fields.Many2one('res.company','Company',default=lambda self:self.env.company);name=fields.Char('Bulk Request Name');date=fields.Date('Date',default=fields.Date.context_today,required=True,index=True);emp_tag_ids=fields.Many2many('hr.employee.category','bulk_request_tag_rel','bulk_id','emp_tag_id',string='Employee Tags');state=fields.Selection([('draft','Draft'),('sent','For Approval'),('approved','Approved')],string='State',default=lambda self:'draft',tracking=True,readonly=True);type=fields.Selection([('ot','Overtime'),('ob','Official Business')],string='Request Type',default=lambda self:'ot');time=fields.Char('Time Range',required=False,help='Enter time in pairs. Prefix with N for next day. Example: 6p 10p 11p N07:30');auth_hrs=fields.Float('Auth. Hours');note=fields.Text(string='Notes');request_ids=fields.One2many('ez.time.request','bulk_id','Requests')
	@api.model
	def custom_add(self,rec,request,employee_id):return False
	def btn_add(A):
		A.ensure_one()
		if A.state!='draft':return
		E=A.request_ids.mapped('employee_id.id');filter=[('id','not in',E)];D=[A.id for A in A.emp_tag_ids]
		if D:filter.append(('category_ids','in',D))
		F=A.env['hr.employee'].search(filter)
		for C in F:
			_logger.debug('btn_add: %s',C.name);B={}
			if A.type=='ot'and A.auth_hrs>.0:B.update({'auth_hrs':A.auth_hrs})
			elif A.type=='ob'and A.time:B.update({'auth_hrs':A.auth_hrs,'time':A.time})
			else:A.custom_add(B,A,C)
			if B:B.update({'bulk_id':A.id,'employee_id':C.id,'name':A.name,'type':A.type,'date':A.date});A.sudo().request_ids.create(B)
	def btn_approve(A):
		A.ensure_one()
		for B in A.request_ids:B._check_approval_update('approved');B._check_timecard();B._change_state('approved')
		A.state='approved'
	def btn_for_approval(A):
		A.ensure_one()
		for B in A.request_ids:B._check_timecard();B.sudo()._change_state('sent',process_new_records=False)
		A.state='sent'
	def btn_draft(A):
		A.ensure_one()
		for B in A.request_ids:B._check_timecard();B._change_state('draft')
		A.state='draft'
	def unlink(A):
		if'approved'in A.mapped('state'):raise UserError(_('You cannot delete an approved request.'))
		return super(RequestsBulk,A).unlink()
	@api.onchange('time')
	def onchange_time(self):
		E=self.env['ez.time.record']
		for A in self:
			if A.time and A.time[:3]!='ERR':
				try:
					B=E.parse_sched(A.time);D=[]
					for C in range(0,len(B),2):
						if B[C]<B[C+1]:D.append('%s-%s'%(B[C],B[C+1]))
						else:raise ValidationError(_('Wrong format.'))
					A.time=' '.join(D)
				except:A.time='ERR '+A.time