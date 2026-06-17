import base64
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class SupportController(http.Controller):

    @http.route(
        '/support/submit',
        type='http',
        auth='public',
        methods=['POST'],
        csrf=False,
        cors='*',
    )
    def support_submit(self, **kwargs):
        required_fields = ['customer_name', 'customer_email', 'subject', 'description']
        missing = [f for f in required_fields if not kwargs.get(f)]
        if missing:
            return request.make_json_response(
                {'success': False, 'error': f'Missing required fields: {", ".join(missing)}'},
                status=400,
            )

        try:
            ticket_vals = {
                'customer_name': kwargs['customer_name'],
                'customer_email': kwargs['customer_email'],
                'customer_phone': kwargs.get('customer_phone', ''),
                'subject': kwargs['subject'],
                'description': kwargs['description'],
                'category': kwargs.get('category', 'general'),
                'priority': kwargs.get('priority', 'medium'),
                'database_link': kwargs.get('database_link', ''),
                'module_link': kwargs.get('module_link', ''),
            }

            files = request.httprequest.files.getlist('attachments')
            attachment_ids = []
            for f in files:
                if f and f.filename:
                    data = base64.b64encode(f.read())
                    att = request.env['ir.attachment'].sudo().create({
                        'name': f.filename,
                        'datas': data,
                        'res_model': 'support.ticket',
                        'type': 'binary',
                    })
                    attachment_ids.append(att.id)
            if attachment_ids:
                ticket_vals['attachment_ids'] = [(6, 0, attachment_ids)]

            ticket = request.env['support.ticket'].sudo().create(ticket_vals)
            return request.make_json_response({
                'success': True,
                'ticket_id': ticket.name,
                'message': 'Your support ticket has been submitted successfully.',
            })
        except Exception:
            _logger.exception('Failed to create support ticket')
            return request.make_json_response(
                {'success': False, 'error': 'An error occurred. Please try again.'},
                status=500,
            )

    @http.route(
        '/demo/submit',
        type='http',
        auth='public',
        methods=['POST'],
        csrf=False,
        cors='*',
    )
    def demo_submit(self, **kwargs):
        required_fields = ['name', 'email']
        missing = [f for f in required_fields if not kwargs.get(f)]
        if missing:
            return request.make_json_response(
                {'success': False, 'error': f'Missing required fields: {", ".join(missing)}'},
                status=400,
            )

        # The landing page sends the modal label ("Request a Demo" /
        # "Book a Consultation"); use it to title the lead.
        request_label = (kwargs.get('request_type') or 'Website Inquiry').strip()

        try:
            lead = request.env['crm.lead'].sudo().create({
                'name': f'{request_label} - {kwargs["name"]}',
                'type': 'lead',
                'contact_name': kwargs['name'],
                'email_from': kwargs['email'],
                'phone': kwargs.get('phone', ''),
                'description': kwargs.get('message', ''),
            })
            return request.make_json_response({
                'success': True,
                'lead_id': lead.id,
                'message': 'Your request has been submitted successfully.',
            })
        except Exception:
            _logger.exception('Failed to create CRM lead')
            return request.make_json_response(
                {'success': False, 'error': 'An error occurred. Please try again.'},
                status=500,
            )
