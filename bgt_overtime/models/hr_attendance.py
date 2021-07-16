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
import dateutil.parser


class HRAttendance(models.Model):
    _inherit = 'hr.attendance'

    overtime = fields.Float("Overtime")
 
    @api.model
    def create(self, vals):
        if 'check_out' in vals :
            # check overtime
            DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
            if vals['check_out'] :
                # import pdb;pdb.set_trace()
                # check_out = datetime.strptime(str(vals['check_out']), DATETIME_FORMAT)
                # check_out = dateutil.parser.parse(str(vals['check_out'])).date()
                # sign_in = dateutil.parser.parse(str(vals['check_in'])).date()
                check_out = datetime.strptime(vals['check_out'], DATETIME_FORMAT)
                sign_in = datetime.strptime(vals['check_in'], DATETIME_FORMAT)
                state = 'validate'
                emp_over = self.env['hr.overtime.employee'].search([('employee_id','=',vals['employee_id']),
                                                                    ('overtime_id.tgl_lembur','=',sign_in),
                                                                    ('overtime_id.state','=',state)])
                if emp_over:
                    if emp_over.overtime_id.catering :
                        vals['catering'] = True
                    lembur = 0
                    for eo in emp_over:
                        start_ovt = datetime.strptime(eo.overtime_id.date_from, DATETIME_FORMAT)
                        end_ovt = datetime.strptime(eo.overtime_id.date_to, DATETIME_FORMAT)
                        if check_out > start_ovt and check_out <= end_ovt:
                            selisih = check_out - start_ovt 
                            lembur = (float(selisih.seconds) / 3600)
                        elif check_out > end_ovt :
                            lembur = eo.overtime_id.number_of_hours_temp
                        eo.write({"ovt_hour":round(lembur,2)})
                        vals['overtime'] = round(lembur,2)
        return super(HRAttendance, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'check_out' in vals :
            # check overtime
            DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
            if vals['check_out'] :
                check_out = datetime.strptime(vals['check_out'], DATETIME_FORMAT)
                sign_in = datetime.strptime(self.check_in, DATETIME_FORMAT)
                state = 'validate'
                emp_over = self.env['hr.overtime.employee'].sudo().search([('employee_id','=',self.employee_id.id),
                                                                    ('overtime_id.tgl_lembur','=',sign_in),
                                                                    ('overtime_id.state','=',state)])
                if emp_over:
                    if emp_over.overtime_id.catering :
                        vals['catering'] = True
                    lembur = 0
                    for eo in emp_over:
                        start_ovt = datetime.strptime(eo.overtime_id.date_from, DATETIME_FORMAT)
                        end_ovt = datetime.strptime(eo.overtime_id.date_to, DATETIME_FORMAT)
                        if check_out > start_ovt and check_out <= end_ovt:
                            selisih = check_out - start_ovt 
                            lembur = (float(selisih.seconds) / 3600)
                        elif check_out > end_ovt :
                            lembur = eo.overtime_id.number_of_hours_temp
                        eo.write({"ovt_hour":round(lembur,2)})
                        vals['overtime'] = round(lembur,2)
        return super(HRAttendance, self).write(vals)

HRAttendance()