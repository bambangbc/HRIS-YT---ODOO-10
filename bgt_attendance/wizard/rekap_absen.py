import time
import calendar
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, exceptions, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.exceptions import ValidationError, RedirectWarning, UserError
from collections import OrderedDict

class HRAttendanceFinger(models.Model):
    _name = 'report_rekap_absen'

    dates        = fields.Date("Date")

    @api.multi
    def fill_table(self):

        self._cr.execute("DELETE FROM laporan_rekap_absen")
        shift = self.env['hr.rolling.shift.detail'].search([('date_start','<=',self.dates),('date_end','>=',self.dates)])
        datess = self.dates + " " + "00:00:00"
        datess_day = datetime.strptime(datess,"%Y-%m-%d %H:%M:%S")
        dayofweek = datetime.strptime(datess,"%Y-%m-%d %H:%M:%S").isoweekday() - 1
        #import pdb;pdb.set_trace()
        for rekap in shift :
            if rekap.schedule_id.shift_type != 'shift malam' :
                for detail in rekap.schedule_id.attendance_ids :
                    if detail.dayofweek == str(dayofweek) :
                        date_start_shift1 = str(datess_day+timedelta(hours=detail.hour_from)-timedelta(hours=13.5))
                        date_start_shift2 = str(datess_day+timedelta(hours=detail.hour_from)-timedelta(hours=6.5))
                        date_end_shift1 = str(datess_day+timedelta(hours=detail.hour_to)+timedelta(hours=1))
                        date_end_shift2 = str(datess_day+timedelta(hours=detail.hour_to)-timedelta(hours=6.5))

            if rekap.schedule_id.shift_type == 'shift malam' :
                for detail in rekap.schedule_id.attendance_ids :
                    if detail.dayofweek == str(dayofweek) :
                        date_start_shift1 = str(datess_day+timedelta(hours=detail.hour_from)-timedelta(hours=13.5))
                        date_start_shift2 = str(datess_day+timedelta(hours=detail.hour_from)-timedelta(hours=6.5))
                        date_end_shift1 = str(datess_day+timedelta(hours=detail.hour_to)+timedelta(days=1, hours=1))
                        date_end_shift2 = str(datess_day+timedelta(hours=detail.hour_to)+timedelta(days=1)-timedelta(hours=6.5))
            att_in =self.env['hr.attendance.finger'].sudo().search([('absen_id','=',rekap.employee_id.absen_id),('date','>=',date_start_shift1),('date','<=',date_start_shift2)],order='date asc', limit=1)
            att_out =self.env['hr.attendance.finger'].sudo().search([('absen_id','=',rekap.employee_id.absen_id),('date','>=',date_end_shift2),('date','<=',date_end_shift1)],order='date desc', limit=1)
            rekap_create = self.env['laporan.rekap.absen'].create({'name':rekap.employee_id.id,'department_id':rekap.employee_id.department_id.id,'shift_id':rekap.schedule_id.id,'log_in':att_in.date,'log_out':att_out.date})
        ctx = dict(self.env.context)
        return {
            'name': _('Rekap Absen'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'laporan.rekap.absen',
            'res_id': rekap_create.id,
            'type': 'ir.actions.act_window',
            'context': ctx,
        }