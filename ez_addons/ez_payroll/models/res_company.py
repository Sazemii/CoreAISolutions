from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
import re,logging
_logger=logging.getLogger(__name__)
class Company(models.Model):_inherit='res.company';payslip_header=fields.Char('Payslip Header')