from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError,UserError
import logging
_logger=logging.getLogger(__name__)
class RequestsBulk(models.Model):
	_inherit='ez.time.request.bulk';type=fields.Selection(selection_add=[('change_approver_timekeeping','Change Timekeeping Approver'),('change_approver_timeoff','Change Time Off Approver'),('change_approver_attendance','Change Attendance Approver')]);new_approver_id=fields.Many2one('res.users',string='New Approver')
	@api.model
	def custom_add(self,rec,request,employee_id):
		B=request;A=self;C=super(RequestsBulk,A).custom_add(rec,B,employee_id)
		if B.type in('change_approver_timekeeping','change_approver_timeoff','change_approver_attendance')and A.approver_id:rec.update({'approver_id':A.approver_id.id});return True
		else:return C
class Requests(models.Model):
	_inherit='ez.time.request';type=fields.Selection(selection_add=[('change_approver_timekeeping','Change Timekeeping Approver'),('change_approver_timeoff','Change Time Off Approver'),('change_approver_attendance','Change Attendance Approver')]);new_approver_id=fields.Many2one('res.users',string='New Approver');old_approver_id=fields.Many2one('res.users',string='Previous Approver')
	@api.onchange('employee_id')
	def oc_employee_id(self):self.old_approver_id=self.employee_id.timekeeping_manager_id.id
	def _change_state(D,new_state,process_new_records=True):
		C=new_state;super()._change_state(C,process_new_records)
		for A in D.sudo():
			_logger.debug('Change app: %s %s',A.employee_id,A.new_approver_id)
			if A.type in('change_approver_timekeeping','change_approver_timeoff','change_approver_attendance'):
				A.old_approver_id=A.employee_id.timekeeping_manager_id.id;B=A.new_approver_id.id
				if not B:raise ValidationError(_('Approver %s has no login on the system.')%A.approver_id.name)
				A.state=C
				if C=='approved':
					if A.type=='change_approver_timekeeping':A.employee_id.timekeeping_manager_id=B
					elif A.type=='change_approver_timeoff':A.employee_id.leave_manager_id=B
					elif A.type=='change_approver_attendance':A.employee_id.attendance_manager_id=B
	@api.depends('state','employee_id','new_approver_id')
	def _compute_can_approve(self):
		B=self;C=B.env.user.has_group('ez_timekeeping.group_timekeeping_manager');D=B.env.user.has_group('ez_timekeeping.group_timekeeping_user')
		for A in B.sudo():
			A.is_timekeeping_user=D
			if A.employee_id.timekeeping_manager_id.id==B.env.user.id or C:A.can_approve=True
			elif A.new_approver_id.id==B.env.user.id:A.can_approve=True
			else:A.can_approve=False