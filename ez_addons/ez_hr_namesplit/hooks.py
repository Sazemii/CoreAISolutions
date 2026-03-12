import logging
_logger=logging.getLogger(__name__)
def load_demo_data(env,demo=True):
	from.import random_names as C;D=env['ir.module.module'].search([('name','=','ez_hr_namesplit')])
	if demo and not D.demo:return
	E=env['hr.employee'].search([])
	for A in E:B=A.name.split(' ');G,H,F=C.get_random_name();A.first_name=B[0];A.last_name=B[1];A.middle_name=F;_logger.debug('ez_hr_namesplit: name = %s, %s %s',A.last_name,A.first_name,A.middle_name)
def uninstall_hook(env):
	B=env['hr.employee'].search([]);_logger.debug('ez_hr_namesplit: %s',len(B))
	for A in B:C=A.first_name+' '+A.last_name;env.cr.execute('UPDATE hr_employee SET name = %s WHERE id = %s',(C,A.id));_logger.debug('rename: %s',C)