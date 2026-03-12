from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
import logging,re,base64,requests,pprint
_logger=logging.getLogger(__name__)
class Payroll(models.Model):
	_inherit='hr.ph.payroll'
	def _send_email(B,payslip_id):A=payslip_id;C={};C['email_to']=A.employee_id.work_email;H=B.env.lang or'en_US';D=f"""
            <p>Dear {A.employee_id.name},</p>
            <p>Attached is your payslip for the period of
            {A.date_from.strftime("%B %d, %Y")}
            to {A.date_to.strftime("%B %d, %Y")}.</p>
            </p>
            <p>Thank you for your hard work!</p>
            <p><b>{A.company_id.name}</b></p>
        """;_logger.debug('Email body rendered: %s',pprint.pformat(D));E=B.env.ref('ez_payroll.action_print_single_payslip');F,I=E._render_qweb_pdf(E.report_name,res_ids=[A.id]);G=base64.b64encode(F);J=B.env['mail.mail'].sudo().create({'subject':f"Payslip for {A.employee_id.name}",'email_from':A.company_id.email_formatted,'body_html':D,'attachment_ids':[(0,0,{'name':f"Payslip - {A.employee_id.name}.pdf",'datas':G,'mimetype':'application/pdf'})],**C})
	def action_email_payslips(A):
		def D(email):A='^[\\w\\.-]+@[\\w\\.-]+\\.\\w+$';return re.match(A,email)is not None
		A.ensure_one()
		if not A.payslip:raise ValidationError(_('No payslip to email.'))
		for B in A.payslip:
			C=B.employee_id.work_email
			if C and D(C):A._send_email(B)