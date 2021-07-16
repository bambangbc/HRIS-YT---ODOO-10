# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 widianajuniar@gmail.com
#    All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

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
    _name = 'hr.attendance.finger'
    _order = 'date desc'
    _rec_name = 'absen_id'


    employee_id = fields.Many2one("hr.employee", "Employee")
    date        = fields.Datetime("Date")
    absen_id    = fields.Char(string="ID Absen")
    no_mesin    = fields.Char(string="No Mesin")
    tanggal     = fields.Char(string="Tanggal")
    bulan       = fields.Char(string="Bulan")
    tahun       = fields.Char(string="Tahun")
    status      = fields.Char(string="Status")
    telat       = fields.Integer(string="Telat")
    notes       = fields.Char(string="Notes")

    def cron_fill_attendance(self):

        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        eksekusi = self.env['hr.attendance.finger'].search([('date','!=',False),('absen_id','!=',False),('notes','=',False)], order='tanggal asc')
        for att in eksekusi:
            employee = self.env['hr.employee'].sudo().search([('absen_id','=',att.absen_id)], limit=1)
            if employee:
                date = att.date
                # search checkout terakhir atas employee yg sama
                last_attendance = self.env['hr.attendance'].search([('employee_id','=',employee.id)],order='check_in desc',limit=1)
                if last_attendance and not last_attendance.check_out :
                    last = datetime.strptime(last_attendance.check_in,DATETIME_FORMAT)
                    now = datetime.strptime(date,DATETIME_FORMAT)
                    gap = now-last
                    gap_days = gap.days
                    gap_hours = gap.seconds/60/60
                    if gap_days > 0 :
                        att.write({'notes' : 'Data attendance sebelumnya belum check out selama lebih dari sehari'})
                        continue
                    elif gap_hours >= 16 :
                        att.write({'notes' : 'Data attendance sebelumnya belum check out selama lebih dari 16 jam'})
                        continue
                    else :
                        last_attendance.write({'check_out' : att.date})
                        message = "Attendance Employee "+ employee.name + " Updated.. "
                    self._cr.execute("DELETE FROM hr_attendance_finger WHERE id = %d" %(att.id))
                else :
                    #import pdb;pdb.set_trace()
                    if date <= last_attendance.check_out :
                        att.write({'notes' : 'Tanggal finger bentrok dengan data attendance sebelumnya'})
                        continue
                    # proteksi 10 menit jika employee absen ulang jeda dibahawah 10 menit
                    co = datetime.strptime(last_attendance.check_out,DATETIME_FORMAT)
                    ci = datetime.strptime(date,DATETIME_FORMAT)
                    cico = ci-co
                    if cico.seconds > 0.0 :
                        gap_ci_co = cico.seconds/60
                        if gap_ci_co <= 10.0 :
                            att.write({'notes' : 'Data attendance ini terpaut kurang dari 10 menit dari data attendance sebelumnya'})
                            continue
                    data = {
                        'employee_id'   : employee.id,
                        'check_in'      : date,
                        'absen_id'      : att.absen_id,
                        'no_mesin'      : att.no_mesin,
                        'tanggal'       : att.tanggal,
                        'bulan'         : att.bulan,
                        'tahun'         : att.tahun,
                        'status'        : att.status,
                        'telat'         : att.telat,
                        }
                    message = "Attendance Employee "+ employee.name + " Created.. "
                    self.env['hr.attendance'].create(data)
                    self._cr.execute("DELETE FROM hr_attendance_finger WHERE id = %d" %(att.id))

        return True


    def cron_clear_finger_print_attendance(self):
        """
            Delete semua data di tabel hr.attendance.finger
        """
        return self._cr.execute("DELETE FROM hr_attendance_finger")


HRAttendanceFinger()


class HRAttendance(models.Model):
    _inherit = 'hr.attendance'

    # def real_working_hours_on_day(self, employee_id, datetime_day):
    #     #import pdb;pdb.set_trace()
    #     masuk = datetime_day - timedelta(hours=7)
    #     day = masuk.strftime("%Y-%m-%d 00:00:00")
    #     day2 = masuk.strftime("%Y-%m-%d 24:00:00")
    def real_working_hours_on_day(self, employee_id, datetime_day):
        #day = datetime_day.strftime("%Y-%m-%d 00:00:00")
        #day2 = datetime_day.strftime("%Y-%m-%d 24:00:00")
        day = str(datetime_day-timedelta(hours=7))
        day2 = str(datetime_day+timedelta(hours=17))

        # shift
        day_shift = str(datetime_day)[:10]
        obj_shift = self.env['hr.rolling.shift.detail']
        #obj_shift_detail = self.env['resource.calendar']
        dayofweek = datetime_day.isoweekday() - 1

        clause_1 = ['&',('date_start','<=', day_shift),'|',('date_end', '=', False),('date_end','>=', day_shift)]
        clause_final =  [('employee_id', '=', employee_id)] +clause_1
        contract  = self.env['hr.contract'].search(clause_final, order="date_end desc", limit=1)

        if contract.shift_working_schedule == False :

            working_hours_exist = contract.working_hours
        else :

            working_hours_exist = obj_shift.sudo().search([('employee_id','=',employee_id),('date_start','<=',day_shift),('date_end','>=',day_shift)], limit=1, order='id desc')
        #employee attendance non ganti hari
        if working_hours_exist :
            if contract.shift_working_schedule == False :
                master_shift = self.env['resource.calendar'].sudo().search([('id', '=', working_hours_exist.id)])
            else :
                master_shift = self.env['resource.calendar'].sudo().search([('id', '=', working_hours_exist.schedule_id.id)])
            if master_shift.shift_type != 'shift malam' :
                for detail in master_shift.attendance_ids :
                    if detail.dayofweek == str(dayofweek) :
                        date_start_shift1 = str(datetime_day+timedelta(hours=detail.hour_from)-timedelta(hours=13))
                        date_start_shift2 = str(datetime_day+timedelta(hours=detail.hour_from)-timedelta(hours=6))
                        date_end_shift1 = str(datetime_day+timedelta(hours=detail.hour_to)+timedelta(hours=1))
                        date_end_shift2 = str(datetime_day+timedelta(hours=detail.hour_to)-timedelta(hours=7.5))

            if master_shift.shift_type == 'shift malam' :
                for detail in master_shift.attendance_ids :
                    if detail.dayofweek == str(dayofweek) :
                        date_start_shift1 = str(datetime_day+timedelta(hours=detail.hour_from)-timedelta(hours=13))
                        date_start_shift2 = str(datetime_day+timedelta(hours=detail.hour_from)-timedelta(hours=6))
                        date_end_shift1 = str(datetime_day+timedelta(hours=detail.hour_to)+timedelta(days=1, hours=1))
                        date_end_shift2 = str(datetime_day+timedelta(hours=detail.hour_to)+timedelta(days=1)-timedelta(hours=7.5))
            employees = self.env['hr.employee'].sudo().search([('id','=',employee_id)])
            att_in =self.env['hr.attendance.finger'].sudo().search([('absen_id','=',employees.absen_id),('date','>=',date_start_shift1),('date','<=',date_start_shift2)],order='date asc', limit=1)
            att_out =self.env['hr.attendance.finger'].sudo().search([('absen_id','=',employees.absen_id),('date','>=',date_end_shift2),('date','<=',date_end_shift1)],order='date desc', limit=1)

            time1=0
            time2=0
            if att_in :
                time1 = datetime.strptime(att_in.date,"%Y-%m-%d %H:%M:%S")
            if att_out :
                time2 = datetime.strptime(att_out.date,"%Y-%m-%d %H:%M:%S")

            if time2 or time1:
                delta = 8
                #delta = (time2 - time1).seconds / 3600.00
            else:
                delta = 0

            return delta

    job_id      = fields.Many2one("hr.job", "Jabatan",related="employee_id.job_id", store=True)
    department_id      = fields.Many2one("hr.department", "Department",related="employee_id.department_id", store=True)
    absen_id    = fields.Char(string="ID Absen")
    no_mesin    = fields.Char(string="No Mesin")
    tanggal     = fields.Char(string="Tanggal")
    bulan       = fields.Char(string="Bulan")
    tahun       = fields.Char(string="Tahun")
    status      = fields.Char(string="Status")
    telat       = fields.Integer(string="Telat")

    # @api.multi
    # def check_attendance(self,absen_id2,no_mesin2,date,tanggal,bulan,tahun,status,telat):
    #     #import pdb;pdb.set_trace()
    #     for i in self :
    #         employee = self.env['hr.employee']
    #         employee_exist = employee.sudo().search([('absen_id','=',absen_id),('no_mesin','=',no_mesin)])
    #         if not employee_exist :
    #             return False
    #         for e in employee_exist :
    #             # cari data sign in
    #             signin = self.search([('employee_id','=',e.id),
    #                                 ('check_in','<',date),
    #                                 ('check_out','=',False)], order='check_in desc', limit=1)

    #             if signin :
    #                 signin.write({'check_out'   : date})
    #                 return True
    #             else :
    #                 # antisipasi data sign in/out yg lebih tua dari data insert
    #                 sign = self.search([('employee_id','=',e.id),('check_in','>=',date)], order='check_in desc', limit=1)
    #                 if sign :
    #                     return False
    #                 self.create({'employee_id'  : e.id,
    #                                 'check_in'  : date,
    #                                 'absen_id'  : absen_id,
    #                                 'no_mesin'  : no_mesin,
    #                                 'tanggal'   : tanggal,
    #                                 'bulan'     : bulan,
    #                                 'tahun'     : tahun,
    #                                 'status'    : status,
    #                                 'telat'     : telat})
    #             return True


HRAttendance()
