from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
_logger=logging.getLogger(__name__)
class WorkTypeGroup(models.Model):
	_name='ez.work.type.group';_description='Compensation Type Group';_order='name';name=fields.Char('Name',required=True);work_type_line=fields.One2many('ez.work.type','work_type_group_id','Compensation Types',copy=True);active=fields.Boolean()
	def copy(A,default=None):B=default;A.ensure_one();B=dict(B or{},name=_('%s (copy)')%A.name);return super(WorkTypeGroup,A).copy(B)
class WorkType(models.Model):_name='ez.work.type';_inherit='hr.ph.payslip.line.template';_description='Type of Work';_order='seq, name';work_type_group_id=fields.Many2one('ez.work.type.group','Compensation Type Group',required=True,ondelete='cascade');unit=fields.Selection(default='hour');active=fields.Boolean(related='work_type_group_id.active')