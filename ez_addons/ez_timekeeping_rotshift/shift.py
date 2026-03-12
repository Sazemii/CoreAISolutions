from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
_logger=logging.getLogger(__name__)
DF='%Y-%m-%d'
class Shift(models.Model):
	_inherit='ez.shift'
	def get_rotate_start(B):A=fields.Date.from_string(fields.Date.context_today(B));C=A.weekday();A=A-relativedelta(days=C);return A
	is_rotate_shift=fields.Boolean('Rotating Shift');rotate_date_start=fields.Date('Date Start',default=get_rotate_start);rotate_ids=fields.One2many('ez.shift.rotate','shift_id','Rotate Schedule');invisible_sched=fields.Boolean(compute='_get_invisible_sched2')
	@api.depends('is_rotate_shift')
	def _get_invisible_sched2(self):
		for A in self:A.invisible_sched=A.is_rotate_shift
	@api.model
	def get_schedule(self,date1,date2):
		H=date2;G=date1;A=self;A.ensure_one();_logger.debug('get_schedule: %s to %s',G,H)
		if A.is_rotate_shift:
			I={};C=fields.Date.from_string(G);Q=fields.Date.from_string(H);N=fields.Date.from_string(A.rotate_date_start);J={};B=0;F=0
			for K in A.rotate_ids:
				if len(K.line_shift_id.details)!=7:raise ValidationError(_('Config error. Schedule for rotating shifts must be of 7 days.\n%s - %s')%(A.name,K.line_shift_id.name))
				for L in K.line_shift_id.details:D='%s-%s'%(B,L.day);J[D]=L;_logger.debug('base schedule: k=%s day=%s',D,L.day);F+=1
				B+=1
			_logger.debug('schedule: %s',J);O=B
			if F==0:raise ValidationError(_('Invalid rotating shift definition.\n%s')%A.name)
			R=int(N.strftime('%w'));P=(10000*F+(C-N).days)%F;E=P%7;B=(P-E)/7%O
			while C<=Q:
				D='%s-%s'%(int(B),(E+R)%7);M=J.get(D);_logger.debug('schedule: k=%s date=%s day=%s dow=%s',D,C.strftime(DF),M and M.day,C.strftime('%w'));I[C.strftime(DF)]=M;C+=relativedelta(days=1);E+=1
				if E>=7:B=(B+1)%O;E=0
		else:I=super(Shift,A).get_schedule(G,H)
		return I
class RotateLines(models.Model):_name='ez.shift.rotate';_description='Rotating Shift Schedule';_order='sequence, id';shift_id=fields.Many2one('ez.shift','Shift',ondelete='cascade',readonly=True);sequence=fields.Integer('Seq',default=10);line_shift_id=fields.Many2one('ez.shift','Shift Line');name=fields.Char(related='line_shift_id.name',readonly=True);days=fields.Integer(default=7);note=fields.Text('Notes')