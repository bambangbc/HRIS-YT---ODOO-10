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

from odoo import api, fields, models, tools, _, SUPERUSER_ID

class HRPayrollReport2(models.Model):
    _name = "hr.payroll.report2"

    sequence = fields.Integer("Sequence")
    name = fields.Char("Division")
    department_id = fields.Many2one(comodel_name="hr.department", string="Department")
    contract_type_id = fields.Many2one("hr.contract.type",string="Contract Type")
    level_id = fields.Many2one("hr.job.level",string="Job Level")
    date_to = fields.Date(string='Date')
    lembur = fields.Float("Lembur")
    tunjangan = fields.Float("Tunjangan")
    upah = fields.Float("Upah")
    total = fields.Float("Total")
    bank = fields.Many2one("res.bank", "Payment Methode")

HRPayrollReport2()