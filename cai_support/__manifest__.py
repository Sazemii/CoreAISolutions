{
    'name': 'CAI Support Ticketing',
    'version': '19.0.1.0.0',
    'category': 'Services/Support',
    'summary': 'Customer-facing support ticketing system with email notifications',
    'description': """
        Support ticketing system for Core AI Solutions.

        Features:
        - API endpoint for ticket submission from embedded website form
        - Auto-generated ticket IDs (TKT-00001)
        - Email notifications to support team on new tickets
        - Backend ticket management with chatter
    """,
    'author': 'CoreAI Solutions',
    'website': 'https://coreaisolutionsopc.com',
    'depends': [
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'data/mail_data.xml',
        'views/support_ticket_views.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}
