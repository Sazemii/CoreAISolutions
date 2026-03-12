from collections import OrderedDict
from operator import itemgetter
from odoo import _,http
from odoo.exceptions import AccessError,MissingError
from odoo.http import request
from odoo.tools import groupby as groupbyelem
from odoo.addons.portal.controllers.portal import CustomerPortal,pager as portal_pager
import random,hashlib
from.import portal_payslip_controller
import logging
_logger=logging.getLogger(__name__)
class PortalBIR2316(portal_payslip_controller.PortalPayslip):
	_items_per_page=20
	def _get_bir2316_counters(C):
		A={};D=request.env['ir.config_parameter'].sudo();E=int(D.get_param('bir2316_count','0').strip())
		if E and'bir2316_count':
			F=request.env['ez.bir.alphalist.schedule1'].sudo();B=F.search_count(C._get_bir2316_domain(),limit=1)
			if not B:G=request.env['ez.bir.alphalist.schedule2'].sudo();B=G.search_count(C._get_bir2316_domain(),limit=1)
			A['bir2316_count']=B
		else:A['bir2316_count']=0
		return A
	def _prepare_home_portal_values(D,counters):
		A=counters;B=super()._prepare_home_portal_values(A)
		for(C,E)in D._get_bir2316_counters().items():
			if C in A:B[C]=E
		return B
	def _get_bir2316_domain(B):A=[('employee_id.work_email','=',request.env.user.login),('state','!=','draft')];return A
	def _get_bir2316_searchbar_sortings(B):A={'date':{'label':_('Date'),'order':'date_end desc'},'net_taxable_income':{'label':_('Taxable Income'),'order':'net_taxable_income desc'}};_logger.debug('_get_searchbar_sortings 2316: %s',A);return A
	def _get_bir2316_searchbar_filters(A):return{'all':{'label':_('All'),'domain':[]}}
	def _bir2316_prepare_my_values(B,page,date_begin,date_end,sortby,filterby,searchbar_sortings,searchbar_filters,domain=None,url='/my/bir2316s',model='ez.bir.alphalist.schedule1',page_name='bir2316'):
		C=model;D=request.env['ez.bir.alphalist.schedule1'].sudo();E=D.search(B._get_bir2316_domain(),limit=1)
		if not E:C='ez.bir.alphalist.schedule2'
		A=B._prepare_my_values(page,date_begin,date_end,sortby,filterby,searchbar_sortings,searchbar_filters,domain=domain,url=url,model=C,page_name=page_name);A['model']=C;A.update(B._get_bir2316_counters());_logger.debug('_prepare_my_values 2316: %s',A);return A
	@http.route(['/my/bir2316s','/my/bir2316s/page/<int:page>'],type='http',auth='user',website=True)
	def portal_my_bir2316s(self,page=1,date_begin=None,date_end=None,sortby=None,filterby=None,**J):D=date_end;C=date_begin;B=self;C=False;D=False;G=B._get_bir2316_domain();H=B._get_bir2316_searchbar_sortings();I=B._get_bir2316_searchbar_filters();A=B._bir2316_prepare_my_values(page,C,D,sortby,filterby,H,I,domain=G);E=portal_pager(**A['pager']);F=A['records'](E['offset']);request.session['my_bir2316s_history']=F.ids[:100];A.update({'records':F,'pager':E,'schedule':A.get('model')=='ez.bir.alphalist.schedule1'and 1 or 0});return request.render('ez_payroll_ess.portal_my_bir2316',A)