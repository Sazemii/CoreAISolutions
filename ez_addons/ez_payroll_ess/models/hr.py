from odoo import api,fields,models,tools,_
import logging
_logger=logging.getLogger(__name__)
def get_google_maps_url(latitude,longitude):return'https://maps.google.com?q=%s,%s'%(latitude,longitude)
class HrEmployeeGeofence(models.Model):
	_name='hr.employee.geofence';_description='Employee Geofence';name=fields.Char();latitude=fields.Float(digits=(10,7));longitude=fields.Float(digits=(10,7));radius=fields.Float(digits=(5,2),default=1e2);note=fields.Text('Notes')
	def action_show_maps(A):A.ensure_one();return{'type':'ir.actions.act_url','url':get_google_maps_url(A.latitude,A.longitude),'target':'new'}
class HrEmployee(models.Model):
	_inherit='hr.employee';mfa_code=fields.Char();mfa_count=fields.Integer(default=0);check_in_ids=fields.Many2many('hr.employee.geofence','rel_check_in_employee_geofence','employee_id','geofence_id',string='Check In Locations');check_out_ids=fields.Many2many('hr.employee.geofence','rel_check_out_employee_geofence','employee_id','geofence_id',string='Check Out Locations');json_config=fields.Text('JSON Config')
	@api.model
	def set_geofence_check_in(self,employee_id,latitude,longitude):
		B=self.env['hr.employee.geofence'];C=self.browse(employee_id);D='Check In [%s]'%C.name;A=B.search([('name','=',D)],limit=1)
		if not A:A=B.create({'name':D})
		A.write({'latitude':latitude,'longitude':longitude});C.check_in_ids=[(4,A.id)];return{'res':True}
	@api.model
	def set_geofence_check_out(self,employee_id,latitude,longitude):
		B=self.env['hr.employee.geofence'];C=self.browse(employee_id);D='Check Out [%s]'%C.name;A=B.search([('name','=',D)],limit=1)
		if not A:A=B.create({'name':D})
		A.write({'latitude':latitude,'longitude':longitude});C.check_out_ids=[(4,A.id)];return{'res':True}
class HrEmployeePublic(models.Model):_inherit='hr.employee.public';mfa_code=fields.Char();mfa_count=fields.Integer(default=0)
class HrAttendance(models.Model):
	_inherit='hr.attendance'
	def _update_overtime(A,employee_attendance_dates=None):0