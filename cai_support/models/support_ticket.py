from markupsafe import Markup

from odoo import api, fields, models

SUPPORT_RECIPIENTS = (
   'oshan@coreaisolutionsopc.com,'
   'sales@coreaisolutionsopc.com,'
   'functional@coreaisolutionsopc.com'
)


class SupportTicket(models.Model):
    _name = 'support.ticket'
    _description = 'Support Ticket'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'display_name'

    name = fields.Char(
        string='Ticket ID',
        readonly=True,
        copy=False,
        default='New',
    )
    subject = fields.Char(string='Subject', required=True, tracking=True)
    description = fields.Text(string='Description', required=True)
    customer_name = fields.Char(string='Customer Name', required=True)
    customer_email = fields.Char(string='Customer Email', required=True)
    customer_phone = fields.Char(string='Contact Number')
    category = fields.Selection(
        [
            ('general', 'General Inquiry'),
            ('technical', 'Technical Support'),
            ('bug', 'Bug Report'),
            ('feature', 'Feature Request'),
        ],
        string='Category',
        default='general',
        required=True,
        tracking=True,
    )
    priority = fields.Selection(
        [
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
        ],
        string='Priority',
        default='medium',
        tracking=True,
    )
    state = fields.Selection(
        [
            ('new', 'New'),
            ('in_progress', 'In Progress'),
            ('resolved', 'Resolved'),
            ('closed', 'Closed'),
        ],
        string='Status',
        default='new',
        required=True,
        tracking=True,
    )

    @api.depends('name', 'subject')
    def _compute_display_name(self):
        for ticket in self:
            if ticket.name and ticket.name != 'New':
                ticket.display_name = f'[{ticket.name}] {ticket.subject or ""}'
            else:
                ticket.display_name = ticket.subject or 'New Ticket'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'support.ticket'
                ) or 'New'
        tickets = super().create(vals_list)
        for ticket in tickets:
            ticket._send_notification_email()
            ticket._send_customer_confirmation()
        return tickets

    def _send_notification_email(self):
        """Send notification email to the support team."""
        category_label = dict(
            self._fields['category'].selection
        ).get(self.category, self.category)
        priority_label = dict(
            self._fields['priority'].selection
        ).get(self.priority, self.priority)

        body_html = Markup("""
            <div style="font-family: Arial, sans-serif; max-width: 600px;">
                <h2 style="color: #191a23;">New Support Ticket: {name}</h2>
                <table style="width: 100%%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;
                                   font-weight: 600; width: 140px;">Ticket ID</td>
                        <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;">{name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;
                                   font-weight: 600;">Subject</td>
                        <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;">{subject}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;
                                   font-weight: 600;">Category</td>
                        <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;">{category}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;
                                   font-weight: 600;">Priority</td>
                        <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;">{priority}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;
                                   font-weight: 600;">Customer</td>
                        <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;">
                            {customer_name} ({customer_email})</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;
                                   font-weight: 600;">Phone</td>
                        <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;">{phone}</td>
                    </tr>
                </table>
                <h3 style="color: #191a23; margin-top: 16px;">Description</h3>
                <div style="background: #f9f9f9; padding: 16px; border-radius: 8px;
                            border: 1px solid #e2e8f0; white-space: pre-wrap;">{description}</div>
            </div>
        """).format(
            name=self.name,
            subject=self.subject,
            category=category_label,
            priority=priority_label,
            customer_name=self.customer_name,
            customer_email=self.customer_email,
            phone=self.customer_phone or 'N/A',
            description=self.description,
        )

        mail_values = {
            'subject': f'[{self.name}] {self.subject}',
            'email_to': SUPPORT_RECIPIENTS,
            'email_from': self.customer_email,
            'body_html': body_html,
            'state': 'outgoing',
        }
        self.env['mail.mail'].sudo().create(mail_values).send()

    def _send_customer_confirmation(self):
        """Send confirmation email to the customer."""
        body_html = Markup("""
            <div style="font-family: Arial, sans-serif; max-width: 600px;">
                <h2 style="color: #191a23;">Thank you for contacting us!</h2>
                <p>We have received your support ticket and our team will review
                   it shortly.</p>
                <div style="background: #f9f9f9; padding: 16px; border-radius: 8px;
                            border: 1px solid #e2e8f0; margin: 16px 0;">
                    <p style="margin: 4px 0;"><strong>Ticket ID:</strong> {name}</p>
                    <p style="margin: 4px 0;"><strong>Subject:</strong> {subject}</p>
                </div>
                <p>We aim to respond within 24 hours. If your issue is urgent,
                   please contact us directly at
                   <a href="tel:+639985542698">+63 998 554 2698</a>.</p>
                <p style="color: #666; font-size: 12px; margin-top: 24px;">
                    &mdash; Core AI Solutions Support Team</p>
            </div>
        """).format(
            name=self.name,
            subject=self.subject,
        )

        mail_values = {
            'subject': f'[{self.name}] Ticket Received - {self.subject}',
            'email_to': self.customer_email,
            'email_from': SUPPORT_RECIPIENTS.split(',')[1].strip(),
            'body_html': body_html,
            'state': 'outgoing',
        }
        self.env['mail.mail'].sudo().create(mail_values).send()

    def action_in_progress(self):
        self.write({'state': 'in_progress'})

    def action_resolve(self):
        self.write({'state': 'resolved'})

    def action_close(self):
        self.write({'state': 'closed'})
