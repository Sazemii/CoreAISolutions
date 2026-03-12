from odoo import api,fields,models,tools,_
from odoo.exceptions import ValidationError
import time,logging
_logger=logging.getLogger(__name__)
class Timecard(models.Model):_inherit='ez.time.card'