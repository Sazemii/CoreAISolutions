from odoo import models,fields,api,_
from odoo.exceptions import UserError
import logging,random,base64
from.signature_utils import generate_signature_image_bytes,DEFAULT_FONT_NAME
_logger=logging.getLogger(__name__)
class HrEmployee(models.Model):
	_inherit='hr.employee';signature_image=fields.Binary('Signature',groups='hr.group_hr_user');signature_name_override=fields.Char('Name for Signature',groups='hr.group_hr_user',help="If blank, the employee's full name will be used. Use this to specify a different name or a preferred format for the signature.");signature_enabled=fields.Boolean(related='company_id.signature_enabled',compute_sudo=True,groups='base.group_user')
	def action_generate_signature(A):
		A.ensure_one();B=A.signature_name_override or A.name
		if not B:raise UserError(_('Employee name is not set. Cannot generate signature.'))
		if 1:D=random.uniform(-3,3);C=generate_signature_image_bytes(B,font_name=DEFAULT_FONT_NAME,rotation_angle=D);_logger.debug(f"ESIG: {A.name} - {C}");A.signature_image=base64.b64encode(C).decode('utf-8')
		return True
class HrEmployeePublic(models.Model):_inherit='hr.employee.public';signature_enabled=fields.Boolean(related='employee_id.signature_enabled',compute_sudo=True)