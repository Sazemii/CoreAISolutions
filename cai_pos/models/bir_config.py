from odoo import api, fields, models, _
from odoo.exceptions import UserError
import hashlib
import logging

_logger = logging.getLogger(__name__)


class BIRConfig(models.Model):
    _name = 'bir.config'
    _description = 'BIR Configuration'
    _rec_name = 'name'
    _inherit = ['pos.load.mixin']

    name = fields.Char(string='Name', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, 
                                default=lambda self: self.env.company)
    
    # ========== MANAGER AUTHENTICATION (Security Controls) ==========
    manager_pin = fields.Char(
        string='Manager PIN',
        size=6,
        help='4-6 digit PIN for manager override functions (void, returns)',
        groups='point_of_sale.group_pos_manager'
    )
    
    require_manager_auth_for_void = fields.Boolean(
        string='Require Manager Auth for Void',
        default=True,
        help='Cashier must enter manager PIN to void transactions'
    )
    
    require_manager_auth_for_return = fields.Boolean(
        string='Require Manager Auth for Returns',
        default=True,
        help='Cashier must enter manager PIN to process returns'
    )
    
    # ========== DASHBOARD STATISTICS (Computed) ==========
    today_sales = fields.Monetary(
        string="Today's Sales",
        compute='_compute_dashboard_stats',
        currency_field='currency_id'
    )
    
    today_transactions = fields.Integer(
        string="Today's Transactions",
        compute='_compute_dashboard_stats'
    )
    
    today_voids = fields.Integer(
        string="Today's Voids",
        compute='_compute_dashboard_stats'
    )
    
    today_void_amount = fields.Monetary(
        string="Today's Void Amount",
        compute='_compute_dashboard_stats',
        currency_field='currency_id'
    )
    
    open_sessions_count = fields.Integer(
        string='Open Sessions',
        compute='_compute_dashboard_stats'
    )
    
    pending_zreading = fields.Boolean(
        string='Pending Z-Reading',
        compute='_compute_dashboard_stats',
        help='True if yesterday has no Z-reading'
    )
    
    permit_days_remaining = fields.Integer(
        string='Permit Days Remaining',
        compute='_compute_dashboard_stats'
    )
    
    @api.depends_context('uid')
    def _compute_dashboard_stats(self):
        """Compute dashboard statistics for today
        
        Today's Sales = Gross Sales - Voided Amounts
        This ensures voided transactions are explicitly subtracted from the total.
        """
        from datetime import date, datetime, time, timedelta
        
        for config in self:
            today = date.today()
            yesterday = today - timedelta(days=1)
            
            date_start = datetime.combine(today, time.min)
            date_end = datetime.combine(today, time.max)
            
            # Get ALL today's orders (including voided) for gross sales
            all_orders = self.env['pos.order'].search([
                ('date_order', '>=', date_start),
                ('date_order', '<=', date_end),
                ('state', 'in', ['paid', 'done', 'invoiced']),
                ('company_id', '=', config.company_id.id),
                ('amount_total', '>=', 0)  # Exclude refunds from sales total
            ])
            
            # Calculate gross sales (all orders)
            gross_sales = sum(all_orders.mapped('amount_total'))
            
            # Get non-voided orders for transaction count
            non_voided_orders = all_orders.filtered(lambda o: not o.is_voided)
            config.today_transactions = len(non_voided_orders)
            
            # Voids today - get approved voids
            voids = self.env['pos.order.void'].search([
                ('void_date', '>=', date_start),
                ('void_date', '<=', date_end),
                ('state', '=', 'approved'),
                ('company_id', '=', config.company_id.id)
            ])
            void_amount = sum(voids.mapped('amount_voided'))
            config.today_voids = len(voids)
            config.today_void_amount = void_amount
            
            # Today's Sales = Gross Sales - Voided Amounts
            config.today_sales = gross_sales - void_amount
            
            # Open sessions
            open_sessions = self.env['pos.session'].search([
                ('state', 'not in', ['closed']),
                ('company_id', '=', config.company_id.id)
            ])
            config.open_sessions_count = len(open_sessions)
            
            # Pending Z-reading check (yesterday)
            yesterday_z = self.env['pos.zreading'].search([
                ('reading_date', '=', yesterday),
                ('company_id', '=', config.company_id.id)
            ], limit=1)
            # Only flag as pending if there were orders yesterday
            yesterday_orders = self.env['pos.order'].search([
                ('date_order', '>=', datetime.combine(yesterday, time.min)),
                ('date_order', '<=', datetime.combine(yesterday, time.max)),
                ('state', 'in', ['paid', 'done', 'invoiced']),
                ('company_id', '=', config.company_id.id)
            ], limit=1)
            config.pending_zreading = bool(yesterday_orders) and not bool(yesterday_z)
            
            # Permit days remaining
            if config.permit_valid_until:
                config.permit_days_remaining = (config.permit_valid_until - today).days
            else:
                config.permit_days_remaining = -1  # No expiry set
    
    # Company/Business Information (for receipt)
    business_name = fields.Char(
        string='Registered Business Name',
        help='Business name as registered with BIR (appears on receipt)'
    )
    business_address = fields.Text(
        string='Business Address',
        help='Complete business address for receipt'
    )
    
    # BIR Registration
    tin = fields.Char(string='TIN', required=True, help='Tax Identification Number')
    permit_number = fields.Char(string='BIR Permit Number', required=True)
    permit_date_issued = fields.Date(string='Permit Date Issued')
    permit_valid_until = fields.Date(string='Permit Valid Until')
    
    # BIR Accreditation
    accreditation_number = fields.Char(
        string='Accreditation Number',
        help='BIR POS system accreditation number'
    )
    min_number = fields.Char(
        string='MIN',
        help='Machine Identification Number'
    )
    serial_number = fields.Char(
        string='Serial Number',
        help='POS terminal serial number'
    )
    branch_code = fields.Char(
        string='Branch Code',
        size=2,
        required=True,
        default='01',
        help='2-digit branch code for eSales (e.g., 01 for main branch, 02 for branch 2)'
    )
    
    # POS Terminal Information
    terminal_id = fields.Char(
        string='Terminal ID',
        help='Unique identifier for this POS terminal'
    )
    pos_machine_brand = fields.Char(
        string='POS Machine Brand/Model',
        help='Brand and model of POS hardware'
    )
    
    # POS Software
    pos_software_name = fields.Char(
        string='POS Software Name',
        default='Odoo POS',
        help='Name of POS software'
    )
    pos_software_version = fields.Char(
        string='POS Software Version',
        default='18.0',
        help='Version of POS software'
    )
    
    # Receipt Numbering
    receipt_prefix = fields.Char(
        string='Receipt Prefix',
        default='OR',
        help='Prefix for receipt numbers (e.g., OR, SI)'
    )
    current_receipt_number = fields.Integer(
        string='Current Receipt Number',
        default=1,
        help='Current receipt serial number for this terminal'
    )
    
    # Z-Reading
    z_reading_counter = fields.Integer(
        string='Z-Reading Counter',
        default=0,
        help='Number of Z-readings generated'
    )
    last_z_reading_date = fields.Date(
        string='Last Z-Reading Date',
        help='Date of last Z-reading'
    )
    
    # Void Counter (BIR Requirement)
    void_counter = fields.Integer(
        string='Void Counter',
        default=0,
        help='Number of void transactions generated'
    )
    total_void_amount = fields.Monetary(
        string='Total Void Amount',
        currency_field='currency_id',
        default=0.0,
        help='Cumulative amount of all voided transactions'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='company_id.currency_id',
        readonly=True
    )
    
    # Validity
    valid_from = fields.Date(string='Valid From')
    valid_until = fields.Date(string='Valid Until')
    
    active = fields.Boolean(default=True)
    
    @api.constrains('company_id', 'active')
    def _check_active_config(self):
        """Ensure only one active BIR configuration per company"""
        for record in self:
            if record.active:
                existing = self.search([
                    ('company_id', '=', record.company_id.id),
                    ('active', '=', True),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise models.ValidationError(
                        _("Only one active BIR configuration is allowed per company."))
    
    
    @api.constrains('permit_valid_until')
    def _check_permit_validity(self):
        """Warn if permit is expired or expiring soon"""
        from datetime import date, timedelta
        for record in self:
            if record.permit_valid_until:
                if record.permit_valid_until < date.today():
                    raise models.ValidationError(
                        _("BIR Permit has expired. Please renew your permit before using this configuration."))
                elif record.permit_valid_until < date.today() + timedelta(days=30):
                    # This is just a warning, not blocking
                    pass
    
    @api.constrains('current_receipt_number')
    def _check_receipt_number(self):
        """Ensure receipt number is positive"""
        for record in self:
            if record.current_receipt_number < 1:
                raise models.ValidationError(
                    _("Receipt number must be at least 1."))
    
    def get_next_receipt_number(self):
        """Get and increment the next receipt number with transaction safety"""
        self.ensure_one()
        import logging
        _logger = logging.getLogger(__name__)
        
        # Use database-level locking to prevent race conditions
        # This ensures that concurrent POS terminals cannot generate duplicate receipt numbers
        try:
            self.env.cr.execute(
                "SELECT current_receipt_number FROM bir_config "
                "WHERE id = %s FOR UPDATE NOWAIT",
                (self.id,)
            )
            result = self.env.cr.fetchone()
            if not result:
                raise models.ValidationError(_("BIR Config record not found"))
            
            current = result[0]
            
            # Update in same transaction
            self.env.cr.execute(
                "UPDATE bir_config SET current_receipt_number = %s WHERE id = %s",
                (current + 1, self.id)
            )
            
            receipt_no = f"{self.receipt_prefix}{current:08d}"
            _logger.info(f"Generated receipt number {receipt_no} for terminal {self.terminal_id}")
            
            return receipt_no
            
        except Exception as e:
            _logger.error(f"Failed to generate receipt number: {str(e)}")
            # If locking fails, fall back to regular method (with warning)
            _logger.warning("Using non-locked receipt number generation - potential race condition!")
            current = self.current_receipt_number
            self.write({'current_receipt_number': current + 1})
            return f"{self.receipt_prefix}{current:08d}"
    
    def increment_z_reading(self):
        """Increment Z-reading counter with transaction safety
        
        Uses database-level locking to prevent race conditions when
        multiple Z-readings could be generated simultaneously.
        """
        self.ensure_one()
        from datetime import date
        import logging
        _logger = logging.getLogger(__name__)
        
        try:
            # Use database-level locking to prevent race conditions
            self.env.cr.execute(
                "SELECT z_reading_counter FROM bir_config "
                "WHERE id = %s FOR UPDATE NOWAIT",
                (self.id,)
            )
            result = self.env.cr.fetchone()
            if not result:
                raise models.ValidationError(_("BIR Config record not found"))
            
            current_counter = result[0]
            new_counter = current_counter + 1
            
            # Update in same transaction
            self.env.cr.execute(
                "UPDATE bir_config SET z_reading_counter = %s, last_z_reading_date = %s WHERE id = %s",
                (new_counter, date.today(), self.id)
            )
            
            # Invalidate cache so subsequent reads get the new value
            self.invalidate_recordset(['z_reading_counter', 'last_z_reading_date'])
            
            _logger.info(f"Z-reading counter incremented to {new_counter} for config {self.name}")
            return new_counter
            
        except Exception as e:
            _logger.error(f"Failed to increment Z-reading counter: {str(e)}")
            # If locking fails (another process has lock), raise error
            # Don't fall back silently - Z-reading counter integrity is critical for BIR
            raise models.ValidationError(
                _("Cannot increment Z-reading counter. Another Z-reading may be in progress. "
                  "Please wait and try again.\n\nError: %s") % str(e)
            )
    
    def increment_void_counter(self, void_amount=0.0):
        """Increment void counter with transaction safety
        
        Uses database-level locking to prevent race conditions when
        multiple void transactions could be created simultaneously.
        
        Args:
            void_amount: Amount of the voided transaction (added to total_void_amount)
            
        Returns:
            New void counter value
        """
        self.ensure_one()
        import logging
        _logger = logging.getLogger(__name__)
        
        try:
            # Use database-level locking to prevent race conditions
            self.env.cr.execute(
                "SELECT void_counter, total_void_amount FROM bir_config "
                "WHERE id = %s FOR UPDATE NOWAIT",
                (self.id,)
            )
            result = self.env.cr.fetchone()
            if not result:
                raise models.ValidationError(_("BIR Config record not found"))
            
            current_counter = result[0] or 0
            current_total = result[1] or 0.0
            new_counter = current_counter + 1
            new_total = current_total + void_amount
            
            # Update in same transaction
            self.env.cr.execute(
                "UPDATE bir_config SET void_counter = %s, total_void_amount = %s WHERE id = %s",
                (new_counter, new_total, self.id)
            )
            
            # Invalidate cache so subsequent reads get the new value
            self.invalidate_recordset(['void_counter', 'total_void_amount'])
            
            _logger.info(f"[BIR VOID] Void counter incremented to {new_counter}, total void amount: {new_total} for config {self.name}")
            return new_counter
            
        except Exception as e:
            _logger.error(f"Failed to increment void counter: {str(e)}")
            # If locking fails (another process has lock), raise error
            raise models.ValidationError(
                _("Cannot increment void counter. Another void may be in progress. "
                  "Please wait and try again.\n\nError: %s") % str(e)
            )
    
    # POS Load Mixin Implementation
    @api.model
    def _load_pos_data_domain(self, data):
        """Define which BIR config records to load for this POS session
        
        The data parameter is the response dictionary from pos.session.load_data()
        containing loaded model data. We extract the pos.config record to find the linked BIR config.
        """
        import logging
        _logger = logging.getLogger(__name__)
        
        try:
            # data is a dictionary like: {'pos.config': {'data': [...], 'fields': [...]}, ...}
            # Get the first pos.config record if it exists
            if not isinstance(data, dict):
                _logger.warning(f"[BIR Config] Unexpected data type: {type(data)}, returning empty domain")
                return [('id', '=', False)]
            
            if 'pos.config' not in data or not data['pos.config'].get('data'):
                _logger.warning("[BIR Config] No pos.config data found in load data")
                return [('id', '=', False)]
            
            config_data = data['pos.config']['data']
            if not config_data:
                _logger.warning("[BIR Config] pos.config data list is empty")
                return [('id', '=', False)]
            
            # Get the first config's ID
            config_id = config_data[0].get('id')
            if not config_id:
                _logger.warning("[BIR Config] No config ID found in pos.config data")
                return [('id', '=', False)]
            
            config = self.env['pos.config'].browse(config_id)
            if not config.exists():
                _logger.warning(f"[BIR Config] POS Config with ID {config_id} does not exist")
                return [('id', '=', False)]
            
            if config.bir_config_id:
                _logger.info(f"[BIR Config] Loading BIR config: {config.bir_config_id.name} for POS: {config.name}")
                return [('id', '=', config.bir_config_id.id)]
            
            _logger.debug(f"[BIR Config] No BIR config linked to POS config: {config.name}")
            return [('id', '=', False)]
            
        except Exception as e:
            _logger.error(f"[BIR Config] Error in _load_pos_data_domain: {str(e)}", exc_info=True)
            return [('id', '=', False)]
    
    @api.model
    def _load_pos_data_fields(self, config_id):
        """Define which fields to load into POS frontend"""
        return [
            'name',
            'business_name',
            'business_address',
            'tin',
            'permit_number',
            'accreditation_number',
            'serial_number',
            'min_number',
            'terminal_id',
            'receipt_prefix',
            'current_receipt_number',
            'pos_software_name',
            'pos_software_version',
            'permit_valid_until',
            'valid_from',
            'valid_until',
            # Security settings (loaded into POS frontend)
            'require_manager_auth_for_void',
            'require_manager_auth_for_return',
        ]
    
    # ========== MANAGER PIN VERIFICATION (RPC Method) ==========
    
    @api.model
    def verify_manager_pin(self, config_id, pin):
        """
        Verify manager PIN for sensitive operations.
        Called from POS frontend when voiding or processing returns.
        
        Args:
            config_id: ID of the bir.config record
            pin: The PIN entered by the user
            
        Returns:
            dict: {'success': True/False, 'message': str}
        """
        if not config_id or not pin:
            return {'success': False, 'message': _('Invalid request')}
        
        config = self.browse(config_id)
        if not config.exists():
            return {'success': False, 'message': _('Configuration not found')}
        
        # Check if PIN is set
        if not config.manager_pin:
            # No PIN configured - allow operation (with warning logged)
            _logger.warning(f"[BIR Security] No manager PIN configured for {config.name}. Allowing operation.")
            return {'success': True, 'message': _('No PIN required')}
        
        # Verify PIN
        if pin == config.manager_pin:
            _logger.info(f"[BIR Security] Manager PIN verified successfully for {config.name}")
            return {'success': True, 'message': _('PIN verified')}
        else:
            _logger.warning(f"[BIR Security] Invalid manager PIN attempt for {config.name}")
            return {'success': False, 'message': _('Invalid PIN')}
    
    def action_set_manager_pin(self):
        """Action to open wizard for setting manager PIN"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Set Manager PIN'),
            'res_model': 'bir.config.set.pin.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_config_id': self.id}
        }
