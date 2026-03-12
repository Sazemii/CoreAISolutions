from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools.safe_eval import safe_eval
import random,logging
_logger=logging.getLogger(__name__)
class TimecardGrpup(models.Model):
	_name='ez.time.card.group';_description='Time Card Group';_auto=False;_rec_name='id';_order='date2 desc, date1 desc, company_id';company_id=fields.Many2one('res.company',string='Company');name=fields.Char(compute='_get_name');date1=fields.Date(string='Date From');date2=fields.Date(string='Date To');color=fields.Integer(string='Color Index',compute='_get_default_color');count=fields.Integer(string='Count');states=fields.Html(compute='_compute_states');multi_company=fields.Binary(compute='_compute_multi_company')
	def _compute_multi_company(A):
		B=A.env.user.has_group('base.group_multi_company')
		for C in A:C.multi_company=B
	def _compute_states(F):
		G=F.env['ez.time.card']
		for C in F:
			A={};I=G.search([('company_id','=',C.company_id.id),('date1','=',C.date1),('date2','=',C.date2)])
			for J in I:
				E=dict(G._fields['state'].selection).get(J.state)
				if E not in A:A[E]=1
				else:A[E]+=1
			H=[]
			for B in sorted(A.keys()):
				K=A[B]
				if B=='Denied':D='text-bg-danger'
				elif B=='Approved':D='text-bg-success'
				elif B=='For Approval':D='text-bg-warning'
				else:D='text-bg-light'
				L=f"{B} - {K}";H.append(f'<span class="badge rounded-pill {D}">{L}</span>')
			C.states=' '.join(H)
	def _get_name(B):
		for A in B:A.name='Group %s to %s'%(fields.Date.from_string(A.date1).strftime('%B-%d'),fields.Date.from_string(A.date2).strftime('%B-%d-%Y'))
	def _get_default_color(B):
		A=0
		for C in B:C.color=A%10+1;A+=1
	def init(A):tools.drop_view_if_exists(A.env.cr,'ez_time_card_group');A.env.cr.execute('\n            CREATE VIEW ez_time_card_group AS (\n                SELECT\n                    MIN(tc.id) AS id,\n                    e.company_id AS company_id,\n                    tc.date1 AS date1,\n                    tc.date2 AS date2,\n                    COUNT(tc.*) AS count\n                FROM ez_time_card AS tc\n                INNER JOIN hr_employee AS e\n                    ON e.id = tc.employee_id\n                GROUP BY company_id, date1, date2                \n            )')
	def action_view_timecards(A):A.ensure_one();_logger.info('action_view_timecards %s',A.id);B=A.env.context;C='ez.time.card';return{'name':A.name,'type':'ir.actions.act_window','view_mode':'list,form','res_model':C,'target':'current','domain':[('company_id','=',A.company_id.id),('date1','=',A.date1),('date2','=',A.date2)],'context':B}