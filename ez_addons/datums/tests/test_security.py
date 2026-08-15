# -*- coding: utf-8 -*-
import json
import time
from odoo.tests.common import HttpCase, tagged

@tagged('post_install', '-at_install')
class TestDatumsSecurity(HttpCase):

    def setUp(self):
        super(TestDatumsSecurity, self).setUp()
        
        # 1. Ensure we have allowed IPs configured to include localhost
        self.env['ir.config_parameter'].sudo().set_param('datums.allowed_ips', '127.0.0.1')
        
        # 2. Get or create datums.config
        self.config = self.env['datums.config'].sudo().search([], limit=1)
        if not self.config:
            self.config = self.env['datums.config'].sudo().create({
                'datums_access_key': 'test_access_key_123',
                'datums_secret_key': 'test_secret_key_456',
            })
        else:
            if not self.config.datums_access_key:
                self.config.sudo().write({'datums_access_key': 'test_access_key_123'})
            if not self.config.datums_secret_key:
                self.config.sudo().write({'datums_secret_key': 'test_secret_key_456'})

    def test_01_module_installation(self):
        # Verify the module is installed successfully
        module = self.env['ir.module.module'].sudo().search([('name', '=', 'datums')])
        self.assertTrue(module, "Datums module should be found in registry")
        self.assertEqual(module.state, 'installed', "Datums module should be successfully installed")

    def test_02_api_query_refuses_no_user_id(self):
        # /api/query refuses a request with no user_id
        url = '/api/query'
        payload = {
            "access_key": self.config.datums_access_key,
            "query": "U0VMRUNUICogRlJPTSByZXNfdXNlcnM="  # "SELECT * FROM res_users" base64
        }
        response = self.url_open(
            url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(response.status_code, 200)
        res_json = response.json()
        
        self.assertEqual(res_json.get('success'), 0)
        self.assertIn("user_id is required", res_json.get('message', ''))

    def test_03_non_admin_cannot_read_restricted_table(self):
        # A non-admin user cannot read a table they lack access to
        demo_user = self.env['res.users'].sudo().search([('login', '=', 'demo')], limit=1)
        self.assertTrue(demo_user, "Demo user should exist")

        url = '/api/query'
        # datums_config maps to datums.config, which demo user has no read access to
        payload = {
            "access_key": self.config.datums_access_key,
            "user_id": str(demo_user.id),
            "query": "U0VMRUNUICogRlJPTSBkYXR1bXNfY29uZmln"  # "SELECT * FROM datums_config" base64
        }
        response = self.url_open(
            url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(response.status_code, 200)
        res_json = response.json()
        
        # The query execution fails with permission denial
        self.assertEqual(res_json.get('success'), 1)
        self.assertIn("You do not have permission to access", res_json.get('message', ''))
