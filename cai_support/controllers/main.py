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
