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
import datetime

class Hr_contract_detail(models.Model):
    _name = 'hr.contract.detail'

    schedule_id 			= fields.Many2one(comodel_name='resource.calendar', string='Schedule')
    contract_id				= fields.Many2one(comodel_name='hr.contract', string='Contract')
    start_date	 			= fields.Date("Starting Date")
    end_date	 			= fields.Date("End Date")
    rolling_id				= fields.Many2one(comodel_name='hr.rolling.shift', string='Rolling Shift')

Hr_contract_detail()