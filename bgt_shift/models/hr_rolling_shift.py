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


class Hr_rolling_shift(models.Model):
    _name = 'hr.rolling.shift'
    _description = 'Rolling Shift'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _rec_name = 'code'
    _order = "code desc"

    @api.multi
    @api.depends('code', 'shift_berjalan')
    def name_get(self):
        result = []
        for i in self:
            name = i.code
            if i.shift_berjalan :
                name = name +' ('+i.shift_berjalan.name+')'
            result.append((i.id, name))
        return result

    @api.model
    def unlink(self):
        self.env["hr.rolling.shift.detail"].search([('rolling_shift_id','=',self.id)]).unlink()
        res = super(Hr_rolling_shift, self).unlink()

    @api.model
    def create(self, vals):
        if not vals.get('code', False) or vals['code'] == 'New':
            vals['code'] = self.env['ir.sequence'].next_by_code('hr.rolling.shift') or 'Number not found !'
        return super(Hr_rolling_shift, self).create(vals)

    @api.multi
    def unlink(self):
        for i in self:
            if i.state != 'draft' :
                raise UserError(_('Data yang bisa dihapus hanya yg berstatus draft'))
        return super(Hr_rolling_shift, self).unlink()

    def _default_employee(self):
        return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    # def _default_employees(self):
    #
    #     employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
    #     employee_ids = self.env['hr.employee'].search(
    #         [('department_id', '=', employee_id.department_id.id)])
    #     if employee_ids:
    #         emp_ids = []
    #         for emp in employee_ids :
    #             emp_ids.append((0, 0, {'employee_id' : emp.id}))
    #         return emp_ids

    @api.onchange('shift_berjalan','date_start','date_end')
    def onchange_date_end(self):
        if self.shift_berjalan and self.date_start and self.date_end:
            employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
            employee_ids = self.env['hr.employee'].search(
                [('department_id', '=', self.department_id.id)])
            if employee_ids:
                emp_ids = []
                for emp in employee_ids :
                    rolling_shift_exist_id = False
                    shift_exist = self.env['hr.rolling.shift.detail'].search([('rolling_shift_id.date_start','>=',self.date_start),
                                                    ('rolling_shift_id.date_end','<=',self.date_end),
                                                    ('employee_id','=',emp.id)],limit=1)
                    if shift_exist :
                        rolling_shift_exist_id = shift_exist.rolling_shift_id.id
                    emp_ids.append((0, 0, {'employee_id' : emp.id, 'rolling_shift_exist_id' : rolling_shift_exist_id}))
                self.rolling_shift_detail_ids = emp_ids


    user_id                      = fields.Many2one("res.users", string="User", default=lambda self: self.env.user)
    date                         = fields.Datetime("Created Date",default=lambda self:time.strftime("%Y-%m-%d %H:%M:%S"))
    employee_id                  = fields.Many2one("hr.employee","Employee", copy=False, default=_default_employee,
                                                   required=True, track_visibility='onchange', readonly=True,
                                                   states={'draft': [('readonly', False)]})
    department_id                = fields.Many2one("hr.department","Department", related="employee_id.department_id", store=True)

    code                         = fields.Char(string="Code", default="New", copy=False)
    shift_berjalan               = fields.Many2one(comodel_name="resource.calendar", string="Shift", copy=False,
                                                   track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})
    schedule_1                   = fields.Many2one(comodel_name="resource.calendar", string="Schedule 1", copy=False)
    schedule_2                   = fields.Many2one(comodel_name="resource.calendar", string="Schedule 2", copy=False)
    schedule_3                   = fields.Many2one(comodel_name="resource.calendar", string="Schedule 3", copy=False)
    active                       = fields.Boolean(string="Active",default=True)
    rolling_shift_detail_ids     = fields.One2many(comodel_name="hr.rolling.shift.detail", inverse_name="rolling_shift_id",
                                                   string="Employee", readonly=True, states={'draft': [('readonly', False)]},)# default=_default_employees)
    state                        = fields.Selection([('draft','Draft'),('waiting','Waiting Confirm'),('confirmed','Confirmed'),('done','Done'),('cancel','Cancelled')], default="draft",string="State", track_visibility='onchange')
    notes                        = fields.Text("Notes", copy=False)
    date_start                   = fields.Date("Date Start", copy=False, track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})
    date_end                     = fields.Date("Date End", copy=False, track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})
    employee_count = fields.Integer(compute='_compute_employee', string="Total Employee")

    def _compute_employee(self):
        emp_count = self.env['hr.rolling.shift.detail'].sudo().search([('rolling_shift_id','=',self.id)])
        self.employee_count = len(emp_count)

    @api.multi
    def button_send_to_confirm(self):
        for i in self:
            if not i.rolling_shift_detail_ids :
                raise UserError(_('Data karyawan tidak boleh kosong'))
            i.write({'state':'waiting'})
            for detail in i.rolling_shift_detail_ids :
                detail.write({'state':'waiting','schedule_id':i.shift_berjalan.id,'date_start':i.date_start,'date_end':i.date_end})
        return True

    @api.multi
    def button_confirm(self):
        for i in self:
            i.write({'state':'confirmed'})
            for detail in i.rolling_shift_detail_ids :
                detail.write({'state':'confirmed','schedule_id':i.shift_berjalan.id,'date_start':i.date_start,'date_end':i.date_end})
        return True

    @api.multi
    def button_cancel(self):
        for i in self:
            i.write({'state':'cancel'})
            for detail in i.rolling_shift_detail_ids :
                detail.write({'state':'cancel','schedule_id':i.shift_berjalan.id,'date_start':i.date_start,'date_end':i.date_end})
        return True

    @api.multi
    def button_set_to_draft(self):
        for i in self:
            i.write({'state':'draft'})
            for detail in i.rolling_shift_detail_ids :
                detail.write({'state':'draft','schedule_id':i.shift_berjalan.id,'date_start':i.date_start,'date_end':i.date_end})
        return True

    @api.multi
    def button_validate(self):
        contract_obj = self.env['hr.contract']
        contract_detail_obj = self.env['hr.contract.detail']
        for i in self.rolling_shift_detail_ids:
            #date_start = self.date_start
            #date_end = self.date_end

            #contract = contract_obj.search([('shift_working_schedule','=',True),
            #                                            ('employee_id','=',i.employee_id.id),
            #                                            ('state','!=','close')])
            #if contract:
            #    for c in contract:
                    # search dulu jika rolling shift ini sdh pernah di add atas employee yg sama maka bypass
            #        rolling_exist = contract_detail_obj.search([('rolling_id','=',self.id),('contract_id','=',contract.id)])
            #        if not rolling_exist :
            #            data = {
            #                'schedule_id'   : self.shift_berjalan.id,
            #                'contract_id'   : c.id,
            #                'start_date'    : date_start,
            #                'end_date'      : date_end,
            #                'rolling_id'    : self.id
            #                }
            #            contract_detail_obj.create(data)
            i.write({'state':'done','schedule_id':self.shift_berjalan.id,'date_start':self.date_start,'date_end':self.date_end})
        self.write({'state':'done'})
        return True

    # def cron_rolling_shift(self):
    #     for e in self.env['hr.rolling.shift'].search([('shift_berjalan','!=',False),('active','=',True)]):
    #         if e.shift_berjalan == e.schedule_1:
    #             e.shift_berjalan = e.schedule_2
    #         elif e.shift_berjalan == e.schedule_3:
    #             e.shift_berjalan = e.schedule_1
    #         elif e.shift_berjalan == e.schedule_2:
    #             if e.schedule_3:
    #                 e.shift_berjalan = e.schedule_3
    #             else:
    #                 e.shift_berjalan = e.schedule_1

    #         for i in e.rolling_shift_detail_ids:
    #             date_now = datetime.now().strftime("%Y-%m-%d")
    #             date_start = datetime.now() + timedelta(days=1)
    #             date_end = datetime.now() + timedelta(days=7)

    #             contract = self.env['hr.contract'].search([('employee_id','=',i.employee_id.id),('date_start','<',date_now),'|',('date_end','>',date_now),('date_end','=',False)])
    #             if contract:
    #                 for c in contract:
    #                     data = {
    #                         'schedule_id':e.shift_berjalan.id,
    #                         'contract_id':c.id,
    #                         'start_date':date_start.strftime("%Y-%m-%d"),
    #                         'end_date':date_end.strftime("%Y-%m-%d"),
    #                     }
    #                     self.env['hr.contract.detail'].create(data)