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

class Hr_resource_calendar(models.Model):
    _name = 'resource.calendar'
    _inherit = 'resource.calendar'

    shift_type     = fields.Selection([('shift pagi', 'Shift Pagi'), 
                                    ('shift siang', 'Shift Siang'), 
                                    ('shift malam', 'Shift Malam'),],string='Shift Type')
    contract_detail_ids	 		 = fields.One2many(comodel_name="hr.contract.detail", inverse_name="schedule_id", string="contract")