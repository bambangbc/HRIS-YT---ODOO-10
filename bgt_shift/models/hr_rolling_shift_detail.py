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

class Hr_rolling_shift_detail(models.Model):
    _name = 'hr.rolling.shift.detail'
    _rec_name = 'employee_id'

    # @api.depends('employee_id')
    # def _compute_rolling_shift_exist(self):
    #     if self :
    #         for employee in self:
    #             if employee.rolling_shift_id and employee.rolling_shift_id.date_start and employee.rolling_shift_id.date_end and employee.rolling_shift_id.employee_id:
    #                 shift_exist = self.search([('rolling_shift_id.date_start','>=',employee.rolling_shift_id.date_start),
    #                                                 ('rolling_shift_id.date_end','<=',employee.rolling_shift_id.date_end),
    #                                                 ('employee_id','=',employee.employee_id.id),
    #                                                 ('rolling_shift_id','!=',employee.rolling_shift_id.id)],limit=1)
    #                 if shift_exist :
    #                     employee.rolling_shift_exist_id = shift_exist.rolling_shift_id.id

    rolling_shift_id = fields.Many2one(comodel_name='hr.rolling.shift', string='Rolling Shift')
    employee_id		 = fields.Many2one(comodel_name='hr.employee', string='Employee')
    nik              = fields.Char(string="NIK",related="employee_id.nik")
    job              = fields.Char(string='Job Title')
    department       = fields.Char(string='Department')
    rolling_shift_exist_id = fields.Many2one('hr.rolling.shift', 'Shift Existing',)# compute='_compute_rolling_shift_exist', store=True)
    date_start = fields.Date('Date Start')
    date_end = fields.Date('Date End')
    state = fields.Char('State')
    schedule_id = fields.Many2one(comodel_name="resource.calendar", string="Shift", copy=False,
                                                   track_visibility='onchange')

    @api.onchange('employee_id')
    def _get_employee(self):
        employee = self.employee_id
        if employee:
        	for e in employee:
        		self.nik = e.nik
        		self.job = e.job_id.name
        		self.department = e.department_id.name

Hr_rolling_shift_detail()