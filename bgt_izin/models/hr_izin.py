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


class HRIzin(models.Model):
    _name = "hr.izin"
    _description = "Pengelolaan Izin karyawan"
    _order = "name desc"
    _inherit = ['mail.thread', 'ir.needaction_mixin']


    name = fields.Char("Number", size=25, default="New", copy=False)
    user_id = fields.Many2one("res.users", string="User", default=lambda self: self.env.user)
    date = fields.Datetime("Created Date",default=lambda self:time.strftime("%Y-%m-%d %H:%M:%S"))
    employee_id = fields.Many2one("hr.employee","Employee", required=True, track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})
    nik = fields.Char("NIK", related="employee_id.nik", store=True)
    parent_id = fields.Many2one("hr.employee","Atasan", related="employee_id.parent_id", store=True)
    department_id = fields.Many2one("hr.department","Department", related="employee_id.department_id", store=True)
    job_id = fields.Many2one("hr.job","Job Title", related="employee_id.job_id", store=True)
    state = fields.Selection([('draft','Draft'),('approved','Approved'),('reject','Reject')], default="draft",string="State", track_visibility='onchange')
    notes = fields.Text("Notes", track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})
    date_late = fields.Datetime("Waktu", track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})
    type = fields.Selection([('terlambat','Terlambat'),('pulang_cepat','Pulang Cepat')], string="Type Izin")

    _sql_constraints = [
        ('unique_name', 'unique(name)', 'Nomor duplikat !'),
    ]

    @api.one
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        raise UserError(_('Data tidak bisa di duplikasi !'))
        return super(HRIzin, self).copy(default=default)


    @api.model
    def create(self,vals):
    	if not vals.get('name', False) or vals['name'] == 'New':
	       sequence = self.env['ir.sequence'].next_by_code('hr.izin') or 'Number not found !'
	       vals['name'] = sequence
        return super(HRIzin, self).create(vals)

    @api.multi
    def unlink(self):
        for i in self:
            if i.state != 'draft' :
                raise UserError(_('Data yang bisa dihapus hanya yg berstatus draft'))
        return super(HRIzin, self).unlink()

    @api.multi
    def button_approve(self):
        for i in self:
            group_id = self.env['ir.model.data'].sudo().get_object('hr', 'group_hr_manager')
            #if self._uid not in group_id.users.mapped('id') :
                # cek jika harus approve pimpinan dept
            #    if not i.department_id.manager_id :
            #        raise UserError(_('Manager untuk department %s belum di set !') % (str(i.department_id.name)))
            #    elif i.department_id.manager_id.user_id.id != i._uid :
            #        raise UserError(_('Anda tidak punya akses untuk menyetujui dokumen ini ! (Manager Dept : %s) ') % (str(i.department_id.manager_id.name)))
            data = {
                            'date'   : self.date_late,
                            'absen_id'   : self.employee_id.absen_id,
                            }
            self.env['hr.attendance.finger'].sudo().create(data)
            i.write({'state':'approved'})

        return True

    @api.multi
    def button_reject(self):
        for i in self:
            i.write({'state':'reject'})
        return True


HRIzin()