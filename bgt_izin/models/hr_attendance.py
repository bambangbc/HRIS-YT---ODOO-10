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
    def _compute_izin(self):
        for attendance in self:
            check_in = datetime.strptime(attendance.check_in,'%Y-%m-%d %H:%M:%S')
            # kasih gap 4 jam kebelakang untuk search
            check_in4 = check_in-timedelta(hours=4)
            # kasih gap 8 jam kedepan untuk search
            check_in8 = check_in+timedelta(hours=8)
            terlambat_exist = self.env['hr.izin'].sudo().search([('employee_id','=',attendance.employee_id.id),
                                                                ('date_late','>',str(check_in4)),
                                                                ('date_late','<',str(check_in8)),
                                                                ('state','=','approved'),
                                                                ('type','=','terlambat')]
                                                                ,order="date_late asc", limit=1)
            if terlambat_exist :
                attendance.terlambat = 1.0

            if attendance.check_out :
                check_out = datetime.strptime(attendance.check_out,'%Y-%m-%d %H:%M:%S')
                # kasih gap 4 jam kedepan untuk search
                check_out4 = check_out+timedelta(hours=4)
                # kasih gap 8 jam kebelakang untuk search
                check_out8 = check_out-timedelta(hours=8)
                pulang_cepat_exist = self.env['hr.izin'].sudo().search([('employee_id','=',attendance.employee_id.id),
                                                                ('date_late','<',str(check_out4)),
                                                                ('date_late','>',str(check_out8)),
                                                                ('state','=','approved'),
                                                                ('type','=','pulang_cepat')]
                                                                ,order="date_late desc", limit=1)
                if pulang_cepat_exist :
                    attendance.pulang_cepat = 1.0

    terlambat = fields.Float("Terlambat", compute='_compute_izin', store=True)
    pulang_cepat = fields.Float("Pulang Cepat", compute='_compute_izin', store=True)

HRAttendance()
