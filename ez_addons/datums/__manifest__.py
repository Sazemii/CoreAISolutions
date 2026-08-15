{
    'name': 'datumsAI',
    'version': '19.0.1.0.0',
    'summary': 'datumsAI dashboard, API key settings, and database structure tools',
    'description': 'Transform Odoo ERP Data into AI-Powered Insights & Dashboards',
    'category': 'Tools',
    'author': 'Hidden Brains InfoTech Pvt. Ltd.',
    'website': 'https://www.hiddenbrains.com/',
    'images': [
        'static/description/icon.png',
    ],
    'depends': ['base', 'web', 'base_setup'],
    'external_dependencies': {
        'python': ['sqlglot'],
    },
    'data': [
        'security/ir.model.access.csv',
        'data/ir_config_parameter_data.xml',
        'views/extend_base_settings_views.xml',
        'views/datums_script_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'datums/static/src/xml/dashboard_viewer.xml',
            'datums/static/src/css/datums_button.css',
            'datums/static/src/css/dashboard_viewer.css',
            'datums/static/src/js/datums_button.js',
            'datums/static/src/js/dashboard_viewer.js',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
