from ast import literal_eval
import babel
from dateutil.relativedelta import relativedelta
import itertools,json,base64,xlwt
from babel.dates import format_datetime,format_date
from odoo import http,fields,_
from odoo.http import request,content_disposition
from odoo.tools import float_round
from.pdfutil import create_pdf2,clean_tin
from zipfile import ZipFile,ZipInfo
import io,logging
_logger=logging.getLogger(__name__)
class PdfCreatorController(http.Controller):
	'\n    http://yourdomain.com/web/image/your_model/record_id/field_name\n    https://demo.eztechsoft.com/web/image/ez.bir.alphalist/8/signature_data\n    /web/image/<string:model>/<int:id>/<string:field>\n    '
	@http.route(['/bir2316-1/<int:alphalist1_id>','/bir2316-2/<int:alphalist2_id>','/bir2316-sched1/<int:schedule1_id>','/bir2316-sched2/<int:schedule2_id>'],type='http',auth='user')
	def bir2316(self,alphalist1_id=False,alphalist2_id=False,schedule1_id=False,schedule2_id=False):
		X=schedule2_id;W=schedule1_id;V=alphalist2_id;U=alphalist1_id;K='';L=request.env['ir.config_parameter'].sudo().get_param('web.base.url');A='document.pdf'
		if W:
			M=request.env['ez.bir.alphalist.schedule1'].browse([W])
			if M:N=M[0];C=N.employee_id;D,E,F,G=clean_tin(N.tin_no);A='%s_%s_%s.pdf'%(C.last_name,D+E+F+G,'1231'+N.alphalist_id.year);H=N.alphalist_id.year
			_logger.debug('PDF 2316: %s %s',M,L);K=create_pdf2(M,L,date=H);O=[('Content-Type','application/pdf'),('Content-Disposition',content_disposition(A))]
		elif X:
			P=request.env['ez.bir.alphalist.schedule2'].browse([X])
			if P:Q=P[0];C=Q.employee_id;D,E,F,G=clean_tin(Q.tin_no);A='%s_%s_%s.pdf'%(C.last_name,D+E+F+G,'1231'+Q.alphalist_id.year);H=Q.alphalist_id.year
			K=create_pdf2(P,L,is_mwe=True,date=H);O=[('Content-Type','application/pdf'),('Content-Disposition',content_disposition(A))]
		elif U:
			I=io.BytesIO()
			with ZipFile(I,'w')as R:
				B=request.env['ez.bir.alphalist'].browse([U]);M=B.schedule1_ids;H=B.year
				for J in B.schedule1_ids:C=J.employee_id;D,E,F,G=clean_tin(J.tin_no);A='%s_%s_%s.pdf'%(C.last_name,D+E+F+G,'1231'+B.year);S=ZipInfo(A);T=create_pdf2(J,L,date=H);R.writestr(S,T)
			K=I.getvalue();I.close();A='Schedule1 2316.zip';O=[('Content-Type','application/zip'),('Content-Disposition',content_disposition(A))]
		elif V:
			I=io.BytesIO()
			with ZipFile(I,'w')as R:
				B=request.env['ez.bir.alphalist'].browse([V]);P=B.schedule2_ids;H=B.year
				for J in B.schedule2_ids:C=J.employee_id;D,E,F,G=clean_tin(J.tin_no);A='%s_%s_%s.pdf'%(C.last_name,D+E+F+G,'1231'+B.year);S=ZipInfo(A);T=create_pdf2(J,L,is_mwe=True,date=H);R.writestr(S,T)
			K=I.getvalue();I.close();A='Schedule2 2316.zip';O=[('Content-Type','application/zip'),('Content-Disposition',content_disposition(A))]
		return request.make_response(K,headers=O)