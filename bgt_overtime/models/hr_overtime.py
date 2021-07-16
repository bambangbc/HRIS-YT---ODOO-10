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

from odoo import api, fields, models, _
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import dateutil.parser
from odoo.exceptions import ValidationError, RedirectWarning, UserError

SESSION_STATES =[('draft','Draft'),('confirm','Waiting Approval'),('confirm_manager','Waiting Second Approval'),("refuse","Refused"),("validate", "Approved"),("cancel", "Cancelled")]

class hr_overtime(models.Model):
    _name = "hr.overtime"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = "Overtime"
    _order = "date_from asc"

    
    def generate_overtime(self):
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"       
        for detail in self.employee_ids :
            if self.hari_libur == True :
                    date_str1 = str(datetime.strptime(self.date_from, DATETIME_FORMAT)-timedelta(hours=4))
                    date_str2 = str(datetime.strptime(self.date_from, DATETIME_FORMAT)+timedelta(hours=4)) 
                    date_ends1 = str(datetime.strptime(self.date_to, DATETIME_FORMAT)-timedelta(hours=4))
                    date_ends2 = str(datetime.strptime(self.date_to, DATETIME_FORMAT)+timedelta(hours=4))
                    date_exist_str = self.env['hr.attendance.finger'].search([('date','>=',date_str1),('date','<=',date_str2),('absen_id','=',detail.employee_id.absen_id)], limit=1,order='date desc')
                    date_exist_ends = self.env['hr.attendance.finger'].search([('date','>=',date_ends1),('date','<=',date_ends2),('absen_id','=',detail.employee_id.absen_id)], limit=1,order='date desc')
                    if date_exist_str.date <= self.date_from and date_exist_ends.date >= self.date_from :
                        detail.write({'ovt_hour':self.number_of_hours_temp})
                    else :
                        date_fr = datetime.strptime(date_exist_str.date, DATETIME_FORMAT)
                        date_en = datetime.strptime(date_exist_ends.date, DATETIME_FORMAT)

                        date1 = date_en - date_fr
                        diff_day1 = (float(date1.seconds) / 3600) - self.break_hour
                        if diff_day1-int(diff_day1) >= 0.75 :
                            detail.write({'ovt_hour':round(diff_day1)})
                        else :
                            detail.write({'ovt_hour':int(diff_day1)})
            elif self.lembur_awal == True :
                date_str = str(datetime.strptime(self.date_from, DATETIME_FORMAT)-timedelta(hours=3)) 
                date_exist = self.env['hr.attendance.finger'].search([('date','>=',date_str),('date','<=',self.date_to),('absen_id','=',detail.employee_id.absen_id)],limit=1, order='date desc')
                if date_exist.date <= self.date_from :
                    detail.write({'ovt_hour':self.number_of_hours_temp})
                else :
                    date_fr = datetime.strptime(date_exist.date, DATETIME_FORMAT)
                    date_en = datetime.strptime(self.date_to, DATETIME_FORMAT)

                    date1 = date_en - date_fr
                    diff_day1 = (float(date1.seconds) / 3600) - self.break_hour
                    if diff_day1-int(diff_day1) >= 0.75 :
                        detail.write({'ovt_hour':round(diff_day1)})
                    else :
                        detail.write({'ovt_hour':int(diff_day1)})
            elif self.lembur_awal == False :
                date_ends = str(datetime.strptime(self.date_to, DATETIME_FORMAT)+timedelta(hours=3)) 
                date_exist = self.env['hr.attendance.finger'].search([('date','>=',self.date_from),('date','<=',date_ends),('absen_id','=',detail.employee_id.absen_id)],limit=1, order='date desc')
                if date_exist.date >= self.date_to :
                    detail.write({'ovt_hour':self.number_of_hours_temp})
                else :
                    date_fr = datetime.strptime(self.date_from, DATETIME_FORMAT)
                    date_en = datetime.strptime(date_exist.date, DATETIME_FORMAT)

                    date1 = date_en - date_fr
                    diff_day1 = (float(date1.seconds) / 3600) - self.break_hour
                    if diff_day1-int(diff_day1) >= 0.75 :
                        detail.write({'ovt_hour':round(diff_day1)})
                    else :
                        detail.write({'ovt_hour':int(diff_day1)})

        return True 

    def cron_overtime(self):
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"        
        date_now =  str((datetime.now()+timedelta(hours=7))-timedelta(days=1))[:10]
        date_start = str(datetime.strptime(date_now+' 00:00:00',DATETIME_FORMAT)-timedelta(hours=7))
        date_end = str(datetime.strptime(date_now+' 23:59:59',DATETIME_FORMAT)-timedelta(hours=7))
        overtime = self.env['hr.overtime'].search([('state','=','validate'),('date_from','>=',date_start),('date_to','<=',date_end)])
        for overt in overtime :

            #date_start = str(fields.Datetime.from_string(overt.date_from)-timedelta(hours=3))
            #date_end = str(fields.Datetime.from_string(overt.date_to)+timedelta(hours=3))

            for detail in overt.employee_ids :
                #import pdb;pdb.set_trace()
                if overt.hari_libur == True :
                    date_str1 = str(datetime.strptime(overt.date_from, DATETIME_FORMAT)-timedelta(hours=3))
                    date_str2 = str(datetime.strptime(overt.date_from, DATETIME_FORMAT)+timedelta(hours=3)) 
                    date_ends1 = str(datetime.strptime(overt.date_to, DATETIME_FORMAT)-timedelta(hours=3))
                    date_ends2 = str(datetime.strptime(overt.date_to, DATETIME_FORMAT)+timedelta(hours=3))
                    date_exist_str = self.env['hr.attendance.finger'].search([('date','>=',date_str1),('date','<=',date_str2),('absen_id','=',detail.employee_id.absen_id)], limit=1,order='date desc')
                    date_exist_ends = self.env['hr.attendance.finger'].search([('date','>=',date_ends1),('date','<=',date_ends2),('absen_id','=',detail.employee_id.absen_id)], limit=1,order='date desc')
                    if date_exist_str <= overt.date_from and date_exist_ends >= overt.date_from :
                        detail.write({'ovt_hour':overt.number_of_hours_temp})
                    else :
                        date_fr = datetime.strptime(date_exist_str, DATETIME_FORMAT)
                        date_en = datetime.strptime(date_exist_ends, DATETIME_FORMAT)

                        date1 = date_en - date_fr
                        diff_day1 = (float(date1.second) / 3600) - overt.break_hour
                        if diff_day1-int(diff_day1) >= 0.75 :
                            detail.write({'ovt_hour':round(diff_day1)})
                        else :
                            detail.write({'ovt_hour':int(diff_day1)})
                elif overt.lembur_awal == True :
                    date_str = str(datetime.strptime(overt.date_from, DATETIME_FORMAT)-timedelta(hours=3)) 
                    date_exist = self.env['hr.attendance.finger'].search([('date','>=',date_str),('date','<=',overt.date_to),('absen_id','=',detail.employee_id.absen_id)],limit=1, order='date desc')
                    if date_exist.date <= overt.date_from :
                        detail.write({'ovt_hour':overt.number_of_hours_temp})
                    else :
                        date_fr = datetime.strptime(date_exist.date, DATETIME_FORMAT)
                        date_en = datetime.strptime(overt.date_to, DATETIME_FORMAT)

                        date1 = date_en - date_fr
                        diff_day1 = (float(date1.seconds) / 3600) - overt.break_hour
                        if diff_day1-int(diff_day1) >= 0.75 :
                            detail.write({'ovt_hour':round(diff_day1)})
                        else :
                            detail.write({'ovt_hour':int(diff_day1)})               
                elif overt.lembur_awal == False :
                    date_ends = str(datetime.strptime(overt.date_to, DATETIME_FORMAT)+timedelta(hours=3)) 
                    date_exist = self.env['hr.attendance.finger'].search([('date','>=',overt.date_from),('date','<=',date_ends),('absen_id','=',detail.employee_id.absen_id)],limit=1, order='date desc')
                    if date_exist.date >= overt.date_to :
                        detail.write({'ovt_hour':overt.number_of_hours_temp})
                    else :
                        date_fr = datetime.strptime(overt.date_from, DATETIME_FORMAT)
                        date_en = datetime.strptime(date_exist.date, DATETIME_FORMAT)

                        date1 = date_en - date_fr
                        diff_day1 = (float(date1.seconds) / 3600) - overt.break_hour
                        if diff_day1-int(diff_day1) >= 0.75 :
                            detail.write({'ovt_hour':round(diff_day1)})
                        else :
                            detail.write({'ovt_hour':int(diff_day1)})

        return True
            

    name                = fields.Char("Description", required=True, readonly=True, states={"draft":[("readonly",False)]}, size=64)
    state               = fields.Selection(string="State",
                                            selection=SESSION_STATES,
                                            required=True,
                                            readonly=True,
                                            default=SESSION_STATES[0][0], track_visibility='onchange')


    schedule_id         = fields.Many2one(comodel_name='resource.calendar',
                                                string='Schedule', readonly=True, states={"draft":[("readonly",False)]}, track_visibility='onchange')
    user_id             = fields.Many2one("res.users", "Creator", default=lambda self: self.env.user,readonly=True)
    date_from           = fields.Datetime("Start Date", readonly=True, states={"draft":[("readonly",False)]},default=lambda self: self._context.get("date", fields.Date.context_today(self)) , track_visibility='onchange')
    date_to             = fields.Datetime("End Date", readonly=True, states={"draft":[("readonly",False)]},default=lambda self: self._context.get("date", fields.Date.context_today(self)) , track_visibility='onchange')
    notes               = fields.Text("Notes", readonly=True, states={"draft":[("readonly",False)]})
    number_of_hours_temp= fields.Float("Overtime Hours", default=1, readonly=True, states={"draft":[("readonly",False)]}, track_visibility='onchange')
    hari_libur          = fields.Boolean("Day Off?", readonly=True, states={"draft":[("readonly",False)]},help="Tanggal merah kalender", track_visibility='onchange')
    catering             = fields.Boolean("Catering?", readonly=True, states={"draft":[("readonly",False)]},help="Jika dicentang otomatis form catering akan dibuat", track_visibility='onchange')
    number_of_days_temp = fields.Float("Overtime Days", readonly=True, states={"draft":[("readonly",False)]}, track_visibility='onchange')
    department_id       = fields.Many2one("hr.department", "Department", readonly=True, default=lambda self: self._get_default_department())
    type_id             = fields.Many2one("hr.overtime.hour", "Overtime Type", required=True, readonly=True, states={"draft":[("readonly",False)]}, track_visibility='onchange')
    date                = fields.Date("Date", default=lambda self: self._context.get("date", fields.Date.context_today(self)))
    break_hour          = fields.Float("Break Hours", readonly=True, states={"draft":[("readonly",False)]}, track_visibility='onchange')
    month               = fields.Char("Month", default=lambda *a: time.strftime("%Y-%m"))
    nominal             = fields.Integer("Nominal")
    employee_ids        = fields.One2many("hr.overtime.employee", "overtime_id", "Employee's", readonly=True, states={"draft":[("readonly",False)]},copy=False,)# default=_default_employees)
    manager_id          = fields.Many2one("hr.employee","Manager", store=True)
    tgl_lembur          = fields.Date(string="Tanggal lembur")
    employee_count = fields.Integer(compute='_compute_employee', string="Total Employee")
    lembur_awal         = fields.Boolean("Lembur Awal")

    def _compute_employee(self):
        emp_count = self.env['hr.overtime.employee'].sudo().search([('overtime_id','=',self.id)])
        self.employee_count = len(emp_count)


    _sql_constraints = [
        ("date_check", "CHECK ( number_of_hours_temp > 0 )", "The number of hours must be greater than 0 !"),
        ("date_check2", "CHECK (date_from < date_to)", "The start date must be before the end date !")
    ]

    @api.model
    def _get_default_department(self):
        employee = self.env['hr.employee']
        employee_det = employee.sudo().search([('user_id','=',self.env.user.id)])
        return employee_det.department_id

    # TODO: can be improved using resource calendar method
    def _get_number_of_hours(self, date_from, date_to, istirahat):
        """Returns a float equals to the timedelta between two dates given as string."""

        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        from_dt = datetime.strptime(date_from, DATETIME_FORMAT)
        to_dt = datetime.strptime(date_to, DATETIME_FORMAT)
        timedelta = to_dt - from_dt
        diff_day =(float(timedelta.seconds) / 3600) - istirahat
        return diff_day

    def _get_number_of_days(self, date_from, date_to):
        """Returns a float equals to the timedelta between two dates given as string."""

        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        from_dt = datetime.strptime(date_from, DATETIME_FORMAT)
        to_dt = datetime.strptime(date_to, DATETIME_FORMAT)
        timedelta = to_dt - from_dt
        diff_days = timedelta.days + float(timedelta.seconds) / 86400
        return diff_days

    # def unlink(self):
    #     for rec in self:
    #         if rec.state <> "draft":
    #             raise UserError(_("Warning!"),_("You cannot delete a overtime which is not in draft state !"))
    #     return super(hr_overtime, self).unlink(ids, context)

    @api.onchange('date_to','date_from','break_hour')
    def _get_number_of_hours(self):
        """Returns an overtime hours."""
        if self.date_to:
            DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
            from_dt = datetime.strptime(self.date_from, DATETIME_FORMAT)
            to_dt = datetime.strptime(self.date_to, DATETIME_FORMAT)
            timedelta = to_dt - from_dt
            diff_day =(float(timedelta.seconds) / 3600) - self.break_hour
            self.number_of_hours_temp = diff_day


    @api.onchange('date_from')
    def _calc_date(self):
        if self.date_from:
            DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
            date_field1 = datetime.strptime(self.date_from, DATETIME_FORMAT)
            self.tgl_lembur = date_field1 + timedelta(hours=7)
            employee = self.env['hr.employee']
            contract = self.env['hr.contract']
            contract_shift = self.env['hr.contract.detail']
            schedule = False
            dates = self.date_from[:10]
            employee_exist = employee.sudo().search([('user_id','=',self.user_id.id)],limit=1)
            if not employee_exist:
                raise UserError(_('Data employee %s belum ada !') % (self.user_id.name))
            contract_exist = contract.sudo().search([('employee_id','=',employee_exist.id),
                                                        ('date_start','<=',dates),('date_end','>=',dates),
                                                        ('shift_working_schedule','=',False),
                                                        ('working_hours','!=',False)],
                                                        limit=1, order='id desc')
            if contract_exist  :
                schedule = contract_exist.working_hours
            else :
                contract_exist =  contract_shift.sudo().search([('contract_id.employee_id','=',employee_exist.id),
                                                        ('start_date','<=',dates),('end_date','>=',dates),
                                                        ('contract_id.shift_working_schedule','=',True)],
                                                        limit=1, order='id desc')
                if contract_exist :
                    schedule = contract_exist.schedule_id
            if schedule :
                self.schedule_id = schedule.id
            self.department_id = employee_exist.department_id.id
        return {}

    @api.onchange('type_id')
    def onchange_type_id(self):
        if self.type_id.special:
            self.hari_libur = True
        else :
            self.hari_libur = False

    # @api.depends('date_from')
    # def _calc_date(self):
    #     for date in self:
    #         DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    #         date_field1 = datetime.strptime(date.date_from, DATETIME_FORMAT)

    #         date.tgl_lembur = date_field1 + timedelta(hours=7)
    #     return {}


    #action for state / workflow
    @api.multi
    def action_draft(self):
        self.state = SESSION_STATES[0][0]
    @api.multi
    def action_confirm_admin(self):
        if not self.employee_ids:
            raise UserError(_('Data employee harus diisi !'))
        self.state = SESSION_STATES[1][0]
    @api.multi
    def action_confirm_manager(self):
        self.state = SESSION_STATES[2][0]
    @api.multi
    def action_refuse(self):
        self.state = SESSION_STATES[3][0]
    @api.multi
    def action_cancel(self):
        self.state = SESSION_STATES[5][0]
    @api.multi
    def action_validate(self):
        #import pdb;pdb.set_trace()
        self.ensure_one()
        employee = self.env['hr.employee']
        catering = self.env['hr.catering']
        catering_detail = self.env['hr.catering.detail']
        catering_exist = catering.sudo().search([('overtime_id','=',self.id),('state','=','draft')],limit=1)
        #import pdb;pdb.set_trace()
        if self.catering == True :
            if catering_exist :
                for emp in self.employee_ids :
                    employee_cat_exist = catering_detail.sudo().search([('catering_id','=',catering_exist.id),
                                                                        ('employee_id','=',emp.employee_id.id)])
                    if not employee_cat_exist :
                        catering_detail.create({'catering_id'   : catering_exist.id,
                                                'employee_id'   : emp.employee_id.id})
            else :
                employee_cat_exist = True
                catering_exist_approved = catering.sudo().search([('overtime_id','=',self.id),('state','!=','draft')],limit=1)
                # create form catering baru
                lines = []
                for emp in self.employee_ids :
                    if not catering_exist_approved :
                        lines.append((0,0,{'employee_id'    : emp.employee_id.id,
                                                'schedule_id'   : emp.schedule_id.id}))
                    else :
                        employee_cat_exist = catering_detail.sudo().search([('catering_id','=',catering_exist_approved.id),
                                                                        ('employee_id','=',emp.employee_id.id)])
                        if not employee_cat_exist :
                            lines.append((0,0,{'employee_id'    : emp.employee_id.id,
                                                'schedule_id'   : emp.schedule_id.id}))


                employee_exist = employee.sudo().search([('user_id','=',self.user_id.id)],limit=1)
                if not employee_exist:
                    raise UserError(_('Data employee %s belum ada !') % (self.user_id.name))
                if not catering_exist_approved or not employee_cat_exist:
                    catering.sudo().create({'employee_id'   : employee_exist.id,
                                            'state'         : 'draft',
                                            'schedule_id'   : self.schedule_id.id,
                                            'employee_ids'  : lines,
                                            'overtime_id'   : self.id,
                                            'notes'         : "Created from Overtime: "+self.name})
        self.state = SESSION_STATES[4][0]

    @api.one
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        raise UserError(_('Data tidak bisa di duplikasi !'))
        return super(hr_overtime, self).copy(default=default)


    @api.multi
    def unlink(self):
        for i in self:
            if i.state != 'draft' :
                raise UserError(_('Data yang bisa dihapus hanya yg berstatus draft'))
        return super(hr_overtime, self).unlink()

hr_overtime()



class hr_overtime_employee(models.Model) :
    _name = "hr.overtime.employee"
    _inherit = ['ir.needaction_mixin']
    _description = "Detail Employee"


    @api.depends('employee_id','ovt_hour')
    def _hitung_lembur(self):
        for obj in self:
            jam = float(obj.ovt_hour)
            if not obj.overtime_id.type_id.special :
                overtime_type = obj.overtime_id.type_id.hour_ids
                x = 0
                tot = 0
                # sisa = jam
                for over in overtime_type :
                    if jam > 0:
                        sampai = float(over.to_hour)
                        dari = float(over.from_hour)
                        if sampai == 0.0 :
                            sampai = float(1000)
                        if dari != 0.0 :
                            if dari == 1 :
                                i = sampai
                            if dari > 1  :
                                i = sampai - dari
                                if i == 0 :
                                    i = 1

                            if jam >= i :
                                tot = i * over.calculation
                            elif jam < i :
                                tot = jam * over.calculation
                            jam = jam - i
                            x = x + tot

                obj.total_jam = round(x,2)
            #obj.write({"total_jam1":round(x,2)})



    overtime_id         = fields.Many2one("hr.overtime", "overtime_id", ondelete="cascade")
    employee_id         = fields.Many2one("hr.employee", "Employee", required=True, track_visibility='onchange')
    ovt_hour            = fields.Float("Real Overtime Hours")
    total_jam           = fields.Float(compute="_hitung_lembur",store=True, readonly=True,string="Total Overtime Hours")
    department_id       = fields.Many2one("hr.department", "Department", related="overtime_id.department_id", store=True)
    type_id             = fields.Many2one("hr.overtime.hour", "Overtime Type", related="overtime_id.type_id", store=True)
    date                = fields.Date("Date", related="overtime_id.date", store=True)
    month               = fields.Char("Month", related="overtime_id.month", store=True)
    schedule_id         = fields.Many2one(comodel_name='resource.calendar', string='Schedule', related="overtime_id.schedule_id", store=True)
    state               = fields.Selection(string="State",
                                            selection=SESSION_STATES,
                                            required=True,
                                            readonly=True,
                                            default=SESSION_STATES[0][0],related="overtime_id.state",store=True)
    #total_jam1  = fields.Float("Total Overtime Hours (Store DB)")


class overtime_hour(models.Model):
    _name = "hr.overtime.hour"
    _description = "Pengali jam lembur"


    name = fields.Char("Name", required=True)
    special = fields.Boolean("Special", help="Jika dicentang maka Lembur tidak dihitung/dibayar")
    hour_ids = fields.One2many("hr.overtime.hour.detail","hour_type", "Hours")

overtime_hour()


class overtime_hour_detail(models.Model):
    _name = "hr.overtime.hour.detail"


    from_hour = fields.Selection([("1","Jam 1"),("2","Jam 2"),("3","Jam 3"),("4","Jam 4"),("5","Jam 5"),("6","Jam 6"),("7","Jam 7"),
            ("8","Jam 8"),("9","Jam 9"),("10","Jam 10"),("11","Jam 11"),("12","Jam 12"),("13","Jam 13"),("14","Jam 14"),("15","Jam 15"),
            ("16","Jam 16"),("17","Jam 17"),("18","Jam 18"),("19","Jam 19"),("20","Jam 20"),("21","Jam 21"),("22","Jam 22"),("23","Jam 23"),("24","Jam 24")], string="Start Hour", required=True)
    to_hour = fields.Selection([("1","Jam 1"),("2","Jam 2"),("3","Jam 3"),("4","Jam 4"),("5","Jam 5"),("6","Jam 6"),("7","Jam 7"),
            ("8","Jam 8"),("9","Jam 9"),("10","Jam 10"),("11","Jam 11"),("12","Jam 12"),("13","Jam 13"),("14","Jam 14"),("15","Jam 15"),
            ("16","Jam 16"),("17","Jam 17"),("18","Jam 18"),("19","Jam 19"),("20","Jam 20"),("21","Jam 21"),("22","Jam 22"),("23","Jam 23"),("24","Jam 24")], string="End Hour", required=True)
    calculation = fields.Float("Calculation" , required=True)
    hour_type = fields.Many2one("hr.overtime.hour","Overtime Type")

overtime_hour_detail()