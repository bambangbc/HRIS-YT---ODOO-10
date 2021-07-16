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


class HRKenaikanUpah(models.Model):
    _name = "hr.kenaikan.upah"
    _description = "Pengelolaan Kenaikan Upah"
    _order = "name desc"
    _inherit = ['mail.thread', 'ir.needaction_mixin']


    name = fields.Char("Number", size=25, default="New")
    user_id = fields.Many2one("res.users", string="User", default=lambda self: self.env.user)
    date = fields.Datetime("Created Date",default=lambda self:time.strftime("%Y-%m-%d %H:%M:%S"))
    tanggal = fields.Date("Tanggal Kenaikan Upah", track_visibility='onchange')
    employee_ids = fields.One2many("hr.kenaikan.upah.detail", "kenaikan_upah_id", "Employee")
    state = fields.Selection([('draft','Draft'),('confirmed','Confirmed'),('done','Done'),('cancel','Cancelled')], default="draft",string="State", track_visibility='onchange')
    notes = fields.Text("Notes")

    _sql_constraints = [
        ('unique_name', 'unique(name)', 'Nomor duplikat !'),
    ]

    @api.one
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        raise UserError(_('Data tidak bisa di duplikasi !'))
        return super(HRKenaikanUpah, self).copy(default=default)

    @api.model
    def create(self, vals):
        if not vals.get('name', False) or vals['name'] == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.kenaikan.upah') or 'Number not found !'
        return super(HRKenaikanUpah, self).create(vals)

    @api.multi
    def unlink(self):
        for i in self:
            if i.state != 'draft' :
                raise UserError(_('Data yang bisa dihapus hanya yg berstatus draft'))
        return super(HRKenaikanUpah, self).unlink()

    @api.multi
    def button_confirm(self):
        sql = self._cr.execute("delete from hr_kenaikan_upah_detail where kenaikan_upah_id = %s", ( self.id,))
        if sql :
            self._cr.execute(sql)
        sql2 = """INSERT INTO hr_kenaikan_upah_detail (
                    kenaikan_upah_id,
                    employee_id,
                    nik,
                    job_id,
                    department_id,
                    old_wage,
                    contract_id
                    )
                    (
                    SELECT
                        %s as kenaikan_upah_id,
                        hc.employee_id,
                        he.nik,
                        he.job_id,
                        he.department_id,
                        hc.wage,
                        hc.id
                            FROM
                                hr_contract hc
                                    LEFT JOIN hr_employee he ON he.id = hc.employee_id
                                        WHERE
                                        date_end > '%s' or date_end IS NULL
                                            GROUP BY
                                                hc.employee_id,
                                                he.nik,
                                                he.job_id,
                                                he.department_id,
                                                hc.wage,
                                                hc.id
                                                    HAVING COUNT(hc.employee_id) = 1
                    )
                        """ % ( self.id, self.tanggal)
        self._cr.execute(sql2)
        return self.write({'state':'confirmed'})

    @api.multi
    def button_cancel(self):
        for i in self:
            i.write({'state':'cancel'})
        return True

    @api.multi
    def button_set_to_draft(self):
        for i in self:
            i.write({'state':'draft'})
        return True


    @api.multi
    def button_approve(self):
        for i in self:
            tgl = datetime.strptime(i.tanggal,'%Y-%m-%d')
            #import pdb;pdb.set_trace()
            minus1hari = str(tgl+timedelta(days=-1))[:10]
            for contract in i.employee_ids.filtered(lambda x: x.new_wage > 0.0) :
                datas = {'date_start'       : i.tanggal,
                            'notes'         : "Created by Kenaikan Upah Tahunan  : " + i.name,
                            'state'         :'draft',
                            'wage'      : contract.new_wage}
                if contract.contract_id.date_end :
                    datas.update({'date_end' : contract.contract_id.date_end})
                else :
                    datas.update({'date_end' : False})
                contract.contract_id.write({'date_end' : minus1hari,'notes' : "Closed by Kenaikan Upah Tahunan : " + i.name})
                new_contract = contract.contract_id.copy(datas)
                contract.new_contract_id = new_contract.id
            i.write({'state':'done'})
        return True

HRKenaikanUpah()


class HRKenaikanUpahDetail(models.Model):
    _name = "hr.kenaikan.upah.detail"
    _inherit = ['mail.thread']
    _rec_name = "nik"

    def get_lama_kerja(self):
        for x in self:
            if x.employee_id.work_date :
                date_now    = str(fields.date.today())
                dt_now      = datetime.strptime(date_now, '%Y-%m-%d')
                dt_start    = datetime.strptime(x.employee_id.work_date, '%Y-%m-%d')
                date        = relativedelta(dt_now,dt_start)
                x.tahun     = date.years
                x.bulan     = date.months
                x.hari      = date.days


    @api.depends('contract_id.shift_working_schedule', 'new_contract_id.shift_working_schedule')
    def get_working_days(self):

        def was_on_leave_interval(employee_id, date_from, date_to):
            date_from = fields.Datetime.to_string(date_from)
            date_to = fields.Datetime.to_string(date_to)
            return self.env['hr.holidays'].search([
                ('state', '=', 'validate'),
                ('employee_id', '=', employee_id),
                ('type', '=', 'remove'),
                ('date_from', '<=', date_from),
                ('date_to', '>=', date_to),
                ('holiday_status_id.is_public_holiday','=',True)
            ], limit=1)

        for x in self:
            working_days = 0
            public_holi = 0
            attendance = 0
            import pdb;pdb.set_trace()
            day_from    = fields.Datetime.from_string(x.tanggal)-relativedelta(years=1)
            date        = relativedelta(fields.Datetime.from_string(x.tanggal),day_from)
            year        = date.years
            month       = date.months
            day         = date.days
            durasi      = (year*365)+(month*30)+day
            #import pdb;pdb.set_trace()
            for day in range(0, durasi) :
                interval_data = []
                holidays = self.env['hr.holidays']
                obj_shift = self.env['hr.contract.detail']
                date = (day_from + timedelta(days=day))
                dates = str(date)[:10]
                working_intervals_on_day = []
                # jika kerja shift-shift an
                if x.contract_id.shift_working_schedule and x.state == 'done':
                    working_hours_exist = obj_shift.sudo().search([('contract_id','=',x.contract_id.id),
                                                                ('start_date','<=',dates),('end_date','>=',dates)],
                                                                limit=1, order='id desc')
                    if not working_hours_exist :
                        continue
                    working_intervals_on_day = working_hours_exist.schedule_id.get_working_intervals_of_day(start_dt=day_from + timedelta(days=day))
                # jika non shift
                elif not x.contract_id.shift_working_schedule and x.contract_id.working_hours and x.state == 'done':
                    working_intervals_on_day = x.contract_id.working_hours.get_working_intervals_of_day(start_dt=day_from + timedelta(days=day))

                for interval in working_intervals_on_day:
                    interval_data.append((interval, was_on_leave_interval(x.contract_id.employee_id.id, interval[0], interval[1])))
                for interval, holiday in interval_data:
                    holidays |= holiday
                    if holiday :
                        public_holi += 1
                    else :
                        working_days += 1
                        # cari kehadiran
                        real_working_hours_on_day = self.env['hr.attendance'].real_working_hours_on_day(x.contract_id.employee_id.id, day_from + timedelta(days=day))
                        if real_working_hours_on_day >= 0.000000000000000001 :
                            attendance += 1
            x.working_days = working_days-public_holi
            x.attendance = attendance
            x.absen = working_days-public_holi-attendance
            try:
                x.percent = (float(attendance) / float(working_days-public_holi-attendance)) * 100
            except ZeroDivisionError:
                x.percent = 0.0

    @api.depends('contract_id.wage', 'new_contract_id.wage')
    def get_perubahan_gaji(self):
        for x in self:
            if x.new_contract_id :
                wage = x.new_contract_id.wage
                last_contract = self.env['hr.contract'].search([('employee_id','=',x.employee_id.id),
                                                                ('wage','!=',wage),
                                                                ('date_start','<',x.new_contract_id.date_start)]
                                                                ,order="date_start desc", limit=1)
                if last_contract :
                    x.perubahan_gaji_terakhir = last_contract.date_start
                else :
                    x.perubahan_gaji_terakhir = x.new_contract_id.date_start
            else :
                x.perubahan_gaji_terakhir = x.contract_id.date_start

    def get_upah(self):
        for x in self:
            if x.contract_id :
                x.old_up = x.contract_id.wage + x.contract_id.meals
            if x.new_contract_id :
                x.new_up = x.new_contract_id.wage + x.new_contract_id.meals
                x.selisih_un = x.new_wage - x.old_wage

    kenaikan_upah_id =fields.Many2one("hr.kenaikan.upah","Kenaikan Upah Tahunan")
    tanggal = fields.Date("Date",related="kenaikan_upah_id.tanggal", store=True)
    employee_id = fields.Many2one("hr.employee","Employee", required=True, track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})
    work_date = fields.Date("Mulai Kerja", related="employee_id.work_date", store=True)
    nik = fields.Char("NIK", related="employee_id.nik", store=True)
    bank_account_id = fields.Many2one("res.partner.bank","Norek",related="employee_id.bank_account_id", store=True)
    old_wage = fields.Float("Wage" , readonly=True, group_operator="avg")
    new_wage = fields.Float("New Wage", readonly=True, states={'draft': [('readonly', False)],'confirmed': [('readonly', False)]}, track_visibility='onchange', group_operator="avg")
    department_id = fields.Many2one("hr.department","Department", related="employee_id.department_id", store=True)
    job_id = fields.Many2one("hr.job","Job Title", related="employee_id.job_id", store=True)
    contract_id = fields.Many2one("hr.contract","Contract", readonly=True, states={'draft': [('readonly', False)]},domain="[('employee_id','=',employee_id)]")
    type_id = fields.Many2one("hr.contract.type","Pay Status", related="contract_id.type_id", store=True)
    old_meals = fields.Float("Old Meals",related="contract_id.meals", store=True)
    old_up = fields.Float("Old UP",compute="get_upah")
    old_gapok = fields.Float("Old Bruto",related="contract_id.gapok", store=True)
    new_meals = fields.Float("New Meals",related="new_contract_id.meals", store=True)
    new_up = fields.Float("New Bruto",compute="get_upah")
    new_gapok = fields.Float("New GP",related="new_contract_id.gapok", store=True)
    selisih_un = fields.Float("Selisih Upah",compute="get_upah")
    new_contract_id = fields.Many2one("hr.contract","New Contract",domain="[('employee_id','=',employee_id)]")
    state = fields.Selection(related="kenaikan_upah_id.state", string="State",store=True, track_visibility='onchange')
    tahun = fields.Integer("Tahun", compute="get_lama_kerja")
    bulan = fields.Integer("Bulan", compute="get_lama_kerja")
    hari = fields.Integer("hari", compute="get_lama_kerja")
    working_days = fields.Integer("Working Days", compute="get_working_days", store=True)
    attendance = fields.Integer("Attendance", compute="get_working_days", store=True)
    absen = fields.Integer("Absen", compute="get_working_days", store=True)
    percent = fields.Float("% Kehadiran", compute="get_working_days", store=True)
    perubahan_gaji_terakhir = fields.Date("Perubahan Gaji Terakhir", compute="get_perubahan_gaji", store=True)



HRKenaikanUpahDetail()