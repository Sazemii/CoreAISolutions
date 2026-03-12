import logging
_logger=logging.getLogger(__name__)
def load_demo_data(env,demo=True):
	A=env['ir.module.module'].search([('name','=','ez_timekeeping')])
	if demo and not A.demo:return
	B=env['ez.time.card'];B.demo_add_emp_shift()
def uninstall_hook(env):0