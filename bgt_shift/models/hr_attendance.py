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


class HRAttendance(models.Model):
    _inherit = 'hr.attendance'

    @api.depends('check_in', 'check_out')
    def _compute_schedule(self):
        contract = self.env['hr.contract']
        contract_shift = self.env['hr.contract.detail']
        for attendance in self:
            schedule = False
            dates = attendance.check_in[:10]
            contract_exist = contract.sudo().search([('employee_id','=',attendance.employee_id.id),
                                                        ('date_start','<=',dates),('date_end','>=',dates),
                                                        ('shift_working_schedule','=',False),
                                                        ('working_hours','!=',False)],
                                                        limit=1, order='id desc')
            if contract_exist  :
                schedule = contract_exist.working_hours
            else :
                contract_exist =  contract_shift.sudo().search([('contract_id.employee_id','=',attendance.employee_id.id),
                                                        ('start_date','<=',dates),('end_date','>=',dates),
                                                        ('contract_id.shift_working_schedule','=',True)],
                                                        limit=1, order='id desc')
                if contract_exist :
                    schedule = contract_exist.schedule_id
            if schedule :
                attendance.schedule_id = schedule.id


    schedule_id             = fields.Many2one(comodel_name='resource.calendar', 
                                                string='Schedule', 
                                                compute="_compute_schedule", 
                                                store=True)

HRAttendance()